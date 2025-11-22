"""
Orchestrator for managing AI agent workflows.
This module coordinates calls to the LLM and manages agent interactions.
Based on the system architecture diagram with UI -> Service -> AI Orchestrator -> Agents workflow.

LANGCHAIN UNIFIED LLM SETUP:
Now uses LangChain for unified LLM provider switching.
Switch providers via environment variable:
- LLM_PROVIDER=groq (default) - Groq Cloud API 
- LLM_PROVIDER=ollama - Local Ollama

No code changes needed to switch providers!
"""
import os
from typing import Dict, Any, List, Optional
import json
import re
import time
import uuid
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# LangChain Unified LLM Client
from AI_Slop.llm_client import UnifiedLLMClient

# Import tracing with fallback
try:
    from .tracing import AgentTracer, TracingContextManager
    TRACING_AVAILABLE = True
except ImportError:
    TRACING_AVAILABLE = False
    print("[DEBUG] Tracing not available - running without trace logging")


class Orchestrator:
    """
    Orchestrator class that manages the workflow of AI agents.
    It coordinates calls to the local LLM and handles agent communication.
    Implements the architecture: UI -> Service -> AI Orchestrator -> Agents (1,2,3) with data consistency.
    
    CURRENT SETUP: Groq Cloud API (for traveling/remote work)
    
    QUICK SETUP FOR GROQ:
    1. pip install groq
    2. Get free API key: https://console.groq.com/
    3. export GROQ_API_KEY="your-key-here"
    4. Ready to use! (6,000 requests/day free)
    
    TO SWITCH BACK TO LOCAL OLLAMA:
    - See instructions in query_llm method below
    - Make sure ollama serve is running locally
    """
    
    def __init__(self, model: str = "llama3"):
        """
        Initialize the orchestrator with unified LLM client.
        
        Args:
            model: The model name (used for backward compatibility)
        """
        self.model = model
        self.agents = []
        self.context = {}
        self.status_callback = None
        self.job_data_cache = {}  # Cache for consistent job data across agents
        self.skills_database = []  # In-memory skills storage until DB implementation
        
        # Initialize tracing
        if TRACING_AVAILABLE:
            self.tracer = AgentTracer()
        else:
            self.tracer = None
        
        # Initialize unified LLM client with LangChain
        try:
            self.llm_client = UnifiedLLMClient()
            provider_info = self.llm_client.get_provider_info()
            print(f"[ORCHESTRATOR] Using {provider_info['provider'].upper()} LLM provider")
            if not provider_info['available']:
                print(f"[ORCHESTRATOR] Warning: LLM provider not fully available - {provider_info.get('error')}")
        except Exception as e:
            print(f"[ORCHESTRATOR] LLM client initialization failed: {e}")
            self.llm_client = None
    
    def set_status_callback(self, callback):
        """Set a callback function to update status messages."""
        self.status_callback = callback
    
    def _update_status(self, message: str):
        """Update status if callback is set."""
        if self.status_callback:
            self.status_callback(message)
    
    def register_agent(self, agent):
        """
        Register an agent with the orchestrator.
        
        Args:
            agent: An agent instance to register
        """
        self.agents.append(agent)
    
    def query_llm(self, prompt: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Query the LLM using unified LangChain interface.
        
        Provider switching handled automatically via LLM_PROVIDER environment variable:
        - LLM_PROVIDER=groq (default) - Uses Groq Cloud API
        - LLM_PROVIDER=ollama - Uses local Ollama
        
        No code changes needed to switch providers!
        
        Args:
            prompt: The prompt to send to the LLM
            context: Optional context dictionary to enhance the prompt
            
        Returns:
            str: The LLM's response
        """
        if not self.llm_client:
            return "ERROR: LLM client not initialized. Please check your configuration."
        
        if context:
            # Enhance prompt with context
            context_str = self._format_context(context)
            enhanced_prompt = f"{context_str}\n\n{prompt}"
        else:
            enhanced_prompt = prompt
        
        # Single unified interface - works with both Groq and Ollama!
        return self.llm_client.query(enhanced_prompt)
    
    def _format_context(self, context: Dict[str, Any]) -> str:
        """
        Format the context dictionary into a string for the LLM.
        
        Args:
            context: Dictionary containing context information
            
        Returns:
            str: Formatted context string
        """
        context_parts = []
        for key, value in context.items():
            context_parts.append(f"{key}: {value}")
        return "Context:\n" + "\n".join(context_parts)
    
    def execute_workflow(self, job_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a complete job search and analysis workflow following the architecture diagram.
        
        Workflow: UI -> Service -> AI Orchestrator -> [Agent1, Agent2, Agent3] -> Results
        
        Args:
            job_data: Dictionary containing job position, keywords, and resume data
            
        Returns:
            Dict containing consolidated results from all agents with data consistency
        """
        self._update_status("Initializing workflow...")
        
        # Step 1: Validate and normalize input data for consistency
        normalized_data = self._normalize_input_data(job_data)
        
        # Start tracing session if available
        session = None
        session_id = str(uuid.uuid4())[:8]  # Simple session ID for tracing
        
        if self.tracer:
            session = self.tracer.start_session(
                job_position=normalized_data.get('job_position', 'Unknown'),
                job_keywords=normalized_data.get('job_keywords', '')
            )
        
        # Cache normalized data for agent consistency
        self.job_data_cache = normalized_data
        
        results = {
            "job_position": normalized_data.get("job_position"),
            "job_keywords": normalized_data.get("job_keywords"),
            "workflow_stages": {},
            "final_recommendations": {},
            "skills_extracted": [],
            "data_consistency_log": [],
            "llm_provider_info": self.get_llm_provider_info()
        }
        
        # Step 2: Execute Job Site API Integration
        raw_job_postings = self._fetch_job_postings(normalized_data)
        
        # Check if job fetching failed
        if raw_job_postings.startswith("ERROR:"):
            results["workflow_stages"]["job_fetch_error"] = raw_job_postings
            results["final_recommendations"] = {
                "summary": "Job search failed - API unavailable",
                "error": raw_job_postings,
                "next_steps": [
                    "Set up RAPIDAPI_KEY environment variable",
                    "Create JSearch client integration", 
                    "Retry job search once API is configured"
                ]
            }
            self._update_status("Workflow stopped - Job API unavailable")
            return results
        
        # Step 3: Agent 1 - Job Posting Extraction and Filtering
        self._update_status("Running Job Extraction Agent...")
        if self._has_agent_by_name("ExtractJobPostingInfo"):
            agent1_result = self._execute_agent_with_validation("ExtractJobPostingInfo", {
                **normalized_data,
                "job_postings": raw_job_postings
            }, session_id)
            results["workflow_stages"]["job_extraction"] = agent1_result
            self.context["filtered_jobs"] = agent1_result
            # Store result with proper key name for JobRankingAndAnalysisAgent
            self.context["ExtractJobPostingInfo_result"] = agent1_result
        else:
            results["workflow_stages"]["job_extraction"] = "Agent not registered"
        
        # Step 4: Agent 2 - Job Ranking and Skills Extraction (follows diagram logic)
        # Skip JobAnalysisAgent - go directly from extraction to ranking per architecture diagram
        self._update_status("Running Job Ranking Agent...")
        if self._has_agent_by_name("JobRankingAndAnalysisAgent"):
            agent3_result = self._execute_agent_with_validation("JobRankingAndAnalysisAgent", {
                **normalized_data,
                **self.context
            }, session_id)
            results["workflow_stages"]["job_ranking"] = agent3_result
            
            # Store result in context for spreadsheet export
            self.context["JobRankingAndAnalysisAgent_result"] = agent3_result
            
            # Extract skills for database storage
            extracted_skills = self._extract_skills_from_result(agent3_result)
            results["skills_extracted"] = extracted_skills
            self.skills_database.extend(extracted_skills)
        else:
            results["workflow_stages"]["job_ranking"] = "Agent not registered"
        
        # Step 5: Spreadsheet Export for Testing
        self._update_status("Exporting results to spreadsheet...")
        if self._has_agent_by_name("SpreadsheetExportAgent"):
            export_result = self._execute_agent_with_validation("SpreadsheetExportAgent", {
                **normalized_data,
                **self.context
            }, session_id)
            results["workflow_stages"]["spreadsheet_export"] = export_result
        else:
            results["workflow_stages"]["spreadsheet_export"] = "SpreadsheetExportAgent not registered"
        
        # Step 6: Data Persistence (when DB is implemented)
        # TODO: Store results in database
        # - Save job postings with metadata
        # - Store user interaction history
        # - Update skills database
        # - Cache results for future queries
        results["data_persistence_status"] = "TODO: Implement database storage"
        
        # Step 7: Generate Final Consolidated Response
        final_response = self._consolidate_agent_results(results)
        results["final_recommendations"] = final_response
        
        # Log data consistency checks
        results["data_consistency_log"] = self._validate_data_consistency()
        
        self._update_status("Workflow complete!")
        return results
    
    def process_job_application(
        self, 
        job_position: str, 
        job_keywords: str, 
        resume_content: str
    ) -> str:
        """
        Process a job application with the given information.
        
        Args:
            job_position: Comma-delimited job positions
            job_keywords: Comma-delimited keywords
            resume_content: The content of the resume
            
        Returns:
            str: AI-generated response
        """
        self._update_status("Analyzing job requirements...")
        
        # Prepare context for the LLM
        context = {
            "job_position": job_position,
            "job_keywords": job_keywords,
            "resume": resume_content[:1000]  # Limit resume length for context
        }
        
        prompt = """Based on the provided job position(s), keywords, and resume, 
please provide insights on how well the candidate matches the job requirements 
and suggest improvements."""

        self._update_status("Querying AI model...")
        result = self.query_llm(prompt, context)
        self._update_status("Analysis complete!")
        
        return result
    
    # Data Consistency and Validation Methods
    
    def _normalize_input_data(self, job_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize and validate input data to ensure consistency across agents.
        
        Args:
            job_data: Raw input data from UI
            
        Returns:
            Dict: Normalized data with consistent formatting
        """
        normalized = {}
        
        # Normalize job positions - ensure consistent comma-separated format
        positions = job_data.get("job_position", "")
        if isinstance(positions, list):
            normalized["job_position"] = ", ".join(positions)
        else:
            normalized["job_position"] = str(positions).strip()
        
        # Normalize keywords - ensure consistent comma-separated format  
        keywords = job_data.get("job_keywords", "")
        if isinstance(keywords, list):
            normalized["job_keywords"] = ", ".join(keywords)
        else:
            normalized["job_keywords"] = str(keywords).strip()
        
        # Normalize resume content
        resume = job_data.get("resume", "")
        normalized["resume"] = str(resume).strip()
        
        # Add metadata for consistency tracking
        from datetime import datetime
        normalized["processing_timestamp"] = datetime.now().isoformat()
        normalized["data_version"] = "1.0"
        
        return normalized
    
    def _has_agent_by_name(self, agent_name: str) -> bool:
        """Check if an agent with the given name is registered."""
        return any(agent.name == agent_name for agent in self.agents)
    
    def _execute_agent_with_validation(self, agent_name: str, context: Dict[str, Any], session_id: str = None) -> str:
        """
        Execute an agent with input/output validation and tracing.
        
        Args:
            agent_name: Name of the agent to execute
            context: Validated context data
            
        Returns:
            str: Agent result with consistency validation
        """
        agent = next((a for a in self.agents if a.name == agent_name), None)
        if not agent:
            return f"Agent {agent_name} not found"
        
        # Pre-execution validation
        self._validate_agent_input(agent_name, context)
        
        # Extract prompt for tracing
        prompt_preview = self._extract_agent_prompt(agent, context)
        
        # Simple trace logging
        start_time = time.time()
        success = True
        error_msg = ""
        
        try:
            # Execute agent with tracing if available
            if self.tracer and TRACING_AVAILABLE:
                with TracingContextManager(
                    tracer=self.tracer,
                    agent_name=agent_name,
                    prompt=prompt_preview,
                    context=context,
                    llm_provider=getattr(self.llm_client, 'provider', 'unknown')
                ) as trace_ctx:
                    result = agent.execute(context, self)
                    trace_ctx.set_response(result)
            else:
                result = agent.execute(context, self)
                
        except Exception as e:
            success = False
            error_msg = str(e)
            result = f"Agent execution failed: {e}"
            
        finally:
            # Log to TraceEntry model
            execution_time = int((time.time() - start_time) * 1000)
            try:
                from .models import TraceEntry
                TraceEntry.objects.create(
                    session_id=session_id,
                    agent_name=agent_name,
                    job_position=context.get('job_position', ''),
                    keywords=context.get('job_keywords', ''),
                    prompt_preview=str(prompt_preview),  # Store full prompt
                    response_preview=str(result),        # Store full response
                    content=str(prompt_preview),         # Also store full prompt in content field
                    success=success,
                    error_message=error_msg,
                    execution_time_ms=execution_time,
                    llm_provider=getattr(self.llm_client, 'provider', 'unknown'),
                    prompt_hash=str(hash(str(prompt_preview))),
                    token_count=len(str(prompt_preview).split()) + len(str(result).split())
                )
            except Exception as trace_error:
                print(f"[DEBUG] Trace logging failed: {trace_error}")
        
        # Post-execution validation
        validated_result = self._validate_agent_output(agent_name, result, context)
        
        return validated_result
    
    def _extract_agent_prompt(self, agent, context: Dict[str, Any]) -> str:
        """
        Extract the prompt that will be sent to the LLM for tracing purposes.
        """
        try:
            # Try to get prompt from agent if it has a method to build prompts
            if hasattr(agent, '_build_prompt'):
                return agent._build_prompt(context)
            elif hasattr(agent, 'prompt_template'):
                return agent.prompt_template.format(**context)
            else:
                # Generic prompt reconstruction
                job_position = context.get('job_position', 'Unknown')
                job_keywords = context.get('job_keywords', 'None')
                return f"Agent: {agent.name}\nPosition: {job_position}\nKeywords: {job_keywords}"
        except Exception as e:
            return f"Agent {agent.name} execution (prompt extraction failed: {str(e)})"
    
    def _validate_agent_input(self, agent_name: str, context: Dict[str, Any]) -> None:
        """Validate that agent receives consistent input data."""
        required_fields = {
            "ExtractJobPostingInfo": ["job_position", "job_keywords", "job_postings"],
            "JobRankingAndAnalysisAgent": ["job_position", "job_keywords", "resume"],
            "SpreadsheetExportAgent": ["job_position", "job_keywords"]
        }
        
        if agent_name in required_fields:
            for field in required_fields[agent_name]:
                if field not in context:
                    self._log_consistency_issue(f"Missing required field '{field}' for {agent_name}")
    
    def _validate_agent_output(self, agent_name: str, result: str, context: Dict[str, Any]) -> str:
        """
        Validate and potentially correct agent output for consistency.
        
        Args:
            agent_name: Name of the agent
            result: Raw agent output
            context: Input context for reference
            
        Returns:
            str: Validated/corrected output
        """
        # Basic output validation
        if not result or len(result.strip()) < 10:
            corrected_result = self._generate_fallback_response(agent_name, context)
            self._log_consistency_issue(f"{agent_name} produced insufficient output, using fallback")
            return corrected_result
        
        # Agent-specific validation
        if agent_name == "ExtractJobPostingInfo":
            if "No matching jobs found" in result and len(result.split('\n')) < 3:
                # If no jobs found, ensure proper formatting
                return "No matching jobs found based on the specified criteria."
        
        elif agent_name == "JobRankingAndAnalysisAgent":
            # Ensure skills extraction is present
            if "SKILLS_FOR_DB" not in result:
                self._log_consistency_issue(f"{agent_name} missing skills extraction section")
        
        return result
    
    def _generate_fallback_response(self, agent_name: str, context: Dict[str, Any]) -> str:
        """Generate a fallback response when agent fails or produces poor output."""
        fallbacks = {
            "ExtractJobPostingInfo": "No job postings available for extraction at this time.",
            "JobRankingAndAnalysisAgent": "Job ranking analysis unavailable. Please review job requirements manually.",
            "SpreadsheetExportAgent": "Spreadsheet export unavailable. Results are available in text format only."
        }
        return fallbacks.get(agent_name, "Agent response unavailable.")
    
    def _fetch_job_postings(self, normalized_data: Dict[str, Any]) -> str:
        """
        Fetch job postings from JSearch API (RapidAPI).
        Integrates with real job sites: LinkedIn, Indeed, Monster, ZipRecruiter, etc.
        
        Returns:
            str: Real job postings data or error message if API unavailable
        """
        positions = normalized_data.get("job_position", "")
        keywords = normalized_data.get("job_keywords", "")
        
        try:
            # Import and use JSearch client
            from AI_Slop.jsearch_client import JSearchClient
            
            self._update_status("Connecting to job search APIs...")
            
            # Initialize JSearch client
            jsearch_client = JSearchClient()
            
            self._update_status("Fetching real job postings...")
            
            # Search for jobs using positions and keywords
            jobs = jsearch_client.search_jobs_by_position_and_keywords(
                job_positions=positions,
                job_keywords=keywords,
                location="United States",
                max_results=15  # Get more jobs for better analysis
            )
            
            if not jobs:
                return "No job postings found matching the specified criteria."
            
            # Format jobs for agent consumption
            formatted_jobs = jsearch_client.format_jobs_for_agents(jobs)
            
            # Store raw job data for later use by agents
            self.context["raw_job_data"] = jobs
            
            # DEBUGGING: Save job data to file for analysis (only once)
            debug_file = "/Users/jamiepeterson/Desktop/example/AI_Slop/exports/debug_jobs_data.txt"
            if not os.path.exists(debug_file):
                try:
                    os.makedirs(os.path.dirname(debug_file), exist_ok=True)
                    with open(debug_file, 'w') as f:
                        f.write(f"DEBUG: Job Search Results\n")
                        f.write(f"API returned: {len(jobs)} jobs\n")
                        f.write(f"Position: {positions}\n")
                        f.write(f"Keywords: {keywords}\n")
                        f.write(f"Timestamp: {datetime.now()}\n")
                        f.write(f"{'='*60}\n\n")
                        
                        for i, job in enumerate(jobs[:5], 1):  # Save first 5 jobs for analysis
                            f.write(f"Job {i}:\n")
                            f.write(f"Title: {job.get('title', 'N/A')}\n")
                            f.write(f"Company: {job.get('company', 'N/A')}\n")
                            f.write(f"Location: {job.get('location', 'N/A')}\n")
                            f.write(f"Description: {job.get('description', 'N/A')[:200]}...\n")
                            f.write(f"Required Skills: {job.get('required_skills', 'N/A')}\n")
                            f.write(f"Apply Link: {job.get('apply_link', 'N/A')}\n")
                            f.write(f"-"*40 + "\n\n")
                        
                        f.write(f"\nFormatted Jobs Text (first 1000 chars):\n")
                        f.write(f"{'='*60}\n")
                        f.write(formatted_jobs[:1000] + "...")
                    
                    print(f"[DEBUG] Saved job data to {debug_file}")
                except Exception as e:
                    print(f"[DEBUG] Could not save job data: {e}")
            
            self._update_status(f"Found {len(jobs)} relevant job postings")
            
            return formatted_jobs
            
        except ImportError:
            error_msg = "JSearch client not available. Please create AI_Slop/jsearch_client.py with JSearchClient class."
            self._update_status("Job API unavailable")
            return f"ERROR: {error_msg}"
            
        except ValueError as e:
            if "RapidAPI key" in str(e):
                error_msg = f"JSearch API Error: {str(e)}\n\nPlease set RAPIDAPI_KEY environment variable with your RapidAPI key."
                self._update_status("API key missing")
                return f"ERROR: {error_msg}"
            else:
                error_msg = f"JSearch API configuration error: {str(e)}"
                self._update_status("API configuration error")
                return f"ERROR: {error_msg}"
                
        except Exception as e:
            error_msg = f"JSearch API error: {str(e)}"
            self._update_status("Job search failed")
            print(f"[ORCHESTRATOR] {error_msg}")
            return f"ERROR: {error_msg}"
    

    
    def _extract_skills_from_result(self, agent_result: str) -> List[Dict[str, Any]]:
        """
        Extract structured skills data from agent result for database storage.
        
        Args:
            agent_result: Raw result from JobRankingAndAnalysisAgent
            
        Returns:
            List: Structured skills data ready for database insertion
        """
        skills = []
        
        # Look for SKILLS_FOR_DB section in agent result
        if "SKILLS_FOR_DB:" in agent_result:
            skills_section = agent_result.split("SKILLS_FOR_DB:")[1]
            
            # Try to extract JSON-like skill objects
            # This is a simplified extraction - in production, use proper JSON parsing
            lines = skills_section.split('\n')
            for line in lines:
                if '"skill":' in line and '"frequency":' in line:
                    # Extract skill data (simplified regex parsing)
                    skill_match = re.search(r'"skill":\s*"([^"]+)"', line)
                    freq_match = re.search(r'"frequency":\s*(\d+)', line)
                    cat_match = re.search(r'"category":\s*"([^"]+)"', line)
                    
                    if skill_match and freq_match:
                        skills.append({
                            "skill": skill_match.group(1),
                            "frequency": int(freq_match.group(1)),
                            "category": cat_match.group(1) if cat_match else "General",
                            "extracted_date": "2025-11-12"  # TODO: Use actual timestamp
                        })
        
        return skills
    
    def _consolidate_agent_results(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Consolidate results from all agents into final recommendations.
        
        Args:
            results: Complete workflow results
            
        Returns:
            Dict: Final consolidated recommendations
        """
        consolidation = {
            "summary": "Job search analysis completed",
            "total_jobs_analyzed": 0,
            "top_recommendations": [],
            "skill_gaps": [],
            "next_steps": []
        }
        
        # Extract key insights from each stage
        if results["workflow_stages"].get("job_extraction"):
            extraction_result = results["workflow_stages"]["job_extraction"]
            # Count jobs found (simplified counting)
            job_count = extraction_result.count("Job Posting") if "Job Posting" in extraction_result else 0
            consolidation["total_jobs_analyzed"] = job_count
        
        if results["workflow_stages"].get("job_ranking"):
            ranking_result = results["workflow_stages"]["job_ranking"]
            # Extract top 3 recommendations (simplified extraction)
            if "Job #1:" in ranking_result:
                consolidation["top_recommendations"].append("Review highest-ranked position for immediate application")
            consolidation["next_steps"].append("Focus on skill development based on job analysis")
        
        # Add skills-based recommendations
        if results["skills_extracted"]:
            high_freq_skills = [s for s in results["skills_extracted"] if s.get("frequency", 0) > 2]
            consolidation["skill_gaps"] = [s["skill"] for s in high_freq_skills[:5]]
        
        return consolidation
    
    def _validate_data_consistency(self) -> List[str]:
        """
        Validate data consistency across the entire workflow.
        
        Returns:
            List: Log of consistency issues found
        """
        consistency_log = []
        
        # Check if cached job data matches current context
        if self.job_data_cache:
            for key in ["job_position", "job_keywords"]:
                if key in self.context and key in self.job_data_cache:
                    if self.context[key] != self.job_data_cache[key]:
                        consistency_log.append(f"Data inconsistency detected in {key}")
        
        # Check agent result consistency
        agent_results = [key for key in self.context.keys() if key.endswith("_result")]
        if len(agent_results) != len(self.agents):
            consistency_log.append(f"Missing results from {len(self.agents) - len(agent_results)} agents")
        
        return consistency_log
    
    def _log_consistency_issue(self, issue: str):
        """Log a data consistency issue for debugging."""
        print(f"[CONSISTENCY WARNING] {issue}")  # TODO: Use proper logging system
    
    def validate_llm_setup(self) -> Dict[str, Any]:
        """
        Validate that LLM setup is working properly.
        
        Returns:
            Dict containing validation results
        """
        validation = {
            "llm_client_initialized": self.llm_client is not None,
            "provider_info": {},
            "test_query_successful": False,
            "recommendations": []
        }
        
        if self.llm_client:
            # Get provider info
            provider_info = self.llm_client.get_provider_info()
            validation["provider_info"] = provider_info
            
            if provider_info["available"]:
                # Test a simple query
                try:
                    test_response = self.llm_client.query("Hello! Please respond with 'LLM test successful'")
                    validation["test_query_successful"] = "successful" in test_response.lower()
                    validation["test_response"] = test_response[:100]
                except Exception as e:
                    validation["test_error"] = str(e)
            else:
                validation["recommendations"].append(f"Check {provider_info['provider'].upper()} configuration: {provider_info.get('error')}")
        else:
            validation["recommendations"].append("LLM client failed to initialize - check LangChain installation")
        
        return validation

    def get_llm_provider_info(self) -> Dict[str, Any]:
        """
        Get information about the current LLM provider.
        
        Returns:
            Dict containing provider information and status
        """
        if not self.llm_client:
            return {"provider": "none", "available": False, "error": "LLM client not initialized"}
        
        return self.llm_client.get_provider_info()
    
    def switch_llm_provider(self, provider: str) -> bool:
        """
        Switch LLM provider at runtime.
        
        Args:
            provider: "groq" or "ollama"
            
        Returns:
            bool: True if switch successful, False otherwise
        """
        if not self.llm_client:
            return False
        
        try:
            self.llm_client.switch_provider(provider)
            print(f"[ORCHESTRATOR] Switched to {provider.upper()} provider")
            return True
        except Exception as e:
            print(f"[ORCHESTRATOR] Failed to switch to {provider}: {e}")
            return False
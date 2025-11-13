"""
Orchestrator for managing AI agent workflows.
This module coordinates calls to the local LLM and manages agent interactions.
Based on the system architecture diagram with UI -> Service -> AI Orchestrator -> Agents workflow.
"""
from AI_Slop.ollama_client import query_ollama
from typing import Dict, Any, List, Optional
import json
import re


class Orchestrator:
    """
    Orchestrator class that manages the workflow of AI agents.
    It coordinates calls to the local LLM and handles agent communication.
    Implements the architecture: UI -> Service -> AI Orchestrator -> Agents (1,2,3) with data consistency.
    """
    
    def __init__(self, model: str = "llama3"):
        """
        Initialize the orchestrator with a specific model.
        
        Args:
            model: The name of the Ollama model to use (default: llama3)
        """
        self.model = model
        self.agents = []
        self.context = {}
        self.status_callback = None
        self.job_data_cache = {}  # Cache for consistent job data across agents
        self.skills_database = []  # In-memory skills storage until DB implementation
    
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
        Query the local LLM with a prompt and optional context.
        
        Args:
            prompt: The prompt to send to the LLM
            context: Optional context dictionary to enhance the prompt
            
        Returns:
            str: The LLM's response
        """
        if context:
            # Enhance prompt with context
            context_str = self._format_context(context)
            enhanced_prompt = f"{context_str}\n\n{prompt}"
        else:
            enhanced_prompt = prompt
        
        return query_ollama(self.model, enhanced_prompt)
    
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
        
        # Cache normalized data for agent consistency
        self.job_data_cache = normalized_data
        
        results = {
            "job_position": normalized_data.get("job_position"),
            "job_keywords": normalized_data.get("job_keywords"),
            "workflow_stages": {},
            "final_recommendations": {},
            "skills_extracted": [],
            "data_consistency_log": []
        }
        
        # Step 2: Execute Job Site API Integration (when implemented)
        # TODO: Implement job site API calls based on normalized position titles and keywords
        # This would fetch raw job postings from multiple sources (Indeed, LinkedIn, etc.)
        raw_job_postings = self._fetch_job_postings(normalized_data)
        
        # Step 3: Agent 1 - Job Posting Extraction and Filtering
        self._update_status("Running Job Extraction Agent...")
        if self._has_agent_by_name("ExtractJobPostingInfo"):
            agent1_result = self._execute_agent_with_validation("ExtractJobPostingInfo", {
                **normalized_data,
                "job_postings": raw_job_postings
            })
            results["workflow_stages"]["job_extraction"] = agent1_result
            self.context["filtered_jobs"] = agent1_result
        else:
            results["workflow_stages"]["job_extraction"] = "Agent not registered"
        
        # Step 4: Agent 2 - Job Analysis and Matching  
        self._update_status("Running Job Analysis Agent...")
        if self._has_agent_by_name("JobAnalysisAgent"):
            agent2_result = self._execute_agent_with_validation("JobAnalysisAgent", {
                **normalized_data,
                "filtered_jobs": self.context.get("filtered_jobs", "")
            })
            results["workflow_stages"]["job_analysis"] = agent2_result
        else:
            results["workflow_stages"]["job_analysis"] = "Agent not registered"
        
        # Step 5: Agent 3 - Job Ranking and Skills Extraction
        self._update_status("Running Job Ranking Agent...")
        if self._has_agent_by_name("JobRankingAndAnalysisAgent"):
            agent3_result = self._execute_agent_with_validation("JobRankingAndAnalysisAgent", {
                **normalized_data,
                **self.context
            })
            results["workflow_stages"]["job_ranking"] = agent3_result
            
            # Extract skills for database storage
            extracted_skills = self._extract_skills_from_result(agent3_result)
            results["skills_extracted"] = extracted_skills
            self.skills_database.extend(extracted_skills)
        else:
            results["workflow_stages"]["job_ranking"] = "Agent not registered"
        
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
        normalized["processing_timestamp"] = "2025-11-12"  # TODO: Use actual timestamp
        normalized["data_version"] = "1.0"
        
        return normalized
    
    def _has_agent_by_name(self, agent_name: str) -> bool:
        """Check if an agent with the given name is registered."""
        return any(agent.name == agent_name for agent in self.agents)
    
    def _execute_agent_with_validation(self, agent_name: str, context: Dict[str, Any]) -> str:
        """
        Execute an agent with input/output validation for consistency.
        
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
        
        # Execute agent
        result = agent.execute(context, self)
        
        # Post-execution validation
        validated_result = self._validate_agent_output(agent_name, result, context)
        
        return validated_result
    
    def _validate_agent_input(self, agent_name: str, context: Dict[str, Any]) -> None:
        """Validate that agent receives consistent input data."""
        required_fields = {
            "ExtractJobPostingInfo": ["job_position", "job_keywords", "job_postings"],
            "JobAnalysisAgent": ["job_position", "job_keywords", "resume"],
            "JobRankingAndAnalysisAgent": ["job_position", "job_keywords", "resume"]
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
            "JobAnalysisAgent": f"Basic analysis: The candidate profile for {context.get('job_position', 'specified positions')} requires further evaluation.",
            "JobRankingAndAnalysisAgent": "Job ranking analysis unavailable. Please review job requirements manually."
        }
        return fallbacks.get(agent_name, "Agent response unavailable.")
    
    def _fetch_job_postings(self, normalized_data: Dict[str, Any]) -> str:
        """
        Fetch job postings from external APIs.
        TODO: Implement actual API calls to job sites (Indeed, LinkedIn, etc.)
        """
        # Placeholder for job site API integration
        # This would use normalized_data to query multiple job boards
        positions = normalized_data.get("job_position", "")
        keywords = normalized_data.get("job_keywords", "")
        
        # TODO: Implement actual API calls here
        # - Indeed API integration
        # - LinkedIn Jobs API
        # - Other job board APIs
        # - Web scraping with Playwright/Selenium (as noted in diagram)
        
        # Return mock data for now
        return f"""
        Mock Job Posting 1: Software Engineer at TechCorp
        Requirements: {keywords}
        Location: Remote
        Description: Looking for a software engineer with experience in the specified technologies.
        
        Mock Job Posting 2: Senior Developer at StartupInc  
        Requirements: Related to {positions}
        Location: San Francisco
        Description: Senior role requiring expertise in relevant technologies.
        
        [Additional job postings would be fetched from APIs]
        """
    
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
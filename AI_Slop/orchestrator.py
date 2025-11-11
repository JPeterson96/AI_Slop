"""
Orchestrator for managing AI agent workflows.
This module coordinates calls to the local LLM and manages agent interactions.
"""
from AI_Slop.ollama_client import query_ollama
from typing import Dict, Any, List, Optional


class Orchestrator:
    """
    Orchestrator class that manages the workflow of AI agents.
    It coordinates calls to the local LLM and handles agent communication.
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
        Execute a workflow with multiple agents in sequence.
        
        Args:
            job_data: Dictionary containing job position, keywords, and resume data
            
        Returns:
            Dict containing results from all agents
        """
        results = {
            "job_position": job_data.get("job_position"),
            "job_keywords": job_data.get("job_keywords"),
            "agent_results": []
        }
        
        # Update shared context
        self.context.update(job_data)
        
        # Execute each registered agent in sequence
        for agent in self.agents:
            agent_result = agent.execute(self.context, self)
            results["agent_results"].append({
                "agent_name": agent.name,
                "result": agent_result
            })
            # Update context with agent results
            self.context[f"{agent.name}_result"] = agent_result
        
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
        # Prepare context for the LLM
        context = {
            "job_position": job_position,
            "job_keywords": job_keywords,
            "resume": resume_content[:1000]  # Limit resume length for context
        }
        
        prompt = """Based on the provided job position(s), keywords, and resume, 
please provide insights on how well the candidate matches the job requirements 
and suggest improvements."""
        
        return self.query_llm(prompt, context)

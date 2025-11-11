"""
Generic Agent classes for AI-powered task execution.
This module provides a base agent class that can be extended for specific tasks.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class BaseAgent(ABC):
    """
    Abstract base class for all agents.
    Agents are specialized components that perform specific tasks using the LLM.
    """
    
    def __init__(self, name: str, description: str = ""):
        """
        Initialize the base agent.
        
        Args:
            name: The name of the agent
            description: A description of what this agent does
        """
        self.name = name
        self.description = description
    
    @abstractmethod
    def execute(self, context: Dict[str, Any], orchestrator) -> str:
        """
        Execute the agent's task.
        
        Args:
            context: Dictionary containing shared context data
            orchestrator: Reference to the orchestrator for LLM queries
            
        Returns:
            str: The result of the agent's execution
        """
        pass
    
    def format_context_for_prompt(self, context: Dict[str, Any], keys: list) -> str:
        """
        Helper method to format specific context keys into a string.
        
        Args:
            context: The full context dictionary
            keys: List of keys to extract from context
            
        Returns:
            str: Formatted context string
        """
        parts = []
        for key in keys:
            if key in context:
                parts.append(f"{key}: {context[key]}")
        return "\n".join(parts)


class GenericAgent(BaseAgent):
    """
    A generic agent implementation that can handle various tasks.
    This agent takes a prompt template and executes it with the given context.
    """
    
    def __init__(
        self, 
        name: str = "GenericAgent",
        description: str = "A generic agent for general purpose tasks",
        prompt_template: Optional[str] = None
    ):
        """
        Initialize the generic agent.
        
        Args:
            name: The name of the agent
            description: Description of the agent's purpose
            prompt_template: Optional template for the prompt (can include {variable} placeholders)
        """
        super().__init__(name, description)
        self.prompt_template = prompt_template or "Analyze the following information and provide insights:\n{context}"
    
    def execute(self, context: Dict[str, Any], orchestrator) -> str:
        """
        Execute the generic agent's task by filling in the prompt template
        and querying the LLM.
        
        Args:
            context: Dictionary containing shared context data
            orchestrator: Reference to the orchestrator for LLM queries
            
        Returns:
            str: The LLM's response
        """
        # Format the prompt with context
        prompt = self._format_prompt(context)
        
        # Query the LLM through the orchestrator
        result = orchestrator.query_llm(prompt)
        
        return result
    
    def _format_prompt(self, context: Dict[str, Any]) -> str:
        """
        Format the prompt template with context data.
        
        Args:
            context: Dictionary containing context data
            
        Returns:
            str: Formatted prompt
        """
        # Simple context string formatting
        if "{context}" in self.prompt_template:
            context_str = "\n".join([f"{k}: {v}" for k, v in context.items()])
            return self.prompt_template.format(context=context_str)
        
        # Try to format with specific context keys
        try:
            return self.prompt_template.format(**context)
        except KeyError:
            # If template variables don't match context, just append context
            context_str = "\n".join([f"{k}: {v}" for k, v in context.items()])
            return f"{self.prompt_template}\n\nContext:\n{context_str}"


class JobAnalysisAgent(BaseAgent):
    """
    Specialized agent for analyzing job requirements and resume matching.
    """
    
    def __init__(self):
        super().__init__(
            name="JobAnalysisAgent",
            description="Analyzes job requirements and matches them with resume content"
        )
    
    def execute(self, context: Dict[str, Any], orchestrator) -> str:
        """
        Analyze the job requirements against the resume.
        
        Args:
            context: Dictionary containing job_position, job_keywords, and resume
            orchestrator: Reference to the orchestrator for LLM queries
            
        Returns:
            str: Analysis results
        """
        job_position = context.get("job_position", "")
        job_keywords = context.get("job_keywords", "")
        resume = context.get("resume", "")
        
        prompt = f"""You are a professional career advisor. Analyze the following:

            Job Position(s): {job_position}
            Required Keywords: {job_keywords}

            Resume Content: {resume[:3000]}

            Please provide:
            1. How well the candidate matches each position
            2. Which keywords from the job requirements appear in the resume
            3. Missing skills or keywords that should be highlighted
            4. Suggestions for improving the resume for these positions
            """
        
        return orchestrator.query_llm(prompt)

class ExtractJobPostingInfo(BaseAgent):
    """
    Specialized agent for extracting and filtering job postings that match specified positions and keywords.
    """
    
    def __init__(self):
        super().__init__(
            name="ExtractJobPostingInfo",
            description="Filters and extracts job postings that match provided job positions and keywords"
        )
    
    def execute(self, context: Dict[str, Any], orchestrator) -> str:
        """
        Extract only the job postings that match the specified positions and keywords.
        
        Args:
            context: Dictionary containing job_position, job_keywords, and job_postings
            orchestrator: Reference to the orchestrator for LLM queries
            
        Returns:
            str: List of matching job postings
        """
        job_position = context.get("job_position", "")
        job_keywords = context.get("job_keywords", "")
        job_postings = context.get("job_postings", "")
        
        prompt = f"""You are a job filtering system. Your task is to extract ONLY the job postings that match the specified criteria.

        **Target Job Positions:** {job_position}

        And that either match the following keywords or contain similar/related terms:
        **Required Keywords:** {job_keywords}

        **Job Postings List:**
        {job_postings[:5000]}

        **Instructions:**
        1. Review each job posting in the list above
        2. Extract ONLY jobs that match one or more of the target positions
        3. For each job, check if it contains the required keywords or similar/related terms
        4. Return the complete matching job postings in their original format

        **Matching Rules:**
        - Include jobs with titles similar to the target positions (e.g., "Software Dev" matches "Software Developer")
        - Accept similar keywords (e.g., "ML" matches "Machine Learning", "Python3" matches "Python")
        - If a job matches the position OR contains multiple keywords, include it

        **Output:**
        Return ONLY the matching job postings. If no jobs match, respond with: "No matching jobs found."
        """
        
        return orchestrator.query_llm(prompt)
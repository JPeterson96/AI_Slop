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
    
class JobRankingAndAnalysis(BaseAgent):
    """
    Specialized agent for sorting jobs by best fit along with pros and cons of each.
    Extracts skills for database storage and provides comprehensive job analysis.
    """
    
    def __init__(self):
        super().__init__(
            name="JobRankingAndAnalysisAgent",
            description="Ranks jobs based on best fit for user and creates detailed analysis with pros/cons and skills extraction"
        )
    
    def execute(self, context: Dict[str, Any], orchestrator) -> str:
        """
        Analyze each job for best fit and provide detailed feedback.
        
        Args:
            context: Dictionary containing job_position, job_keywords, resume, and filtered_jobs
            orchestrator: Reference to the orchestrator for LLM queries
            
        Returns:
            str: Comprehensive analysis results with rankings, summaries, pros/cons, and skills
        """
        job_position = context.get("job_position", "")
        job_keywords = context.get("job_keywords", "")
        resume = context.get("resume", "")
        
        # Get filtered jobs from ExtractJobPostingInfo agent result
        filtered_jobs = context.get("ExtractJobPostingInfo_result", "")
        if not filtered_jobs or filtered_jobs == "No matching jobs found.":
            return "No jobs available for ranking and analysis. Please run job extraction first."
        
        orchestrator._update_status("Analyzing job fit and relevance...")
        
        prompt = f"""You are an expert career advisor and job matching specialist. Analyze the following information to provide comprehensive job rankings and insights.

**CANDIDATE PROFILE:**
Target Position(s): {job_position}
Desired Keywords: {job_keywords}
Resume Content: {resume[:3000]}

**AVAILABLE JOB POSTINGS:**
{filtered_jobs[:4000]}

**TASK INSTRUCTIONS:**
You must provide a comprehensive analysis in the following structured format:

## JOB RANKINGS (Best to Worst Fit)

For each job, provide:

### Job #[NUMBER]: [Job Title] at [Company]
**Match Score: [X/10]**
**Summary:** [2-3 sentence overview of the role and why it matches/doesn't match]

**PROS:**
- [Specific positive aspects that align with candidate's profile]
- [Growth opportunities, company benefits, skill development]
- [Location, salary, culture fit indicators]

**CONS:**
- [Missing requirements or skill gaps]
- [Potential challenges or mismatches]
- [Areas where candidate might struggle]

**Key Skills Required:** [List 5-8 main technical/soft skills from job posting]
**Skills Match:** [Which candidate skills align] / [Which are missing]

---

## OVERALL SKILLS ANALYSIS

**All Skills Mentioned Across Jobs:**
- [Skill Name]: Mentioned in [X] jobs
- [Skill Name]: Mentioned in [X] jobs
- [Continue for all unique skills found]

**Candidate's Strongest Matches:**
- [Skills from resume that appear frequently in job postings]

**Priority Skills to Develop:**
- [Most frequently requested skills missing from resume]

**RECOMMENDATIONS:**
1. [Specific advice for improving candidacy]
2. [Skills to prioritize learning]
3. [Resume enhancement suggestions]

Please ensure jobs are ranked from highest match score (best fit) to lowest match score (worst fit)."""
        
        orchestrator._update_status("Generating job rankings and analysis...")
        result = orchestrator.query_llm(prompt)
        
        # Extract and format skills for future database storage
        skills_extraction_prompt = f"""Based on the job analysis above, extract all unique skills mentioned across all job postings into a clean, structured list for database storage.

**Previous Analysis:**
{result[:2000]}

**Extract and format as:**
SKILLS_FOR_DB:
[
  {{"skill": "Python", "frequency": 3, "category": "Programming Language"}},
  {{"skill": "Machine Learning", "frequency": 2, "category": "Technical Skill"}},
  {{"skill": "Leadership", "frequency": 4, "category": "Soft Skill"}},
  ...continue for all skills
]

Focus on:
- Technical skills (programming languages, tools, frameworks)
- Soft skills (communication, leadership, etc.)
- Industry-specific skills
- Certifications mentioned

Categorize each skill and count how many job postings mentioned it."""
        
        orchestrator._update_status("Extracting skills data...")
        skills_data = orchestrator.query_llm(skills_extraction_prompt)
        
        # Combine the results
        final_result = f"""{result}

---

## SKILLS DATABASE EXTRACTION
{skills_data}

---
**Analysis completed by {self.name}**
**Timestamp: Generated for job search optimization and skills gap analysis**"""
        
        return final_result
    
    def _calculate_match_score(self, job_requirements: str, resume: str, keywords: str) -> int:
        """
        Helper method to calculate a rough match score between job and candidate.
        This could be enhanced with more sophisticated matching algorithms.
        
        Args:
            job_requirements: The job posting text
            resume: Candidate's resume text
            keywords: Desired keywords
            
        Returns:
            int: Match score from 1-10
        """
        # This is a placeholder for more sophisticated matching logic
        # In a real implementation, you might use NLP techniques, skill extraction, etc.
        
        job_lower = job_requirements.lower()
        resume_lower = resume.lower()
        keywords_lower = keywords.lower().split(',')
        
        matches = 0
        total_keywords = len(keywords_lower)
        
        for keyword in keywords_lower:
            if keyword.strip() in job_lower and keyword.strip() in resume_lower:
                matches += 1
        
        # Basic scoring: 5 base points + keyword matches
        score = min(10, 5 + (matches / max(1, total_keywords)) * 5)
        return int(score)
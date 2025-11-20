"""
Generic Agent classes for AI-powered task execution.
This module provides a base agent class that can be extended for specific tasks.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import re


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
    Works with both JSearch API real data and fallback mock data.
    """
    
    def __init__(self):
        super().__init__(
            name="ExtractJobPostingInfo",
            description="Filters and extracts job postings that match provided job positions and keywords from JSearch API data"
        )
    
    def execute(self, context: Dict[str, Any], orchestrator) -> str:
        """
        Extract and analyze job postings from JSearch API data.
        
        Args:
            context: Dictionary containing job_position, job_keywords, job_postings, and raw_job_data
            orchestrator: Reference to the orchestrator for LLM queries
            
        Returns:
            str: Analysis and filtering of job postings
        """
        job_position = context.get("job_position", "")
        job_keywords = context.get("job_keywords", "")
        job_postings = context.get("job_postings", "")
        raw_job_data = context.get("raw_job_data", [])
        
        # Check if we have structured JSearch data
        if raw_job_data and isinstance(raw_job_data, list):
            return self._process_jsearch_data(raw_job_data, job_position, job_keywords, orchestrator)
        else:
            return self._process_text_data(job_postings, job_position, job_keywords, orchestrator)
    
    def _process_jsearch_data(self, jobs: list, job_position: str, job_keywords: str, orchestrator) -> str:
        """Process structured JSearch API data."""
        if not jobs:
            return "No job postings found from JSearch API."
        
        # Create summary of JSearch jobs for agent analysis
        job_summaries = []
        for i, job in enumerate(jobs, 1):
            summary = f"""
Job {i}: {job['title']} at {job['company']}
Location: {job['location']} {'(Remote)' if job['is_remote'] else ''}
Type: {job['employment_type']}
Apply: {job['apply_link']}

Description: {job['description'][:300]}...

Required Skills: {', '.join(job['required_skills']) if job['required_skills'] else 'Not specified'}
Responsibilities: {', '.join(job['responsibilities'][:3]) if job['responsibilities'] else 'Not specified'}

Salary: {f"${job['salary_min']:,} - ${job['salary_max']:,} {job['salary_currency']}" if job['salary_min'] and job['salary_max'] else 'Not disclosed'}
"""
            job_summaries.append(summary)
        
        jobs_text = "\n---\n".join(job_summaries)
        
        keywords_text = job_keywords if job_keywords and job_keywords.strip() and job_keywords != "No specific skills filter" else "No specific skill filters (showing all jobs for the positions)"
        
        prompt = f"""You are analyzing {len(jobs)} real job postings from JSearch API (LinkedIn, Indeed, Monster, etc.).

**Target Positions:** {job_position}
**Skill Filters:** {keywords_text}

**JSearch Job Postings:**
{jobs_text}

**Analysis Tasks:**
1. Evaluate how well each job matches the target positions and keywords
2. Identify the most relevant jobs (give each a relevance score 1-10)
3. Highlight key requirements and qualifications across all jobs
4. Note any common patterns or trending skills

**Output Format:**
## JSearch Job Analysis Summary

**Total Jobs Found:** {len(jobs)}
**Source:** JSearch API (Real job postings from major job sites)

**Top Matching Jobs:**
[List the 3-5 most relevant jobs with brief explanations]

**Common Requirements Across Jobs:**
[List the most frequently mentioned skills/requirements]

**Keyword Match Analysis:**
[How well the jobs match the specified keywords]

**Recommendations:**
[Brief advice based on the job market data]
"""
        
        return orchestrator.query_llm(prompt)
    
    def _process_text_data(self, job_postings: str, job_position: str, job_keywords: str, orchestrator) -> str:
        """Process text-based job posting data (fallback mode)."""
        
        keywords_text = job_keywords if job_keywords and job_keywords.strip() and job_keywords != "No specific skills filter" else "No specific skill filters (accepting all jobs for the positions)"
        
        prompt = f"""You are a job filtering system working with job posting text data.

**Target Job Positions:** {job_position}
**Skill Filters:** {keywords_text}

**Job Postings Data:**
{job_postings[:5000]}

**Instructions:**
1. Review each job posting in the data above
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
        
        keywords_text = job_keywords if job_keywords and job_keywords.strip() and job_keywords != "No specific skills filter" else "No specific skill filters provided"
        
        prompt = f"""You are an expert career advisor and job matching specialist. Analyze the following information to provide comprehensive job rankings and insights.

        **CANDIDATE PROFILE:**
        Target Position(s): {job_position}
        Skill Preferences: {keywords_text}
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
    
class ResumeAndCoverLetter(BaseAgent):
    """
    Specialized agent for tailoring the provided resume and writing a cover letter based ont he resume to each job listing.
    """
    
    def __init__(self):
        super().__init__(
            name="ResumeAndCoverLetterAgent",
            description="Modifying resume and creating cover letter to match each job listing"
        )
    
    def execute(self, context: Dict[str, Any], orchestrator) -> str:
        """
       Modify resume to match job listing and create cover letter based on the resune that aligns with the job listing
        
        Args:
            context: Dictionary containing list of ordered and filtered jobs from other agents, job_position, job_keywords, and resume
            orchestrator: Reference to the orchestrator for LLM queries
            
        Returns:
            str: a resume and cover letter for each position
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


class SpreadsheetExportAgent(BaseAgent):
    """
    Specialized agent for exporting job analysis results to spreadsheet format for testing purposes.
    Creates structured Excel/CSV files with job rankings, analysis, and skills data.
    """
    
    def __init__(self):
        super().__init__(
            name="SpreadsheetExportAgent",
            description="Exports job analysis results to Excel/CSV format for testing and review"
        )
    
    def execute(self, context: Dict[str, Any], orchestrator) -> str:
        """
        Export job analysis results to a spreadsheet file.
        
        Args:
            context: Dictionary containing all workflow results and analysis data
            orchestrator: Reference to the orchestrator for status updates
            
        Returns:
            str: Status message about spreadsheet export
        """
        import pandas as pd
        import re
        from datetime import datetime
        import os
        
        orchestrator._update_status("Preparing spreadsheet export...")
        
        try:
            # Get data from context
            job_position = context.get("job_position", "Unknown Position")
            job_keywords = context.get("job_keywords", "No keywords specified")
            ranking_results = context.get("JobRankingAndAnalysisAgent_result", "")
            raw_job_data = context.get("raw_job_data", [])
            
            if not ranking_results:
                return "No ranking results available for export"
            
            orchestrator._update_status("Parsing job analysis data...")
            
            # Parse job rankings from the analysis text
            jobs_data = self._parse_job_rankings(ranking_results, raw_job_data)
            
            # Parse skills data
            skills_data = self._parse_skills_data(ranking_results)
            
            # Create timestamp for file naming
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Create output directory if it doesn't exist
            output_dir = "/Users/jamiepeterson/Desktop/example/AI_Slop/exports"
            os.makedirs(output_dir, exist_ok=True)
            
            orchestrator._update_status("Creating Excel file...")
            
            # Create Excel file with multiple sheets
            filename = f"job_analysis_results_{timestamp}.xlsx"
            filepath = os.path.join(output_dir, filename)
            
            with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
                # Sheet 1: Job Rankings
                if jobs_data:
                    jobs_df = pd.DataFrame(jobs_data)
                    jobs_df.to_excel(writer, sheet_name='Job Rankings', index=False)
                
                # Sheet 2: Skills Analysis
                if skills_data:
                    skills_df = pd.DataFrame(skills_data)
                    skills_df.to_excel(writer, sheet_name='Skills Analysis', index=False)
                
                # Sheet 3: Summary
                summary_data = [{
                    'Target Positions': job_position,
                    'Skill Filter Keywords': job_keywords,
                    'Search Note': 'Keywords used for skill filtering, not job title matching',
                    'Total Jobs Analyzed': len(jobs_data),
                    'Export Date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    'Top Ranked Job': jobs_data[0]['Job Title'] if jobs_data else 'No jobs found',
                    'Average Match Score': sum(job.get('Match Score', 0) for job in jobs_data) / len(jobs_data) if jobs_data else 0
                }]
                summary_df = pd.DataFrame(summary_data)
                summary_df.to_excel(writer, sheet_name='Summary', index=False)
                
                # Sheet 4: Raw Analysis Text
                raw_analysis = pd.DataFrame([{
                    'Complete Analysis': ranking_results
                }])
                raw_analysis.to_excel(writer, sheet_name='Raw Analysis', index=False)
            
            orchestrator._update_status("Spreadsheet export completed!")
            
            return f"""
## SPREADSHEET EXPORT COMPLETED

**File Created:** {filename}
**Location:** {filepath}
**Sheets Created:**
- Job Rankings: {len(jobs_data)} jobs with match scores and analysis
- Skills Analysis: {len(skills_data)} skills extracted across all jobs
- Summary: High-level overview and statistics  
- Raw Analysis: Complete text analysis from AI

**Export Statistics:**
- Jobs Analyzed: {len(jobs_data)}
- Skills Identified: {len(skills_data)}
- Export Time: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

The spreadsheet is ready for review and can be opened in Excel, Google Sheets, or any spreadsheet application.
"""
        
        except Exception as e:
            error_msg = f"Spreadsheet export failed: {str(e)}"
            orchestrator._update_status("Export failed")
            return f"ERROR: {error_msg}"
    
    def _parse_job_rankings(self, analysis_text: str, raw_job_data: list) -> list:
        """
        Parse job rankings from analysis text into structured data.
        
        Args:
            analysis_text: Complete analysis text from JobRankingAndAnalysisAgent
            raw_job_data: Original job data from API
            
        Returns:
            list: Structured job data for spreadsheet
        """
        jobs = []
        
        # Look for job entries in the analysis
        job_sections = re.split(r'### Job #\d+:', analysis_text)
        
        for i, section in enumerate(job_sections[1:], 1):  # Skip first empty split
            try:
                # Extract job title and company
                title_match = re.search(r'^([^at]+?)\s+at\s+(.+?)$', section.split('\n')[0].strip())
                if title_match:
                    job_title = title_match.group(1).strip()
                    company = title_match.group(2).strip()
                else:
                    job_title = f"Job {i}"
                    company = "Unknown Company"
                
                # Extract match score
                score_match = re.search(r'\*\*Match Score:\s*(\d+)/10\*\*', section)
                match_score = int(score_match.group(1)) if score_match else 0
                
                # Extract summary
                summary_match = re.search(r'\*\*Summary:\*\*\s*([^\n]+)', section)
                summary = summary_match.group(1) if summary_match else ""
                
                # Extract pros and cons
                pros_section = re.search(r'\*\*PROS:\*\*(.*?)\*\*CONS:\*\*', section, re.DOTALL)
                pros = pros_section.group(1).strip() if pros_section else ""
                
                cons_section = re.search(r'\*\*CONS:\*\*(.*?)(\*\*|$)', section, re.DOTALL)
                cons = cons_section.group(1).strip() if cons_section else ""
                
                # Try to match with raw job data for additional info
                location = ""
                salary = ""
                apply_link = ""
                
                if raw_job_data:
                    # Find matching job in raw data (simplified matching)
                    for raw_job in raw_job_data:
                        if any(word in raw_job.get('title', '').lower() for word in job_title.lower().split()[:2]):
                            location = raw_job.get('location', '')
                            if raw_job.get('salary_min') and raw_job.get('salary_max'):
                                salary = f"${raw_job['salary_min']:,} - ${raw_job['salary_max']:,}"
                            apply_link = raw_job.get('apply_link', '')
                            break
                
                jobs.append({
                    'Rank': i,
                    'Job Title': job_title,
                    'Company': company,
                    'Match Score': match_score,
                    'Location': location,
                    'Salary Range': salary,
                    'Summary': summary,
                    'Pros': pros.replace('- ', '').replace('\n', ' | '),
                    'Cons': cons.replace('- ', '').replace('\n', ' | '),
                    'Apply Link': apply_link
                })
                
            except Exception as e:
                print(f"Error parsing job {i}: {e}")
                continue
        
        return jobs
    
    def _parse_skills_data(self, analysis_text: str) -> list:
        """
        Parse skills analysis from text into structured data.
        
        Args:
            analysis_text: Complete analysis text
            
        Returns:
            list: Structured skills data
        """
        skills = []
        
        try:
            # Look for skills section
            if "SKILLS_FOR_DB:" in analysis_text:
                skills_section = analysis_text.split("SKILLS_FOR_DB:")[1]
                
                # Parse skill entries
                skill_lines = re.findall(r'\{"skill":\s*"([^"]+)",\s*"frequency":\s*(\d+),\s*"category":\s*"([^"]+)"\}', skills_section)
                
                for skill_name, frequency, category in skill_lines:
                    skills.append({
                        'Skill': skill_name,
                        'Frequency': int(frequency),
                        'Category': category,
                        'Demand Level': 'High' if int(frequency) >= 3 else 'Medium' if int(frequency) == 2 else 'Low'
                    })
            
            # Also parse from regular skills analysis section
            if "All Skills Mentioned Across Jobs:" in analysis_text:
                skills_text = analysis_text.split("All Skills Mentioned Across Jobs:")[1]
                if "Candidate's Strongest Matches:" in skills_text:
                    skills_text = skills_text.split("Candidate's Strongest Matches:")[0]
                
                # Parse skill mentions
                skill_mentions = re.findall(r'-\s*([^:]+):\s*Mentioned in (\d+) jobs?', skills_text)
                
                for skill_name, count in skill_mentions:
                    # Avoid duplicates
                    if not any(s['Skill'] == skill_name.strip() for s in skills):
                        skills.append({
                            'Skill': skill_name.strip(),
                            'Frequency': int(count),
                            'Category': 'General',
                            'Demand Level': 'High' if int(count) >= 3 else 'Medium' if int(count) == 2 else 'Low'
                        })
        
        except Exception as e:
            print(f"Error parsing skills: {e}")
        
        # Sort by frequency descending
        skills.sort(key=lambda x: x['Frequency'], reverse=True)
        
        return skills
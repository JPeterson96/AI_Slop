"""
Generic Agent classes for AI-powered task execution.
This module provides a base agent class that can be extended for specific tasks.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import re
from datetime import datetime
import os


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
            description="Extracts ALL job postings related to or containing the target positions from JSearch API data"
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
        
        keywords_text = job_keywords if job_keywords and job_keywords.strip() and job_keywords != "No specific skills filter" else "No specific ranking keywords (all jobs included based on position relevance only)"
        
        prompt = f"""You are analyzing {len(jobs)} real job postings from JSearch API (LinkedIn, Indeed, Monster, etc.).

**Target Positions:** {job_position}
**Keywords for Ranking:** {keywords_text}

**JSearch Job Postings:**
{jobs_text}

**Analysis Instructions:**
1. INCLUDE ALL jobs that are related to or contain elements of the target positions
2. Do NOT filter out jobs based on keywords - keywords are for ranking only
3. Provide a brief analysis of each job's relevance to the target positions
4. Note which jobs have the specified keywords for better ranking later

**Output Format:**
## Job Extraction Results - ALL POSITION-RELATED JOBS

**Total Jobs Analyzed:** {len(jobs)}
**Target Positions:** {job_position}
**Ranking Keywords:** {keywords_text}

**All Position-Related Jobs (to be included in spreadsheet):**

[For each relevant job, provide:]
### Job: [Title] at [Company]
**Position Relevance:** [How it relates to target positions]
**Keyword Presence:** [Which ranking keywords are mentioned, if any]
**Brief Summary:** [2-3 sentences about the role]

**Jobs Summary:**
- Total jobs included: [X]
- Jobs with ranking keywords: [Y]
- Most common job types: [List]
"""
        
        return orchestrator.query_llm(prompt)
    
    def _process_text_data(self, job_postings: str, job_position: str, job_keywords: str, orchestrator) -> str:
        """Process text-based job posting data (fallback mode)."""
        
        keywords_text = job_keywords if job_keywords and job_keywords.strip() and job_keywords != "No specific skills filter" else "No ranking keywords (including all position-related jobs)"
        
        prompt = f"""You are a job extraction system working with job posting text data.

**Target Job Positions:** {job_position}
**Ranking Keywords:** {keywords_text}

**Job Postings Data:**
{job_postings[:5000]}

**Instructions:**
1. Review each job posting in the data above
2. Extract ALL jobs that are related to or contain elements of the target positions
3. Do NOT filter out jobs based on keywords - keywords are for ranking assistance only
4. Include jobs even if they don't have the specified keywords
5. Return all relevant job postings with position relevance noted

**Inclusion Rules:**
- Include jobs with titles related to the target positions (e.g., "Frontend Dev", "Backend Engineer" for "Software Developer")
- Include junior, senior, lead, principal variations
- Include specialized roles (e.g., "Python Developer", "Full Stack Engineer")
- Note which jobs contain ranking keywords for later scoring

**Output Format:**
For each relevant job, provide:

**Job: [Title]**
Company: [Company]
Position Relevance: [How it relates to target positions]
Ranking Keywords Present: [List keywords found, or "None"]
[Original job details...]

---

If no position-related jobs found, respond with: "No position-related jobs found."
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
        
        keywords_text = job_keywords if job_keywords and job_keywords.strip() and job_keywords != "No specific skills filter" else "No ranking keywords provided (scoring based on position match only)"
        
        prompt = f"""You are an expert career advisor and job matching specialist. Analyze ALL the provided job postings to rank them by best fit.

        **CANDIDATE PROFILE:**
        Target Position(s): {job_position}
        Ranking Keywords (for scoring): {keywords_text}
        Resume Content: {resume[:3000]}

        **ALL AVAILABLE JOB POSTINGS:**
        {filtered_jobs[:4000]}

        **RANKING INSTRUCTIONS:**
        - Include ALL jobs in your analysis and ranking
        - Use the ranking keywords to boost scores for jobs that mention them
        - Jobs without keywords can still rank highly if they match positions well
        - Rank from best fit to worst fit based on position relevance + keyword presence

        **REQUIRED OUTPUT FORMAT:**

        ## JOB RANKINGS (Best to Worst Fit - ALL JOBS INCLUDED)

        For EVERY job, provide:

        ### Job #[NUMBER]: [Job Title] at [Company]
        **Match Score: [X/10]** (Position relevance: [Y/5] + Keyword bonus: [Z/5])
        **Summary:** [2-3 sentence overview of the role and fit explanation]

        **PROS:**
        - [Specific positive aspects that align with candidate's profile]
        - [Growth opportunities, company benefits, skill development]
        - [Location, salary, culture fit indicators]

        **CONS:**
        - [Missing requirements or skill gaps]
        - [Potential challenges or mismatches]
        - [Areas where candidate might struggle]

        **Key Skills Required:** [List 5-8 main technical/soft skills from job posting]
        **Ranking Keywords Found:** [List any of the specified keywords present]
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
        
        # DEBUG: Save analysis result for debugging parsing issues
        debug_analysis_file = "/Users/jamiepeterson/Desktop/example/AI_Slop/exports/debug_analysis_result.txt"
        if not os.path.exists(debug_analysis_file):
            try:
                os.makedirs(os.path.dirname(debug_analysis_file), exist_ok=True)
                with open(debug_analysis_file, 'w') as f:
                    f.write(f"DEBUG: AI Analysis Result\n")
                    f.write(f"Timestamp: {datetime.now()}\n")
                    f.write(f"Result length: {len(result)} characters\n")
                    f.write(f"{'='*60}\n\n")
                    f.write(result)
                print(f"[DEBUG] Saved analysis result to {debug_analysis_file}")
            except Exception as e:
                print(f"[DEBUG] Could not save analysis result: {e}")
        
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
        try:
            import pandas as pd
            import re
            from datetime import datetime
            import os
        except ImportError as e:
            error_msg = f"Required packages not installed: {e}. Run: pip install pandas openpyxl"
            orchestrator._update_status("Missing dependencies")
            return f"ERROR: {error_msg}"
        
        print("[DEBUG] Starting spreadsheet export...")
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
            print(f"[DEBUG] Ranking results length: {len(ranking_results)}")
            print(f"[DEBUG] Raw job data count: {len(raw_job_data)}")
            
            # Parse job rankings from the analysis text
            try:
                jobs_data = self._parse_job_rankings(ranking_results, raw_job_data)
                print(f"[DEBUG] Parsed {len(jobs_data)} jobs")
            except Exception as e:
                print(f"[DEBUG] Job parsing failed: {e}")
                jobs_data = []
            
            # Parse skills data
            try:
                skills_data = self._parse_skills_data(ranking_results)
                print(f"[DEBUG] Parsed {len(skills_data)} skills")
            except Exception as e:
                print(f"[DEBUG] Skills parsing failed: {e}")
                skills_data = []
            
            # Create timestamp for file naming
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Create output directory if it doesn't exist
            output_dir = "/Users/jamiepeterson/Desktop/example/AI_Slop/exports"
            os.makedirs(output_dir, exist_ok=True)
            
            orchestrator._update_status("Creating Excel file...")
            
            # Create Excel file with multiple sheets
            filename = f"job_analysis_results_{timestamp}.xlsx"
            filepath = os.path.join(output_dir, filename)
            
            print(f"[DEBUG] Creating Excel file at: {filepath}")
            
            with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
                # Sheet 1: MAIN Job Analysis (detailed breakdown - primary purpose)
                if jobs_data:
                    job_analysis_data = []
                    for job in jobs_data:
                        # Extract detailed job info for the main analysis sheet
                        job_analysis_data.append({
                            'Rank': job.get('Rank', 0),
                            'Job Title': job.get('Job Title', 'Unknown'),
                            'Company': job.get('Company', 'Unknown'),
                            'Location': job.get('Location', 'Not specified'),
                            'Match Score': f"{job.get('Match Score', 0)}/10",
                            'Salary Range': job.get('Salary Range', 'Not disclosed'),
                            'Summary': job.get('Summary', 'No summary available'),
                            'Pros': job.get('Pros', 'See raw analysis'),
                            'Cons': job.get('Cons', 'See raw analysis'), 
                            'Key Skills Required': job.get('Key Skills', 'Not specified'),
                            'Keywords Found': job.get('Keywords Found', 'None'),
                            'Skills Match': job.get('Skills Match', 'Not analyzed'),
                            'Apply Link': job.get('Apply Link', 'Not available'),
                            'Employment Type': job.get('Employment Type', 'Not specified'),
                            'Remote Available': job.get('Remote', 'Unknown'),
                            'Experience Level': job.get('Experience Level', 'Not specified')
                        })
                    
                    job_analysis_df = pd.DataFrame(job_analysis_data)
                    job_analysis_df.to_excel(writer, sheet_name='Job Analysis', index=False)
                
                # Sheet 2: Job Rankings (simplified view)
                if jobs_data:
                    jobs_df = pd.DataFrame(jobs_data)
                    jobs_df.to_excel(writer, sheet_name='Job Rankings', index=False)
                
                # Sheet 3: Skills Analysis
                if skills_data:
                    skills_df = pd.DataFrame(skills_data)
                    skills_df.to_excel(writer, sheet_name='Skills Analysis', index=False)
                
                # Sheet 4: Summary
                summary_data = [{
                    'Target Positions': job_position,
                    'Ranking Keywords': job_keywords,
                    'Search Note': 'All position-related jobs included, keywords used for ranking only',
                    'Total Jobs Analyzed': len(jobs_data),
                    'Export Date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    'Top Ranked Job': jobs_data[0]['Job Title'] if jobs_data else 'No jobs found',
                    'Average Match Score': sum(job.get('Match Score', 0) for job in jobs_data) / len(jobs_data) if jobs_data else 0,
                    'Jobs with Keywords': len([j for j in jobs_data if j.get('Keywords Found', 'None') != 'None']) if jobs_data else 0
                }]
                summary_df = pd.DataFrame(summary_data)
                summary_df.to_excel(writer, sheet_name='Summary', index=False)
                
                # Sheet 5: Raw Analysis Text
                truncated_analysis = ranking_results[:15000] + "..." if len(ranking_results) > 15000 else ranking_results
                raw_analysis = pd.DataFrame([{
                    'Complete Analysis': truncated_analysis
                }])
                raw_analysis.to_excel(writer, sheet_name='Raw Analysis', index=False)
            
            print(f"[DEBUG] Excel file created successfully at: {filepath}")
            
            # Verify file exists
            if os.path.exists(filepath):
                file_size = os.path.getsize(filepath)
                print(f"[DEBUG] File verified: {filepath} ({file_size} bytes)")
            else:
                print(f"[DEBUG] WARNING: File not found after creation: {filepath}")
            
            orchestrator._update_status("Spreadsheet export completed!")
            
            return f"""
## SPREADSHEET EXPORT COMPLETED

**File Created:** {filename}
**Location:** {filepath}
**Sheets Created:**
- **Job Analysis**: {len(jobs_data)} jobs with complete breakdown (MAIN SHEET)
- Job Rankings: Simplified job ranking view
- Skills Analysis: {len(skills_data)} skills extracted across all jobs
- Summary: High-level overview and statistics  
- Raw Analysis: Complete text analysis from AI

**Export Statistics:**
- Jobs Analyzed: {len(jobs_data)}
- Skills Identified: {len(skills_data)}
- Export Time: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

**Main Purpose:** The 'Job Analysis' sheet contains the comprehensive breakdown that is the core purpose of this application.

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
        
        try:
            # Look for job entries in the analysis with improved patterns
            job_sections = []
            
            # Try multiple patterns to find job sections
            patterns = [
                r'### Job #\[\d+\]:',  # New format: ### Job #[1]:
                r'### Job #\d+:',      # Old format: ### Job #1:
                r'### Job \d+:',       # Alternative: ### Job 1:
                r'## Job #?\d+',       # Fallback patterns
                r'\*\*Job \d+\*\*'
            ]
            
            best_sections = []
            best_count = 0
            
            for pattern in patterns:
                sections = re.split(pattern, analysis_text)
                print(f"[DEBUG] Pattern '{pattern}' found {len(sections)-1} sections")
                if len(sections) > best_count:
                    best_sections = sections
                    best_count = len(sections)
            
            job_sections = best_sections
            print(f"[DEBUG] Using best pattern with {len(job_sections)-1} job sections")
            print(f"[DEBUG] Analysis text length: {len(analysis_text)}")
            print(f"[DEBUG] First 300 chars of analysis: {analysis_text[:300]}...")
            
            for i, section in enumerate(job_sections[1:], 1):  # Skip first empty split
                if i > 10:  # Safety limit to prevent infinite loops
                    print(f"[DEBUG] Limiting to first 10 jobs")
                    break
                    
                try:
                    # Extract job title and company
                    lines = section.split('\n')
                    first_line = lines[0].strip() if lines else f"Job {i}"
                    
                    # Try different patterns for title and company extraction
                    title_match = re.search(r'^([^at]+?)\s+at\s+(.+?)$', first_line)
                    if not title_match:
                        # Try pattern without " at " separator
                        title_match = re.search(r'^(.+?)\s+(.+?)$', first_line)
                    
                    if title_match and ' at ' in first_line:
                        parts = first_line.split(' at ', 1)
                        job_title = parts[0].strip()
                        company = parts[1].strip()
                    elif title_match:
                        job_title = title_match.group(1).strip()
                        company = title_match.group(2).strip() if len(title_match.groups()) > 1 else "Unknown Company"
                    else:
                        job_title = first_line[:50] if len(first_line) > 50 else first_line
                        company = "Unknown Company"
                    
                    # Extract match score
                    score_match = re.search(r'\*\*Match Score:\s*(\d+)/10\*\*', section)
                    match_score = int(score_match.group(1)) if score_match else 0
                    
                    # Extract summary
                    summary_match = re.search(r'\*\*Summary:\*\*\s*([^\n]+)', section)
                    summary = summary_match.group(1)[:200] if summary_match else f"Analysis for {job_title}"
                    
                    # Extract pros and cons with better parsing
                    pros_match = re.search(r'\*\*PROS:\*\*\s*(.*?)\*\*CONS:\*\*', section, re.DOTALL)
                    pros = pros_match.group(1).strip() if pros_match else "See Raw Analysis sheet for details"
                    
                    cons_match = re.search(r'\*\*CONS:\*\*\s*(.*?)\*\*', section, re.DOTALL)  
                    cons = cons_match.group(1).strip() if cons_match else "See Raw Analysis sheet for details"
                    
                    # Extract key skills
                    skills_match = re.search(r'\*\*Key Skills Required:\*\*\s*([^\n]+)', section)
                    key_skills = skills_match.group(1).strip() if skills_match else "Not specified"
                    
                    # Extract ranking keywords found
                    keywords_match = re.search(r'\*\*Ranking Keywords Found:\*\*\s*([^\n]+)', section)
                    if not keywords_match:
                        keywords_match = re.search(r'\*\*Skills Match:\*\*\s*([^\n/]+)', section)
                    keywords_found = keywords_match.group(1).strip() if keywords_match else "None"
                    
                    # Extract skills match
                    skills_match_text = re.search(r'\*\*Skills Match:\*\*\s*([^\n]+)', section)
                    skills_match_info = skills_match_text.group(1).strip() if skills_match_text else "Not analyzed"
                    
                    # Try to match with raw job data for additional info
                    location = ""
                    salary = ""
                    apply_link = ""
                    employment_type = ""
                    remote = ""
                    
                    if raw_job_data and i <= len(raw_job_data):
                        raw_job = raw_job_data[i-1]
                        location = raw_job.get('location', '')
                        employment_type = raw_job.get('employment_type', '')
                        remote = "Yes" if raw_job.get('is_remote', False) else "No"
                        if raw_job.get('salary_min') and raw_job.get('salary_max'):
                            salary = f"${raw_job['salary_min']:,} - ${raw_job['salary_max']:,}"
                        apply_link = raw_job.get('apply_link', '')
                    
                    jobs.append({
                        'Rank': i,
                        'Job Title': job_title,
                        'Company': company,
                        'Match Score': match_score,
                        'Location': location,
                        'Salary Range': salary,
                        'Employment Type': employment_type,
                        'Remote': remote,
                        'Summary': summary,
                        'Pros': pros[:500] + "..." if len(pros) > 500 else pros,  # Limit length for Excel
                        'Cons': cons[:500] + "..." if len(cons) > 500 else cons,
                        'Key Skills': key_skills,
                        'Keywords Found': keywords_found,
                        'Skills Match': skills_match_info,
                        'Apply Link': apply_link
                    })
                    
                    print(f"[DEBUG] Parsed job {i}: {job_title}")
                    
                except Exception as e:
                    print(f"[DEBUG] Error parsing job {i}: {e}")
                    continue
        
        except Exception as e:
            print(f"[DEBUG] Job parsing error: {e}")
            # Return at least one job entry to prevent empty sheets
            jobs = [{
                'Rank': 1,
                'Job Title': 'Analysis Available',
                'Company': 'See Raw Analysis',
                'Match Score': 0,
                'Location': '',
                'Salary Range': '',
                'Summary': 'Job data available in Raw Analysis sheet',
                'Pros': 'See Raw Analysis sheet',
                'Cons': 'See Raw Analysis sheet',
                'Apply Link': ''
            }]
        
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
            print(f"[DEBUG] Skills parsing error: {e}")
            # Return minimal skills data to avoid complete failure
            skills = [{
                'Skill': 'Analysis Available',
                'Frequency': 1,
                'Category': 'See Raw Analysis',
                'Demand Level': 'N/A'
            }]
        
        # Sort by frequency descending
        if skills:
            skills.sort(key=lambda x: x.get('Frequency', 0), reverse=True)
        
        return skills
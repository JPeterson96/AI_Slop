"""
JSearch API Client for fetching real job data from RapidAPI.
This module handles all interactions with the JSearch API to retrieve job postings.

JSearch API Documentation: https://rapidapi.com/letscrape-6bRBa3QguO5/api/jsearch
"""
import os
import requests
from typing import Dict, List, Any, Optional
import json
import time
import logging
from dotenv import load_dotenv

# Load environment variables from auth.env file
load_dotenv('auth.env')


class JSearchClient:
    """
    Client for interacting with JSearch API via RapidAPI.
    Provides methods to search for jobs and retrieve detailed job information.
    
    SETUP INSTRUCTIONS:
    1. Sign up at https://rapidapi.com/
    2. Subscribe to JSearch API (has free tier)
    3. Get your RapidAPI key
    4. Set environment variable: export RAPIDAPI_KEY="your-key-here"
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize JSearch client.
        
        Args:
            api_key: RapidAPI key. If not provided, will look for RAPIDAPI_KEY env var
        """
        self.api_key = api_key or os.getenv("RAPIDAPI_KEY")
        self.base_url = "https://jsearch.p.rapidapi.com"
        self.rapidapi_host = os.getenv("RAPIDAPI_HOST", "jsearch.p.rapidapi.com")
        self.headers = {
            "X-RapidAPI-Key": self.api_key,
            "X-RapidAPI-Host": self.rapidapi_host
        }
        
        if not self.api_key:
            raise ValueError("RapidAPI key not provided. Set RAPIDAPI_KEY environment variable or pass api_key parameter.")
    
    def search_jobs(
        self,
        query: str,
        page: int = 1,
        num_pages: int = 200,
        date_posted: str = "all",
        remote_jobs_only: bool = False,
        employment_types: str = "FULLTIME",
        company_types: str = None,
        country: str = "US"
    ) -> Dict[str, Any]:
        """
        Search for jobs using JSearch API.
        
        Args:
            query: Search query (e.g., "Python developer in New York")
            page: Page number to retrieve (default: 1)
            num_pages: Number of pages to retrieve (default: 1, max: 20)
            date_posted: Filter by date posted ("all", "today", "3days", "week", "month")
            remote_jobs_only: Whether to search only remote jobs
            employment_types: Employment types ("FULLTIME", "CONTRACTOR", "PARTTIME", "INTERN")
            job_requirements: Experience requirements ("under_3_years_experience", "more_than_3_years_experience", "no_experience", "no_degree")
            company_types: Company types to filter by
            country: Country code (default: "US")
            
        Returns:
            Dict containing job search results
        """
        url = f"{self.base_url}/search"
        
        params = {
            "query": query,
            "page": str(page),
            "num_pages": str(num_pages),
            "date_posted": date_posted,
            "remote_jobs_only": str(remote_jobs_only).lower(),
            "employment_types": employment_types,
            "country": country
        }
        
        # Add optional parameters
        if company_types:
            params["company_types"] = company_types
        
        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            return {
                "status": "error",
                "message": f"JSearch API error: {str(e)}",
                "data": []
            }
    
    def get_job_details(self, job_id: str) -> Dict[str, Any]:
        """
        Get detailed information for a specific job.
        
        Args:
            job_id: The job ID from JSearch
            
        Returns:
            Dict containing detailed job information
        """
        url = f"{self.base_url}/job-details"
        
        params = {
            "job_id": job_id
        }
        
        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            return {
                "status": "error",
                "message": f"JSearch API error: {str(e)}",
                "data": {}
            }
    
    def search_jobs_by_position_and_keywords(
        self,
        job_positions: str,
        job_keywords: str,
        location: str = "United States",
        max_results: int = 2000
    ) -> List[Dict[str, Any]]:
        """
        Search for jobs based on positions and keywords - optimized for orchestrator integration.
        Keywords are used for skill/requirement filtering, NOT for job title matching.
        
        Args:
            job_positions: Comma-separated job positions (e.g., "Software Engineer, Data Scientist")
            job_keywords: Comma-separated keywords for skill filtering (e.g., "Python, Machine Learning, Docker")
            location: Location to search in (default: "United States")
            max_results: Maximum number of results to return (default: 10)
            
        Returns:
            List of standardized job dictionaries
        """
        all_jobs = []
        positions = [pos.strip() for pos in job_positions.split(',')]
        keywords = [kw.strip() for kw in job_keywords.split(',') if kw.strip()]
        
        # Search for each position
        for position in positions:
            if len(all_jobs) >= max_results:
                break
                
            # Create search query - only use position and location, NOT keywords in search
            # Keywords will be used for filtering the results
            query = f"{position} in {location}"
            
            # Make API call
            results = self.search_jobs(
                query=query,
                num_pages=200,
                employment_types="FULLTIME,CONTRACTOR",
                date_posted="month"  # Recent jobs only
            )
            
            if results.get("status") == "OK" and results.get("data"):
                jobs = results["data"]
                print(f"[JSearch] API returned {len(jobs)} jobs for position: {position}")
                
                # Filter and standardize job data
                for job in jobs:
                    if len(all_jobs) >= max_results:
                        break
                    
                    # Filter jobs that match keywords in skills/requirements
                    if self._job_matches_keywords(job, keywords):
                        standardized_job = self._standardize_job_data(job)
                        all_jobs.append(standardized_job)
            
            # Rate limiting - be respectful to the API
            time.sleep(0.5)
        
        return all_jobs
    
    def _job_matches_keywords(self, job: Dict[str, Any], keywords: List[str]) -> bool:
        """
        Check if a job matches the specified keywords in skills/requirements (NOT job title).
        Keywords should represent skills, technologies, or requirements.
        
        Args:
            job: Job data from JSearch API
            keywords: List of keywords to match (skills, technologies, frameworks)
            
        Returns:
            bool: True if job matches keywords in skills/requirements
        """
        if not keywords:
            return True
        
        # Focus on skills/requirements sections, NOT job title
        # Get job highlights which contain skills and qualifications
        highlights = job.get("job_highlights", {})
        qualifications = highlights.get("Qualifications", [])
        responsibilities = highlights.get("Responsibilities", [])
        benefits = highlights.get("Benefits", [])
        
        # Combine skills-focused text (exclude job title to avoid title bias)
        skills_text_parts = [
            job.get("job_description", ""),  # Full description contains skills
            " ".join(qualifications) if qualifications else "",
            " ".join(responsibilities) if responsibilities else "",
            " ".join(benefits) if benefits else ""
        ]
        
        searchable_text = " ".join(skills_text_parts).lower()
        
        # Check each keyword individually
        matches = []
        for keyword in keywords:
            keyword_lower = keyword.lower()
            
            # Check for exact match and common variations
            keyword_variations = [
                keyword_lower,
                keyword_lower.replace(" ", "-"),  # "machine learning" -> "machine-learning"
                keyword_lower.replace("-", " "),  # "full-stack" -> "full stack"
                keyword_lower.replace("javascript", "js"),  # Common abbreviations
                keyword_lower.replace("js", "javascript")
            ]
            
            for variation in keyword_variations:
                if variation in searchable_text:
                    matches.append(keyword)
                    break
        
        match_percentage = len(matches) / len(keywords)
        required_match_percentage = 0.4  # At least 40% of keywords must match
        
        return match_percentage >= required_match_percentage
    
    def _standardize_job_data(self, job: Dict[str, Any]) -> Dict[str, Any]:
        """
        Standardize JSearch job data for use with orchestrator agents.
        
        Args:
            job: Raw job data from JSearch API
            
        Returns:
            Dict: Standardized job data
        """
        # Extract highlights and requirements
        highlights = job.get("job_highlights", {})
        qualifications = highlights.get("Qualifications", [])
        responsibilities = highlights.get("Responsibilities", [])
        
        return {
            "job_id": job.get("job_id"),
            "title": job.get("job_title", ""),
            "company": job.get("employer_name", ""),
            "location": f"{job.get('job_city', '')}, {job.get('job_state', '')}".strip(", "),
            "employment_type": job.get("job_employment_type", ""),
            "is_remote": job.get("job_is_remote", False),
            "description": job.get("job_description", ""),
            "apply_link": job.get("job_apply_link", ""),
            "posted_date": job.get("job_posted_at_datetime_utc", ""),
            "salary_min": job.get("job_min_salary"),
            "salary_max": job.get("job_max_salary"),
            "salary_currency": job.get("job_salary_currency"),
            "required_skills": qualifications,
            "responsibilities": responsibilities,
            "experience_required": job.get("job_required_experience", {}),
            "education_required": job.get("job_required_education", {}),
            "company_website": job.get("employer_website"),
            "company_logo": job.get("employer_logo"),
            
            # Raw data for agents that need full context
            "raw_data": job
        }
    
    def format_jobs_for_agents(self, jobs: List[Dict[str, Any]]) -> str:
        """
        Format job data as text for agent consumption.
        
        Args:
            jobs: List of standardized job dictionaries
            
        Returns:
            str: Formatted job data for agents
        """
        if not jobs:
            return "No job postings found matching the specified criteria."
        
        formatted_jobs = []
        
        for i, job in enumerate(jobs, 1):
            job_text = f"""
Job Posting {i}: {job['title']} at {job['company']}
Location: {job['location']} {'(Remote)' if job['is_remote'] else ''}
Employment Type: {job['employment_type']}
Apply Link: {job['apply_link']}

Description: {job['description'][:500]}{'...' if len(job['description']) > 500 else ''}

Required Skills: {', '.join(job['required_skills']) if job['required_skills'] else 'Not specified'}
Key Responsibilities: {', '.join(job['responsibilities']) if job['responsibilities'] else 'Not specified'}

---"""
            formatted_jobs.append(job_text)
        
        return "\n".join(formatted_jobs)


def test_jsearch_integration():
    """
    Test function to verify JSearch integration works.
    Run this to test your API key and connection.
    """
    try:
        client = JSearchClient()
        
        # Test basic search
        results = client.search_jobs_by_position_and_keywords(
            job_positions="Software Engineer",
            job_keywords="Python, Django",
            max_results=3
        )
        
        print(f"Found {len(results)} jobs")
        for job in results:
            print(f"- {job['title']} at {job['company']} ({job['location']})")
        
        return True
        
    except Exception as e:
        print(f"JSearch integration test failed: {e}")
        return False


if __name__ == "__main__":
    # Run test when script is executed directly
    test_jsearch_integration()

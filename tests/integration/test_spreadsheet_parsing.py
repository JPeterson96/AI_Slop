#!/usr/bin/env python
"""
Test of spreadsheet parsing with sample data
"""

import os
import sys
import unittest

# Add the project directory to Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from AI_Slop.agents import SpreadsheetExportAgent


class TestSpreadsheetParsing(unittest.TestCase):
    """Test spreadsheet parsing functionality"""
    
    def setUp(self):
        """Set up test data"""
        # Sample analysis text in the new format
        self.sample_analysis = """## JOB RANKINGS (Best to Worst Fit - ALL JOBS INCLUDED)

### Job #[1]: Java, Javascript, Python, NodeJS Software Engineer at Walmart
**Match Score: 9/10** (Position relevance: 4/5 + Keyword bonus: 5/5)
**Summary:** This role is a direct match for the target positions, requiring skills in Java, Python, JavaScript, and NodeJS.

**PROS:**
- Perfect match for Python and JavaScript skills
- Strong company reputation and benefits
- Remote work available

**CONS:**
- May require Java experience which candidate lacks
- High competition for this role

**Key Skills Required:** Python, JavaScript, Java, NodeJS, React, SQL
**Ranking Keywords Found:** Python, JavaScript
**Skills Match:** Python (aligned), JavaScript (aligned) / Java (missing)

---

### Job #[2]: Frontend Developer - React Specialist at TechCorp
**Match Score: 7/10** (Position relevance: 4/5 + Keyword bonus: 3/5)
**Summary:** Good match for frontend development with React focus and some Python integration.

**PROS:**
- React expertise matches well
- Growing company with good culture
- Competitive salary range

**CONS:**
- Limited backend development opportunities
- Startup environment may be unstable

**Key Skills Required:** React, JavaScript, HTML, CSS, Python
**Ranking Keywords Found:** Python, JavaScript
**Skills Match:** React (aligned), JavaScript (aligned) / Backend (limited)

---

## OVERALL SKILLS ANALYSIS

**All Skills Mentioned Across Jobs:**
- Python: Mentioned in 2 jobs
- JavaScript: Mentioned in 2 jobs
- React: Mentioned in 2 jobs
"""
        
        # Sample raw job data
        self.sample_raw_data = [
            {
                'title': 'Java, Javascript, Python, NodeJS Software Engineer',
                'company': 'Walmart',
                'location': 'Alexandria, Virginia',
                'employment_type': 'Full-time',
                'is_remote': True,
                'salary_min': 80000,
                'salary_max': 120000,
                'apply_link': 'https://example.com/job1'
            },
            {
                'title': 'Frontend Developer - React Specialist',
                'company': 'TechCorp',
                'location': 'San Francisco, CA',
                'employment_type': 'Full-time',
                'is_remote': False,
                'salary_min': 90000,
                'salary_max': 130000,
                'apply_link': 'https://example.com/job2'
            }
        ]
        
        self.agent = SpreadsheetExportAgent()
    
    def test_job_parsing(self):
        """Test job ranking parsing"""
        jobs = self.agent._parse_job_rankings(self.sample_analysis, self.sample_raw_data)
        
        self.assertGreater(len(jobs), 0, "Should parse at least one job")
        
        # Check first job structure
        first_job = jobs[0]
        self.assertIn('Rank', first_job)
        self.assertIn('Job Title', first_job)
        self.assertIn('Company', first_job)
        self.assertIn('Match Score', first_job)
        
        print(f"✅ Parsed {len(jobs)} jobs successfully")
        
    def test_skills_parsing(self):
        """Test skills data parsing"""
        skills = self.agent._parse_skills_data(self.sample_analysis)
        
        self.assertGreater(len(skills), 0, "Should parse at least one skill")
        
        # Check skills structure
        for skill in skills[:3]:  # Check first 3 skills
            self.assertIn('Skill', skill)
            
        print(f"✅ Parsed {len(skills)} skills successfully")
        
    def test_complete_parsing_workflow(self):
        """Test the complete parsing workflow"""
        jobs = self.agent._parse_job_rankings(self.sample_analysis, self.sample_raw_data)
        skills = self.agent._parse_skills_data(self.sample_analysis)
        
        # Verify we got data
        self.assertGreater(len(jobs), 0)
        self.assertGreater(len(skills), 0)
        
        # Verify job details
        for job in jobs:
            self.assertIsNotNone(job.get('Job Title'))
            self.assertIsNotNone(job.get('Company'))
            
        print(f"✅ Complete parsing workflow successful: {len(jobs)} jobs, {len(skills)} skills")


if __name__ == "__main__":
    unittest.main()
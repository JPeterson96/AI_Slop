#!/usr/bin/env python
"""
Quick integration test with mock data to verify orchestrator workflow
"""

import os
import sys
import unittest

# Add the project directory to Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'AI_Slop.settings')
import django
django.setup()

from AI_Slop.orchestrator import Orchestrator
from AI_Slop.agents import SpreadsheetExportAgent


class TestJobAnalysisWorkflow(unittest.TestCase):
    """Test the job analysis workflow with mock data"""
    
    def setUp(self):
        """Set up test environment"""
        self.orchestrator = Orchestrator()
        
        # Mock job data for testing
        self.mock_job_data = {
            "job_position": "Software Developer",
            "job_keywords": "Python, Django", 
            "resume": "Experienced developer with Python and web development skills."
        }
    
    def test_orchestrator_initialization(self):
        """Test that orchestrator initializes properly"""
        self.assertIsInstance(self.orchestrator, Orchestrator)
        self.assertIsNotNone(self.orchestrator.llm_client)
        print("✅ Orchestrator initialized successfully")
    
    def test_mock_workflow_execution(self):
        """Test workflow execution with mock data"""
        
        # Set up mock context for testing
        self.orchestrator.context["ExtractJobPostingInfo_result"] = """Job Extraction Results

Job 1: Senior Python Developer at Google
Position Relevance: Perfect match for Software Developer with Python focus
Keywords Present: Python
Summary: Excellent opportunity for experienced Python developer

Job 2: Full Stack Engineer at Microsoft  
Position Relevance: Good match for Software Developer role
Keywords Present: Python, Django
Summary: Full stack role with Django backend development"""

        self.orchestrator.context["JobRankingAndAnalysisAgent_result"] = """## JOB RANKINGS (Best to Worst Fit - ALL JOBS INCLUDED)

### Job #[1]: Senior Python Developer at Google
**Match Score: 9/10** (Position relevance: 5/5 + Keyword bonus: 4/5)
**Summary:** Perfect match for target Software Developer position with strong Python focus and excellent career growth.

**PROS:**
- Perfect Python skill match
- Excellent company reputation and benefits
- Strong learning opportunities
- Competitive compensation package

**CONS:**
- High competition for role
- May require advanced algorithms knowledge

**Key Skills Required:** Python, Algorithms, System Design, Git, Linux
**Ranking Keywords Found:** Python
**Skills Match:** Python (perfect match) / Advanced algorithms (to develop)

---

### Job #[2]: Full Stack Engineer at Microsoft
**Match Score: 8/10** (Position relevance: 4/5 + Keyword bonus: 4/5)
**Summary:** Excellent match for full-stack development with Django backend and strong career prospects.

**PROS:**
- Django framework experience directly applicable
- Full-stack development aligns with career goals  
- Microsoft benefits and stability
- Remote work options available

**CONS:**
- May require frontend framework learning
- Large corporate environment

**Key Skills Required:** Django, Python, React, JavaScript, SQL, Azure
**Ranking Keywords Found:** Python, Django
**Skills Match:** Python, Django (excellent match) / React (to learn)

---

## OVERALL SKILLS ANALYSIS

**All Skills Mentioned Across Jobs:**
- Python: Mentioned in 2 jobs
- Django: Mentioned in 1 job
- JavaScript: Mentioned in 1 job
- React: Mentioned in 1 job
- SQL: Mentioned in 1 job"""

        # Add mock raw data
        self.orchestrator.context["raw_job_data"] = [
            {
                'title': 'Senior Python Developer',
                'company': 'Google',
                'location': 'Mountain View, CA',
                'employment_type': 'Full-time',
                'is_remote': False,
                'salary_min': 150000,
                'salary_max': 200000,
                'apply_link': 'https://careers.google.com/python-dev'
            },
            {
                'title': 'Full Stack Engineer',
                'company': 'Microsoft',
                'location': 'Seattle, WA',
                'employment_type': 'Full-time', 
                'is_remote': True,
                'salary_min': 130000,
                'salary_max': 180000,
                'apply_link': 'https://careers.microsoft.com/fullstack'
            }
        ]
        
        # Test spreadsheet export directly
        export_agent = SpreadsheetExportAgent()
        
        result = export_agent.execute({
            **self.mock_job_data,
            **self.orchestrator.context
        }, self.orchestrator)
        
        # Verify result is not None and contains expected content
        self.assertIsNotNone(result)
        self.assertIn("spreadsheet", result.lower())
        
        print("✅ Mock workflow execution successful")
        print(f"📊 Export Result Preview: {result[:100]}...")
        
    def test_context_management(self):
        """Test that orchestrator manages context properly"""
        test_key = "test_data"
        test_value = "test_value"
        
        self.orchestrator.context[test_key] = test_value
        self.assertEqual(self.orchestrator.context[test_key], test_value)
        
        print("✅ Context management working properly")


if __name__ == "__main__":
    print("🚀 Quick Job Analysis Integration Test\n")
    unittest.main()
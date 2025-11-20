#!/usr/bin/env python3
"""
Test script to verify SpreadsheetExportAgent file creation works.
"""
import sys
import os
from datetime import datetime

# Add project root to path
sys.path.insert(0, '/Users/jamiepeterson/Desktop/example/AI_Slop')

def test_spreadsheet_export():
    """Test spreadsheet export functionality."""
    print("🧪 Testing SpreadsheetExportAgent file creation...")
    
    try:
        from AI_Slop.agents import SpreadsheetExportAgent
        from AI_Slop.orchestrator import Orchestrator
        
        # Create test context
        test_context = {
            "job_position": "Software Developer",
            "job_keywords": "Python, Django",
            "JobRankingAndAnalysisAgent_result": """
## JOB RANKINGS (Best to Worst Fit)

### Job #1: Senior Python Developer at TechCorp
**Match Score: 8/10**
**Summary:** Strong alignment with Python expertise and remote work preference

**PROS:**
- Perfect match for Python/Django skills
- Remote-first company culture  
- Competitive salary range ($120k-160k)

**CONS:**
- Requires 2+ years DevOps experience
- Fast-paced startup environment

### Job #2: Junior Software Engineer at StartupCo
**Match Score: 6/10**
**Summary:** Good entry-level opportunity with growth potential

**PROS:**
- Great for career growth
- Modern tech stack
- Flexible work arrangements

**CONS:**
- Lower salary range
- High-pressure environment

## OVERALL SKILLS ANALYSIS

**All Skills Mentioned Across Jobs:**
- Python: Mentioned in 2 jobs
- Django: Mentioned in 2 jobs
- Docker: Mentioned in 1 jobs

**SKILLS_FOR_DB:**
[
{"skill": "Python", "frequency": 2, "category": "Programming Language"},
{"skill": "Django", "frequency": 2, "category": "Framework"},
{"skill": "Docker", "frequency": 1, "category": "DevOps"}
]
""",
            "raw_job_data": [
                {
                    "title": "Senior Python Developer",
                    "company": "TechCorp",
                    "location": "Remote",
                    "salary_min": 120000,
                    "salary_max": 160000,
                    "apply_link": "https://example.com/job1"
                },
                {
                    "title": "Junior Software Engineer", 
                    "company": "StartupCo",
                    "location": "San Francisco, CA",
                    "salary_min": 80000,
                    "salary_max": 100000,
                    "apply_link": "https://example.com/job2"
                }
            ]
        }
        
        # Create mock orchestrator with status callback
        class MockOrchestrator:
            def _update_status(self, message):
                print(f"[STATUS] {message}")
        
        orchestrator = MockOrchestrator()
        
        # Create and test agent
        agent = SpreadsheetExportAgent()
        print(f"Agent created: {agent.name}")
        
        # Execute export
        result = agent.execute(test_context, orchestrator)
        print(f"Export result:\n{result}")
        
        # Check if file was created
        exports_dir = "/Users/jamiepeterson/Desktop/example/AI_Slop/exports"
        if os.path.exists(exports_dir):
            files = os.listdir(exports_dir)
            xlsx_files = [f for f in files if f.endswith('.xlsx')]
            print(f"\nFiles in exports directory: {len(xlsx_files)} Excel files")
            
            if xlsx_files:
                latest_file = max(xlsx_files, key=lambda f: os.path.getctime(os.path.join(exports_dir, f)))
                filepath = os.path.join(exports_dir, latest_file)
                file_size = os.path.getsize(filepath)
                print(f"✅ Latest file: {latest_file} ({file_size:,} bytes)")
                
                # Try to read the file to verify it's valid
                try:
                    import pandas as pd
                    excel_data = pd.read_excel(filepath, sheet_name=None)
                    print(f"✅ File is readable. Sheets: {list(excel_data.keys())}")
                    return True
                except Exception as e:
                    print(f"❌ File exists but can't be read: {e}")
                    return False
            else:
                print(f"❌ No Excel files found in {exports_dir}")
                return False
        else:
            print(f"❌ Exports directory doesn't exist: {exports_dir}")
            return False
            
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure pandas and openpyxl are installed: pip install pandas openpyxl")
        return False
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🔍 Testing Spreadsheet Export Functionality\n")
    
    success = test_spreadsheet_export()
    
    if success:
        print(f"\n🎉 Spreadsheet export test PASSED!")
        print(f"✅ File creation is working correctly")
    else:
        print(f"\n❌ Spreadsheet export test FAILED!")
        print(f"🔧 Check the error messages above for troubleshooting")
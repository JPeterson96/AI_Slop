#!/usr/bin/env python3
"""
Test script to verify orchestrator workflow execution.
Run this to test the complete AI workflow.
"""
import sys

# Add project root to path
sys.path.insert(0, '/Users/jamiepeterson/Desktop/example/AI_Slop')

def test_orchestrator_workflow():
    """Test the complete orchestrator workflow."""
    print("🧪 Testing Orchestrator Workflow...")
    
    try:
        from AI_Slop.orchestrator import Orchestrator
        from AI_Slop.agents import ExtractJobPostingInfo, JobRankingAndAnalysis, SpreadsheetExportAgent
        
        # Initialize orchestrator
        orchestrator = Orchestrator()
        
        # Register agents
        orchestrator.register_agent(ExtractJobPostingInfo())
        orchestrator.register_agent(JobRankingAndAnalysis())
        orchestrator.register_agent(SpreadsheetExportAgent())
        
        print(f"✅ Orchestrator initialized with {len(orchestrator.agents)} agents")
        
        # Test LLM setup
        validation = orchestrator.validate_llm_setup()
        print(f"LLM Setup Valid: {validation['test_query_successful']}")
        
        if not validation['test_query_successful']:
            print("❌ LLM setup failed - cannot continue with workflow test")
            return False
        
        # Test basic workflow with mock data
        test_job_data = {
            "job_position": "Software Developer",
            "job_keywords": "Python, Django",
            "resume": "Experienced software developer with 3 years of Python and Django experience. Built web applications and REST APIs."
        }
        
        print("\n🔄 Testing workflow execution...")
        
        # Execute workflow (this will try to fetch real jobs)
        results = orchestrator.execute_workflow(test_job_data)
        
        print(f"✅ Workflow completed")
        print(f"Stages completed: {len(results['workflow_stages'])}")
        print(f"LLM Provider: {results['llm_provider_info']['provider']}")
        
        # Check if all expected stages completed
        expected_stages = ["job_extraction", "job_ranking", "spreadsheet_export"]
        completed_stages = list(results['workflow_stages'].keys())
        
        all_stages_completed = all(stage in completed_stages for stage in expected_stages)
        
        if all_stages_completed:
            print(f"✅ All workflow stages completed successfully")
            return True
        else:
            missing_stages = [stage for stage in expected_stages if stage not in completed_stages]
            print(f"❌ Missing workflow stages: {missing_stages}")
            return False
        
    except Exception as e:
        print(f"❌ Orchestrator workflow test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🔍 Testing Orchestrator Workflow\n")
    
    success = test_orchestrator_workflow()
    
    if success:
        print(f"\n🎉 Orchestrator workflow test PASSED!")
        print(f"✅ Complete workflow is working correctly")
    else:
        print(f"\n❌ Orchestrator workflow test FAILED!")
        print(f"🔧 Check the error messages above for troubleshooting")
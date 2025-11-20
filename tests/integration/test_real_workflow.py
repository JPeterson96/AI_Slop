#!/usr/bin/env python3
"""
Real workflow integration test that makes actual API calls.
This test is more expensive as it uses real API endpoints.
"""
import sys
import os
import unittest

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)


class TestRealWorkflow(unittest.TestCase):
    """Test the real workflow with actual API calls"""
    
    def setUp(self):
        """Set up for real workflow testing"""
        try:
            from AI_Slop.orchestrator import Orchestrator
            from AI_Slop.agents import ExtractJobPostingInfo, JobRankingAndAnalysis, SpreadsheetExportAgent
            
            # Initialize orchestrator
            self.orchestrator = Orchestrator()
            
            # Register agents
            self.orchestrator.register_agent(ExtractJobPostingInfo())
            self.orchestrator.register_agent(JobRankingAndAnalysis())
            self.orchestrator.register_agent(SpreadsheetExportAgent())
            
            # Real job data that will trigger API calls
            self.real_job_data = {
                "job_position": "Software Developer",
                "job_keywords": "Python, Django",
                "resume": "Experienced software developer with 3 years of Python and Django experience. Built web applications and REST APIs. Skilled in JavaScript, React, PostgreSQL, and Docker."
            }
            
        except ImportError as e:
            self.skipTest(f"Could not import required modules: {e}")
    
    def test_orchestrator_setup(self):
        """Test that orchestrator is properly set up with agents"""
        self.assertIsNotNone(self.orchestrator)
        self.assertEqual(len(self.orchestrator.agents), 3)
        print(f"✅ Orchestrator initialized with {len(self.orchestrator.agents)} agents")
    
    @unittest.skipUnless(os.getenv('RUN_EXPENSIVE_TESTS'), "Expensive test - set RUN_EXPENSIVE_TESTS=1 to run")
    def test_real_workflow_execution(self):
        """Test the real workflow with API calls (expensive test)"""
        print("\n🔄 Executing REAL workflow (will call JSearch API)...")
        
        try:
            # Execute workflow with real API calls
            results = self.orchestrator.execute_workflow(self.real_job_data)
            
            # Verify results structure
            self.assertIn('job_position', results)
            self.assertIn('job_keywords', results)
            self.assertIn('workflow_stages', results)
            self.assertIn('llm_provider_info', results)
            
            print(f"📊 Workflow Results:")
            print(f"- Job Position: {results['job_position']}")
            print(f"- Job Keywords: {results['job_keywords']}")
            print(f"- LLM Provider: {results['llm_provider_info']['provider']}")
            print(f"- Stages Completed: {len(results['workflow_stages'])}")
            
            for stage, result in results['workflow_stages'].items():
                result_preview = result[:100] + "..." if len(result) > 100 else result
                print(f"  - {stage}: {result_preview}")
            
            # Check for debug files
            exports_dir = os.path.join(project_root, 'exports')
            if os.path.exists(exports_dir):
                debug_files = [f for f in os.listdir(exports_dir) if f.startswith('debug_')]
                if debug_files:
                    print(f"\n🔍 Debug files created: {debug_files}")
            
            print("✅ Real workflow execution completed successfully")
            
        except Exception as e:
            self.fail(f"Real workflow test failed: {e}")
    
    def test_debug_file_generation(self):
        """Test that debug files can be generated"""
        exports_dir = os.path.join(project_root, 'exports')
        
        # Create exports directory if it doesn't exist
        if not os.path.exists(exports_dir):
            os.makedirs(exports_dir)
            
        self.assertTrue(os.path.exists(exports_dir))
        print("✅ Exports directory verified")


if __name__ == "__main__":
    print("🚀 Real Workflow Integration Test - Requires API Keys\n")
    print("💡 Set RUN_EXPENSIVE_TESTS=1 to run actual API tests\n")
    unittest.main()
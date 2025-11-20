#!/usr/bin/env python3
"""
Test script to verify JSearch API integration works.
Run this to test your API key and connection.
"""
import sys

# Add project root to path
sys.path.insert(0, '/Users/jamiepeterson/Desktop/example/AI_Slop')

def test_jsearch_integration():
    """
    Test function to verify JSearch integration works.
    Run this to test your API key and connection.
    """
    try:
        from AI_Slop.jsearch_client import JSearchClient
        
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
    print("🔍 Testing JSearch API Integration\n")
    
    success = test_jsearch_integration()
    
    if success:
        print(f"\n🎉 JSearch integration test PASSED!")
        print(f"✅ API connection is working correctly")
    else:
        print(f"\n❌ JSearch integration test FAILED!")
        print(f"🔧 Check your RAPIDAPI_KEY and internet connection")
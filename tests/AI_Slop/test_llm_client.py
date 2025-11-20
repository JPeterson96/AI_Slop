#!/usr/bin/env python3
"""
Test script to verify LangChain integration with Groq and Ollama.
Run this to test your LLM provider setup.
"""
import os
import sys
from dotenv import load_dotenv

# Add the project root to Python path
sys.path.insert(0, '/Users/jamiepeterson/Desktop/example/AI_Slop')

# Load environment variables
load_dotenv('auth.env')

def test_llm_client():
    """Test the unified LLM client."""
    print("🔍 Testing LangChain Unified LLM Client...")
    
    try:
        from AI_Slop.llm_client import UnifiedLLMClient
        
        # Test current provider
        client = UnifiedLLMClient()
        
        print(f"✅ LLM Client initialized")
        print(f"Provider: {client.provider}")
        
        # Get provider info
        info = client.get_provider_info()
        print(f"Model: {info['model']}")
        print(f"Available: {info['available']}")
        
        if info['error']:
            print(f"❌ Error: {info['error']}")
            return False
        
        # Test basic query
        print("\n🧪 Testing basic query...")
        response = client.query("Say 'Hello from AI Job Search System!' and nothing else.")
        print(f"Response: {response}")
        
        # Test job-related query
        print("\n🧪 Testing job analysis query...")
        job_query = """
        Analyze this job posting briefly:
        
        Position: Software Engineer
        Requirements: Python, Django, REST APIs
        Company: TechCorp
        
        Respond with just: "Good match for Python developers" or similar.
        """
        
        job_response = client.query(job_query)
        print(f"Job Analysis: {job_response}")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Install LangChain: pip install langchain langchain-groq langchain-ollama")
        return False
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def test_orchestrator():
    """Test the orchestrator with LangChain."""
    print("\n🔍 Testing Orchestrator with LangChain...")
    
    try:
        from AI_Slop.orchestrator import Orchestrator
        
        # Initialize orchestrator
        orchestrator = Orchestrator()
        
        # Check LLM validation
        validation = orchestrator.validate_llm_setup()
        print(f"LLM Setup Valid: {validation['test_query_successful']}")
        
        if validation['recommendations']:
            print("Recommendations:")
            for rec in validation['recommendations']:
                print(f"  - {rec}")
        
        # Test simple query
        response = orchestrator.query_llm("What is machine learning? Answer in one sentence.")
        print(f"Orchestrator Response: {response[:100]}...")
        
        return validation['test_query_successful']
        
    except Exception as e:
        print(f"❌ Orchestrator test failed: {e}")
        return False

def test_provider_switching():
    """Test switching between providers."""
    print("\n🔍 Testing Provider Switching...")
    
    try:
        from AI_Slop.llm_client import UnifiedLLMClient
        
        client = UnifiedLLMClient()
        original_provider = client.provider
        
        print(f"Original provider: {original_provider}")
        
        # Try to switch (will fail if other provider not available, but should handle gracefully)
        other_provider = "ollama" if original_provider == "groq" else "groq"
        
        try:
            client.switch_provider(other_provider)
            print(f"✅ Successfully switched to {other_provider}")
            
            # Switch back
            client.switch_provider(original_provider)
            print(f"✅ Successfully switched back to {original_provider}")
            
        except Exception as e:
            print(f"⚠️  Provider switching failed (expected if {other_provider} not configured): {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Provider switching test failed: {e}")
        return False

def check_environment():
    """Check environment configuration."""
    print("🔍 Checking Environment Configuration...")
    
    required_vars = {
        "LLM_PROVIDER": os.getenv("LLM_PROVIDER", "groq"),
        "GROQ_API_KEY": os.getenv("GROQ_API_KEY"),
        "RAPIDAPI_KEY": os.getenv("RAPIDAPI_KEY")
    }
    
    all_good = True
    
    for var, value in required_vars.items():
        if value:
            masked_value = value[:8] + "..." if len(str(value)) > 8 else "set"
            print(f"✅ {var}: {masked_value}")
        else:
            print(f"❌ {var}: not set")
            all_good = False
    
    provider = required_vars["LLM_PROVIDER"]
    if provider == "groq" and not required_vars["GROQ_API_KEY"]:
        print("⚠️  Groq selected but GROQ_API_KEY not set")
        all_good = False
    elif provider == "ollama":
        print("ℹ️  Ollama selected - ensure 'ollama serve' is running")
    
    return all_good

if __name__ == "__main__":
    print("🤖 AI Job Search LangChain Integration Test\n")
    
    # Check environment
    check_environment()
    
    # Run tests
    tests = [
        ("LLM Client", test_llm_client),
        ("Orchestrator", test_orchestrator),
        ("Provider Switching", test_provider_switching)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{'='*50}")
        success = test_func()
        results.append((test_name, success))
    
    # Summary
    print(f"\n{'='*50}")
    print("📊 TEST SUMMARY:")
    
    all_passed = True
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if not success:
            all_passed = False
    
    if all_passed:
        print(f"\n🎉 All tests passed! LangChain integration is working.")
        print(f"🚀 Ready to run: python manage.py runserver")
    else:
        print(f"\n⚠️  Some tests failed. Check your configuration.")
        print(f"📖 See SETUP.md for troubleshooting guide.")
    
    print(f"\n💡 Switch providers anytime with LLM_PROVIDER environment variable!")
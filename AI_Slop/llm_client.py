"""
Unified LLM client using LangChain for easy provider switching.
Supports both Groq Cloud API and local Ollama with seamless switching via environment variables.
"""
import os
from typing import Optional, Dict, Any
from dotenv import load_dotenv

# LangChain imports
from langchain_core.messages import HumanMessage
from langchain_groq import ChatGroq
from langchain_ollama import ChatOllama

load_dotenv()

class UnifiedLLMClient:
    """
    Unified client for both Groq and Ollama using LangChain.
    Switch providers via LLM_PROVIDER environment variable.
    """
    
    def __init__(self, provider: Optional[str] = None):
        """
        Initialize LLM client.
        
        Args:
            provider: "groq" or "ollama". If None, uses LLM_PROVIDER env var (defaults to "groq")
        """
        self.provider = provider or os.getenv("LLM_PROVIDER", "groq").lower()
        self.client = self._initialize_client()
        
        # Log which provider is being used
        print(f"[LLM_CLIENT] Initialized {self.provider.upper()} provider")
    
    def _initialize_client(self):
        """Initialize the appropriate LLM client based on provider."""
        if self.provider == "groq":
            return self._initialize_groq()
        elif self.provider == "ollama":
            return self._initialize_ollama()
        else:
            raise ValueError(f"Unsupported LLM provider: {self.provider}. Use 'groq' or 'ollama'")
    
    def _initialize_groq(self):
        """Initialize Groq client."""
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError(
                "GROQ_API_KEY not found in environment. "
                "Get your free API key from https://console.groq.com/"
            )
        
        model = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
        
        return ChatGroq(
            api_key=api_key,
            model=model,
            temperature=0.7,
            max_tokens=4000,
            timeout=60
        )
    
    def _initialize_ollama(self):
        """Initialize Ollama client."""
        base_url = os.getenv("OLLAMA_HOST", "http://localhost:11434")
        model = os.getenv("OLLAMA_MODEL", "llama3")
        
        return ChatOllama(
            base_url=base_url,
            model=model,
            temperature=0.7,
            timeout=60
        )
    
    def query(self, prompt: str) -> str:
        """
        Query the LLM with unified interface.
        
        Args:
            prompt: The prompt to send to the LLM
            
        Returns:
            str: LLM response content
        """
        try:
            message = HumanMessage(content=prompt)
            response = self.client.invoke([message])
            return response.content
        
        except Exception as e:
            error_msg = f"LLM Error ({self.provider}): {str(e)}"
            print(f"[LLM_CLIENT] {error_msg}")
            
            # Return a fallback message instead of raising
            return f"Sorry, I encountered an error while processing your request. Please check your {self.provider.upper()} configuration and try again."
    
    def get_provider_info(self) -> Dict[str, Any]:
        """Get information about current provider and its status."""
        info = {
            "provider": self.provider,
            "model": getattr(self.client, 'model', 'unknown'),
            "available": False,
            "error": None
        }
        
        try:
            # Test connection with a simple query
            test_response = self.query("Hello")
            info["available"] = not test_response.startswith("LLM Error")
            if not info["available"]:
                info["error"] = test_response
        except Exception as e:
            info["error"] = str(e)
        
        return info
    
    def switch_provider(self, new_provider: str):
        """
        Switch to a different LLM provider at runtime.
        
        Args:
            new_provider: "groq" or "ollama"
        """
        if new_provider.lower() not in ["groq", "ollama"]:
            raise ValueError(f"Unsupported provider: {new_provider}")
        
        old_provider = self.provider
        self.provider = new_provider.lower()
        
        try:
            self.client = self._initialize_client()
            print(f"[LLM_CLIENT] Switched from {old_provider.upper()} to {self.provider.upper()}")
        except Exception as e:
            # Revert on failure
            self.provider = old_provider
            self.client = self._initialize_client()
            raise Exception(f"Failed to switch to {new_provider}: {e}")


def test_llm_client():
    """
    Test function to verify LLM client works with current configuration.
    """
    try:
        client = UnifiedLLMClient()
        
        print(f"\n🔍 Testing {client.provider.upper()} LLM client...")
        
        # Get provider info
        info = client.get_provider_info()
        print(f"Provider: {info['provider']}")
        print(f"Model: {info['model']}")
        print(f"Available: {info['available']}")
        
        if info['error']:
            print(f"Error: {info['error']}")
            return False
        
        # Test basic query
        response = client.query("Say 'Hello, AI job search system is working!' in exactly those words.")
        print(f"Test Response: {response[:100]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ LLM client test failed: {e}")
        return False


if __name__ == "__main__":
    # Run test when script is executed directly
    success = test_llm_client()
    if success:
        print("✅ LLM client test passed!")
    else:
        print("❌ LLM client test failed!")
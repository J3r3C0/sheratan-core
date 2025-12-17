"""
Multi-LLM Fallback Client for Sheratan Core
Adapted from GPT Hub gpt_core.py

Provides LLM calls with fallback chain.
"""

import os
import requests
from typing import Optional, List
from dataclasses import dataclass


@dataclass
class LLMResponse:
    text: str
    provider: str
    success: bool
    error: Optional[str] = None


class LLMFallbackClient:
    """
    LLM Client with automatic fallback chain.
    
    Tries providers in order:
    1. WebRelay (ChatGPT via browser)
    2. OpenAI API (direct)
    3. Ollama (local)
    4. LM Studio (local)
    """
    
    def __init__(self):
        self.providers = self._init_providers()
    
    def _init_providers(self) -> List[dict]:
        """Initialize available providers from environment."""
        providers = []
        
        # WebRelay
        webrelay_url = os.getenv("WEBRELAY_URL", "http://localhost:3000/api/llm/call")
        providers.append({
            "name": "webrelay",
            "url": webrelay_url,
            "type": "webrelay",
            "enabled": True
        })
        
        # OpenAI
        openai_key = os.getenv("OPENAI_API_KEY")
        if openai_key:
            providers.append({
                "name": "openai",
                "url": "https://api.openai.com/v1/chat/completions",
                "api_key": openai_key,
                "model": os.getenv("OPENAI_MODEL", "gpt-4"),
                "type": "openai",
                "enabled": True
            })
        
        # Ollama
        ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434/v1/chat/completions")
        providers.append({
            "name": "ollama",
            "url": ollama_url,
            "model": os.getenv("OLLAMA_MODEL", "llama2"),
            "type": "openai_compatible",
            "enabled": os.getenv("OLLAMA_ENABLED", "false").lower() == "true"
        })
        
        # LM Studio
        lm_studio_url = os.getenv("LM_STUDIO_URL", "http://localhost:1234/v1/chat/completions")
        providers.append({
            "name": "lm_studio",
            "url": lm_studio_url,
            "model": os.getenv("LM_STUDIO_MODEL", "local-model"),
            "type": "openai_compatible",
            "enabled": os.getenv("LM_STUDIO_ENABLED", "false").lower() == "true"
        })
        
        return [p for p in providers if p.get("enabled", False)]
    
    def _call_webrelay(self, prompt: str, provider: dict) -> LLMResponse:
        """Call WebRelay endpoint."""
        try:
            response = requests.post(
                provider["url"],
                json={"prompt": prompt},
                timeout=60
            )
            if response.status_code == 200:
                data = response.json()
                text = data.get("summary") or data.get("text") or str(data)
                return LLMResponse(text=text, provider="webrelay", success=True)
            else:
                return LLMResponse(text="", provider="webrelay", success=False, 
                                   error=f"HTTP {response.status_code}")
        except Exception as e:
            return LLMResponse(text="", provider="webrelay", success=False, error=str(e))
    
    def _call_openai_compatible(self, prompt: str, provider: dict, system_message: str = None) -> LLMResponse:
        """Call OpenAI or OpenAI-compatible endpoint."""
        try:
            headers = {"Content-Type": "application/json"}
            if provider.get("api_key"):
                headers["Authorization"] = f"Bearer {provider['api_key']}"
            
            messages = []
            if system_message:
                messages.append({"role": "system", "content": system_message})
            messages.append({"role": "user", "content": prompt})
            
            response = requests.post(
                provider["url"],
                headers=headers,
                json={
                    "model": provider.get("model", "gpt-4"),
                    "messages": messages,
                    "temperature": 0.7
                },
                timeout=60
            )
            
            if response.status_code == 200:
                data = response.json()
                text = data["choices"][0]["message"]["content"]
                return LLMResponse(text=text, provider=provider["name"], success=True)
            else:
                return LLMResponse(text="", provider=provider["name"], success=False,
                                   error=f"HTTP {response.status_code}")
        except Exception as e:
            return LLMResponse(text="", provider=provider["name"], success=False, error=str(e))
    
    def call(self, prompt: str, system_message: str = None) -> LLMResponse:
        """
        Call LLM with automatic fallback.
        
        Tries each provider in order until one succeeds.
        """
        errors = []
        
        for provider in self.providers:
            if provider["type"] == "webrelay":
                result = self._call_webrelay(prompt, provider)
            else:
                result = self._call_openai_compatible(prompt, provider, system_message)
            
            if result.success:
                return result
            else:
                errors.append(f"{provider['name']}: {result.error}")
        
        # All providers failed
        return LLMResponse(
            text="",
            provider="none",
            success=False,
            error=f"All providers failed: {'; '.join(errors)}"
        )


# Singleton instance
_client: Optional[LLMFallbackClient] = None


def get_client() -> LLMFallbackClient:
    """Get or create singleton LLM client."""
    global _client
    if _client is None:
        _client = LLMFallbackClient()
    return _client


def ask_llm(prompt: str, system_message: str = None) -> str:
    """
    Simple interface to call LLM with fallback.
    
    Returns response text or error message.
    """
    client = get_client()
    result = client.call(prompt, system_message)
    
    if result.success:
        return result.text
    else:
        return f"⚠️ LLM Error: {result.error}"


# ============================================
# Tool Handler Interface (for worker_loop.py)
# ============================================

def handle_llm_call_fallback(params: dict) -> dict:
    """
    Tool handler for kind: "llm_call_fallback"
    
    params:
        prompt: str
        system_message: str (optional)
    """
    prompt = params.get("prompt", "")
    system_message = params.get("system_message")
    
    client = get_client()
    result = client.call(prompt, system_message)
    
    return {
        "ok": result.success,
        "text": result.text,
        "provider": result.provider,
        "error": result.error
    }

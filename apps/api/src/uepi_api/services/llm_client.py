"""LLM Client - Supports OpenAI, Anthropic, and local fallback"""
import json
import os
from typing import Dict, Any, List, Optional
from abc import ABC, abstractmethod

from uepi_api.config import get_settings

settings = get_settings()


class LLMClient(ABC):
    """Abstract base class for LLM clients"""
    
    def __init__(self):
        self.last_token_usage = {"input_tokens": 0, "output_tokens": 0}
    
    @abstractmethod
    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        context: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> Dict[str, Any]:
        """Generate response from LLM"""
        pass


class OpenAIClient(LLMClient):
    """OpenAI API client"""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4-turbo-preview"):
        self.api_key = api_key or settings.openai_api_key or os.getenv("OPENAI_API_KEY")
        self.model = model or settings.openai_model
        
        if not self.api_key:
            raise ValueError("OpenAI API key not provided. Set OPENAI_API_KEY environment variable or configure in settings.")
        
        try:
            import openai
            self.client = openai.OpenAI(api_key=self.api_key)
        except ImportError:
            raise ImportError("OpenAI package not installed. Install with: pip install openai")
    
    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        context: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> Dict[str, Any]:
        """Generate response using OpenAI API"""
        import openai
        
        messages = [
            {"role": "system", "content": system_prompt}
        ]
        
        if context:
            messages.append({"role": "system", "content": f"Context: {context}"})
        
        messages.append({"role": "user", "content": user_prompt})
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature or settings.llm_temperature,
                max_tokens=max_tokens or settings.llm_max_tokens,
                response_format={"type": "json_object"}  # Force JSON output
            )
            
            # Track token usage
            self.last_token_usage = {
                "input_tokens": response.usage.prompt_tokens,
                "output_tokens": response.usage.completion_tokens
            }
            
            content = response.choices[0].message.content
            
            # Try to parse as JSON
            try:
                parsed = json.loads(content)
                return {
                    "content": parsed.get("natural_language", content),
                    "structured_output": parsed.get("structured_output", {}),
                    "next_steps": parsed.get("next_steps", []),
                    "confidence": parsed.get("confidence", "MEDIUM"),
                    "requires_clarification": parsed.get("requires_clarification", False),
                    "clarification_questions": parsed.get("clarification_questions", [])
                }
            except json.JSONDecodeError:
                # If not JSON, return as natural language
                return {
                    "content": content,
                    "structured_output": {},
                    "next_steps": [],
                    "confidence": "MEDIUM",
                    "requires_clarification": False,
                    "clarification_questions": []
                }
        except Exception as e:
            raise Exception(f"OpenAI API error: {str(e)}")


class AnthropicClient(LLMClient):
    """Anthropic Claude API client"""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "claude-3-opus-20240229"):
        self.api_key = api_key or settings.anthropic_api_key or os.getenv("ANTHROPIC_API_KEY")
        self.model = model or settings.anthropic_model
        
        if not self.api_key:
            raise ValueError("Anthropic API key not provided. Set ANTHROPIC_API_KEY environment variable or configure in settings.")
        
        try:
            import anthropic
            self.client = anthropic.Anthropic(api_key=self.api_key)
        except ImportError:
            raise ImportError("Anthropic package not installed. Install with: pip install anthropic")
    
    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        context: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> Dict[str, Any]:
        """Generate response using Anthropic API"""
        import anthropic
        
        full_prompt = f"{system_prompt}\n\n"
        if context:
            full_prompt += f"Context: {context}\n\n"
        full_prompt += f"User: {user_prompt}\n\nAssistant:"
        
        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens or settings.llm_max_tokens,
                temperature=temperature or settings.llm_temperature,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": user_prompt}
                ]
            )
            
            # Track token usage
            self.last_token_usage = {
                "input_tokens": message.usage.input_tokens,
                "output_tokens": message.usage.output_tokens
            }
            
            content = message.content[0].text if message.content else ""
            
            # Try to parse as JSON
            try:
                parsed = json.loads(content)
                return {
                    "content": parsed.get("natural_language", content),
                    "structured_output": parsed.get("structured_output", {}),
                    "next_steps": parsed.get("next_steps", []),
                    "confidence": parsed.get("confidence", "MEDIUM"),
                    "requires_clarification": parsed.get("requires_clarification", False),
                    "clarification_questions": parsed.get("clarification_questions", [])
                }
            except json.JSONDecodeError:
                return {
                    "content": content,
                    "structured_output": {},
                    "next_steps": [],
                    "confidence": "MEDIUM",
                    "requires_clarification": False,
                    "clarification_questions": []
                }
        except Exception as e:
            raise Exception(f"Anthropic API error: {str(e)}")


class LocalFallbackClient(LLMClient):
    """Local fallback client - uses rule-based parsing when LLM is not available"""
    
    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        context: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> Dict[str, Any]:
        """Generate response using rule-based parsing (fallback)"""
        # This is the existing rule-based logic
        # In production, this would be replaced by actual LLM calls
        return {
            "content": "I understand your request. Let me help you with that using rule-based parsing.",
            "structured_output": {},
            "next_steps": ["Review the generated output"],
            "confidence": "LOW",
            "requires_clarification": True,
            "clarification_questions": ["Please provide more details about your request."]
        }


def get_llm_client() -> LLMClient:
    """Get appropriate LLM client based on configuration"""
    provider = settings.llm_provider.lower()
    
    if provider == "openai":
        try:
            return OpenAIClient()
        except (ValueError, ImportError) as e:
            print(f"Warning: OpenAI client not available: {e}. Falling back to local.")
            return LocalFallbackClient()
    
    elif provider == "anthropic":
        try:
            return AnthropicClient()
        except (ValueError, ImportError) as e:
            print(f"Warning: Anthropic client not available: {e}. Falling back to local.")
            return LocalFallbackClient()
    
    else:
        # Local fallback
        return LocalFallbackClient()


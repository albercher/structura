"""OpenAI LLM client for structured data extraction."""
import json
import logging
from typing import Dict, Any, Optional
from openai import AsyncOpenAI
from src.config import OPENAI_API_KEY, OPENAI_BASE_URL, LLM_MODEL, LLM_TEMPERATURE

logger = logging.getLogger(__name__)


class OpenAIClient:
    """Client for interacting with OpenAI API or Ollama (OpenAI-compatible endpoint)."""
    
    def __init__(self, api_key: str = None, base_url: str = None, model: str = None, temperature: float = None):
        """
        Initialize OpenAI client.
        
        Args:
            api_key: OpenAI API key. If not provided, uses config default. For Ollama, any string works.
            base_url: Base URL for the API. If not provided, uses config default (None = OpenAI default).
                      Set to "http://localhost:11434/v1" for Ollama.
            model: LLM model name. If not provided, uses config default.
            temperature: Temperature for LLM. If not provided, uses config default.
        """
        self.base_url = base_url or OPENAI_BASE_URL
        self.api_key = api_key or OPENAI_API_KEY
        self.model = model or LLM_MODEL
        self.temperature = temperature if temperature is not None else LLM_TEMPERATURE
        
        # For Ollama, API key is optional (any string works)
        # For OpenAI, API key is required unless using a local endpoint
        if not self.base_url and not self.api_key:
            raise ValueError(
                "OpenAI API key is required when using OpenAI. "
                "Set OPENAI_API_KEY environment variable, or set OPENAI_BASE_URL for Ollama/local endpoints."
            )
        
        # Use "ollama" as default API key for Ollama if base_url is set and no key provided
        if self.base_url and not self.api_key:
            self.api_key = "ollama"
            logger.info("Using default API key 'ollama' for Ollama/local endpoint")
        
        # Initialize client with base_url if provided (for Ollama compatibility)
        client_kwargs = {"api_key": self.api_key}
        if self.base_url:
            client_kwargs["base_url"] = self.base_url
            logger.info(f"Using custom base URL: {self.base_url}")
        
        self.client = AsyncOpenAI(**client_kwargs)
    
    async def extract_structured_data(self, prompt: str) -> Dict[str, Any]:
        """
        Extract structured data using LLM.
        
        Args:
            prompt: The prompt containing markdown and schema instructions
            
        Returns:
            Extracted data as dictionary
            
        Raises:
            Exception: If extraction fails
        """
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful assistant that extracts structured data from unstructured content. Always return valid JSON only, with no additional text or formatting."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=self.temperature,
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content.strip()
            
            # Parse JSON response
            try:
                result = json.loads(content)
                return result
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse LLM response as JSON: {content}")
                raise ValueError(f"LLM returned invalid JSON: {str(e)}")
                
        except Exception as e:
            logger.error(f"Error during LLM extraction: {str(e)}")
            raise Exception(f"Failed to extract structured data: {str(e)}")


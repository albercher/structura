"""OpenAI LLM client for structured data extraction."""
import json
import logging
from typing import Dict, Any, Optional
from openai import AsyncOpenAI
from src.config import OPENAI_API_KEY, LLM_MODEL, LLM_TEMPERATURE

logger = logging.getLogger(__name__)


class OpenAIClient:
    """Client for interacting with OpenAI API."""
    
    def __init__(self, api_key: str = None, model: str = None, temperature: float = None):
        """
        Initialize OpenAI client.
        
        Args:
            api_key: OpenAI API key. If not provided, uses config default.
            model: LLM model name. If not provided, uses config default.
            temperature: Temperature for LLM. If not provided, uses config default.
        """
        self.api_key = api_key or OPENAI_API_KEY
        self.model = model or LLM_MODEL
        self.temperature = temperature if temperature is not None else LLM_TEMPERATURE
        
        if not self.api_key:
            raise ValueError("OpenAI API key is required. Set OPENAI_API_KEY environment variable.")
        
        self.client = AsyncOpenAI(api_key=self.api_key)
    
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


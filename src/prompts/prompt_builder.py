"""Builds LLM prompts from markdown and blueprint schemas."""
import json
from typing import Dict, Any


class PromptBuilder:
    """Combines markdown content and blueprint schema into LLM prompt."""
    
    @staticmethod
    def build_extraction_prompt(markdown: str, blueprint: Dict[str, Any], domain: str) -> str:
        """
        Build a prompt for the LLM to extract structured data.
        
        Args:
            markdown: Raw markdown content from Firecrawl
            blueprint: JSON schema blueprint for the domain
            domain: Domain name (e.g., "e-commerce")
            
        Returns:
            Formatted prompt string for the LLM
        """
        schema_str = json.dumps(blueprint, indent=2)
        
        prompt = f"""You are a data extraction specialist. Extract structured data from the following markdown content based on the provided JSON schema.

Domain: {domain}

JSON Schema:
{schema_str}

Markdown Content:
{markdown[:20000] if len(markdown) > 20000 else markdown}

Instructions:
1. Extract all relevant information from the markdown content
2. Return ONLY valid JSON that strictly adheres to the provided schema
3. Use null for missing optional fields
4. For arrays, return an empty array [] if no items are found
5. Ensure all required fields are present
6. Ensure numeric values are actual numbers, not strings
7. Ensure boolean values are true/false, not strings
8. For currency codes, use standard 3-letter ISO codes (e.g., USD, EUR, GBP)
9. Extract prices as numbers (remove currency symbols and commas)

Return the extracted data as a valid JSON object matching the schema above:"""

        return prompt


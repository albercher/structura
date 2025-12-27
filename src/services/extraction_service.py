"""Main service for extracting structured data from URLs."""
import json
import logging
from typing import Dict, Any
from pathlib import Path

from src.extractors.firecrawl_extractor import FirecrawlExtractor
from src.prompts.prompt_builder import PromptBuilder
from src.llm.openai_client import OpenAIClient
from src.validators.schema_validator import SchemaValidator
from src.config import BLUEPRINTS_DIR

logger = logging.getLogger(__name__)


class ExtractionService:
    """Service that orchestrates the extraction pipeline."""
    
    def __init__(self):
        """Initialize the extraction service with all required components."""
        self.extractor = FirecrawlExtractor()
        self.llm_client = OpenAIClient()
        self.prompt_builder = PromptBuilder()
        self.validator = SchemaValidator()
    
    def load_blueprint(self, domain: str, schema_version: str = "v1") -> Dict[str, Any]:
        """
        Load blueprint schema for a domain.
        
        Args:
            domain: Domain name (e.g., "e-commerce")
            schema_version: Schema version (currently not used, but reserved for future)
            
        Returns:
            Blueprint schema as dictionary
            
        Raises:
            FileNotFoundError: If blueprint file doesn't exist
            ValueError: If blueprint JSON is invalid
        """
        # Convert domain to filename (e.g., "e-commerce" -> "e-commerce.json")
        blueprint_file = Path(BLUEPRINTS_DIR) / f"{domain}.json"
        
        if not blueprint_file.exists():
            raise FileNotFoundError(
                f"Blueprint not found for domain '{domain}'. "
                f"Expected file: {blueprint_file}"
            )
        
        try:
            with open(blueprint_file, "r", encoding="utf-8") as f:
                blueprint = json.load(f)
            return blueprint
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in blueprint file {blueprint_file}: {str(e)}")
    
    async def extract(self, url: str, domain: str, schema_version: str = "v1") -> Dict[str, Any]:
        """
        Extract structured data from a URL.
        
        Args:
            url: URL to extract data from
            domain: Domain name (determines blueprint schema)
            schema_version: Schema version (reserved for future use)
            
        Returns:
            Extracted structured data as dictionary
            
        Raises:
            Exception: If extraction fails at any stage
        """
        try:
            # Step 1: Load blueprint schema
            logger.info(f"Loading blueprint for domain: {domain}")
            blueprint = self.load_blueprint(domain, schema_version)
            
            # Step 2: Extract markdown from URL
            logger.info(f"Extracting markdown from URL: {url}")
            markdown = await self.extractor.extract_markdown(url)
            
            if not markdown or len(markdown.strip()) == 0:
                raise ValueError("No content extracted from URL")
            
            # Step 3: Build prompt
            logger.info("Building extraction prompt")
            prompt = self.prompt_builder.build_extraction_prompt(markdown, blueprint, domain)
            
            # Step 4: Extract structured data using LLM
            logger.info("Extracting structured data using LLM")
            extracted_data = await self.llm_client.extract_structured_data(prompt)
            
            # Step 5: Validate against schema
            logger.info("Validating extracted data against schema")
            is_valid, error_message = self.validator.validate_data(extracted_data, blueprint)
            
            if not is_valid:
                logger.warning(f"Validation failed: {error_message}")
                # Try to fix required fields
                extracted_data = self.validator.validate_and_fix_required_fields(
                    extracted_data, blueprint
                )
                # Validate again
                is_valid, error_message = self.validator.validate_data(extracted_data, blueprint)
                if not is_valid:
                    logger.error(f"Validation still failed after fixes: {error_message}")
                    # Still return the data, but log the warning
                    # In production, you might want to raise an exception here
            
            logger.info("Extraction completed successfully")
            return extracted_data
            
        except Exception as e:
            logger.error(f"Error during extraction: {str(e)}")
            raise


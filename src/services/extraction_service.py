"""Main service for extracting structured data from URLs."""
import json
import logging
from typing import Dict, Any, Optional

from src.extractors.firecrawl_extractor import FirecrawlExtractor
from src.prompts.prompt_builder import PromptBuilder
from src.llm.openai_client import OpenAIClient
from src.validators.schema_validator import SchemaValidator
from src.blueprints.open_blueprints import get_open_blueprint, is_open_blueprint
from src.blueprints.firebase_client import FirebaseBlueprintClient

logger = logging.getLogger(__name__)


class ExtractionService:
    """Service that orchestrates the extraction pipeline."""
    
    def __init__(self):
        """Initialize the extraction service with all required components."""
        self.extractor = FirecrawlExtractor()
        self.llm_client = OpenAIClient()
        self.prompt_builder = PromptBuilder()
        self.validator = SchemaValidator()
        self.firebase_client = None
        try:
            self.firebase_client = FirebaseBlueprintClient()
        except ValueError:
            # Firebase not configured - that's okay, protected blueprints won't be available
            logger.info("Firebase not configured - protected blueprints will not be available")
    
    async def load_blueprint(self, domain: str, schema_version: str = "v1", api_key: Optional[str] = None) -> Dict[str, Any]:
        """
        Load blueprint schema for a domain.
        
        Checks open source blueprints first, then protected blueprints from Firebase.
        
        Args:
            domain: Domain name (e.g., "e-commerce", "medical", "legal")
            schema_version: Schema version (currently not used, but reserved for future)
            api_key: API key for accessing protected blueprints (required for protected domains)
            
        Returns:
            Blueprint schema as dictionary
            
        Raises:
            ValueError: If blueprint not found or access denied
            KeyError: If domain is not in open source blueprints
        """
        # Check if it's an open source blueprint
        if is_open_blueprint(domain):
            logger.info(f"Loading open source blueprint for domain: {domain}")
            return get_open_blueprint(domain)
        
        # Otherwise, try to fetch from protected blueprints (Firebase)
        if not self.firebase_client:
            raise ValueError(
                f"Protected blueprint '{domain}' requires Firebase configuration. "
                f"Set FIREBASE_PROJECT_ID and FIREBASE_COLLECTION environment variables, "
                f"or use an open source blueprint (e.g., 'e-commerce')."
            )
        
        logger.info(f"Loading protected blueprint for domain: {domain}")
        return await self.firebase_client.get_blueprint(domain, api_key)
    
    async def extract(self, url: str, domain: str, schema_version: str = "v1", api_key: Optional[str] = None) -> Dict[str, Any]:
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
            blueprint = await self.load_blueprint(domain, schema_version, api_key)
            
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


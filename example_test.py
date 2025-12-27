"""Example script to test the extraction API."""
import asyncio
import json
from src.services.extraction_service import ExtractionService


async def test_extraction():
    """Test the extraction service with an example URL."""
    service = ExtractionService()
    
    # Example e-commerce product URL (replace with a real product page)
    test_url = "https://example.com/product-page"
    domain = "e-commerce"
    schema_version = "v1"
    
    try:
        print(f"Extracting data from: {test_url}")
        print(f"Domain: {domain}")
        print("=" * 50)
        
        result = await service.extract(
            url=test_url,
            domain=domain,
            schema_version=schema_version
        )
        
        print("\nExtracted Data:")
        print(json.dumps(result, indent=2))
        
    except Exception as e:
        print(f"Error: {str(e)}")


if __name__ == "__main__":
    asyncio.run(test_extraction())


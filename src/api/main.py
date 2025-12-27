"""FastAPI application main file."""
import logging
from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl
from typing import Optional

from src.services.extraction_service import ExtractionService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

app = FastAPI(
    title="Structura",
    description="API for extracting structured data from URLs using Firecrawl and LLM",
    version="1.0.0"
)

# Enable CORS - configure for production use
# WARNING: allow_origins=["*"] is permissive. For production, specify allowed origins.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure allowed origins in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize service
extraction_service = ExtractionService()


class ExtractRequest(BaseModel):
    """Request model for extraction endpoint."""
    url: HttpUrl
    domain: str
    schema_version: Optional[str] = "v1"
    api_key: Optional[str] = None  # Required for protected blueprints


class ExtractResponse(BaseModel):
    """Response model for extraction endpoint."""
    success: bool
    data: dict
    error: Optional[str] = None


@app.post("/extract", response_model=ExtractResponse)
async def extract(
    request: ExtractRequest,
    x_api_key: Optional[str] = Header(None, alias="X-API-Key")
):
    """
    Extract structured data from a URL.
    
    API key can be provided in two ways:
    1. In request body: `{"api_key": "..."}`
    2. In header: `X-API-Key: ...` (recommended for RapidAPI)
    
    Header takes precedence if both are provided.
    
    Args:
        request: ExtractRequest containing url, domain, and schema_version
        x_api_key: API key from X-API-Key header (optional)
        
    Returns:
        ExtractResponse with extracted data
    """
    try:
        # Convert HttpUrl to string
        url_str = str(request.url)
        
        # Use header API key if provided, otherwise use body API key
        api_key = x_api_key or request.api_key
        
        # Extract data
        extracted_data = await extraction_service.extract(
            url=url_str,
            domain=request.domain,
            schema_version=request.schema_version,
            api_key=api_key
        )
        
        return ExtractResponse(
            success=True,
            data=extracted_data
        )
        
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        import traceback
        import os
        error_traceback = traceback.format_exc()
        logging.error(f"Unexpected error: {str(e)}")
        # Only include full traceback in debug mode to avoid leaking sensitive info
        is_debug = os.getenv("DEBUG", "false").lower() == "true"
        error_detail = f"Internal server error: {str(e)}"
        if is_debug:
            error_detail += f"\n\nTraceback:\n{error_traceback}"
        raise HTTPException(status_code=500, detail=error_detail)


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


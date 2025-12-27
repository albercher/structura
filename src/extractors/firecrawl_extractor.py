"""Firecrawl markdown extractor."""
import asyncio
from concurrent.futures import ThreadPoolExecutor
from firecrawl import Firecrawl
from src.config import FIRECRAWL_API_KEY

# Thread pool executor for running synchronous Firecrawl calls
_executor = ThreadPoolExecutor(max_workers=5)


class FirecrawlExtractor:
    """Extracts markdown content from URLs using Firecrawl."""
    
    def __init__(self, api_key: str = None):
        """
        Initialize Firecrawl extractor.
        
        Args:
            api_key: Firecrawl API key. If not provided, uses config default.
        """
        self.api_key = api_key or FIRECRAWL_API_KEY
        self.app = Firecrawl(api_key=self.api_key) if self.api_key else None
    
    def _extract_sync(self, url: str) -> str:
        """
        Synchronous markdown extraction (runs in thread pool).
        
        Args:
            url: The URL to extract content from
            
        Returns:
            Markdown string extracted from the URL
        """
        if not self.app:
            # If no API key, use a simple HTTP request as fallback
            # Note: This is a fallback, Firecrawl is preferred for better extraction
            import httpx
            response = httpx.get(url, timeout=30.0, follow_redirects=True)
            response.raise_for_status()
            return response.text
        
        # Use Firecrawl to scrape and convert to markdown
        # Firecrawl API is synchronous, so we wrap it in async
        try:
            # Firecrawl API: firecrawl.scrape(url, formats=["markdown"])
            result = self.app.scrape(url, formats=["markdown"])
            
            # Handle Document object (newer Firecrawl API)
            if hasattr(result, 'markdown'):
                return result.markdown
            elif hasattr(result, 'content'):
                return result.content
            
            # Handle dictionary response (older API format)
            if isinstance(result, dict):
                # Check for success flag
                if not result.get("success", True):
                    error_msg = result.get("error", "Firecrawl scrape failed")
                    raise Exception(f"Firecrawl scrape returned success=false: {error_msg}")
                
                # Extract markdown from data field
                if "data" in result and isinstance(result["data"], dict):
                    data = result["data"]
                    if "markdown" in data:
                        return data["markdown"]
                    elif "content" in data:
                        return data["content"]
                # Fallback: check if markdown is directly in result
                elif "markdown" in result:
                    return result["markdown"]
                elif "content" in result:
                    return result["content"]
            
            # Handle string response
            if isinstance(result, str):
                return result
            
            # If we get here, we couldn't extract markdown
            raise ValueError(f"Unexpected Firecrawl response format. Type: {type(result)}, Available attributes: {dir(result)[:20] if hasattr(result, '__dict__') else 'N/A'}")
                
        except Exception as e:
            raise Exception(f"Firecrawl scrape failed: {str(e)}") from e
    
    async def extract_markdown(self, url: str) -> str:
        """
        Extract markdown content from a URL.
        
        Args:
            url: The URL to extract content from
            
        Returns:
            Markdown string extracted from the URL
            
        Raises:
            Exception: If extraction fails
        """
        try:
            # Run synchronous Firecrawl call in thread pool
            loop = asyncio.get_event_loop()
            markdown = await loop.run_in_executor(_executor, self._extract_sync, url)
            
            if not markdown or len(markdown.strip()) == 0:
                raise ValueError("Empty markdown content extracted from URL")
            
            return markdown
                
        except Exception as e:
            # Preserve the original exception with full traceback in the message
            raise Exception(f"Failed to extract markdown from URL: {str(e)}") from e


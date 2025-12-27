"""File content extractor for various file formats."""
import logging
import asyncio
from typing import Optional
from fastapi import UploadFile
import io

logger = logging.getLogger(__name__)


class FileExtractor:
    """Extracts text/markdown content from uploaded files."""
    
    async def extract_markdown(self, file: UploadFile) -> str:
        """
        Extract markdown/text content from an uploaded file.
        
        Supports:
        - Markdown files (.md, .markdown)
        - Text files (.txt)
        - HTML files (.html, .htm)
        - PDF files (.pdf) - requires pdfplumber or pypdf
        
        Args:
            file: FastAPI UploadFile object
            
        Returns:
            Extracted text/markdown content as string
            
        Raises:
            ValueError: If file type is not supported or extraction fails
        """
        try:
            # Read file content
            content = await file.read()
            file_extension = file.filename.split('.')[-1].lower() if file.filename else ''
            
            # Handle different file types
            if file_extension in ['md', 'markdown', 'txt']:
                # Plain text or markdown - decode directly
                try:
                    text = content.decode('utf-8')
                except UnicodeDecodeError:
                    # Try with error handling
                    text = content.decode('utf-8', errors='ignore')
                return text
            
            elif file_extension in ['html', 'htm']:
                # HTML - convert to markdown-like text
                return await self._extract_from_html(content)
            
            elif file_extension == 'pdf':
                # PDF - extract text
                return await self._extract_from_pdf(content)
            
            else:
                # Try to decode as text for unknown extensions
                logger.warning(f"Unknown file extension '{file_extension}', attempting to decode as text")
                try:
                    text = content.decode('utf-8')
                    return text
                except UnicodeDecodeError:
                    raise ValueError(
                        f"Unsupported file type: '{file_extension}'. "
                        f"Supported types: .md, .markdown, .txt, .html, .htm, .pdf"
                    )
                    
        except Exception as e:
            logger.error(f"Error extracting content from file: {str(e)}")
            raise ValueError(f"Failed to extract content from file: {str(e)}") from e
    
    async def _extract_from_html(self, content: bytes) -> str:
        """Extract text from HTML content."""
        try:
            from bs4 import BeautifulSoup
            html = content.decode('utf-8', errors='ignore')
            soup = BeautifulSoup(html, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Get text and convert to markdown-like format
            text = soup.get_text()
            # Clean up whitespace
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = '\n'.join(chunk for chunk in chunks if chunk)
            
            return text
        except ImportError:
            # Fallback: simple regex-based extraction
            import re
            html = content.decode('utf-8', errors='ignore')
            # Remove script and style tags
            html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
            html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL | re.IGNORECASE)
            # Extract text from tags
            text = re.sub(r'<[^>]+>', '', html)
            # Clean up whitespace
            text = re.sub(r'\s+', ' ', text)
            return text
    
    async def _extract_from_pdf(self, content: bytes) -> str:
        """Extract text from PDF content."""
        try:
            import pdfplumber
            with pdfplumber.open(io.BytesIO(content)) as pdf:
                text_parts = []
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(page_text)
                return '\n\n'.join(text_parts)
        except ImportError:
            try:
                # Fallback to pypdf
                import pypdf
                pdf_reader = pypdf.PdfReader(io.BytesIO(content))
                text_parts = []
                for page in pdf_reader.pages:
                    text_parts.append(page.extract_text())
                return '\n\n'.join(text_parts)
            except ImportError:
                raise ValueError(
                    "PDF extraction requires either 'pdfplumber' or 'pypdf' package. "
                    "Install with: pip install pdfplumber or pip install pypdf"
                )


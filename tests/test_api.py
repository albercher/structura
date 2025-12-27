"""Tests for the Structura API endpoints."""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
import json
import io

from src.api.main import app

client = TestClient(app)


class TestHealthEndpoint:
    """Tests for the health check endpoint."""
    
    def test_health_endpoint(self):
        """Test that health endpoint returns healthy status."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}


class TestExtractFromURL:
    """Tests for URL-based extraction endpoint."""
    
    @patch('src.api.main.extraction_service.extract')
    def test_extract_from_url_success(self, mock_extract):
        """Test successful extraction from URL."""
        # Mock extraction result - use AsyncMock for async functions
        import asyncio
        async def mock_extract_async(*args, **kwargs):
            return {
                "product_name": "Test Product",
                "price": 29.99,
                "currency": "USD",
                "availability": "in_stock"
            }
        mock_extract.side_effect = mock_extract_async
        
        response = client.post(
            "/extract",
            json={
                "url": "https://example.com/product",
                "domain": "e-commerce",
                "schema_version": "v1"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "product_name" in data["data"]
        assert data["data"]["price"] == 29.99
    
    def test_extract_from_url_missing_domain(self):
        """Test that missing domain returns 422 validation error."""
        response = client.post(
            "/extract",
            json={
                "url": "https://example.com/product"
            }
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_extract_from_url_invalid_url(self):
        """Test that invalid URL returns validation error."""
        response = client.post(
            "/extract",
            json={
                "url": "not-a-valid-url",
                "domain": "e-commerce"
            }
        )
        
        assert response.status_code == 422  # Validation error
    
    @patch('src.api.main.extraction_service.extract')
    def test_extract_from_url_with_api_key_header(self, mock_extract):
        """Test extraction with API key in header."""
        async def mock_extract_async(*args, **kwargs):
            return {"product_name": "Test Product", "price": 29.99}
        mock_extract.side_effect = mock_extract_async
        
        response = client.post(
            "/extract",
            json={
                "url": "https://example.com/product",
                "domain": "e-commerce"
            },
            headers={"X-API-Key": "test-api-key-123"}
        )
        
        assert response.status_code == 200
        # Verify API key was passed
        mock_extract.assert_called_once()
        call_kwargs = mock_extract.call_args[1]
        assert call_kwargs.get("api_key") == "test-api-key-123"
    
    @patch('src.api.main.extraction_service.extract')
    def test_extract_from_url_with_api_key_body(self, mock_extract):
        """Test extraction with API key in request body."""
        async def mock_extract_async(*args, **kwargs):
            return {"product_name": "Test Product", "price": 29.99}
        mock_extract.side_effect = mock_extract_async
        
        response = client.post(
            "/extract",
            json={
                "url": "https://example.com/product",
                "domain": "e-commerce",
                "api_key": "test-api-key-123"
            }
        )
        
        assert response.status_code == 200
        # Verify API key was passed
        call_kwargs = mock_extract.call_args[1]
        assert call_kwargs.get("api_key") == "test-api-key-123"


class TestExtractFromFile:
    """Tests for file-based extraction endpoint."""
    
    @patch('src.api.main.extraction_service.extract')
    @patch('src.api.main.file_extractor.extract_markdown')
    def test_extract_from_markdown_file(self, mock_extract_markdown, mock_extract):
        """Test extraction from markdown file."""
        # Mock file content extraction
        async def mock_markdown_async(*args, **kwargs):
            return "# Product\n\nPrice: $29.99\nName: Test Product"
        mock_extract_markdown.side_effect = mock_markdown_async
        
        # Mock extraction result
        async def mock_extract_async(*args, **kwargs):
            return {
                "product_name": "Test Product",
                "price": 29.99,
                "currency": "USD"
            }
        mock_extract.side_effect = mock_extract_async
        
        # Create a test file
        file_content = b"# Product\n\nPrice: $29.99\nName: Test Product"
        files = {"file": ("test.md", file_content, "text/markdown")}
        data = {
            "domain": "e-commerce",
            "schema_version": "v1"
        }
        
        response = client.post(
            "/extract/file",
            files=files,
            data=data
        )
        
        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
        assert "product_name" in result["data"]
    
    @patch('src.api.main.extraction_service.extract')
    @patch('src.api.main.file_extractor.extract_markdown')
    def test_extract_from_text_file(self, mock_extract_markdown, mock_extract):
        """Test extraction from text file."""
        async def mock_markdown_async(*args, **kwargs):
            return "Product: Test Product\nPrice: 29.99"
        mock_extract_markdown.side_effect = mock_markdown_async
        
        async def mock_extract_async(*args, **kwargs):
            return {"product_name": "Test Product", "price": 29.99}
        mock_extract.side_effect = mock_extract_async
        
        file_content = b"Product: Test Product\nPrice: 29.99"
        files = {"file": ("test.txt", file_content, "text/plain")}
        data = {"domain": "e-commerce"}
        
        response = client.post(
            "/extract/file",
            files=files,
            data=data
        )
        
        assert response.status_code == 200
    
    def test_extract_from_file_missing_domain(self):
        """Test that missing domain returns 422 validation error."""
        file_content = b"Test content"
        files = {"file": ("test.txt", file_content, "text/plain")}
        
        response = client.post(
            "/extract/file",
            files=files
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_extract_from_file_missing_file(self):
        """Test that missing file returns 422 validation error."""
        data = {"domain": "e-commerce"}
        
        response = client.post(
            "/extract/file",
            data=data
        )
        
        assert response.status_code == 422  # Validation error
    
    @patch('src.api.main.extraction_service.extract')
    @patch('src.api.main.file_extractor.extract_markdown')
    def test_extract_from_file_with_api_key(self, mock_extract_markdown, mock_extract):
        """Test file extraction with API key."""
        async def mock_markdown_async(*args, **kwargs):
            return "Test content"
        mock_extract_markdown.side_effect = mock_markdown_async
        
        async def mock_extract_async(*args, **kwargs):
            return {"product_name": "Test"}
        mock_extract.side_effect = mock_extract_async
        
        file_content = b"Test content"
        files = {"file": ("test.txt", file_content, "text/plain")}
        data = {
            "domain": "e-commerce",
            "api_key": "test-api-key-123"
        }
        
        response = client.post(
            "/extract/file",
            files=files,
            data=data
        )
        
        assert response.status_code == 200
        # Verify API key was passed
        call_kwargs = mock_extract.call_args[1]
        assert call_kwargs.get("api_key") == "test-api-key-123"


class TestErrorHandling:
    """Tests for error handling."""
    
    @patch('src.api.main.extraction_service.extract')
    def test_extract_blueprint_not_found(self, mock_extract):
        """Test handling of blueprint not found error."""
        async def mock_extract_async(*args, **kwargs):
            raise ValueError("Blueprint 'unknown' not found")
        mock_extract.side_effect = mock_extract_async
        
        response = client.post(
            "/extract",
            json={
                "url": "https://example.com/product",
                "domain": "unknown"
            }
        )
        
        assert response.status_code == 400
    
    @patch('src.api.main.extraction_service.extract')
    def test_extract_invalid_url_content(self, mock_extract):
        """Test handling of invalid URL content."""
        async def mock_extract_async(*args, **kwargs):
            raise ValueError("No content extracted from URL")
        mock_extract.side_effect = mock_extract_async
        
        response = client.post(
            "/extract",
            json={
                "url": "https://example.com/empty",
                "domain": "e-commerce"
            }
        )
        
        assert response.status_code == 400
    
    @patch('src.api.main.extraction_service.extract')
    def test_extract_internal_error(self, mock_extract):
        """Test handling of internal server errors."""
        async def mock_extract_async(*args, **kwargs):
            raise Exception("Unexpected error")
        mock_extract.side_effect = mock_extract_async
        
        response = client.post(
            "/extract",
            json={
                "url": "https://example.com/product",
                "domain": "e-commerce"
            }
        )
        
        assert response.status_code == 500
        assert "Internal server error" in response.json()["detail"]


class TestFileExtractor:
    """Tests for file extractor functionality."""
    
    @patch('src.extractors.file_extractor.FileExtractor._extract_from_html')
    async def test_extract_html_file(self, mock_html_extract):
        """Test HTML file extraction."""
        from src.extractors.file_extractor import FileExtractor
        from fastapi import UploadFile
        
        mock_html_extract.return_value = "Extracted text from HTML"
        
        extractor = FileExtractor()
        file = UploadFile(
            filename="test.html",
            file=io.BytesIO(b"<html><body>Test</body></html>")
        )
        
        result = await extractor.extract_markdown(file)
        assert result == "Extracted text from HTML"
    
    async def test_extract_markdown_file(self):
        """Test markdown file extraction."""
        from src.extractors.file_extractor import FileExtractor
        from fastapi import UploadFile
        
        extractor = FileExtractor()
        file = UploadFile(
            filename="test.md",
            file=io.BytesIO(b"# Test Markdown\n\nThis is a test.")
        )
        
        result = await extractor.extract_markdown(file)
        assert "# Test Markdown" in result
        assert "This is a test" in result
    
    async def test_extract_text_file(self):
        """Test text file extraction."""
        from src.extractors.file_extractor import FileExtractor
        from fastapi import UploadFile
        
        extractor = FileExtractor()
        file = UploadFile(
            filename="test.txt",
            file=io.BytesIO(b"Plain text content")
        )
        
        result = await extractor.extract_markdown(file)
        assert result == "Plain text content"
    
    async def test_extract_unsupported_file_type(self):
        """Test handling of unsupported file types."""
        from src.extractors.file_extractor import FileExtractor
        from fastapi import UploadFile
        
        extractor = FileExtractor()
        # Create a binary file that can't be decoded as text
        # Use a file extension that's not in the supported list
        file = UploadFile(
            filename="test.exe",  # .exe is not supported
            file=io.BytesIO(b'\x00\x01\x02\x03\x04\xff\xfe')
        )
        
        # The extractor will try to decode as text, which should fail
        # and raise a ValueError about unsupported file type
        with pytest.raises(ValueError):
            await extractor.extract_markdown(file)


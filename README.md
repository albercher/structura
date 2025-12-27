# Structura

A service that extracts structured data from URLs using Firecrawl and LLM. Convert messy product pages, documents, and other web content into clean, standardized JSON.

## Features

- **URL-based extraction**: Extract structured data from any URL
- **Domain-specific schemas**: Use blueprints to define expected data structure per domain
- **LLM-powered**: Uses OpenAI GPT models to intelligently extract and structure data
- **Validation**: Automatically validates extracted data against JSON schemas
- **Firecrawl integration**: Leverages Firecrawl for high-quality markdown extraction

## Architecture

```
┌─────────────┐
│   FastAPI   │
│   /extract  │
└──────┬──────┘
       │
       ▼
┌──────────────────┐
│ ExtractionService│
└──────┬───────────┘
       │
       ├──► FirecrawlExtractor (markdown extraction)
       ├──► PromptBuilder (combines markdown + blueprint)
       ├──► OpenAIClient (LLM extraction)
       └──► SchemaValidator (validation)
```

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 1a. (Optional) Install Ollama for Local Development

If you want to use Ollama instead of OpenAI for local development/testing:

1. **Install Ollama**: Visit [https://ollama.ai](https://ollama.ai) and install Ollama
2. **Pull a model**: Run `ollama pull llama3.2` (or another model)
3. **Start Ollama**: Ollama runs automatically after installation, or start it with `ollama serve`

### 2. Configure Environment Variables

Copy `.env.example` to `.env` and fill in your API keys:

```bash
cp .env.example .env
```

Edit `.env` and add your configuration:

**For OpenAI (default):**
```
OPENAI_API_KEY=your_openai_api_key_here
```

**For Ollama (local development):**
```
OPENAI_BASE_URL=http://localhost:11434/v1
OPENAI_API_KEY=ollama
LLM_MODEL=llama3.2
```

Optionally add Firecrawl API key if using their cloud service:

```
FIRECRAWL_API_KEY=your_firecrawl_api_key_here
```

### 3. Run the API

```bash
python -m src.api.main
```

Or using uvicorn directly:

```bash
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

## Usage

### API Endpoint

**POST** `/extract`

**Request Body:**
```json
{
  "url": "https://example.com/product-page",
  "domain": "e-commerce",
  "schema_version": "v1"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "product_name": "Example Product",
    "price": 29.99,
    "currency": "USD",
    "availability": "in_stock",
    ...
  }
}
```

### Example with cURL

**Windows PowerShell/Command Prompt:**
```powershell
curl.exe -X POST "http://localhost:8000/extract" -H "Content-Type: application/json" -d '{\"url\": \"https://example.com/product\", \"domain\": \"e-commerce\", \"schema_version\": \"v1\"}'
```

**Windows PowerShell (alternative with here-string):**
```powershell
$body = @{
    url = "https://example.com/product"
    domain = "e-commerce"
    schema_version = "v1"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/extract" -Method POST -Body $body -ContentType "application/json"
```

**Linux/Mac/WSL:**
```bash
curl -X POST "http://localhost:8000/extract" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com/product",
    "domain": "e-commerce",
    "schema_version": "v1"
  }'
```

### Example with Python

```python
import requests

response = requests.post(
    "http://localhost:8000/extract",
    json={
        "url": "https://example.com/product",
        "domain": "e-commerce",
        "schema_version": "v1"
    }
)

data = response.json()
print(data["data"])
```

## Blueprints

Blueprints are JSON schemas that define the expected structure for each domain.

### Open Source Blueprints

These blueprints are available in the public repository:

- **e-commerce**: Product information extraction (name, price, availability, images, etc.)

### Protected Blueprints

Protected blueprints (medical, legal, finance, etc.) are available exclusively through the [Structura Cloud API](https://rapidapi.com/your-link) and require an API key. These are stored in Firebase and accessed via authentication.

**Using Protected Blueprints:**

Include an `api_key` in your request:

```json
{
  "url": "https://example.com/medical-report",
  "domain": "medical",
  "schema_version": "v1",
  "api_key": "your_api_key_here"
}
```

### Creating New Blueprints

1. Create a new JSON file in `blueprints/` directory
2. Name it following the pattern: `{domain}.json`
3. Use JSON Schema format to define the structure

Example blueprint structure:
```json
{
  "title": "Domain Schema",
  "type": "object",
  "properties": {
    "field1": {
      "type": "string",
      "description": "Field description"
    }
  },
  "required": ["field1"]
}
```

## Project Structure

```
structura/
├── blueprints/          # JSON schema blueprints
│   └── e-commerce.json
├── src/
│   ├── api/            # FastAPI application
│   │   └── main.py
│   ├── extractors/     # Content extraction
│   │   └── firecrawl_extractor.py
│   ├── llm/            # LLM integration
│   │   └── openai_client.py
│   ├── prompts/        # Prompt building
│   │   └── prompt_builder.py
│   ├── services/       # Business logic
│   │   └── extraction_service.py
│   ├── validators/     # Schema validation
│   │   └── schema_validator.py
│   └── config.py       # Configuration
├── requirements.txt
├── .env.example
└── README.md
```

## API Documentation

Once the server is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Error Handling

The API returns appropriate HTTP status codes:
- `200`: Success
- `400`: Bad request (invalid input)
- `404`: Blueprint not found
- `500`: Internal server error

Error responses include a message:
```json
{
  "success": false,
  "error": "Error message here"
}
```

## Development

<!-- ### Running Tests

(Add test instructions as tests are added) -->

### Adding New Domains

1. Create a new blueprint JSON schema in `blueprints/`
2. Test with sample URLs from that domain
3. Adjust prompts if needed in `src/prompts/prompt_builder.py`

## License

Structura is an **Open Core** project.

- **Core Engine:** The scraper engine, FastAPI wrapper, and E-commerce blueprint are licensed under the **MIT License**. You are free to host, modify, and use these for any purpose.
- **Enterprise Blueprints:** Specialized high-accuracy blueprints (Medical, Legal, Finance) are proprietary and available exclusively through the [Structura Cloud API](https://rapidapi.com/your-link).

## Contributing

Contributions are what make the open-source community such an amazing place to learn, inspire, and create. Any contributions you make are **greatly appreciated**.

**How to contribute:**
1. **Report Bugs:** Open an issue with a clear description and steps to reproduce.
2. **Add Blueprints:** We are always looking for new domain schemas (Legal, Finance, etc.).
3. **Submit a PR:** - Fork the Project
   - Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
   - Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
   - Push to the Branch (`git push origin feature/AmazingFeature`)
   - Open a Pull Request

*Note: As this is a side project, please allow 1-2 weeks for PR reviews.*
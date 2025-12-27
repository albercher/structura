import os
from dotenv import load_dotenv

load_dotenv()

# Firecrawl API key (optional, depends on Firecrawl setup)
FIRECRAWL_API_KEY = os.getenv("FIRECRAWL_API_KEY", "")

# OpenAI configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "") or None  # Optional: set to "http://localhost:11434/v1" for Ollama

# LLM configuration
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")  # Default for standard domains
LLM_MODEL_PREMIUM = os.getenv("LLM_MODEL_PREMIUM", "deepseek-v3")  # For premium domains
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.3"))

# Blueprints directory (for open source blueprints)
BLUEPRINTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "blueprints")

# Firebase configuration (for protected blueprints)
FIREBASE_PROJECT_ID = os.getenv("FIREBASE_PROJECT_ID", "")
FIREBASE_COLLECTION = os.getenv("FIREBASE_COLLECTION", "blueprints")
FIREBASE_CREDENTIALS_PATH = os.getenv("FIREBASE_CREDENTIALS_PATH", "")  # Path to service account JSON file


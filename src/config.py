import os
from dotenv import load_dotenv

load_dotenv()

# Firecrawl API key (optional, depends on Firecrawl setup)
FIRECRAWL_API_KEY = os.getenv("FIRECRAWL_API_KEY", "")

# OpenAI API key for LLM
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# LLM configuration
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.3"))

# Blueprints directory
BLUEPRINTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "blueprints")


"""Open source blueprints available in the public repository."""
import json
import logging
from pathlib import Path
from typing import Dict, Any
from src.config import BLUEPRINTS_DIR

logger = logging.getLogger(__name__)


def _load_open_blueprints() -> Dict[str, Dict[str, Any]]:
    """
    Load all open source blueprints from the blueprints/ directory.
    
    Returns:
        Dictionary mapping domain names to blueprint schemas
    """
    blueprints = {}
    blueprints_path = Path(BLUEPRINTS_DIR)
    
    if not blueprints_path.exists():
        logger.warning(f"Blueprints directory not found: {blueprints_path}")
        return blueprints
    
    # Load all JSON files from blueprints directory
    for blueprint_file in blueprints_path.glob("*.json"):
        try:
            domain = blueprint_file.stem  # Get filename without extension
            with open(blueprint_file, "r", encoding="utf-8") as f:
                schema = json.load(f)
            
            # Store with the filename as key
            blueprints[domain] = schema
            
            # Also create common aliases (e.g., "e-commerce" -> "ecommerce")
            if domain == "e-commerce":
                blueprints["ecommerce"] = schema
            elif domain == "ecommerce":
                blueprints["e-commerce"] = schema
                
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse blueprint file {blueprint_file}: {str(e)}")
        except Exception as e:
            logger.error(f"Error loading blueprint {blueprint_file}: {str(e)}")
    
    return blueprints


# Load blueprints once at module import
OPEN_BLUEPRINTS = _load_open_blueprints()


def get_open_blueprint(domain: str) -> Dict[str, Any]:
    """
    Get an open source blueprint if available.
    
    Args:
        domain: Domain name (e.g., "e-commerce")
        
    Returns:
        Blueprint schema if found
        
    Raises:
        KeyError: If blueprint is not in open source list
    """
    if domain not in OPEN_BLUEPRINTS:
        raise KeyError(f"Domain '{domain}' is not available in open source blueprints")
    return OPEN_BLUEPRINTS[domain]


def is_open_blueprint(domain: str) -> bool:
    """
    Check if a domain has an open source blueprint.
    
    Args:
        domain: Domain name
        
    Returns:
        True if blueprint is open source, False otherwise
    """
    return domain in OPEN_BLUEPRINTS


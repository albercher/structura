"""Validates extracted data against JSON schemas."""
import json
import logging
from typing import Dict, Any, Tuple, Optional
import jsonschema
from jsonschema import validate, ValidationError

logger = logging.getLogger(__name__)


class SchemaValidator:
    """Validates data against JSON schemas."""
    
    @staticmethod
    def validate_data(data: Dict[str, Any], schema: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Validate data against a JSON schema.
        
        Args:
            data: The extracted data to validate
            schema: The JSON schema to validate against
            
        Returns:
            Tuple of (is_valid, error_message)
            If valid, error_message is None
        """
        try:
            validate(instance=data, schema=schema)
            return True, None
        except ValidationError as e:
            error_msg = f"Validation error: {e.message} at path: {'.'.join(str(x) for x in e.path)}"
            logger.warning(f"Schema validation failed: {error_msg}")
            return False, error_msg
        except Exception as e:
            error_msg = f"Unexpected validation error: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    @staticmethod
    def validate_and_fix_required_fields(data: Dict[str, Any], schema: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ensure all required fields are present, using defaults if needed.
        
        Args:
            data: The extracted data
            schema: The JSON schema
            
        Returns:
            Data with required fields ensured
        """
        if "required" not in schema or not schema["required"]:
            return data
        
        required_fields = schema["required"]
        fixed_data = data.copy()
        
        for field in required_fields:
            if field not in fixed_data:
                # Try to get default from schema
                field_schema = schema.get("properties", {}).get(field, {})
                if "default" in field_schema:
                    fixed_data[field] = field_schema["default"]
                else:
                    # Use None as fallback (though this may still fail validation)
                    fixed_data[field] = None
        
        return fixed_data


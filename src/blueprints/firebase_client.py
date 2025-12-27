"""Firebase client for protected blueprints."""
import logging
import json
import os
import asyncio
from typing import Dict, Any, Optional
import firebase_admin
from firebase_admin import credentials, firestore
from src.config import FIREBASE_PROJECT_ID, FIREBASE_COLLECTION, FIREBASE_CREDENTIALS_PATH

logger = logging.getLogger(__name__)

# Global Firebase app instance
_firebase_app = None


class FirebaseBlueprintClient:
    """Client for fetching protected blueprints from Firebase Firestore."""
    
    def __init__(self, project_id: str = None, collection: str = None):
        """
        Initialize Firebase client.
        
        Args:
            project_id: Firebase project ID. If not provided, uses config default.
            collection: Firebase collection name. If not provided, uses config default.
        """
        self.project_id = project_id or FIREBASE_PROJECT_ID
        self.collection = collection or FIREBASE_COLLECTION
        
        if not self.project_id:
            raise ValueError("Firebase project ID is required. Set FIREBASE_PROJECT_ID environment variable.")
        if not self.collection:
            raise ValueError("Firebase collection is required. Set FIREBASE_COLLECTION environment variable.")
        
        # Initialize Firebase Admin SDK
        self._init_firebase()
        self.db = firestore.client()
    
    def _init_firebase(self):
        """Initialize Firebase Admin SDK."""
        global _firebase_app
        
        if _firebase_app is None:
            try:
                # Try to initialize with credentials file
                creds_path = FIREBASE_CREDENTIALS_PATH
                if creds_path and os.path.exists(creds_path):
                    cred = credentials.Certificate(creds_path)
                    _firebase_app = firebase_admin.initialize_app(cred, {
                        'projectId': self.project_id
                    })
                    logger.info("Firebase initialized with credentials file")
                else:
                    # Try to use default credentials (for deployed environments)
                    _firebase_app = firebase_admin.initialize_app()
                    logger.info("Firebase initialized with default credentials")
            except Exception as e:
                logger.error(f"Failed to initialize Firebase: {str(e)}")
                raise ValueError(f"Failed to initialize Firebase: {str(e)}")
    
    def _get_blueprint_sync(self, domain: str, api_key: str) -> Dict[str, Any]:
        """
        Synchronous method to fetch a protected blueprint from Firebase.
        
        Args:
            domain: Domain name (e.g., "medical", "legal")
            api_key: API key for authentication
            
        Returns:
            Blueprint schema as dictionary
        """
        # Validate API key and check access
        doc_ref = self.db.collection(self.collection).document(domain)
        doc = doc_ref.get()
        
        if not doc.exists:
            raise ValueError(f"Blueprint '{domain}' not found in protected blueprints")
        
        data = doc.to_dict()
        
        # Validate API key has access to this blueprint
        if not self._validate_api_key(api_key, domain):
            raise ValueError(f"Access denied to blueprint '{domain}'. Invalid API key.")
        
        # Extract blueprint schema
        # Assuming blueprint is stored in a 'schema' field
        if 'schema' in data:
            if isinstance(data['schema'], str):
                return json.loads(data['schema'])
            elif isinstance(data['schema'], dict):
                return data['schema']
            else:
                raise ValueError(f"Invalid blueprint schema format for '{domain}'")
        else:
            # If schema is not in a 'schema' field, return the whole document
            return data
    
    async def get_blueprint(self, domain: str, api_key: Optional[str] = None) -> Dict[str, Any]:
        """
        Fetch a protected blueprint from Firebase.
        
        Args:
            domain: Domain name (e.g., "medical", "legal")
            api_key: API key for authentication (required for protected blueprints)
            
        Returns:
            Blueprint schema as dictionary
            
        Raises:
            ValueError: If API key is missing or invalid
            Exception: If blueprint not found or fetch fails
        """
        if not api_key:
            raise ValueError(
                f"Protected blueprint '{domain}' requires API key authentication. "
                f"Please provide a valid API key or use an open source blueprint."
            )
        
        try:
            # Run synchronous Firebase call in executor
            loop = asyncio.get_event_loop()
            blueprint = await loop.run_in_executor(None, self._get_blueprint_sync, domain, api_key)
            return blueprint
                
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Error fetching blueprint from Firebase: {str(e)}")
            raise Exception(f"Failed to fetch protected blueprint: {str(e)}") from e
    
    def _validate_api_key(self, api_key: str, domain: str) -> bool:
        """
        Validate API key has access to the requested blueprint.
        
        TODO: Implement proper API key validation logic.
        This could check:
        - API key exists in a 'api_keys' collection
        - API key has access to this specific domain
        - API key is not expired
        - API key usage limits
        
        Args:
            api_key: API key to validate
            domain: Domain name being accessed
            
        Returns:
            True if API key is valid and has access, False otherwise
        """
        # TODO: Implement proper validation
        # For now, this is a placeholder that always returns True
        # You should:
        # 1. Check if api_key exists in your api_keys collection
        # 2. Check if the key has access to this domain
        # 3. Check rate limits, expiration, etc.
        try:
            # Example: Check if API key exists and has access
            key_ref = self.db.collection('api_keys').document(api_key)
            key_doc = key_ref.get()
            
            if not key_doc.exists:
                return False
            
            key_data = key_doc.to_dict()
            allowed_domains = key_data.get('allowed_domains', [])
            
            # Check if domain is in allowed domains list, or if '*' means all domains
            if '*' in allowed_domains or domain in allowed_domains:
                # Check if key is active
                if key_data.get('active', False):
                    return True
            
            return False
        except Exception as e:
            logger.error(f"Error validating API key: {str(e)}")
            return False


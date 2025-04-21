from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import requests
from datetime import datetime
import os
from dotenv import load_dotenv
from loguru import logger

load_dotenv()

class BaseAPIClient(ABC):
    """Base class for all API clients."""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'SmartPick/1.0 (Device Comparison Tool)'
        })
    
    @abstractmethod
    def search_devices(self, query: str, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """Search for devices matching the query."""
        pass
    
    @abstractmethod
    def get_device_details(self, device_id: str) -> Dict[str, Any]:
        """Get detailed information about a specific device."""
        pass
    
    def _make_request(self, url: str, method: str = 'GET', **kwargs) -> Dict[str, Any]:
        """Make an HTTP request with error handling and logging."""
        try:
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {str(e)}")
            raise
    
    def _cache_response(self, key: str, data: Dict[str, Any], expiry_minutes: int = 60) -> None:
        """Cache API response data."""
        # TODO: Implement caching logic
        pass
    
    def _get_cached_response(self, key: str) -> Optional[Dict[str, Any]]:
        """Retrieve cached API response data."""
        # TODO: Implement cache retrieval logic
        pass 
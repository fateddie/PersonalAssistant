"""
API Client for Streamlit
=========================
Simple HTTP client for Assistant API

This client is intended for use by the Streamlit UI layer.
It communicates with the Assistant API via HTTP, maintaining
proper layer separation.
"""
import requests
from typing import List, Dict, Optional
from datetime import date


class AssistantAPIClient:
    """Client for Assistant API"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip("/")

    def health_check(self) -> Dict:
        """Check API health"""
        response = requests.get(f"{self.base_url}/health")
        response.raise_for_status()
        return response.json()

    # Items endpoints
    def list_items(
        self,
        type: Optional[List[str]] = None,
        status: Optional[str] = None,
        source: Optional[str] = None,
        category: Optional[str] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        search: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Dict:
        """
        List items with filtering

        Returns: {"items": [...], "total": int}
        """
        params = {
            "limit": limit,
            "offset": offset
        }

        if type:
            params["type"] = type
        if status:
            params["status"] = status
        if source:
            params["source"] = source
        if category:
            params["category"] = category
        if date_from:
            params["date_from"] = date_from.isoformat()
        if date_to:
            params["date_to"] = date_to.isoformat()
        if search:
            params["search"] = search

        response = requests.get(f"{self.base_url}/items", params=params)
        response.raise_for_status()
        return response.json()

    def get_item(self, item_id: str) -> Dict:
        """Get single item by ID"""
        response = requests.get(f"{self.base_url}/items/{item_id}")
        response.raise_for_status()
        return response.json()

    def create_item(self, item_data: Dict) -> Dict:
        """Create new item"""
        response = requests.post(f"{self.base_url}/items", json=item_data)
        if not response.ok:
            error_detail = response.text[:200] if response.text else f"HTTP {response.status_code}"
            raise Exception(f"{response.status_code} Server Error: {error_detail} for url: {response.url}")
        return response.json()

    def update_item(self, item_id: str, updates: Dict) -> Dict:
        """Update existing item (partial)"""
        response = requests.patch(f"{self.base_url}/items/{item_id}", json=updates)
        if not response.ok:
            error_detail = response.text[:200] if response.text else f"HTTP {response.status_code}"
            raise Exception(f"{response.status_code} Server Error: {error_detail} for url: {response.url}")
        return response.json()

    def delete_item(self, item_id: str) -> None:
        """Delete item"""
        response = requests.delete(f"{self.base_url}/items/{item_id}")
        response.raise_for_status()

    # Stats endpoints
    def get_stats(self) -> Dict:
        """
        Get dashboard statistics

        Returns: {
            "count_by_type": {...},
            "count_by_status": {...},
            "today": {...}
        }
        """
        response = requests.get(f"{self.base_url}/stats/summary")
        response.raise_for_status()
        return response.json()

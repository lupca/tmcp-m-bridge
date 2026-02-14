import json
import httpx
from typing import Any, Dict, List

class PocketBaseClient:
    def __init__(self, base_url: str, user: str, password: str):
        self.base_url = base_url.rstrip("/")
        self.user = user
        self.password = password
        self.token = None
        self.client = httpx.Client(timeout=30.0)

    def authenticate(self):
        # Try admin auth first (via _superusers collection in PB v0.23+)
        try:
            auth_url = f"{self.base_url}/api/collections/_superusers/auth-with-password"
            response = self.client.post(auth_url, json={
                "identity": self.user,
                "password": self.password
            })
            response.raise_for_status()
            data = response.json()
            self.token = data["token"]
            return
        except Exception:
            # Fallback to user auth
            try:
                auth_url = f"{self.base_url}/api/collections/users/auth-with-password"
                response = self.client.post(auth_url, json={
                    "identity": self.user,
                    "password": self.password
                })
                response.raise_for_status()
                data = response.json()
                self.token = data["token"]
            except Exception as e:
                raise RuntimeError(f"Authentication failed: {e}")

    def _get_headers(self) -> Dict[str, str]:
        if not self.token:
            self.authenticate()
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }

    def _request(self, method: str, endpoint: str, **kwargs) -> Any:
        url = f"{self.base_url}{endpoint}"
        headers = self._get_headers()
        
        # Merge created headers with any passed in headers
        if "headers" in kwargs:
            headers.update(kwargs["headers"])
            del kwargs["headers"]
            
        try:
            response = self.client.request(method, url, headers=headers, **kwargs)
            
            # Handle token expiry (401) by re-authenticating once
            if response.status_code == 401:
                self.authenticate()
                headers = self._get_headers()
                response = self.client.request(method, url, headers=headers, **kwargs)
                
            response.raise_for_status()
            return response.json() if response.content else None
        except httpx.HTTPStatusError as e:
            # Try to return the error message from PocketBase if available
            error_message = None
            try:
                error_data = e.response.json()
                error_message = f"PocketBase API Error: {json.dumps(error_data, indent=2)}"
            except Exception:
                pass
            
            if error_message:
                raise RuntimeError(error_message)
            else:
                raise RuntimeError(f"HTTP Error: {e}")
        except Exception as e:
            raise RuntimeError(f"Request failed: {e}")

    def list_collections(self) -> List[Dict[str, Any]]:
        # Use standard API to list collections
        return self._request("GET", "/api/collections")["items"]

    def get_collection_schema(self, collection_name_or_id: str) -> Dict[str, Any]:
        # Use standard API to get collection details
        return self._request("GET", f"/api/collections/{collection_name_or_id}")

    def list_records(self, collection: str, page: int = 1, per_page: int = 30, filter_str: str = "") -> Dict[str, Any]:
        params = {
            "page": page,
            "perPage": per_page,
            "filter": filter_str
        }
        return self._request("GET", f"/api/collections/{collection}/records", params=params)

    def get_record(self, collection: str, record_id: str) -> Dict[str, Any]:
        return self._request("GET", f"/api/collections/{collection}/records/{record_id}")

    def create_record(self, collection: str, data: Dict[str, Any]) -> Dict[str, Any]:
        return self._request("POST", f"/api/collections/{collection}/records", json=data)

    def update_record(self, collection: str, record_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        return self._request("PATCH", f"/api/collections/{collection}/records/{record_id}", json=data)

    def delete_record(self, collection: str, record_id: str) -> bool:
        self._request("DELETE", f"/api/collections/{collection}/records/{record_id}")
        return True

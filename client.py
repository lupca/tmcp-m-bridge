import json
import httpx
from typing import Any, Dict, List, Optional

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
        """List all available PocketBase collections."""
        return self._request("GET", "/api/collections")["items"]

    def get_collection_schema(self, collection_name_or_id: str) -> Dict[str, Any]:
        """Get full schema details for a specific collection."""
        return self._request("GET", f"/api/collections/{collection_name_or_id}")

    def list_records(
        self,
        collection: str,
        page: int = 1,
        per_page: int = 30,
        filter_str: str = "",
        sort: str = "",
        expand: str = "",
        fields: str = "",
    ) -> Dict[str, Any]:
        """List records with pagination, filtering, sorting, expand, and field selection.

        Args:
            collection: Collection name or ID.
            page: Page number (1-based).
            per_page: Number of records per page (max 500).
            filter_str: PB filter expression, e.g. "status = 'Done'".
            sort: Comma-separated fields, prefix with - for DESC, e.g. "-created,name".
            expand: Comma-separated relation fields to expand, e.g. "campaignId,worksheetId".
            fields: Comma-separated field names to return, e.g. "id,name,created".
        """
        params: Dict[str, Any] = {"page": page, "perPage": per_page}
        if filter_str:
            params["filter"] = filter_str
        if sort:
            params["sort"] = sort
        if expand:
            params["expand"] = expand
        if fields:
            params["fields"] = fields
        return self._request("GET", f"/api/collections/{collection}/records", params=params)

    def get_record(
        self,
        collection: str,
        record_id: str,
        expand: str = "",
        fields: str = "",
    ) -> Dict[str, Any]:
        """Retrieve a single record by ID with optional expand and field selection.

        Args:
            collection: Collection name or ID.
            record_id: The record ID.
            expand: Comma-separated relation fields to expand.
            fields: Comma-separated field names to return.
        """
        params: Dict[str, Any] = {}
        if expand:
            params["expand"] = expand
        if fields:
            params["fields"] = fields
        return self._request("GET", f"/api/collections/{collection}/records/{record_id}", params=params)

    def create_record(self, collection: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new record in the specified collection."""
        return self._request("POST", f"/api/collections/{collection}/records", json=data)

    def update_record(self, collection: str, record_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing record by ID."""
        return self._request("PATCH", f"/api/collections/{collection}/records/{record_id}", json=data)

    def delete_record(self, collection: str, record_id: str) -> bool:
        """Delete a record by ID."""
        self._request("DELETE", f"/api/collections/{collection}/records/{record_id}")
        return True

    # --- Token-forwarding methods ---

    def _request_with_token(self, method: str, endpoint: str, token: str, **kwargs) -> Any:
        """Make a request using an externally provided auth token (from the frontend user)."""
        url = f"{self.base_url}{endpoint}"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
        if "headers" in kwargs:
            headers.update(kwargs["headers"])
            del kwargs["headers"]

        try:
            response = self.client.request(method, url, headers=headers, **kwargs)
            response.raise_for_status()
            return response.json() if response.content else None
        except httpx.HTTPStatusError as e:
            error_message = None
            try:
                error_data = e.response.json()
                error_message = f"PocketBase API Error: {json.dumps(error_data, indent=2)}"
            except Exception:
                pass
            raise RuntimeError(error_message or f"HTTP Error: {e}")
        except Exception as e:
            raise RuntimeError(f"Request failed: {e}")

    def get_record_with_token(
        self, collection: str, record_id: str, token: str,
        expand: str = "", fields: str = "",
    ) -> Dict[str, Any]:
        """Retrieve a single record using an external auth token."""
        params: Dict[str, Any] = {}
        if expand:
            params["expand"] = expand
        if fields:
            params["fields"] = fields
        return self._request_with_token(
            "GET", f"/api/collections/{collection}/records/{record_id}",
            token, params=params,
        )

    def list_records_with_token(
        self, collection: str, token: str,
        page: int = 1, per_page: int = 30,
        filter_str: str = "", sort: str = "",
        expand: str = "", fields: str = "",
    ) -> Dict[str, Any]:
        """List records using an external auth token."""
        params: Dict[str, Any] = {"page": page, "perPage": per_page}
        if filter_str:
            params["filter"] = filter_str
        if sort:
            params["sort"] = sort
        if expand:
            params["expand"] = expand
        if fields:
            params["fields"] = fields
        return self._request_with_token(
            "GET", f"/api/collections/{collection}/records",
            token, params=params,
        )

    def create_record_with_token(self, collection: str, data: Dict[str, Any], token: str) -> Dict[str, Any]:
        """Create a new record using an external auth token."""
        return self._request_with_token("POST", f"/api/collections/{collection}/records", token, json=data)

    def update_record_with_token(self, collection: str, record_id: str, data: Dict[str, Any], token: str) -> Dict[str, Any]:
        """Update an existing record using an external auth token."""
        return self._request_with_token("PATCH", f"/api/collections/{collection}/records/{record_id}", token, json=data)

    def delete_record_with_token(self, collection: str, record_id: str, token: str) -> bool:
        """Delete a record using an external auth token."""
        self._request_with_token("DELETE", f"/api/collections/{collection}/records/{record_id}", token)
        return True

    def publish_facebook_variant(self, workspace_id: str, variant_id: str) -> Dict[str, Any]:
        """Publish a facebook platform variant through tmcp-dashboard custom endpoint."""
        return self._request(
            "POST",
            "/api/social/facebook/posts",
            json={"workspace_id": workspace_id, "variant_id": variant_id},
        )

    def publish_facebook_variant_with_token(self, workspace_id: str, variant_id: str, token: str) -> Dict[str, Any]:
        """Publish a facebook platform variant using forwarded user auth token."""
        return self._request_with_token(
            "POST",
            "/api/social/facebook/posts",
            token,
            json={"workspace_id": workspace_id, "variant_id": variant_id},
        )

    def count_records(self, collection: str, filter_str: str = "") -> int:
        """Get total count of records in a collection (with optional filter).

        Uses perPage=1 to minimize data transfer, returns totalItems.
        """
        result = self.list_records(collection, page=1, per_page=1, filter_str=filter_str)
        return result.get("totalItems", 0)

import json
from typing import Any, Dict
from runtime import mcp, pb_client

@mcp.tool()
def list_collections() -> str:
    """Lists all available collections in PocketBase."""
    try:
        collections = pb_client.list_collections()
        return json.dumps([{"name": c["name"], "id": c["id"], "type": c["type"]} for c in collections], indent=2)
    except Exception as e:
        return f"Error: {e}"

@mcp.tool()
def get_collection_schema(collection: str) -> str:
    """Gets the schema (fields and types) for a specific collection.
    Use this to understand what fields are available and required before creating or updating a record.
    """
    try:
        col_data = pb_client.get_collection_schema(collection)
        # Simplify output for the LLM
        fields = []
        # PB v0.23+ uses 'fields', older versions used 'schema'
        schema_fields = col_data.get("fields", col_data.get("schema", []))
        for field in schema_fields:
            fields.append({
                "name": field["name"],
                "type": field["type"],
                "required": field.get("required", False),
                "options": field.get("options", {})
            })
        return json.dumps(fields, indent=2)
    except Exception as e:
        return f"Error: {e}"

@mcp.tool()
def list_records(collection: str, page: int = 1, per_page: int = 30, filter: str = "") -> str:
    """Lists records in a collection with pagination and filtering."""
    try:
        result = pb_client.list_records(collection, page, per_page, filter)
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error: {e}"

@mcp.tool()
def get_record(collection: str, record_id: str) -> str:
    """Retrieves a single record by its ID."""
    try:
        record = pb_client.get_record(collection, record_id)
        return json.dumps(record, indent=2)
    except Exception as e:
        return f"Error: {e}"

@mcp.tool()
def create_record(collection: str, data: Dict[str, Any]) -> str:
    """Creates a new record in the specified collection."""
    try:
        record = pb_client.create_record(collection, data)
        return json.dumps(record, indent=2)
    except Exception as e:
        return f"Error: {e}"

@mcp.tool()
def update_record(collection: str, record_id: str, data: Dict[str, Any]) -> str:
    """Updates an existing record."""
    try:
        record = pb_client.update_record(collection, record_id, data)
        return json.dumps(record, indent=2)
    except Exception as e:
        return f"Error: {e}"

@mcp.tool()
def delete_record(collection: str, record_id: str) -> str:
    """Deletes a record."""
    try:
        pb_client.delete_record(collection, record_id)
        return f"Successfully deleted record {record_id} from {collection}"
    except Exception as e:
        return f"Error: {e}"

import json
from typing import Any, Dict
from runtime import mcp, pb_client

@mcp.tool()
def list_collections() -> str:
    """Lists all available collections in PocketBase.
    Returns each collection's name, id, and type.
    """
    try:
        collections = pb_client.list_collections()
        return json.dumps([{"name": c["name"], "id": c["id"], "type": c["type"]} for c in collections], indent=2)
    except Exception as e:
        return f"Error: {e}"

@mcp.tool()
def get_collection_schema(collection: str) -> str:
    """Gets the schema (fields and types) for a specific collection.
    Use this BEFORE creating or updating records to know required fields and their types.

    Args:
        collection: Collection name (e.g. "worksheets", "brand_identities", "marketing_campaigns")
    """
    try:
        col_data = pb_client.get_collection_schema(collection)
        fields = []
        schema_fields = col_data.get("fields", col_data.get("schema", []))
        for field in schema_fields:
            info = {
                "name": field["name"],
                "type": field["type"],
                "required": field.get("required", False),
            }
            # Include useful options based on field type
            if field["type"] == "select":
                info["values"] = field.get("values", [])
            elif field["type"] == "relation":
                info["collectionId"] = field.get("collectionId", "")
                info["maxSelect"] = field.get("maxSelect", 1)
                info["cascadeDelete"] = field.get("cascadeDelete", False)
            elif field["type"] in ("text", "url"):
                if field.get("max"):
                    info["max"] = field["max"]
            fields.append(info)
        return json.dumps(fields, indent=2)
    except Exception as e:
        return f"Error: {e}"

@mcp.tool()
def list_records(
    collection: str,
    page: int = 1,
    per_page: int = 30,
    filter: str = "",
    sort: str = "",
    expand: str = "",
    fields: str = "",
    auth_token: str = "",
) -> str:
    """Lists records in a collection with pagination, filtering, sorting, and relation expansion.

    Args:
        collection: Collection name (e.g. "worksheets", "campaign_tasks")
        page: Page number, starting from 1
        per_page: Records per page (max 500)
        filter: PocketBase filter expression (e.g. "status = 'Done'", "campaignId = 'abc123'")
        sort: Comma-separated field names. Prefix with - for DESC (e.g. "-created", "name,-updated")
        expand: Comma-separated relation field names to resolve inline (e.g. "campaignId", "worksheetId,campaignId")
        fields: Comma-separated field names to include in response (e.g. "id,name,status")
        auth_token: Optional auth token from the frontend user. If provided, uses this instead of bridge credentials.
    """
    try:
        if auth_token:
            result = pb_client.list_records_with_token(collection, auth_token, page, per_page, filter, sort, expand, fields)
        else:
            result = pb_client.list_records(collection, page, per_page, filter, sort, expand, fields)
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error: {e}"

@mcp.tool()
def get_record(
    collection: str,
    record_id: str,
    expand: str = "",
    fields: str = "",
    auth_token: str = "",
) -> str:
    """Retrieves a single record by its ID, with optional relation expansion.

    Args:
        collection: Collection name
        record_id: The record's unique ID
        expand: Comma-separated relation fields to resolve (e.g. "worksheetId")
        fields: Comma-separated fields to return (e.g. "id,name")
        auth_token: Optional auth token from the frontend user. If provided, uses this instead of bridge credentials.
    """
    try:
        if auth_token:
            record = pb_client.get_record_with_token(collection, record_id, auth_token, expand, fields)
        else:
            record = pb_client.get_record(collection, record_id, expand, fields)
        return json.dumps(record, indent=2)
    except Exception as e:
        return f"Error: {e}"

@mcp.tool()
def create_record(collection: str, data: Dict[str, Any], auth_token: str = "") -> str:
    """Creates a new record in the specified collection.
    IMPORTANT: Call get_collection_schema first to know required fields and types.

    Args:
        collection: Collection name
        data: Record data as a dict (e.g. {"name": "My Campaign", "worksheetId": "abc123"})
        auth_token: Optional auth token from the frontend user.
    """
    try:
        if auth_token:
            record = pb_client.create_record_with_token(collection, data, auth_token)
        else:
            record = pb_client.create_record(collection, data)
        return json.dumps(record, indent=2)
    except Exception as e:
        return f"Error: {e}"

@mcp.tool()
def update_record(collection: str, record_id: str, data: Dict[str, Any], auth_token: str = "") -> str:
    """Updates an existing record. Only include fields you want to change.

    Args:
        collection: Collection name
        record_id: The record's unique ID
        data: Fields to update (e.g. {"status": "Done", "week": 3})
        auth_token: Optional auth token from the frontend user.
    """
    try:
        if auth_token:
            record = pb_client.update_record_with_token(collection, record_id, data, auth_token)
        else:
            record = pb_client.update_record(collection, record_id, data)
        return json.dumps(record, indent=2)
    except Exception as e:
        return f"Error: {e}"

@mcp.tool()
def delete_record(collection: str, record_id: str, auth_token: str = "") -> str:
    """Deletes a record by ID. This action cannot be undone.

    Args:
        collection: Collection name
        record_id: The record's unique ID
        auth_token: Optional auth token from the frontend user.
    """
    try:
        if auth_token:
            pb_client.delete_record_with_token(collection, record_id, auth_token)
        else:
            pb_client.delete_record(collection, record_id)
        return f"Successfully deleted record {record_id} from {collection}"
    except Exception as e:
        return f"Error: {e}"

@mcp.tool()
def count_records(collection: str, filter: str = "") -> str:
    """Returns the total number of records in a collection, with optional filtering.

    Args:
        collection: Collection name
        filter: Optional PocketBase filter (e.g. "status = 'Done'")
    """
    try:
        count = pb_client.count_records(collection, filter)
        return json.dumps({"collection": collection, "totalItems": count, "filter": filter or "(none)"}, indent=2)
    except Exception as e:
        return f"Error: {e}"

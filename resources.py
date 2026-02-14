import json
from runtime import mcp, pb_client

@mcp.resource("pocketbase://")
def list_available_collections() -> str:
    """Lists all available PocketBase collections."""
    try:
        collections = pb_client.list_collections()
        return json.dumps([c["name"] for c in collections], indent=2)
    except Exception as e:
        return f"Error listing collections: {e}"

@mcp.resource("pocketbase://{collection}/schema")
def get_resource_collection_schema(collection: str) -> str:
    """Returns the schema for a specific collection."""
    try:
        schema = pb_client.get_collection_schema(collection)
        # PB v0.23+ uses 'fields', older versions used 'schema'
        return json.dumps(schema.get("fields", schema.get("schema", [])), indent=2)
    except Exception as e:
        return f"Error fetching schema for {collection}: {e}"

@mcp.resource("pocketbase://{collection}/{record_id}")
def get_resource_record(collection: str, record_id: str) -> str:
    """Returns a specific record by ID."""
    try:
        record = pb_client.get_record(collection, record_id)
        return json.dumps(record, indent=2)
    except Exception as e:
        return f"Error fetching record {record_id} from {collection}: {e}"

from mcp.server.fastmcp import FastMCP
from config import POCKETBASE_URL, POCKETBASE_USER, POCKETBASE_PASSWORD
from client import PocketBaseClient

mcp = FastMCP("PocketBase Bridge", host="0.0.0.0", port=7999)
pb_client = PocketBaseClient(POCKETBASE_URL, POCKETBASE_USER, POCKETBASE_PASSWORD)


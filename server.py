from client import PocketBaseClient
from config import POCKETBASE_URL, POCKETBASE_USER, POCKETBASE_PASSWORD
from runtime import mcp
import resources
import tools

def main():
    mcp.run(transport="sse")

if __name__ == "__main__":
    main()

import asyncio
import sys
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def run():
    server_params = StdioServerParameters(
        command=sys.executable,
        args=["tmcp_m_bridge/server.py"],
        env=None
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize the connection
            await session.initialize()

            # List tools
            tools = await session.list_tools()
            print(f"Tools available: {[t.name for t in tools.tools]}")

            # List resources
            resources = await session.list_resources()
            print(f"Resources available: {[r.uri for r in resources.resources]}")

            # Try listing collections
            result = await session.call_tool("list_collections", {})
            print("CollectionsResult:", result.content)

if __name__ == "__main__":
    asyncio.run(run())

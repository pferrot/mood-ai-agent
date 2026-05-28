from langchain_core.tools import BaseTool
from langchain_mcp_adapters.client import MultiServerMCPClient

from .config import settings


async def get_mcp_tools() -> list[BaseTool]:
    """Load tools from all configured MCP servers.

    Returns an empty list when no MCP servers are configured so the agent
    still works out of the box without any external servers.
    """
    if not settings.mcp_servers:
        return []

    client = MultiServerMCPClient(settings.mcp_servers)
    return await client.get_tools()

import logging

from langchain_core.tools import BaseTool
from langchain_mcp_adapters.client import MultiServerMCPClient

from .config import settings

logger = logging.getLogger(__name__)


async def get_mcp_tools() -> list[BaseTool]:
    """Load tools from all configured MCP servers.

    Returns an empty list when no MCP servers are configured so the agent
    still works out of the box without any external servers.
    """
    if not settings.mcp_servers:
        logger.info("No MCP servers configured; continuing without external tools.")
        return []

    try:
        logger.info("Loading MCP tools from servers: %s", ", ".join(settings.mcp_servers))
        client = MultiServerMCPClient(settings.mcp_servers)
        tools = await client.get_tools()
    except Exception:
        logger.exception("Failed to load MCP tools; continuing without external tools.")
        return []

    tool_names = [tool.name for tool in tools]
    if tool_names:
        logger.info("Loaded MCP tools: %s", ", ".join(tool_names))
    else:
        logger.info("No MCP tools loaded from configured servers.")
    return tools

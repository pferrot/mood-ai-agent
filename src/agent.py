import asyncio
import logging
import re
from typing import Any

from langchain.agents import create_agent
from langchain.agents.middleware import wrap_tool_call
from langchain_core.tools import BaseTool
from langchain_ollama import ChatOllama
from langgraph.graph.state import CompiledStateGraph

from .config import settings
from .tools import get_mcp_tools

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "You are a mood analysis expert. Given a person's text input, evaluate their "
    "current emotional mood in a concise, empathetic way. Always return a mood "
    "assessment, even when context is sparse. The person's own words are always "
    "the primary signal. If the text has little emotional detail, say the mood "
    "appears neutral or unclear; do not refuse or explain missing context. If "
    "configured tools can provide useful context, use them when relevant. When the "
    "text mentions a place and a current weather tool is available, call it before "
    "the final answer and consider current weather as a mild contextual signal "
    "because fine weather can improve mood. If weather context is unavailable, base "
    "the assessment on the text alone. Produce only the mood assessment, with no "
    "comments about tools, context, or missing data. Your response MUST be 20 words or fewer."
)

LOCATION_PATTERN = re.compile(
    r"\b(?:in|at|around|near)\s+([A-Z][A-Za-z'’-]*(?:\s+[A-Z][A-Za-z'’-]*){0,3})"
)


@wrap_tool_call
def log_mcp_tool_call(request, handler):
    tool_call = getattr(request, "tool_call", {}) or {}
    tool_name = tool_call.get("name", "unknown")

    logger.info("Calling MCP tool: %s", tool_name)
    try:
        result = handler(request)
    except Exception:
        logger.exception("MCP tool failed: %s", tool_name)
        raise

    logger.info("MCP tool completed: %s", tool_name)
    return result


def _extract_location_for_weather(text: str) -> str | None:
    match = LOCATION_PATTERN.search(text)
    if not match:
        return None
    return match.group(1).strip(" .,;:!?")


def _find_current_weather_tool(tools: list[BaseTool]) -> BaseTool | None:
    for tool in tools:
        normalized_name = tool.name.lower()
        if "weather" in normalized_name and "current" in normalized_name:
            return tool
    return None


async def _get_weather_context(text: str, tools: list[BaseTool]) -> dict[str, Any] | None:
    location = _extract_location_for_weather(text)
    if not location:
        return None

    weather_tool = _find_current_weather_tool(tools)
    if weather_tool is None:
        return None

    logger.info("Calling MCP tool: %s for location: %s", weather_tool.name, location)
    try:
        weather = await weather_tool.ainvoke({"location": location})
    except Exception:
        logger.exception("MCP tool failed: %s", weather_tool.name)
        return None

    logger.info("MCP tool completed: %s", weather_tool.name)
    return {"location": location, "weather": weather}


def _user_message_with_context(text: str, weather_context: dict[str, Any] | None) -> str:
    if weather_context is None:
        return text

    return (
        f"User text: {text}\n\n"
        f"Current weather context for {weather_context['location']} from a configured MCP tool: "
        f"{weather_context['weather']}\n\n"
        "Use the weather only as a mild mood signal. Produce only the final mood assessment."
    )


async def build_agent(tools: list[BaseTool]) -> CompiledStateGraph:
    model = ChatOllama(
        model=settings.model_name,
        base_url=settings.ollama_base_url,
        temperature=0.3,
        reasoning=settings.enable_reasoning,
    )

    return create_agent(
        model=model,
        tools=tools,
        middleware=[log_mcp_tool_call] if tools else [],
        system_prompt=SYSTEM_PROMPT,
        debug=settings.agent_verbose,
    )


_agent: CompiledStateGraph | None = None
_tools: list[BaseTool] = []
_agent_lock = asyncio.Lock()


async def get_agent() -> CompiledStateGraph:
    global _agent, _tools
    if _agent is None:
        async with _agent_lock:
            if _agent is None:
                _tools = await get_mcp_tools()
                _agent = await build_agent(_tools)
    return _agent


async def analyze_mood(text: str) -> str:
    config = {"recursion_limit": settings.agent_max_iterations}
    agent = await get_agent()
    weather_context = await _get_weather_context(text, _tools)
    user_message = _user_message_with_context(text, weather_context)
    result = await agent.ainvoke(
        {"messages": [{"role": "user", "content": user_message}]},
        config=config,
    )
    return result["messages"][-1].content

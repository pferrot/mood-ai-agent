import asyncio

from langchain.agents import create_agent
from langchain_ollama import ChatOllama
from langgraph.graph.state import CompiledStateGraph

from .config import settings
from .tools import get_mcp_tools

SYSTEM_PROMPT = (
    "You are a mood analysis expert. Given a person's text input, evaluate their "
    "current emotional mood in a concise, empathetic way. "
    "Your response MUST be 20 words or fewer."
)


async def build_agent() -> CompiledStateGraph:
    model = ChatOllama(
        model=settings.model_name,
        base_url=settings.ollama_base_url,
        temperature=0.3,
        reasoning=settings.enable_reasoning,
    )

    tools = await get_mcp_tools()

    return create_agent(
        model=model,
        tools=tools,
        system_prompt=SYSTEM_PROMPT,
        debug=settings.agent_verbose,
    )


_agent: CompiledStateGraph | None = None
_agent_lock = asyncio.Lock()


async def get_agent() -> CompiledStateGraph:
    global _agent
    if _agent is None:
        async with _agent_lock:
            if _agent is None:
                _agent = await build_agent()
    return _agent


async def analyze_mood(text: str) -> str:
    config = {"recursion_limit": settings.agent_max_iterations}
    result = await (await get_agent()).ainvoke(
        {"messages": [{"role": "user", "content": text}]},
        config=config,
    )
    return result["messages"][-1].content

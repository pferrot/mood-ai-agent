from langchain.tools import BaseTool


def get_tools() -> list[BaseTool]:
    """Return the list of tools available to the Mood AI Agent.

    Add new tools here as the agent is extended. Example:
        from langchain_community.tools import DuckDuckGoSearchRun
        return [DuckDuckGoSearchRun()]
    """
    return []

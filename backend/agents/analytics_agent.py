from typing import Callable
from langchain_core.messages import SystemMessage
from langchain_core.runnables import RunnableConfig
from core.llm import invoke_with_fallback
from prompts.analytics_prompt import analytics_prompt


def make_analytics_node(tools: list) -> Callable:
    """Build the analytics specialist with its authorized tools."""

    def node(state: dict, config: RunnableConfig) -> dict:
        """Answer the owner's question or request a business tool."""

        messages = [SystemMessage(content=analytics_prompt())]
        messages.extend(state["messages"])

        response = invoke_with_fallback(messages, tools, config)

        return {"messages": [response]}

    return node

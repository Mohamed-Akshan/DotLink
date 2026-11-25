from typing import Callable
from langchain_core.messages import SystemMessage
from langchain_core.runnables import RunnableConfig
from core.llm import invoke_with_fallback
from prompts.finance_prompt import finance_prompt


def make_finance_node(tools: list) -> Callable:
    """Build the finance specialist with its authorized tools."""

    def node(state: dict, config: RunnableConfig) -> dict:
        """Answer the owner's question or request a business tool."""

        messages = [SystemMessage(content=finance_prompt())]
        messages.extend(state["messages"])

        response = invoke_with_fallback(messages, tools, config)

        return {"messages": [response]}

    return node

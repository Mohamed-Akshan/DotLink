from langchain_core.messages import AIMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from core.llm import invoke_with_fallback, message_text
from prompts.supervisor_prompt import supervisor_prompt


def supervisor_node(state: dict, config: RunnableConfig) -> dict:
    """Route the request or ask a focused clarification directly."""

    messages = [SystemMessage(content=supervisor_prompt())]
    messages.extend(state["messages"])

    response = invoke_with_fallback(messages, config=config)
    text = message_text(response.content).strip()
    route = text.lower()

    if route.startswith("clarify:"):

        question = text.split(":", 1)[1].strip()

        if question:

            return {"route": "clarify", "messages": [AIMessage(content=question)]}

    if route not in ("operations", "finance", "analytics", "mixed", "outside"):

        route = "mixed"

    return {"route": route}

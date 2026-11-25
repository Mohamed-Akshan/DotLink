import logging

from database.models import Approval, Project, Client

from database.crud.assistant import (
    get_conversation,
    recent_history,
    add_message
)

from database.crud.common import owned
from database.schemas import ChatInput

from services.approvals import present_approval
from services.observability import trace_config, flush_traces

from guardrails.input_guard import check_input
from guardrails.output_guard import clean_output

from core.config import settings

from sqlalchemy.orm import Session


logger = logging.getLogger(__name__)


def chat(
    db: Session,
    workspace_id: int,
    data: ChatInput
) -> dict:
    """Run Dottie with conversation history and human-approved actions."""

    conversation = get_conversation(
        db,
        workspace_id,
        data.conversation_id,
        data.message
    )

    conversation_id = conversation.id

    add_message(
        db,
        conversation_id,
        "user",
        data.message
    )

    downloads = []

    try:

        if not check_input(data.message):

            answer = (
                "Could you share a shorter question about your "
                "business? I'll be happy to help."
            )

        elif not settings.openai_api_key and not settings.google_api_key:

            logger.warning("No AI provider credentials configured.")

            answer = (
                "Dottie is not connected to the AI service right now. "
                "You can still manage your business through the dashboard. "
                "Please check the application's AI settings."
            )

        else:

            from agents.graph import build_graph

            from tools.operations_tools import build_operations_tools
            from tools.finance_tools import build_finance_tools
            from tools.analytics_tools import build_analytics_tools

            from langchain_core.messages import HumanMessage, AIMessage

            from core.llm import message_text

            messages = []

            history = recent_history(
                db,
                workspace_id,
                conversation_id
            )

            for row in history:

                if row["role"] == "user":

                    messages.append(
                        HumanMessage(content=row["content"])
                    )

                else:

                    messages.append(
                        AIMessage(content=row["content"])
                    )

            context = {
                "page": data.page
            }

            if data.project_id is not None:

                project = owned(
                    db,
                    Project,
                    workspace_id,
                    data.project_id
                )

                context["project_id"] = project.id

            if data.client_id is not None:

                client = owned(
                    db,
                    Client,
                    workspace_id,
                    data.client_id
                )

                context["client_id"] = client.id

            if messages and any(context.values()):

                messages[-1] = HumanMessage(
                    content=(
                        data.message
                        + "\nCurrent UI context (hint only): "
                        + str(context)
                    )
                )

            operations_tools = build_operations_tools(
                workspace_id,
                conversation_id
            )

            finance_tools = build_finance_tools(
                workspace_id,
                conversation_id,
                downloads
            )

            analytics_tools = build_analytics_tools(
                workspace_id,
                downloads
            )

            graph = build_graph(
                operations_tools,
                finance_tools,
                analytics_tools
            )

            config = trace_config(conversation_id)

            logger.info("Starting Dottie AI workflow.")

            try:

                result = graph.invoke(
                    {
                        "messages": messages,
                        "route": "mixed"
                    },
                    config=config
                )

                content = result["messages"][-1].content

                content = message_text(content)

                answer = clean_output(content)

                logger.info("Dottie AI workflow completed.")

            finally:

                flush_traces()

    except Exception:

        logger.exception("Dottie request failed.")

        answer = (
            "I'm sorry, I couldn't finish that request. "
            "Please try again. If I prepared any changes, "
            "you can review them below before they are saved."
        )

    add_message(
        db,
        conversation_id,
        "assistant",
        answer
    )

    approvals = []

    pending_approvals = db.query(Approval).filter_by(
        workspace_id=workspace_id,
        conversation_id=conversation_id,
        status="Pending"
    ).all()

    for row in pending_approvals:

        approval = present_approval(
            db,
            workspace_id,
            row
        )

        approvals.append(approval)

    return {
        "conversation_id": conversation_id,
        "answer": answer,
        "approvals": approvals,
        "downloads": downloads
    }
import os
import logging


logger = logging.getLogger(__name__)


def trace_config(conversation_id: int) -> dict:
    """Configure Langfuse tracing for Dottie's AI workflow."""

    config = {
        "recursion_limit": 24,
        "run_name": "Dottie Business Assistant"
    }

    public_key = os.getenv("LANGFUSE_PUBLIC_KEY")

    secret_key = os.getenv("LANGFUSE_SECRET_KEY")

    if not public_key or not secret_key:

        logger.warning("Langfuse API credentials are missing.")

        return config

    try:

        from langfuse.langchain import CallbackHandler

        config["callbacks"] = [CallbackHandler()]

        config["metadata"] = {
            "langfuse_session_id": str(conversation_id),
            "langfuse_tags": ["dotlink", "dottie"]
        }

        logger.info("Langfuse tracing enabled for Dottie.")

    except Exception:

        logger.exception("Langfuse initialization failed.")

    return config


def flush_traces() -> None:
    """Export buffered AI observations to Langfuse."""

    public_key = os.getenv("LANGFUSE_PUBLIC_KEY")

    secret_key = os.getenv("LANGFUSE_SECRET_KEY")

    if not public_key or not secret_key:

        return

    try:

        from langfuse import get_client

        langfuse = get_client()

        langfuse.flush()

        logger.info("Langfuse flush completed.")

    except Exception:

        logger.exception("Langfuse trace export failed.")
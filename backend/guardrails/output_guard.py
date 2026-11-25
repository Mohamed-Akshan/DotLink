import json
import re


PRIVATE_FIELDS = (
    "id", "workspace_id", "record_id", "conversation_id", "document_id",
    "client_id", "project_id", "service_id", "invoice_id", "dedupe_key",
    "before", "payload", "password_hash", "metadata", "created_at",
    "access_token", "secret_key", "tool_calls",
)


def readable_value(value, depth: int = 0) -> str:
    """Turn accidental structured replies into ordinary readable text."""

    if depth > 3 or value is None:

        return ""

    lines = []

    if isinstance(value, dict):

        for key, item in value.items():

            if key in PRIVATE_FIELDS or key.endswith("_id"):

                continue

            text = readable_value(item, depth + 1)

            if text:

                label = key.replace("_", " ").capitalize()
                lines.append(f"**{label}:** {text}")

        return "\n\n".join(lines)

    if isinstance(value, list):

        for item in value[:30]:

            text = readable_value(item, depth + 1)

            if text:

                lines.append(text)

        return "\n\n".join(lines)

    if isinstance(value, bool):

        return "Yes" if value else "No"

    return str(value)


def format_json(text: str) -> str:
    """Format a JSON object or list without exposing its raw syntax."""

    try:

        value = json.loads(text)

    except (ValueError, TypeError):

        return "I couldn't present those details clearly. Could you ask me to summarize them?"

    result = readable_value(value)

    return result or "Please review the information in your workspace."


def clean_output(answer: str) -> str:
    """Keep assistant replies readable, without raw JSON or code fences."""

    if not isinstance(answer, str) or not answer.strip():

        return "I couldn't prepare a clear response. Could you try asking again?"

    answer = answer[:16000].strip()

    if answer.startswith(("{", "[")) and answer.endswith(("}", "]")):

        return format_json(answer)

    def replace_block(match: re.Match) -> str:
        """Remove raw machine-oriented blocks from a business reply."""

        text = match.group(1).strip()

        if text.startswith(("{", "[")):

            return format_json(text)

        return text

    return re.sub(r"```(?:json|python)?\s*([\s\S]*?)```", replace_block, answer, flags=re.IGNORECASE)

def check_input(message) -> bool:
    """Reject empty or oversized messages before invoking an AI provider."""

    return bool(message.strip()) and len(message) <= 5000

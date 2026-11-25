def allowed_write(action, actions) -> bool:
    """Allow only predefined AI proposal actions."""

    return action in actions

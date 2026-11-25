from database.models import Conversation, Message
from database.crud.common import owned, serialize


def get_conversation(db, workspace_id, conversation_id, message) -> Conversation:
    """Open an existing conversation or create a new one."""

    if conversation_id is not None:

        return owned(db, Conversation, workspace_id, conversation_id)

    row = Conversation(workspace_id=workspace_id, title=message[:80])
    db.add(row)
    db.commit()

    return row


def history(db, workspace_id, conversation_id) -> list:
    """Return authorized conversation messages in order."""

    owned(db, Conversation, workspace_id, conversation_id)

    results = []

    for row in db.query(Message).filter_by(conversation_id=conversation_id).order_by(Message.id).all():

        results.append(serialize(row))

    return results


def add_message(db, conversation_id, role, content) -> None:
    """Save a message in an already authorized conversation."""

    db.add(Message(conversation_id=conversation_id, role=role, content=content))
    db.commit()

    return None


def recent_history(db, workspace_id: int, conversation_id: int, limit: int = 16) -> list:
    """Load only recent messages for AI context, in chronological order."""

    owned(db, Conversation, workspace_id, conversation_id)
    rows = db.query(Message).filter_by(conversation_id=conversation_id).order_by(Message.id.desc()).limit(limit).all()
    results = []

    for row in reversed(rows):

        results.append(serialize(row))

    return results

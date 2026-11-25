from fastapi import APIRouter
from core.security import DB, Tenant
from database.schemas import ChatInput
from database.models import Conversation
from database.crud.common import list_records
from database.crud.assistant import history
from services.chat import chat

router = APIRouter(prefix="/api/chat", tags=["Dottie"])


@router.post("")
def ask(data: ChatInput, db: DB, workspace: Tenant) -> dict:
    """Send a business question to Dottie."""

    return chat(db, workspace.id, data)


@router.get("/conversations")
def conversations(db: DB, workspace: Tenant) -> list:
    """Retrieve the owner's conversation history."""

    return list_records(db, Conversation, workspace.id)


@router.get("/conversations/{record_id}")
def messages(record_id: int, db: DB, workspace: Tenant) -> list:
    """Retrieve messages from an authorized conversation."""

    return history(db, workspace.id, record_id)

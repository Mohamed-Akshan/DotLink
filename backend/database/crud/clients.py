from database.models import Client
from database.crud.common import save, list_records, owned, serialize


def get_clients(db, workspace_id) -> list:
    """List clients in the current workspace."""

    return list_records(db, Client, workspace_id)


def save_client(db, workspace_id, data, record_id=None) -> dict:
    """Create or update a client."""

    return save(db, Client, workspace_id, data.model_dump(), record_id)


def get_client(db, workspace_id, record_id) -> dict:
    """Get one authorized client."""

    return serialize(owned(db, Client, workspace_id, record_id))

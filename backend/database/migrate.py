from sqlalchemy import inspect, text
from sqlalchemy.engine import Connection


def upgrade(connection: Connection) -> None:
    """Upgrade existing PostgreSQL tables without deleting data."""

    if connection.dialect.name != "postgresql":

        return

    columns = {}

    for column in inspect(connection).get_columns("tasks"):

        columns[column["name"]] = column

    if not columns["project_id"]["nullable"]:

        connection.execute(
            text(
                "ALTER TABLE tasks "
                "ALTER COLUMN project_id DROP NOT NULL"
            )
        )

    if "priority" not in columns:

        connection.execute(
            text(
                "ALTER TABLE tasks "
                "ADD COLUMN IF NOT EXISTS priority "
                "VARCHAR(20) NOT NULL DEFAULT 'Medium'"
            )
        )
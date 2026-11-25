from sqlalchemy import inspect, text


def upgrade(engine) -> None:
    """Upgrade the two existing task columns on PostgreSQL without deleting data."""
    if engine.dialect.name != "postgresql":
        return
    columns = {}
    for column in inspect(engine).get_columns("tasks"):
        columns[column["name"]] = column
    with engine.begin() as connection:
        if not columns["project_id"]["nullable"]:
            connection.execute(text("ALTER TABLE tasks ALTER COLUMN project_id DROP NOT NULL"))
        if "priority" not in columns:
            connection.execute(text("ALTER TABLE tasks ADD COLUMN IF NOT EXISTS priority VARCHAR(20) NOT NULL DEFAULT 'Medium'"))

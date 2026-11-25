from datetime import datetime, timezone
from sqlalchemy import Boolean, Column, Date, DateTime, ForeignKey, Integer, JSON, Numeric, String, Text
from database.connection import Base


def now() -> datetime:
    """Return the current UTC time."""

    return datetime.now(timezone.utc)


class User(Base):
    """Store users records."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    full_name = Column(String(150), nullable=False)
    email = Column(String(254), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), default=now, nullable=False)


class Workspace(Base):
    """Store workspaces records."""

    __tablename__ = "workspaces"

    id = Column(Integer, primary_key=True)
    owner_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    business_name = Column(String(150), nullable=False)
    business_email = Column(String(254), default="", nullable=False)
    phone = Column(String(40), default="", nullable=False)
    address = Column(Text, default="", nullable=False)
    currency = Column(String(3), default="LKR", nullable=False)
    timezone = Column(String(60), default="Asia/Colombo", nullable=False)
    created_at = Column(DateTime(timezone=True), default=now, nullable=False)


class Client(Base):
    """Store clients records."""

    __tablename__ = "clients"

    id = Column(Integer, primary_key=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id"), index=True, nullable=False)
    name = Column(String(150), nullable=False)
    company = Column(String(150), default="", nullable=False)
    email = Column(String(254), default="", nullable=False)
    phone = Column(String(40), default="", nullable=False)
    address = Column(Text, default="", nullable=False)
    notes = Column(Text, default="", nullable=False)
    archived = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), default=now, nullable=False)


class Project(Base):
    """Store projects records."""

    __tablename__ = "projects"

    id = Column(Integer, primary_key=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id"), index=True, nullable=False)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    title = Column(String(150), nullable=False)
    description = Column(Text, default="", nullable=False)
    start_date = Column(Date, nullable=False)
    deadline = Column(Date, nullable=False)
    priority = Column(String(20), default="Medium", nullable=False)
    status = Column(String(30), default="Pending", nullable=False)
    archived = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), default=now, nullable=False)


class Task(Base):
    """Store tasks records."""

    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id"), index=True, nullable=False)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
    priority = Column(String(20), default="Medium", nullable=False)
    title = Column(String(150), nullable=False)
    description = Column(Text, default="", nullable=False)
    due_date = Column(Date, nullable=False)
    status = Column(String(30), default="Pending", nullable=False)
    created_at = Column(DateTime(timezone=True), default=now, nullable=False)


class Service(Base):
    """Store services records."""

    __tablename__ = "services"

    id = Column(Integer, primary_key=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id"), index=True, nullable=False)
    name = Column(String(150), nullable=False)
    category = Column(String(100), default="Design", nullable=False)
    description = Column(Text, default="", nullable=False)
    unit_price = Column(Numeric(12,2), nullable=False)
    pricing_unit = Column(String(40), default="design", nullable=False)
    archived = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), default=now, nullable=False)


class Document(Base):
    """Store documents records."""

    __tablename__ = "documents"

    id = Column(Integer, primary_key=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id"), index=True, nullable=False)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
    source_id = Column(Integer, ForeignKey("documents.id"), nullable=True, unique=True)
    document_type = Column(String(20), nullable=False)
    issue_date = Column(Date, nullable=False)
    due_date = Column(Date, nullable=False)
    discount = Column(Numeric(5,2), default=0, nullable=False)
    total = Column(Numeric(12,2), nullable=False)
    status = Column(String(30), default="Draft", nullable=False)
    notes = Column(Text, default="", nullable=False)
    created_at = Column(DateTime(timezone=True), default=now, nullable=False)


class DocumentItem(Base):
    """Store document items records."""

    __tablename__ = "document_items"

    id = Column(Integer, primary_key=True)
    document_id = Column(Integer, ForeignKey("documents.id"), index=True, nullable=False)
    service_id = Column(Integer, ForeignKey("services.id"), nullable=True)
    description = Column(String(250), nullable=False)
    quantity = Column(Numeric(10,2), nullable=False)
    unit_price = Column(Numeric(12,2), nullable=False)
    created_at = Column(DateTime(timezone=True), default=now, nullable=False)


class Payment(Base):
    """Store payments records."""

    __tablename__ = "payments"

    id = Column(Integer, primary_key=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id"), index=True, nullable=False)
    invoice_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    amount = Column(Numeric(12,2), nullable=False)
    payment_date = Column(Date, nullable=False)
    method = Column(String(30), nullable=False)
    reference = Column(String(100), default="", nullable=False)
    notes = Column(Text, default="", nullable=False)
    reversed = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), default=now, nullable=False)


class Conversation(Base):
    """Store conversations records."""

    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id"), index=True, nullable=False)
    title = Column(String(150), nullable=False)
    created_at = Column(DateTime(timezone=True), default=now, nullable=False)


class Message(Base):
    """Store messages records."""

    __tablename__ = "messages"

    id = Column(Integer, primary_key=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), index=True, nullable=False)
    role = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=now, nullable=False)


class Approval(Base):
    """Store approvals records."""

    __tablename__ = "approvals"

    id = Column(Integer, primary_key=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id"), index=True, nullable=False)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=True)
    action = Column(String(50), nullable=False)
    payload = Column(JSON, nullable=False)
    reason = Column(Text, nullable=False)
    status = Column(String(20), default="Pending", nullable=False)
    result = Column(JSON, nullable=True)
    dedupe_key = Column(String(64), unique=True, nullable=True)
    preview = Column(JSON, nullable=True)
    before = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=now, nullable=False)


class ActivityLog(Base):
    """Store activity logs records."""

    __tablename__ = "activity_logs"

    id = Column(Integer, primary_key=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id"), index=True, nullable=False)
    description = Column(Text, nullable=False)
    # Legacy columns retained so existing MVP databases remain compatible.
    # No scheduler or notification endpoint uses them.
    is_notification = Column(Boolean, default=False, nullable=False)
    is_read = Column(Boolean, default=False, nullable=False)
    event_key = Column(String(200), nullable=True, unique=True)
    created_at = Column(DateTime(timezone=True), default=now, nullable=False)


class Expense(Base):
    """Record a paid business expense."""
    __tablename__ = "expenses"
    id = Column(Integer, primary_key=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id"), index=True, nullable=False)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
    title = Column(String(150), nullable=False)
    category = Column(String(100), nullable=False)
    amount = Column(Numeric(12,2), nullable=False)
    expense_date = Column(Date, nullable=False)
    method = Column(String(30), nullable=False)
    notes = Column(Text, default="", nullable=False)
    created_at = Column(DateTime(timezone=True), default=now, nullable=False)

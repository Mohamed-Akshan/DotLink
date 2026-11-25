from typing import Self
from datetime import date
from decimal import Decimal
from typing import Literal
import re
from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator, field_validator


class Schema(BaseModel):
    """Reject unexpected fields, including untrusted workspace IDs."""

    model_config = ConfigDict(extra="forbid")


class Signup(Schema):
    @field_validator("full_name", "business_name", mode="before")
    @classmethod
    def trim_names(cls, value: str) -> str:
        """Reject whitespace-only names."""
        return value.strip() if isinstance(value, str) else value

    full_name: str = Field(min_length=1, max_length=150)
    business_name: str = Field(min_length=1, max_length=150)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    confirm_password: str
    accept_terms: Literal[True]

    @model_validator(mode="after")
    def check_password(self) -> Self:
        """Check password strength and confirmation."""

        if self.password != self.confirm_password:

            raise ValueError("Passwords must match")

        for pattern in [r"[A-Z]", r"[a-z]", r"[0-9]", r"[^A-Za-z0-9\s]"]:

            if not re.search(pattern, self.password):

                raise ValueError("Use uppercase, lowercase, a number and a symbol")

        return self


class Login(Schema):
    email: EmailStr
    password: str = Field(max_length=128)


class ClientInput(Schema):
    name: str = Field(min_length=1, max_length=150)
    company: str = ""
    email: EmailStr
    phone: str = Field(min_length=7, max_length=30)
    address: str = ""
    notes: str = ""

    @field_validator("name", mode="before")
    @classmethod
    def clean_name(cls, value: str) -> str:
        """Reject empty or whitespace-only client names."""

        return value.strip() if isinstance(value, str) else value

    @model_validator(mode="after")
    def check_phone(self) -> "ClientInput":
        """Require a plausible contact number, without inventing one."""

        digits = re.sub(r"[^0-9]", "", self.phone)

        if not re.fullmatch(r"[+0-9 ()-]+", self.phone) or not 7 <= len(digits) <= 15:

            raise ValueError("Enter a valid client phone number")

        return self


def normalize_text(value: str) -> str:
    """Normalize spaces, separators and letter case."""

    if not isinstance(value, str):

        raise ValueError("Please provide a valid value")

    value = value.strip().lower()
    value = value.replace("_", " ").replace("-", " ")

    return " ".join(value.split())


def normalize_choice(value: str, choices: tuple) -> str:
    """Match an ordinary phrase to an allowed stored value."""

    text = normalize_text(value)

    for choice in choices:

        if text == normalize_text(choice):

            return choice

    raise ValueError("Choose " + ", ".join(choices))


class ProjectInput(Schema):
    client_id: int = Field(gt=0)
    title: str = Field(min_length=1, max_length=150)
    description: str = Field(min_length=1, max_length=5000)
    start_date: date
    deadline: date
    priority: Literal["Low", "Medium", "High"] = "Medium"
    status: Literal["Pending", "In progress", "Completed", "On hold"] = "Pending"

    @field_validator("priority", mode="before")
    @classmethod
    def clean_priority(cls, value: str) -> str:
        """Accept priorities regardless of capitalization."""

        return normalize_choice(value, ("Low", "Medium", "High"))

    @field_validator("status", mode="before")
    @classmethod
    def clean_status(cls, value: str) -> str:
        """Normalize project status wording."""

        return normalize_choice(value, ("Pending", "In progress", "Completed", "On hold"))

    @field_validator("title", "description", mode="before")
    @classmethod
    def clean_project_text(cls, value: str) -> str:
        """Reject blank project titles and scopes."""

        return value.strip() if isinstance(value, str) else value

    @model_validator(mode="after")
    def check_dates(self) -> Self:
        """Ensure the deadline follows the start date."""

        if self.deadline < self.start_date:

            raise ValueError("Deadline must follow start date")

        return self


class TaskInput(Schema):
    project_id: int | None = Field(default=None, gt=0)
    priority: Literal["Low", "Medium", "High"] = "Medium"
    title: str = Field(min_length=1, max_length=150)
    description: str = ""
    due_date: date
    status: Literal["Pending", "In progress", "Completed"] = "Pending"

    @field_validator("status", mode="before")
    @classmethod
    def clean_status(cls, value: str) -> str:
        """Normalize task status wording."""

        return normalize_choice(value, ("Pending", "In progress", "Completed"))

    @field_validator("title", mode="before")
    @classmethod
    def clean_title(cls, value: str) -> str:
        """Require a meaningful task title."""

        return value.strip() if isinstance(value, str) else value


def normalize_pricing_unit(unit: str) -> str:
    """Convert common pricing expressions into supported rate-card units."""

    if not isinstance(unit, str):

        raise ValueError("Choose a pricing unit: design, hour, package or item")

    unit = " ".join(unit.strip().lower().split())

    for prefix in ("per ", "for each ", "each ", "a ", "an "):

        if unit.startswith(prefix):

            unit = unit[len(prefix):].strip()

            break

    aliases = {
        "designs": "design",
        "hours": "hour",
        "hourly": "hour",
        "packages": "package",
        "items": "item",
    }

    unit = aliases.get(unit, unit)

    if unit not in ("design", "hour", "package", "item"):

        raise ValueError("Choose a pricing unit: design, hour, package or item")

    return unit


class ServiceInput(Schema):
    name: str = Field(min_length=1, max_length=150)
    category: str = "Design"
    description: str = ""
    unit_price: Decimal = Field(ge=0, max_digits=12, decimal_places=2)
    pricing_unit: Literal["design", "hour", "package", "item"] = "design"

    @field_validator("pricing_unit", mode="before")
    @classmethod
    def clean_pricing_unit(cls, value: str) -> str:
        """Normalize pricing units before checking the allowed values."""

        return normalize_pricing_unit(value)

    @field_validator("name", mode="before")
    @classmethod
    def clean_service_name(cls, value: str) -> str:
        """Require a nonblank service name."""

        return value.strip() if isinstance(value, str) else value


class ItemInput(Schema):
    service_id: int = Field(gt=0)
    quantity: Decimal = Field(gt=0, max_digits=10, decimal_places=2)


class DocumentInput(Schema):
    client_id: int = Field(gt=0)
    project_id: int | None = None
    document_type: Literal["quotation", "invoice"]
    issue_date: date
    due_date: date
    discount: Decimal = Field(default=Decimal("0"), ge=0, le=100, decimal_places=2)
    notes: str = ""
    items: list[ItemInput] = Field(min_length=1, max_length=50)


class ConversionInput(Schema):
    """Require explicit invoice dates when converting a quotation."""

    issue_date: date
    due_date: date

    @model_validator(mode="after")
    def check_dates(self) -> Self:
        """Ensure the due date is not earlier than the issue date."""

        if self.due_date < self.issue_date:

            raise ValueError("Payment due date must be on or after the issue date")

        return self


class QuotationStatusInput(Schema):
    status: Literal["Sent", "Accepted", "Rejected"]

    @field_validator("status", mode="before")
    @classmethod
    def clean_status(cls, value: str) -> str:
        """Accept the ordinary wording of quotation decisions."""

        return normalize_choice(value, ("Sent", "Accepted", "Rejected"))


class InvoiceIssueInput(Schema):
    """Invoice issuance requires only the existing invoice reference."""

    pass


def normalize_payment_method(value: str) -> str:
    """Convert clear payment phrases to supported methods."""

    text = normalize_text(value)

    methods = {
        "cash": "Cash",
        "paid in cash": "Cash",
        "bank transfer": "Bank transfer",
        "bank wire": "Bank transfer",
        "wire transfer": "Bank transfer",
        "online bank transfer": "Bank transfer",
        "paid by bank transfer": "Bank transfer",
        "paid via bank transfer": "Bank transfer",
        "card": "Card",
        "credit card": "Card",
        "debit card": "Card",
        "other": "Other",
    }

    if text not in methods:

        raise ValueError("Choose Cash, Bank transfer, Card or Other")

    return methods[text]


class PaymentInput(Schema):
    invoice_id: int = Field(gt=0)
    amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    payment_date: date
    method: Literal["Cash", "Bank transfer", "Card", "Other"]
    reference: str = Field(default="", max_length=100)
    notes: str = ""

    @field_validator("method", mode="before")
    @classmethod
    def clean_method(cls, value: str) -> str:
        """Normalize the payment method before Literal validation."""

        return normalize_payment_method(value)

    @field_validator("reference", mode="before")
    @classmethod
    def clean_reference(cls, value: str) -> str:
        """Trim spaces from the optional transaction reference."""

        if isinstance(value, str):

            return value.strip()

        return value


class StatusInput(Schema):
    status: str

    @field_validator("status", mode="before")
    @classmethod
    def clean_status(cls, value: str) -> str:
        """Normalize document status for manual API requests."""

        return normalize_choice(value, ("Draft", "Sent", "Accepted", "Rejected", "Unpaid", "Partially paid", "Paid", "Void"))


class WorkspaceInput(Schema):
    @field_validator("business_name", mode="before")
    @classmethod
    def clean_name(cls, value: str) -> str:
        """Require a meaningful workspace name."""
        return value.strip() if isinstance(value, str) else value

    business_name: str = Field(min_length=1, max_length=150)
    business_email: EmailStr | Literal[""] = ""
    phone: str = ""
    address: str = ""


class ChatInput(Schema):
    message: str = Field(min_length=1, max_length=5000)
    conversation_id: int | None = None
    page: Literal["Overview", "Clients", "Projects", "Tasks", "Services", "Finance", "Approvals", "Settings"] | None = None
    project_id: int | None = Field(default=None, gt=0)
    client_id: int | None = Field(default=None, gt=0)


class ReviewInput(Schema):
    decision: Literal["approve", "reject"]
    payload: dict | None = None


class ProfileInput(Schema):
    @field_validator("full_name", mode="before")
    @classmethod
    def clean_name(cls, value: str) -> str:
        """Require a meaningful owner name."""
        return value.strip() if isinstance(value, str) else value

    full_name: str = Field(min_length=1, max_length=150)


class PasswordChange(Schema):
    current_password: str = Field(max_length=128)
    password: str = Field(min_length=8, max_length=128)
    confirm_password: str

    @model_validator(mode="after")
    def check_password(self) -> Self:
        """Validate the new password using the signup policy."""

        if self.password != self.confirm_password:

            raise ValueError("Passwords must match")

        for pattern in [r"[A-Z]", r"[a-z]", r"[0-9]", r"[^A-Za-z0-9\s]"]:

            if not re.search(pattern, self.password):

                raise ValueError("Use uppercase, lowercase, a number and a symbol")

        return self


class ProposalEdit(Schema):
    payload: dict


class ExpenseInput(Schema):
    title: str = Field(min_length=1, max_length=150)
    category: str = Field(min_length=1, max_length=100)
    project_id: int | None = Field(default=None, gt=0)
    amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    expense_date: date
    method: Literal["Cash", "Bank transfer", "Card", "Other"]
    notes: str = ""

    @field_validator("title", "category", mode="before")
    @classmethod
    def clean_text(cls, value: str) -> str:
        """Reject blank expense titles and categories."""
        return value.strip() if isinstance(value, str) else value

    @field_validator("method", mode="before")
    @classmethod
    def clean_method(cls, value: str) -> str:
        """Use the same payment methods as invoices."""
        return normalize_payment_method(value)


class QuoteProjectInput(Schema):
    title: str = Field(min_length=1, max_length=150)
    start_date: date
    deadline: date
    priority: Literal["Low", "Medium", "High"] = "Medium"


class QuoteLinkInput(Schema):
    project_id: int = Field(gt=0)


class ArchiveInput(Schema):
    archived: bool

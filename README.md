<div align="center">

# DotLink

### Connect your business. Create without limits.

An AI-powered business management workspace for freelancers, creative professionals and small businesses.

![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-20232A?style=for-the-badge&logo=react&logoColor=61DAFB)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)
![LangGraph](https://img.shields.io/badge/LangGraph-1C3C3C?style=for-the-badge)
![Langfuse](https://img.shields.io/badge/Langfuse-6366F1?style=for-the-badge)

</div>

---

## The Problem

Freelancers and small creative businesses often manage their operations across disconnected spreadsheets, messaging applications, documents and financial tracking tools.

Creating quotations, tracking deliverables, preparing invoices, recording payments and understanding profitability requires repetitive manual work. As the business grows, managing these fragmented operations becomes increasingly difficult.

Creative professionals spend valuable time managing their businesses instead of focusing on their creative work.

## The Solution

DotLink brings clients, projects, tasks, services, quotations, invoices, payments and expenses into one connected business workspace.

At the heart of DotLink is **Dottie**, an intelligent AI business companion powered by a LangGraph-based multi-agent architecture.

Unlike conventional chatbots that simply provide information, Dottie can retrieve business records, prepare operational changes, assist with financial workflows and generate actionable insights through natural-language conversations.

Every AI-initiated business modification requires explicit human approval before execution, ensuring that users remain in control of their business data.

## Meet Dottie

Dottie bridges the gap between conversational AI and real business operations.

Users can manage their businesses using everyday language rather than navigating multiple forms and menus.

**Example conversations:**

> Prepare a quotation for Noah Technologies using my existing service rates.

> Create a project from the accepted quotation.

> Record an advance payment of Rs. 36,000.

> Show me all overdue tasks across my projects.

> Record an expense of Rs. 7,000 for outsourced design work.

> Analyze my business income, expenses and outstanding payments.

> Generate a downloadable financial performance report.

Dottie retrieves relevant business information, identifies missing requirements, selects appropriate tools and prepares approval requests when modifications are necessary.

## Core Features

### Client Management

- Create and maintain client profiles.
- Access associated projects and financial records.
- Track client payments and outstanding balances.
- View client-specific business activity.

### Project Management

- Create projects manually or from accepted quotations.
- Track project status, deadlines and progress.
- Manage associated tasks and deliverables.
- Monitor project income and expenses.
- Evaluate project-level financial performance.

### Task Management

- Dedicated task management workspace.
- List and Kanban board views.
- Project-specific and standalone tasks.
- Priority, deadline and status management.
- Upcoming and overdue task tracking.

### Services and Rate Cards

- Maintain reusable business services.
- Define service prices and pricing units.
- Select existing services when preparing financial documents.
- Preserve historical document pricing when service rates change.

### Financial Management

- Create and manage quotations.
- Record client acceptance or rejection.
- Convert accepted quotations into invoices.
- Generate downloadable PDF documents.
- Record full and partial payments.
- Track outstanding invoice balances.
- Record project-specific and general business expenses.
- Analyze income, expenses and cash-basis financial performance.

### Business Analytics

- Financial performance dashboard.
- Revenue and expense visualization.
- Cash surplus and margin analysis.
- Project financial performance.
- Outstanding payment summaries.
- Downloadable PDF business reports.

### Human-in-the-Loop Approvals

- Review AI-generated business proposals.
- Edit supported proposal details before execution.
- Approve or decline proposed modifications.
- Validate business rules before committing changes.
- Prevent unauthorized or duplicate execution.

## Multi-Agent AI Architecture

DotLink uses a supervisor-based multi-agent architecture implemented with LangGraph.

| Agent | Responsibility |
|---|---|
| Supervisor Agent | Understands user intent and routes requests to specialized agents. |
| Operations Agent | Manages clients, projects, tasks and operational workflows. |
| Finance Agent | Handles services, quotations, invoices, payments and expenses. |
| Analytics Agent | Retrieves business metrics, analyzes financial performance and generates reports. |

The architecture separates operational responsibilities while maintaining a unified conversational experience.

Specialized agents use workspace-scoped business tools to interact with application services and validated database operations.

```mermaid
flowchart TD
    U[User] --> UI[React Application]
    UI --> API[FastAPI Backend]
    API --> G[Input Guardrails]
    G --> S[Supervisor Agent]

    S --> O[Operations Agent]
    S --> F[Finance Agent]
    S --> A[Analytics Agent]

    O --> T[Business Tools]
    F --> T
    A --> T

    T --> V[Validation and Authorization]

    V --> R[Read Operations]
    V --> W[Write Proposals]

    R --> DB[(PostgreSQL)]

    W --> H[Human Approval]
    H --> E[Approved Execution]
    E --> DB

    S -. Observability .-> L[Langfuse]
    O -. Observability .-> L
    F -. Observability .-> L
    A -. Observability .-> L
```

## Intelligent Tool Execution

Dottie uses natural-language intent understanding rather than predefined question-and-answer matching.

The AI workflow is designed to:

- Identify the user's business objective.
- Retrieve relevant records from the workspace.
- Maintain conversational context.
- Ask follow-up questions when required information is missing.
- Select appropriate business tools.
- Validate inputs and business constraints.
- Prepare approval requests for data modifications.
- Communicate results through clear, natural-language responses.

Business calculations and database modifications are handled by deterministic backend services rather than relying on the language model to perform financial calculations or generate arbitrary database queries.

## Human-in-the-Loop Workflow

```mermaid
sequenceDiagram
    participant User
    participant Dottie
    participant Tools
    participant Approval
    participant Database

    User->>Dottie: Record a business expense
    Dottie->>Tools: Retrieve relevant information
    Tools-->>Dottie: Validated business context
    Dottie->>Approval: Prepare expense proposal
    Approval-->>User: Review proposed expense
    User->>Approval: Approve request
    Approval->>Database: Validate and execute
    Database-->>Approval: Execution result
    Approval-->>User: Expense recorded successfully
```

Read-only requests can retrieve authorized information directly, while AI-initiated modifications require explicit user confirmation.

## AI Guardrails and Reliability

DotLink combines model instructions with backend validation and authorization to establish controlled AI behaviour.

- Business-domain conversational boundaries.
- Workspace-level data isolation.
- Context-aware information retrieval.
- Structured tool input validation.
- Human approval for AI-initiated modifications.
- Duplicate payment prevention.
- Overpayment prevention.
- Financial document lifecycle validation.
- Stale approval protection.
- Primary and fallback language model configuration.

The language model interprets user intent, while backend services enforce application permissions and business rules.

## AI Observability

Langfuse is integrated with the LangGraph workflow to support AI observability and debugging.

The instrumentation is intended to provide visibility into:

- Agent execution and routing.
- Language model inputs and outputs.
- Business tool calls.
- Execution latency.
- Token consumption.
- Estimated model usage costs.
- Conversation sessions.
- AI workflow failures.

This enables developers to inspect agent behaviour and identify opportunities to improve reliability, performance and response quality.

## Technology Stack

| Category | Technologies |
|---|---|
| Frontend | React.js, JavaScript, HTML, CSS |
| Backend | Python, FastAPI, REST APIs |
| Agent Orchestration | LangGraph |
| LLM Integration | LangChain, OpenAI, Google Gemini |
| Database | PostgreSQL |
| ORM | SQLAlchemy |
| Data Validation | Pydantic |
| Authentication | JWT, Argon2 password hashing |
| AI Observability | Langfuse |
| Data Visualization | Recharts |
| PDF Generation | ReportLab |
| UI Icons | Lucide React |
| Dependency Management | UV, Yarn |
| Containerization | Docker, Docker Compose |

## User Experience

DotLink follows a modern, minimalistic SaaS design system focused on usability, accessibility and consistent interactions.

- Responsive desktop, tablet and mobile layouts.
- Animated public landing page.
- Indigo and light-blue visual identity.
- Professional authentication screens.
- Context-aware action buttons.
- Searchable and filterable business records.
- Interactive financial visualizations.
- Dedicated AI conversational workspace.
- Contextual assistant panel.
- Clear validation and approval feedback.

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js
- PostgreSQL
- UV package manager
- Yarn
- OpenAI or Google Gemini API credentials
- Langfuse credentials for optional AI observability

### Clone the Repository

```bash
git clone https://github.com/Mohamed-Akshan/dotlink.git
cd dotlink
```

### Environment Configuration

Create a `.env` file using the provided `.env.example`.

Configure the PostgreSQL connection, authentication secret, AI providers and optional Langfuse credentials.

```env
DATABASE_URL=postgresql+psycopg://postgres:password@localhost:5432/dotlink

SECRET_KEY=your-secret-key

FRONTEND_URL=http://localhost:5173

TIMEZONE=Asia/Colombo

OPENAI_API_KEY=your-openai-api-key
OPENAI_MODEL=your-supported-openai-model

GOOGLE_API_KEY=your-google-api-key
GEMINI_MODEL=your-supported-gemini-model

LANGFUSE_PUBLIC_KEY=your-public-key
LANGFUSE_SECRET_KEY=your-secret-key
LANGFUSE_HOST=https://cloud.langfuse.com
LANGFUSE_BASE_URL=https://cloud.langfuse.com
```

Never commit API credentials, database passwords or authentication secrets to version control.

### Backend Setup

```powershell
cd backend

uv venv --python 3.11

.\.venv\Scripts\Activate.ps1

uv pip install -r requirements.txt

uv run --no-project uvicorn main:app --port 8000
```

### Frontend Setup

Open a separate terminal from the project root.

```bash
cd frontend

yarn install

yarn dev
```

### Access the Application

| Service | Address |
|---|---|
| DotLink Application | http://localhost:5173 |
| FastAPI Documentation | http://localhost:8000/docs |

## Docker

DotLink includes Docker configuration for running the application and its supporting services in a consistent local environment.

Configure the required environment variables before running:

```bash
docker compose up --build
```

## Example Business Workflow

A creative studio receives a branding request from a new client.

Using DotLink, the business owner registers the client, prepares a quotation using existing service rates and records the client's acceptance. The accepted quotation is linked to a project, where deliverables and deadlines are managed.

The quotation is converted into an invoice, advance and final payments are recorded, and project-related expenses are tracked.

Dottie assists throughout the process, allowing the owner to manage operations through natural-language instructions while retaining control over all proposed modifications.

The financial dashboard provides visibility into received income, outstanding balances, expenses and cash-basis financial performance.

## Engineering Highlights

- Supervisor-based multi-agent orchestration.
- Context-aware natural-language tool execution.
- Full-stack REST API development.
- Human-in-the-loop transactional workflows.
- PostgreSQL-backed conversational memory.
- Workspace-scoped database access.
- Deterministic financial calculations.
- Structured data validation.
- Multi-provider LLM configuration.
- AI observability and execution tracing.
- Responsive product-oriented interface design.

## Project Scope

DotLink is an independent AI-powered business management project focused on demonstrating practical agentic AI, full-stack software engineering and reliable business workflow execution.

Its financial analytics are designed for operational cash-basis insights rather than replacing a complete accounting or taxation system.

## Author

**Mohamed Akshan**

Data Science Undergraduate — Cardiff Metropolitan University

Interested in AI Engineering, Agentic AI, Machine Learning and Full-Stack Software Development.

[Portfolio](https://mohamed-akshan-portfolio.vercel.app/) · [LinkedIn](https://www.linkedin.com/in/akshan-mohamed-ashraf/) · [GitHub](https://github.com/Mohamed-Akshan)

---

<div align="center">

**DotLink — Less administration. More imagination.**

Built to connect business operations with intelligent assistance.

</div>
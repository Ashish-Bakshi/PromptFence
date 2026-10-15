# PromptFence 🛡️

> **Status:** 🚧 Active Development  
> **Core Stack:** Python, FastAPI, Pydantic, Docker, SQLite/Postgres

PromptFence is a lightweight security gateway proxy for LLM applications. It sits between your AI agents and your internal systems to validate, audit, and authorize dynamic tool calls before they are executed. 

As LLMs are increasingly given agency to execute code, query databases, or trigger webhooks, PromptFence ensures that generated arguments conform to strict schemas and that destructive payloads are blocked via Role-Based Access Control (RBAC).

## 🏗️ System Architecture

```mermaid
graph TD
    A[LLM / Agent] -->|POST /v1/execute| B(PromptFence Gateway)
    B --> C{Pydantic Schema Validator}
    C -->|Invalid| D[Return 400 Validation Error]
    C -->|Valid| E{RBAC Policy Engine}
    E -->|Unauthorized| F[Log Block & Return 403]
    E -->|Authorized| G[Audit Ledger]
    G --> H((Tool Execution Forwarding))

---
name: developer-modular-structure
description: Enforce strict vertical feature-based modular architecture with shared runtime adapters and isolated DevOps infrastructure
license: MIT
compatibility: opencode
metadata:
  audience: backend-developers
  architecture: vertical-slice
  maturity: production
---

# Developer Modular Structure Skill

This skill enforces a strict vertical feature-based architecture designed for scalability, maintainability, and clean separation of concerns.

This structure must be applied to all new implementations and major refactors.

---------------------------------------------------------------------

CORE PRINCIPLE

Each feature is a self-contained module.

Each feature behaves like a "city":
- It owns its API
- It owns its models
- It owns its business logic
- It owns its repository wrapper

Shared technical infrastructure lives separately.
DevOps infrastructure lives separately.
Boundaries are strict.

---------------------------------------------------------------------

REQUIRED PROJECT STRUCTURE

src/

  user/
    api.py
    models.py
    logic.py
    repository.py
    __init__.py

  order/
    api.py
    models.py
    logic.py
    repository.py
    __init__.py

  shared/
    database/
      connection.py
    ai_client/
      client.py
    messaging/
      producer.py

infra/
  terraform/
  kubernetes/
  ci/

---------------------------------------------------------------------

FEATURE MODULE RULES

Each feature folder MUST contain:

api.py
- Controllers / route handlers only
- No business logic
- No database calls
- No direct shared adapter usage

models.py
- Domain models
- DTOs
- Validation models

logic.py
- Pure business logic
- No direct database connections
- No direct AI calls

repository.py
- Feature-specific wrapper over shared adapters
- All data access logic lives here
- Translates between domain and storage

__init__.py
- Controlled exports only
- No heavy logic

---------------------------------------------------------------------

SHARED RUNTIME ADAPTERS

All technical integrations live under:

src/shared/

Examples:
- Database connection
- AI client
- Messaging system
- Caching client
- External API client

Rules:
- No business logic inside shared
- Shared must never import feature modules
- Shared must expose minimal clean interfaces
- Shared should be replaceable

Shared is technical plumbing only.

---------------------------------------------------------------------

DEVOPS INFRASTRUCTURE ISOLATION

Infrastructure-as-code must live in:

infra/

Allowed content:
- Terraform
- Helm
- Kubernetes manifests
- CI/CD pipelines

Forbidden:
- Runtime application code
- Business logic
- Feature modules

infra/ is deployment only.

---------------------------------------------------------------------

WRAPPER RULE (CRITICAL)

Features must NEVER directly use shared adapters in API or logic layers.

Forbidden pattern:
API → shared adapter
Logic → shared adapter

Correct flow:
API → Logic → Repository → Shared Adapter

Repository is the only allowed bridge.

---------------------------------------------------------------------

AI CLIENT DISCIPLINE

AI client must live in:

src/shared/ai_client/

Each feature must create its own wrapper over the AI client if needed.

No raw AI calls from API.
No AI client calls inside logic layer.

---------------------------------------------------------------------

DATABASE DISCIPLINE

- shared/database handles connection pooling
- repository.py handles domain queries
- No SQL in API
- No ORM usage inside controllers
- No connection creation in logic.py

Repository is the only allowed database access layer.

---------------------------------------------------------------------

DEPENDENCY DIRECTION RULES

Allowed:
Feature → Shared adapter (via repository)
API → Logic
Logic → Repository
Repository → Shared

Forbidden:
Feature → Another feature's internals
API → Shared directly
Logic → Raw DB connection
Shared → Feature
Cross-feature repository imports

Dependencies must flow inward.

---------------------------------------------------------------------

SCALABILITY REQUIREMENTS

This architecture must support:
- Feature extraction into microservices
- Independent team ownership
- Adapter replacement (DB swap, AI swap)
- Safe parallel development

Each feature must be isolatable without major refactor.

---------------------------------------------------------------------

ANTI-PATTERNS (STRICTLY FORBIDDEN)

- Root-level file dumping
- Controllers containing business logic
- Direct DB calls in API
- Direct AI calls in API
- Feature importing another feature's repository
- Runtime code inside infra/
- God modules
- Circular dependencies

Violations must be corrected immediately.

---------------------------------------------------------------------

CLEAN CODE ENFORCEMENT

- Single Responsibility per file
- Small cohesive modules
- Clear naming
- Explicit interfaces
- No hidden side-effects
- No oversized files without justification

---------------------------------------------------------------------

FINAL LAW

Each feature is a city.
Shared is utilities.
Infra is deployment.
Boundaries are sacred.
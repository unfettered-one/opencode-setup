---
name: reviewer-code-quality
description: Enforce clean code principles, SOLID, modularity, and maintainability standards during final review.
license: MIT
compatibility: opencode
metadata:
  role: reviewer
  priority: critical
---

# Reviewer Code Quality Standard

## Purpose

Ensure code meets production-grade engineering standards before approval.

---

## Enforce Clean Architecture

- No business logic inside controllers
- No infrastructure logic inside domain
- Clear separation of:
  - feature modules
  - infrastructure connectors
  - configuration
- No circular dependencies

---

## SOLID Enforcement

### Single Responsibility
Each file/class must have one reason to change.

### Open/Closed
New features should not require modification of stable core modules.

### Liskov
Subtypes must behave correctly without runtime type checks.

### Interface Segregation
No fat interfaces.

### Dependency Inversion
High-level modules depend on abstractions.

---

## Code Hygiene

- No duplicated logic
- No unused imports
- No dead code
- No commented-out production code
- Meaningful naming
- Clear error handling

---

## Violations

Categorize issues:

- CRITICAL → Architecture violation, security risk
- MAJOR → Structural or maintainability issue
- MINOR → Style or clarity issue
- SUGGESTION → Improvement idea
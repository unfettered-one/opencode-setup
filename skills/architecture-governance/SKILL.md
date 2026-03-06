---
name: architecture-governance
description: Enforce high-level and low-level architecture standards including modular structure, SOLID principles, clean layering, and design pattern governance
compatibility: opencode
license: MIT
metadata:
  audience: architects-and-senior-engineers
  scope: structural-design
---


# Architecture Governance Skill

This skill enforces structural correctness, modular design discipline, SOLID compliance, and architectural integrity at both High-Level Design (HLD) and Low-Level Design (LLD).

Use during:
- Full repository audits
- New system design
- Major refactoring
- Architecture governance reviews

---

## 1️⃣ High-Level Architecture Standards

### System Structure Requirements

- Clear module boundaries
- No cyclic dependencies
- Infrastructure isolated from business logic
- Controllers must not contain business logic
- No direct database access from UI layer
- No cross-layer shortcut calls
- No “God modules”

### Architectural Patterns (Use When Justified)

- Clean Architecture
- Hexagonal Architecture
- Layered Architecture
- Modular Monolith (preferred over premature microservices)
- Event-Driven Architecture (only if domain requires async)

Avoid:
- Premature microservices
- Speculative generalization
- Decorative abstraction layers
- Over-engineering

---

## 2️⃣ Low-Level Design Standards (Mandatory)

### SOLID Principles

- Single Responsibility
- Open/Closed
- Liskov Substitution
- Interface Segregation
- Dependency Inversion

Violations must be explicitly identified.

### Clean Code Requirements

- Small cohesive classes
- Pure functions where possible
- Avoid hidden side effects
- Clear, explicit naming
- Avoid methods > 50 lines unless justified
- No business logic inside DTOs
- No duplicated logic across modules

---

## 3️⃣ Modular Folder Structure Enforcement

Projects must follow separation such as:

- domain/
- application/
- infrastructure/
- interfaces/
- config/

Flat root-directory dumping is a structural violation.

---

## 4️⃣ Design Pattern Governance

Allowed patterns (when solving real problems):

- Factory
- Strategy
- Repository
- Adapter
- Builder
- Observer
- Dependency Injection

Flag anti-patterns:

- God Object
- Tight Coupling
- Spaghetti Code
- Shotgun Surgery
- Copy-paste inheritance

---

## 5️⃣ Output Requirements When Used

Architect must provide:

1. Current architecture summary
2. Structural violations
3. Pattern misuse
4. Modularity violations
5. High-level recommendations
6. Explicit statement if architecture is acceptable

---

Use this skill when evaluating structural integrity or designing systems.
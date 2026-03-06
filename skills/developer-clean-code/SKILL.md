---
name: developer-clean-code
description: Enforce clean code practices including readability, maintainability, SOLID adherence, and safe abstractions
compatibility: opencode
license: MIT
metadata:
  audience: developers
  scope: code-quality
---

# Developer Clean Code Skill

This skill enforces maintainable, readable, and scalable code.

Use during:
- Writing new code
- Refactoring
- Improving existing logic

---

## 1️⃣ SOLID Compliance

All new code must follow:

- Single Responsibility
- Open/Closed
- Liskov Substitution
- Interface Segregation
- Dependency Inversion

Violations must be avoided unless explicitly justified.

---

## 2️⃣ Readability Standards

- Clear naming (no abbreviations like tmp, data1, val)
- Functions must do one logical thing
- Avoid deeply nested conditionals
- Avoid duplicated logic
- Avoid magic numbers

---

## 3️⃣ Method & Class Size

- Methods should remain concise
- Classes should not handle multiple unrelated responsibilities
- Avoid God classes
- Split large files logically

---

## 4️⃣ Error Handling

- Explicit error handling
- Avoid silent failures
- Avoid swallowing exceptions
- Use meaningful error messages

---

## 5️⃣ Language-Agnostic Cleanliness

This skill applies to:

- Python
- TypeScript / JavaScript
- C#
- Java
- Any OOP language

Do not assume specific framework unless project uses it.

---

Use this skill to enforce long-term maintainability.
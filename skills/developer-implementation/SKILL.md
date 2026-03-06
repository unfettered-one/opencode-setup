---
name: developer-implementation
description: Enforce disciplined feature implementation following architect plan, layered structure, and minimal safe modifications
compatibility: opencode
license: MIT
metadata:
  audience: developers
  scope: implementation-governance
---

# Developer Implementation Skill

This skill governs how features are implemented in a controlled, production-safe manner.

Use during:
- Feature implementation
- Bug fixes
- Refactoring after tester feedback

---

## 1️⃣ Implementation Discipline

Developer must:

- Implement strictly according to Architect Phase
- Avoid changing architecture unless explicitly recorded
- Keep changes minimal and localized
- Avoid rewriting unrelated modules
- Preserve backward compatibility unless task explicitly allows breaking change

---

## 2️⃣ Scope Control

When implementing:

- Identify exact modules affected
- Modify only necessary files
- Do not introduce unrelated refactoring
- Do not add decorative abstractions

---

## 3️⃣ Refactoring Rules

If refactoring is required:

- Refactor in small steps
- Maintain existing behavior
- Ensure no public contract breaks
- Avoid mixing refactor + feature in same large change unless required

---

## 4️⃣ Code Change Documentation

When finishing implementation:

- Summarize files modified
- Explain why changes were required
- Explain architectural impact (if any)
- Explicitly state if backward compatibility preserved

---

Use this skill for controlled and disciplined implementation.
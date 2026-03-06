---
name: reviewer-security-standards
description: Validate security compliance, authentication enforcement, input validation, and safe data handling.
license: MIT
compatibility: opencode
metadata:
  role: reviewer
  priority: critical
---

# Reviewer Security Validation

## Authentication

- All protected routes enforce authentication
- No bypass paths
- No debug backdoors

---

## Input Validation

- Validate all request bodies
- Validate query params
- Reject malformed inputs
- Proper 400/422 responses

---

## Data Exposure

- No secrets in logs
- No tokens in responses unless required
- No password leakage
- No stack traces in production responses

---

## Injection Risks

- No raw SQL without parameterization
- No dynamic eval execution
- No unsafe deserialization

---

## Dependency Safety

- Avoid unsafe third-party packages
- No direct secrets in source

---

## Severity

Security violations are always CRITICAL.
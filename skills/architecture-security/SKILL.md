---
name: architecture-security
description: Enforce architectural security standards including authentication, authorization, data protection, and secure design practices
compatibility: opencode
license: MIT
metadata:
  audience: architects-and-security-engineers
  scope: security-governance
---

# Architecture Security Skill

This skill enforces secure architectural design and risk evaluation.

Use during:
- Security audits
- Architecture reviews
- API design validation
- Compliance preparation

---

## 1️⃣ Input Validation

- All external inputs must be validated
- No blind trust of client data
- Strict schema validation required
- Proper error handling without exposing internal stack traces

---

## 2️⃣ Authentication & Authorization

- Clear separation between authentication and business logic
- Role-based or policy-based enforcement
- No authorization logic in frontend layer
- Token expiration properly enforced
- Centralized access control checks

---

## 3️⃣ Secrets & Configuration

- No hardcoded secrets
- Environment-based configuration
- Secure secret storage
- Secret rotation considered

---

## 4️⃣ Data Protection

- Sensitive data encrypted where required
- Passwords hashed using strong algorithm
- No logging of secrets or tokens
- No exposure of internal implementation details in errors

---

## 5️⃣ API Security

- Rate limiting evaluated
- Idempotency for critical operations
- CSRF/XSS considerations for web apps
- Secure headers configured where applicable

---

## 6️⃣ Security Risk Classification

All findings must be labeled:

- Critical
- Major
- Minor

Security issues default to Critical unless explicitly justified.

---

Use this skill for architecture-level security evaluation.
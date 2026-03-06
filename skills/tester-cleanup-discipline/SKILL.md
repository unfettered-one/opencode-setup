---
name: tester-cleanup-discipline
description: Ensure all test-created resources are cleaned and no persistent pollution remains after integration tests.
license: MIT
compatibility: opencode
metadata:
  role: tester
  testing-level: hygiene
---

# Cleanup Discipline Skill

## Objective

Ensure no persistent test data remains after testing.

---

## Rules

1. Track every created entity.
2. Delete entities in reverse dependency order.
3. Confirm deletion with verification call.
4. If deletion fails → treat as defect.

---

## Zero-Pollution Standard

After test completion:

- Database should not contain test artifacts.
- No dangling tokens.
- No orphaned records.

---

## Failure Handling

If cleanup fails:

- Report as CRITICAL issue.
- Return phase to developer.
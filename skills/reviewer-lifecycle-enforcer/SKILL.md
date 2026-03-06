---
name: reviewer-lifecycle-enforcer
description: Ensure strict workflow compliance and prevent invalid state transitions.
license: MIT
compatibility: opencode
metadata:
  role: reviewer
  priority: critical
---

# Reviewer Lifecycle Enforcement

## Verify:

- Tester phase appended properly
- Coverage summary present
- Smoke test results present
- Integration results present

---

## Validate Status.json

- phase == reviewer
- history contains:
  architect
  developer
  tester

---

## If Review Passes

1. Append reviewer to history
2. Set completed = true
3. Write full JSON
4. Re-read file
5. Confirm completed == true

---

## If Review Fails

1. Append structured review under `## Reviewer Phase`
2. Append reviewer to history
3. Set phase = tester
4. Write full JSON
5. Confirm update
6. STOP

---

Failure to enforce lifecycle is CRITICAL.
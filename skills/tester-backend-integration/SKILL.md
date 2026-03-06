---
name: tester-backend-integration
description: Perform full backend integration testing including real CRUD operations, authentication lifecycle validation, and edge case verification.
license: MIT
compatibility: opencode
metadata:
  role: tester
  testing-level: integration
---

# Backend Integration Testing Skill

## What I Do

I perform real end-to-end testing against the deployed backend.

This includes:

- Creating test entities
- Performing CRUD operations
- Validating authentication flows
- Testing edge cases
- Cleaning up test data

---

## Integration Flow

If authentication system exists:

1. Create test user
2. Login
3. Obtain access token
4. Call authenticated endpoints
5. Validate authorization enforcement
6. Refresh token
7. Test invalid token
8. Delete user
9. Confirm deletion

---

## Edge Case Testing

- Missing required fields
- Invalid email formats
- Duplicate resource creation
- Unauthorized access
- Expired or malformed token

---

## Validation Criteria

- Correct status codes
- Correct response shape
- No internal server errors
- No inconsistent state after failure

---

## Cleanup Discipline

All test-created data must be deleted before test ends.

No leftover test data allowed.

---

## Failure Handling

On any integration failure:

- Append detailed defect report
- Include request/response examples
- Set phase to developer
- STOP

---

## Safety Rules

- Never use production secrets
- Use dedicated test identifiers
- Confirm cleanup completed
---
name: tester-api-smoke
description: Perform smoke testing of exposed APIs including status validation, response validation, and latency checks.
license: MIT
compatibility: opencode
metadata:
  role: tester
  testing-level: smoke
---

# Tester API Smoke Skill

## What I Do

I validate that all exposed APIs:

- Are reachable
- Return correct HTTP status codes
- Return structurally valid JSON
- Meet basic latency expectations
- Do not crash on simple invalid input

---

## When To Use

Use when:

- Backend service is deployed
- API routes exist
- Smoke validation is required before integration testing

---

## Smoke Testing Rules

1. Discover available routes from:
   - OpenAPI spec
   - Router files
   - API directory

2. For each public endpoint:
   - Send minimal valid request
   - Validate status code
   - Validate JSON structure
   - Validate response time < defined threshold

3. For protected endpoints:
   - Attempt call without token → expect 401
   - Attempt call with malformed token → expect 401/403

4. Never modify production data during smoke unless explicitly allowed.

---

## Latency Standard

- API response must complete within acceptable threshold (default < 2s unless specified).
- Flag endpoints exceeding threshold.

---

## Failure Handling

If any endpoint:
- Crashes
- Returns 500
- Returns invalid structure
- Violates expected status

Then:
- Append detailed report under `## Tester Phase`
- Return phase to `developer`
- STOP progression

---

## Safety

- Use environment variables for BASE_URL.
- Do not hardcode secrets.
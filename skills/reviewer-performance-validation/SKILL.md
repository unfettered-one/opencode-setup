---
name: reviewer-performance-validation
description: Validate performance characteristics including async correctness, blocking calls, and scalability risks.
license: MIT
compatibility: opencode
metadata:
  role: reviewer
  priority: high
---

# Reviewer Performance Standards

## Async Discipline

- No blocking calls inside async functions
- No sequential awaits when parallel possible
- Use concurrency patterns where appropriate

---

## API Performance

- No N+1 database calls
- Avoid repeated expensive computation
- Proper caching where required

---

## Memory & Resource Handling

- No unbounded loops
- No unclosed connections
- No memory leaks via global objects

---

## Scalability

- No tight coupling between modules
- Avoid synchronous bottlenecks
- Validate rate limiting logic if applicable

---

## Severity

Performance regressions:
- Major → Potential scaling issue
- Minor → Optimization opportunity
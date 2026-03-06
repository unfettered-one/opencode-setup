---
name: developer-async-concurrency
description: Enforce proper async design, non-blocking execution, safe concurrency patterns, and parallel execution discipline
license: MIT
compatibility: opencode
metadata:
  audience: backend-developers
  focus: concurrency
  maturity: production
---

# Developer Async & Concurrency Skill

This skill enforces correct asynchronous design and concurrency discipline.

It prevents blocking code, unsafe parallelism, and performance bottlenecks.

---------------------------------------------------------------------

CORE PRINCIPLE

Async is not about syntax.
Async is about non-blocking architecture.

If the system supports async, it must be used correctly.

---------------------------------------------------------------------

WHEN ASYNC IS REQUIRED

Use async when:

- I/O bound operations exist (DB, HTTP, AI, file, messaging)
- External service calls occur
- Parallel independent calls are possible
- Latency reduction is required

Do NOT use async for CPU-bound heavy computation.

---------------------------------------------------------------------

FORBIDDEN PATTERNS

- Blocking I/O inside async functions
- Calling synchronous DB client inside async route
- Using time.sleep in async context
- Sequential awaiting of independent calls
- Fire-and-forget background tasks without control

---------------------------------------------------------------------

PARALLEL EXECUTION RULE

If multiple I/O calls are independent, they must run in parallel.

Incorrect:
await call_a()
await call_b()

Correct:
Run both concurrently using appropriate concurrency primitives for the language.

---------------------------------------------------------------------

SAFE CONCURRENCY RULES

- Protect shared mutable state
- Avoid global mutable variables
- Avoid race conditions
- Use locks only when absolutely necessary
- Prefer stateless services

---------------------------------------------------------------------

DATABASE CONCURRENCY

- Use connection pooling
- Never create new connection per request
- Avoid N+1 query patterns
- Batch queries when possible

---------------------------------------------------------------------

HTTP CLIENT DISCIPLINE

- Use async-capable HTTP clients if the framework supports async
- Do not mix sync and async clients
- Always set timeouts
- Handle cancellation properly

---------------------------------------------------------------------

AI / EXTERNAL API CALLS

- Always enforce timeouts
- Always handle retries safely
- Do not retry non-idempotent operations blindly
- Parallelize independent AI calls when safe

---------------------------------------------------------------------

ERROR HANDLING

- Do not swallow async exceptions
- Propagate meaningful errors
- Log failures clearly
- Ensure awaited tasks are handled

---------------------------------------------------------------------

THREADING VS ASYNC

Do not mix threading and async casually.
Use the framework’s recommended concurrency model.

---------------------------------------------------------------------

PERFORMANCE INTENT

Async must reduce latency.
If no measurable improvement, reconsider design.

---------------------------------------------------------------------

ANTI-PATTERNS

- Async everywhere without reason
- Sequential awaits of independent operations
- Blocking ORM inside async route
- Background tasks without lifecycle control
- Shared mutable caches without protection

---------------------------------------------------------------------

FINAL LAW

Concurrency increases complexity.
Use it intentionally.
Parallelize only when independent.
Never block the event loop.
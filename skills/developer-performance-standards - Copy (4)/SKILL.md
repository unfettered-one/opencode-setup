---
name: developer-performance-standards
description: Enforce measurable performance standards, scalability discipline, and efficiency best practices for production systems
license: MIT
compatibility: opencode
metadata:
  audience: backend-developers
  focus: performance
  maturity: production
---

# Developer Performance Standards Skill

This skill enforces production-grade performance discipline.

Performance is not optional.
Performance is a feature.

---------------------------------------------------------------------

CORE PRINCIPLE

Every design must scale.
Every feature must consider:

- Latency
- Throughput
- Memory usage
- Concurrency impact
- Database efficiency

---------------------------------------------------------------------

LATENCY TARGETS

APIs must aim for:

- Sub-200ms internal APIs
- Sub-500ms external calls
- Avoid multi-second synchronous chains

If slow operations are required:
- Use background processing
- Use caching
- Use parallel execution

---------------------------------------------------------------------

DATABASE PERFORMANCE RULES

- No unbounded queries
- Always use indexes for filtered fields
- Avoid SELECT *
- Avoid N+1 query patterns
- Use pagination
- Batch inserts and updates when possible

---------------------------------------------------------------------

MEMORY DISCIPLINE

- Avoid loading entire datasets into memory
- Use streaming for large responses
- Avoid large object copies
- Release resources properly

---------------------------------------------------------------------

CACHING STRATEGY

Cache when:
- Data is read-heavy
- Computation is expensive
- AI responses are reusable

Do NOT cache:
- Highly volatile data
- Sensitive user-specific secrets

Always define:
- TTL
- Invalidation strategy

---------------------------------------------------------------------

SCALABILITY CHECKLIST

Design must support:

- Horizontal scaling
- Stateless service design
- Externalized session storage
- Connection pooling
- Rate limiting

---------------------------------------------------------------------

LOGGING PERFORMANCE

- Avoid excessive logging in hot paths
- Do not log entire large payloads
- Use structured logs
- Avoid blocking logging operations

---------------------------------------------------------------------

SECURITY & PERFORMANCE BALANCE

Security checks must not:
- Introduce unnecessary blocking calls
- Recompute expensive validations repeatedly

Reuse validated tokens where safe.

---------------------------------------------------------------------

LOAD AWARENESS

When adding features, consider:

- What happens at 10x traffic?
- What happens at 100x traffic?
- What happens under partial outage?

Design for graceful degradation.

---------------------------------------------------------------------

ANTI-PATTERNS

- Blocking I/O in request path
- Large JSON serialization in tight loops
- Multiple DB round-trips in one request
- No pagination on list endpoints
- Heavy computation inside API route

---------------------------------------------------------------------

MEASUREMENT RULE

If performance improvement is claimed,
it must be measurable.

Use:
- Benchmarks
- Load testing
- Profiling

Never guess.

---------------------------------------------------------------------

FINAL LAW

Correctness first.
Then performance.
But performance must always be considered.
Production systems must scale predictably.
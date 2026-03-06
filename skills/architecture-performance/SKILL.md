---
name: architecture-performance
description: Enforce performance, scalability, async correctness, and concurrency standards across systems
compatibility: opencode
license: MIT
metadata:
  audience: architects-and-performance-engineers
  scope: performance-and-scalability
---

# Architecture Performance Skill

This skill governs system efficiency, scalability, concurrency correctness, and resource management.

Use during:
- Performance audits
- Scalability evaluations
- Async validation
- Backend architecture review

---

## 1️⃣ Async & Concurrency Standards

If the language supports async:

- Avoid sequential blocking calls when parallelization is safe
- Use Promise.all / asyncio.gather / Task.WhenAll appropriately
- No blocking I/O inside async flows
- Avoid unnecessary await inside loops
- No synchronous DB or network calls inside async handlers

Concurrency misuse = performance defect.

---

## 2️⃣ Latency & Bottleneck Detection

Architect must check for:

- N+1 query patterns
- Redundant API calls
- Repeated heavy computations
- Excessive serialization/deserialization
- Blocking network calls in critical paths

---

## 3️⃣ Scalability Principles

- Services should be stateless when possible
- Horizontal scaling feasibility evaluated
- Proper pagination on data queries
- Caching opportunities assessed
- Message queues justified, not decorative

---

## 4️⃣ Resource Efficiency

- No unbounded collections
- No uncontrolled memory growth
- Stream large datasets when possible
- Avoid CPU-heavy synchronous loops
- Avoid excessive object creation in hot paths

---

## 5️⃣ Performance Risk Classification

All findings must be categorized:

- Critical
- Major
- Minor

---

Use this skill for performance governance and scalability evaluation.
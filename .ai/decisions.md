# Architecture Decisions Log

## Decision 1: Preserve Core Deduplication Pattern
**Status:** APPROVED  
**Context:** Token refresh deduplication logic prevents refresh storms during 401 cascades  
**Decision:** Keep deduplication logic intact post-migration  
**Rationale:** This pattern is architecture-critical and provides value even with cookie-based auth. The 401 retry mechanism remains important for handling stale cookies or clock skew scenarios.

## Decision 2: Remove Storage Layer Entirely
**Status:** APPROVED  
**Context:** Browser automatically manages HTTP-only cookies, no application-level storage needed  
**Decision:** Delete `src/auth/storage.ts` after removing all dependencies  
**Rationale:** Eliminates attack surface (XSS immunity), simplifies codebase, and removes unnecessary abstraction layer. Browser cookie management is more reliable than localStorage.

## Decision 3: Simplify AuthContext Initialization
**Status:** APPROVED  
**Context:** No need to check localStorage for tokens since authentication is cookie-based  
**Decision:** Update `checkAuth()` to directly call `/auth/me` endpoint; let API response determine auth state  
**Rationale:** Single source of truth is the API response. Browser automatically sends cookies, so presence of tokens is implicit. Simpler and more secure logic flow.

## Decision 4: Maintain Logout Endpoint Call
**Status:** APPROVED  
**Context:** Logout must notify server to invalidate session/refresh tokens  
**Decision:** Keep `logout()` API call even though cookies are auto-managed  
**Rationale:** Server-side session invalidation is critical for security. Browser cannot clear HttpOnly cookies manually; server must explicitly expire them.

## Decision 5: Add Credentials to All Fetch Requests
**Status:** APPROVED  
**Context:** HTTP-only cookies won't be sent unless explicitly requested  
**Decision:** Add `credentials: 'include'` to all authenticated request configurations  
**Rationale:** Browser security model requires explicit opt-in for cross-origin cookie sending. This is required for all requests to auth-protected endpoints.

---

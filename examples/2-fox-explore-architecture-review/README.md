# Example 2: Architecture Analysis & Codebase Exploration (Fox Explore)

This example demonstrates using **Fox Explore** to explain unfamiliar code, research external alternatives, and evaluate trade-offs without editing files.

---

## Scenario Overview

- **Context**: A developer is onboarding to a repository and evaluating how token-based authentication is implemented.
- **Objective**: Understand the request lifecycle, identify architectural trade-offs, and compare the current custom token validation with industry standards.

---

## Why Fox Explore?

1. The task requires understanding and evaluating code, not fixing a bug.
2. Fox Explore is read-only by default and will not modify production code or tests.
3. Grounded analysis: cites exact file paths and separates facts from inferences.

---

## Sample Agent Prompt

```text
/fox-explore Review our authentication architecture:
1. Trace the token validation lifecycle from incoming HTTP request to handler execution.
2. Compare our custom token decoding with standard libraries (e.g. PyJWT or Authlib).
3. Identify trade-offs in our current implementation and advise what to improve and what to leave alone.
```

---

## Expected Agent Output

```markdown
### 1. Request Lifecycle
Incoming requests pass through `src/middleware/auth.py:TokenMiddleware`. The middleware extracts the Authorization header, validates the signature via `src/auth/jwt.py:decode_token()`, and injects user context into `request.state.user`.

### 2. Comparison with Standard Libraries
- **Current Custom Parser**: In `src/auth/jwt.py`, token decoding is implemented with standard library `base64` and `hashlib`.
- **PyJWT / Authlib**: Provide built-in algorithm pinning, clock skew leeway, and constant-time signature comparison.

### 3. Recommendations & Trade-Offs
- **Leave Alone**: The custom token parser is compact (<80 LOC) and avoids external dependencies for simple HS256 HMAC tokens.
- **Improve**: Add clock skew tolerance (leeway) in `src/auth/jwt.py:L45` to prevent false expirations during slight server time drift.
```

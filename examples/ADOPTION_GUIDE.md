# Fox skills adoption guide

This guide shows when to use Fox, Fox Explore, Fox Change Review (`fox-review`), Fox Test Audit (`fox-verify`), or a sequence of them.

---

## Decision Matrix: Which Skill Should You Use?

| Task or Objective | Recommended Skill | Why |
| :--- | :--- | :--- |
| **Fix a localized defect or logic error** (regex parsing, off-by-one errors, math bugs) | **Fox alone** | Isolates the owning layer and fixes it minimally. Builds reproducer first, tests counterexamples, and verifies zero regressions. |
| **Investigate an unfamiliar bug across system boundaries** (CLI to backend, client to server) | **Fox alone** | Traces input through execution to observable output, builds a reproducer, and repairs the owning layer directly. |
| **Onboard to an unfamiliar repository or component** | **Fox Explore alone** | Explains the request flow, identifies architectural patterns, and provides a clear map of the codebase without editing files. |
| **Evaluate trade-offs or compare external alternatives** | **Fox Explore alone** | Researches standard open-source libraries and protocols, compares architectural options, and advises on trade-offs. |
| **Review a diff, branch, commit, or pull request** | **Fox Change Review alone** | Audits the exact change and connected behavior, validates findings, and leaves files unchanged. |
| **Determine whether green tests detect broken behavior** | **Fox Test Audit alone** | Defines observable invariants and challenges the evidence with configured mutation tools or isolated targeted mutations. |
| **Plan an architectural refactor and implement it safely** | **Fox Explore + Fox** | Fox Explore evaluates alternatives and advises on design trade-offs first; Fox implements the minimal complete fix with verification. |
| **Review findings and then repair them** | **Fox Change Review + Fox** | Fox Change Review produces an independent evidence-backed report; Fox implements only the authorized verified findings. |
| **Repair, then challenge the regression test** | **Fox + Fox Test Audit** | Fox repairs and tests the defect; Fox Test Audit independently checks whether the regression test fails when the behavior is broken. |

---

## Example 1: Localized Defect (Fox Alone)

### Scenario
An input validation regex rejects valid inputs. For instance, `validate.URL` rejects URLs with a fragment directly following an empty path, such as `https://example.com#frag`.

The defect is entirely localized to a single regular expression generator inside `src/marshmallow/validate.py`.

### Why Fox Alone?
- The root cause lives at one specific owning location.
- Fox's four-step workflow ensures a reproducer is built first, counterexamples are tested (such as bare `#` and query strings), and the fix remains minimal.

### Sample Prompt
```text
Investigate and fix the issue where validate.URL rejects URLs with fragments directly following an empty path (e.g., 'https://example.com#frag').
1. Trace the defect to the owning component.
2. Build a reproduction script and test counterexamples.
3. Apply a minimal complete fix at the owning layer.
4. Verify with the project test suite.
```

### Agent Workflow with Fox
1. **Ground**: Inspect `src/marshmallow/validate.py` and run the existing test suite (`pytest tests/test_validate.py`). Create a minimal reproducer proving `validate.URL()("https://example.com#frag")` raises an unexpected ValidationError.
2. **Trace**: Follow the URL regex generator pattern down to the path/query/fragment boundary. Identify that the regex requires a trailing slash before a fragment when no query parameters are present.
3. **Decide and Change**: Modify only the regex pattern at the owning line in `src/marshmallow/validate.py`. Do not wrap the validator or add special-case string replaces.
4. **Verify and Deliver**: Run the reproducer to confirm it passes. Test edge cases: `https://example.com#`, `https://example.com/#frag`, and `https://example.com?query=1#frag`. Run the full validation test suite.

---

## Example 2: Architecture Review & Technical Research (Fox Explore Alone)

### Scenario
A developer wants to evaluate an authentication module before expanding it:
- How does the token validation lifecycle work?
- How does our custom token decoding compare to standard libraries like PyJWT or Authlib?
- What are the architectural trade-offs?

### Why Fox Explore Alone?
- No code needs to be modified or debugged.
- The objective is understanding, comparative research, and architectural evaluation.
- Fox Explore is strictly read-only and cites verified repository paths and external documentation.

### Sample Prompt
```text
/fox-explore Review our authentication architecture:
1. Trace the token validation lifecycle from incoming HTTP request to handler execution.
2. Compare our custom token decoding with standard libraries (e.g. PyJWT or Authlib).
3. Identify trade-offs in our current implementation and advise what to improve and what to leave alone.
```

### Agent Workflow with Fox Explore
1. **Understand Question**: Identify scope (authentication middleware and token decoder) and classify as an architectural comparison.
2. **Investigate Evidence**: Trace `src/middleware/auth.py` and `src/auth/jwt.py`. Research standard RFC 7519 specifications and popular library patterns.
3. **Connect & Evaluate**: Separate implementation facts from design inference. Weigh simplicity of stdlib-only implementation against security benefits of external token libraries.
4. **Explain & Recommend**: Deliver a structured explanation with exact line references and clear advice on what to improve and what to leave alone.

---

## Example 3: Explore First, Fix with Proof (Combined Fox + Fox Explore)

### Scenario
A service experiences intermittent authentication failures during slight server time drift. The team wants to research standard clock skew handling, decide on a design, and implement a verified fix.

### Why Use Both Skills?
- **Fox Explore** conducts the read-only technical research and evaluates architectural alternatives before any code is modified.
- **Fox** enforces engineering discipline: builds a reproducer, repairs the owning layer directly, and verifies the outcome with empirical evidence.

### Sample Prompt
```text
1. Use Fox Explore to investigate standard clock-skew tolerance in token validation and recommend an approach.
2. Once the design is clear, use Fox to ground the issue, apply the minimal complete fix in src/auth/jwt.py, and verify with tests.
```

### Sequential Combined Workflow

```text
+-------------------------------------------------------------------+
| 1. Explore & Compare (Fox Explore)                                |
|    - Inspect src/auth/jwt.py:decode_token()                       |
|    - Research RFC 7519 leeway recommendations (default 5-30s)     |
|    - Recommend adding a 10s leeway parameter without breaking API |
+-------------------------------------------------------------------+
                                  |
                                  v
+-------------------------------------------------------------------+
| 2. Ground & Reproduce (Fox)                                       |
|    - Create a test proving failure when token expires by 2s       |
|    - Verify failure before touching production files              |
+-------------------------------------------------------------------+
                                  |
                                  v
+-------------------------------------------------------------------+
| 3. Minimal Complete Fix (Fox)                                     |
|    - Update src/auth/jwt.py with default leeway=10                |
|    - Repair the owning layer directly                             |
+-------------------------------------------------------------------+
                                  |
                                  v
+-------------------------------------------------------------------+
| 4. Verify & Deliver (Fox)                                         |
|    - Run reproducer to confirm it passes                          |
|    - Run proportionate regression checks and report limits        |
+-------------------------------------------------------------------+
```

---

## Example 4: Independent Change Review (Fox Change Review Alone)

### Scenario
A pull request adds account-scoped order lookup. The author wants a pre-merge audit for tenant leaks, regressions, weak tests, and needless complexity.

### Why Fox Change Review Alone?
- The code already exists and the task is assessment, not implementation.
- The reviewer must inspect the diff and connected callers without changing the author's work.
- A clean change must be allowed to pass without invented findings.

### Sample Prompt
```text
/fox-review Review this branch against SPEC.md. Check correctness, tenant isolation,
regression risk, test strength, performance, and unnecessary complexity. Report only
verified actionable findings. Do not edit files.
```

### Agent Workflow with Fox Change Review
1. **Set the target**: Resolve the merge base, branch head, specification, and repository rules.
2. **Trace the change**: Read the diff, query implementation, callers, tests, and schema.
3. **Validate findings**: Exercise duplicate numeric IDs across two accounts and challenge each candidate finding.
4. **Report**: Put verified findings first with severity, location, evidence, consequence, and repair direction. If none remain, say so and disclose untested paths.

---

## Example 5: Adversarial Test Verification (Fox Test Audit Alone)

### Scenario
A pricing change has a green test that only checks `result is not None`. The team wants evidence that the test detects an incorrect member discount, without changing the branch.

### Sample Prompt
```text
/fox-verify Assess whether the pricing tests enforce CONTRACT.md. Establish the passing
baseline, challenge the member-discount behavior with one isolated mutation, report the
exact result and limits, and leave the working tree unchanged.
```

### Agent Workflow with Fox Test Audit
1. **Establish the claim**: State that a member price of 1000 cents must produce 900 cents and confirm the unmodified test passes.
2. **Inspect the evidence path**: Trace the member branch to the test and observe what the assertion can detect.
3. **Challenge safely**: In a disposable copy, replace the discount result with the original price and run only the relevant test.
4. **Report**: If the test still passes, report the surviving mutation and pricing consequence. Do not call it fraud based only on the weak assertion's shape, and do not edit the user's checkout.

---

## Best Practices for Prompting Coding Agents

Coding agents choose skills based on the terminology in user requests:

1. **To trigger Fox**: Use action words related to diagnosis and repair: `investigate root cause`, `fix defect`, `minimal fix`, `reproduce bug`, `verify regressions`.
2. **To trigger Fox Explore**: Use words related to understanding and analysis: `explain architecture`, `walk me through`, `explore alternatives`, `compare implementations`, `advise on trade-offs`.
3. **To trigger Fox Change Review**: Name the review target and use terms such as `review this diff`, `audit the last commit`, `review my PR`, or `pre-merge risk`.
4. **To trigger Fox Test Audit**: Ask to `test the tests`, `run targeted mutation testing`, `challenge this invariant`, or determine whether a green suite detects a named broken behavior. An ordinary request to run tests should not trigger it.
5. **To combine skills**: State the order and authorization boundary, such as read-only exploration, authorized implementation, read-only review, then isolated adversarial verification.

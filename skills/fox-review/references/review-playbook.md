# Fox Change Review playbook

Load this reference when the review target, severity, risk surface, or report format needs more detail.

## Select and bound the target

| Request | Review target | Required context |
| :--- | :--- | :--- |
| Review my work | Uncommitted and staged changes | Working tree diff and repository rules |
| Review the last commit | `HEAD^..HEAD` | Commit message, diff, callers, and tests |
| Review this branch | Merge base through branch head | Base branch, commit range, and changed contracts |
| Review this pull request | PR base and head | PR description, linked requirements, diff, and checks |
| Review these files | Named files and their connected behavior | Callers, callees, tests, and public contracts |

Do not silently broaden a change review into a repository audit. Mention important pre-existing issues only when the target makes them reachable or materially worse.
A change can break code it does not touch, so inspect connected behavior when a contract or data flow changes.

## Review dimensions

Use only dimensions relevant to the change:

- **Correctness:** wrong results, boundary errors, state transitions, partial updates, invalid assumptions.
- **Security and privacy:** trust-boundary validation, authorization, injection, secret or tenant leakage.
- **Reliability:** error paths, retries, idempotency, cancellation, transactions, cleanup, async ordering.
- **Compatibility:** callers, schemas, wire formats, migrations, configuration, supported platforms and versions.
- **Performance:** changed complexity, unbounded work, query count, allocation, blocking, contention under realistic load.
- **Verification:** a missing or weak check that permits a specific material regression.
- **Simplicity:** duplicated behavior, unnecessary dependency, wrapper, abstraction, option, or code that can be removed without losing requirements.

Simplicity comes after correctness and safety. Fewer lines never justify removing validation, error handling, accessibility, or required compatibility.

## Validate before reporting

A valid finding answers all of these:

1. Where is the problem? Give the narrowest path and line or symbol.
2. What execution path reaches it?
3. Which input, state, timing, or environment triggers it?
4. What observable harm follows?
5. Why is this target responsible rather than unrelated existing code?
6. What evidence supports the claim?
7. What focused check or counterexample challenged the claim?
8. What is the smallest repair direction, without implementing it?

Drop a candidate finding when it depends only on taste, an unsupported workload assumption, an imaginary caller, or behavior contradicted by tests or repository policy. If evidence is incomplete but the risk is material, label the finding **unverified** and say what would resolve it.

## Severity

- **Critical:** credible path to severe security breach, irreversible data loss, or widespread outage; blocks release.
- **High:** likely incorrect behavior, authorization failure, data corruption, or major regression on a supported path; blocks merge.
- **Medium:** real defect on a narrower path, significant performance or reliability risk, or missing verification for risky new logic; normally fix before merge.
- **Low:** bounded maintainability or efficiency problem with concrete cost; does not include cosmetic preference.

Severity measures impact and reach, not confidence. Keep confidence separate by using **verified** or **unverified**.

## Checks and counterexamples

Prefer repository-native, read-only checks. Run the smallest relevant test or static command first. Do not modify snapshots, regenerate files, install packages, or use update flags. If a command could write caches or artifacts, use an isolated copy when practical or disclose the limit.

Useful counterexamples include a second tenant with the same numeric ID, zero and omitted values, cancellation during an awaited operation, retry after partial persistence, an old caller using the previous signature, or a clean input that disproves an over-broad warning.

## Report format

```text
Findings

[High] Tenant boundary is omitted — repository.py:18
Evidence: ...
Consequence: ...
Repair direction: ...

No additional verified findings.

Reviewed: <target and base>
Checks: <commands and results, or not run>
Residual risks: <untested paths, missing specification, or none known>
```

Findings come before summaries. Do not add praise, generic best practices, or a score. When no verified findings remain, say **No verified findings** and still disclose review limits.

## Skill boundary

- Use `fox-review` to assess an existing change and report findings without edits.
- Use `fox-explore` for whole-codebase understanding, architecture comparisons, and broad technical research.
- Use `fox` to reproduce a defect, implement the owning-layer repair, and verify regressions.
- When asked to review and then fix, finish the review first and pass only verified findings to `fox`.

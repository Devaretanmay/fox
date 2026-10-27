# Fox Verify adversarial playbook

Load this reference when selecting challenges, interpreting mutation results, or distinguishing a real verification gap from a noisy heuristic.

## Baseline gate

Before an adversarial check:

1. Resolve the exact behavior and test command.
2. Confirm the unmodified target builds and the selected test passes.
3. Confirm the test is not skipped and reaches the relevant behavior. Use existing coverage or test-selection data when available; do not add a coverage dependency.
4. Note nondeterminism, network calls, clocks, shared state, and order dependence. Repeat the baseline when flakiness is plausible.

If the baseline fails, do not call a later failure a killed mutant. Report the original failure separately. If the test never executes the target, classify the challenge as **not covered**, not survived.

## Select a proportionate challenge

Start from the contract, not from every syntactic operator.

| Contract risk | Useful challenge | Evidence expected from a strong test |
| --- | --- | --- |
| Boundary or authorization decision | Invert or remove one condition | Wrongly accepted and wrongly rejected cases fail |
| Returned value or serialization | Replace one meaningful value with empty, null, or a neighboring value | Exact observable output assertion fails |
| Persistence or message emission | Omit one required write or emit | State or event assertion fails |
| Error propagation | Force a dependency error or remove a required raise | Error type, status, rollback, or fallback assertion fails |
| Retry, cleanup, or cancellation | Skip the relevant branch or force partial progress | Count, cleanup, idempotency, or terminal-state assertion fails |

Avoid mutations that violate parsing, typing, imports, or setup before reaching the behavior. Avoid several simultaneous edits because a failure cannot be attributed to one challenge. Do not mutate generated files when source files own the behavior.

## Tool selection and isolation

Use a repository-configured mutation tool when its scope and commands are already documented. Examples include Stryker, PIT, or mutmut, but their presence must be observed in the repository. Preserve the project's configured operators, test runner, exclusions, timeouts, and reports.

Without configured tooling, create a disposable copy or isolated worktree outside the user's working tree. Apply exactly one small edit, run the targeted existing command with a timeout, record the diff and result, then discard the isolation. Do not commit, push, install dependencies, or leave generated mutation state in the repository.

Never advertise a universal speed target. Mutation cost depends on the number of mutants, test selection, process startup, and suite runtime. Prefer a few high-value challenges over an unbounded sweep.

## Interpret outcomes

- **Killed:** the selected test fails because of the challenge. Confirm the failure relates to the invariant rather than unrelated flakiness.
- **Survived:** the selected test passes while the meaningful changed behavior executes.
- **Not covered:** no selected test executes the target.
- **Invalid:** the change cannot build, load, or reach the test. It says nothing about test strength.
- **Timed out:** execution exceeds the chosen limit. Investigate separately; do not automatically count it as a meaningful kill.
- **Blocked:** permissions, unsafe effects, missing tools, or environment failures prevent a valid attempt.

Mutation score is a summary, not a quality verdict. Equivalent mutants, defensive code, generated code, and intentionally unobservable implementation details can survive without revealing a useful missing test. Conversely, one survivor on an authorization or data-integrity invariant can matter more than a high aggregate score.

## Evaluate common “test theater” signals

### Mocks

Trace what is replaced. Mocks at network, clock, randomness, storage, and paid-service boundaries can improve determinism. Report over-mocking only when the mock replaces the production behavior under claim, the assertion merely repeats a configured return, or integration wiring essential to the contract is never exercised.

### Weak assertions

`is not None`, status-only checks, snapshot existence, and call-count assertions can still be useful. Demonstrate weakness with a meaningful wrong result that passes. Recommend the smallest assertion on observable behavior rather than banning an assertion form globally.

### Swallowed errors

Broad catches are sometimes intentional at process, protocol, or user-facing boundaries. Prove that the changed path converts a failure into incorrect success, loses required state, leaks data, or violates a documented fallback before reporting it.

### Duplicate utilities

Name, token, AST, or embedding similarity only creates a candidate. Confirm equivalent purpose, inputs, outputs, error semantics, trust boundary, and supported callers. Distinct policy layers can look structurally identical. Prefer reuse only when contracts actually match.

## Report template

```text
Verdict: Verified verification gap | No verified verification gap | Blocked/inconclusive

Gaps
[Impact] <invariant not enforced> — <path:symbol>
Evidence: baseline <command/result>; challenge <exact edit>; check <command/result>
Consequence: <material behavior that could regress unnoticed>
Direction: <smallest assertion, fixture, or boundary check that would kill it>

Killed challenges
- <challenge> — <test and relevant failure>

Limits
- <unrun paths, invalid/equivalent mutants, missing environment, or none known>
```

Do not repair findings during a read-only verification. If authorized implementation follows, preserve the failing adversarial example as a regression check when practical and route the change through Fox's repair workflow.

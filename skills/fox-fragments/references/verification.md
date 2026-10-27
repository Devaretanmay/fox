# Fragment: focused verification

Read when the task has meaningful regression, compatibility or multi-path risk. Preserve the active task's authorization boundary; verification never permits a review or exploration task to edit.

- Confirm the reproducer fails before repair and passes after, when feasible.
- Check the owning-layer contract and relevant alternate public entry points, callers, failure paths and side effects.
- Test boundaries affected by change: tenant and permission checks, null/empty inputs, errors, retries, concurrency, cancellation, cleanup, migrations and serialization.
- Prefer targeted repository-native commands, then a proportionate existing suite. Do not run an irrelevant test matrix.
- When explicitly asked to challenge test strength, define the observable invariant and run the unmodified baseline first. Prefer a mutation tool already configured by the repository; never install one.
- Otherwise use a temporary detached worktree for committed code or a scoped disposable copy for uncommitted or non-Git code. A worktree at `HEAD` omits local changes. Verify target fidelity, clean up on every exit path, and confirm the original status and target files remain unchanged. Never mutate, stash, reset or clean the user's working tree.
- Classify a challenge as killed, survived, not covered, invalid, timed out or blocked. A survivor proves a gap only when the baseline passed, the test exercised the target, the mutation was meaningful and it was not equivalent behavior.
- Treat mock counts, assertion counts, coverage and structural similarity as signals, not verdicts. Prove that a mock replaces the claimed behavior, a weak assertion accepts a material wrong result, an error is observably swallowed, or a duplicate really shares the same contract.
- During read-only work, do not install packages, update snapshots, regenerate source or use test update flags. Use an isolated copy for checks that write caches or artifacts when practical; otherwise disclose the limit and skip unsafe checks.
- Never state a test ran unless a real tool result confirms it. Report exact commands, outcomes and remaining uncertainty. Keep blocked or partial repairs explicit.
- Instruction-contract and installation tests establish packaging and stated rules, not agent compliance. Behavioral comparisons need matched model, settings, tasks and repeated trials; review accuracy and false positives need independent grading. Use measured structured usage events only; missing metrics stay unknown. Do not claim reliability, token or cost improvements from these checks.

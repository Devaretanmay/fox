# Evaluation results

Date: 27 October 2026

## Deterministic verification

- `python3 -m unittest discover -s tests -v`: 110 tests passed.
- Coverage includes installer compatibility for four supported agents; independent and combined installation of all five packages; optional utilities; reference integrity; activation-label fixtures; review candidate setup; failing repair-fixture validation; and Fox Test Audit's weak/strong mutation controls.
- The verification fixture check establishes a passing baseline in both fixtures, replaces the member discount with the undiscounted price, confirms that this mutation survives the weak non-null suite, and confirms that the strong contract suite kills it.
- The worktree isolation check mutates a detached temporary worktree, removes it, and confirms that the original file bytes and `git status` output remain unchanged.
- A dirty-checkout control confirms that a detached worktree at `HEAD` does not contain uncommitted target changes, preventing false verification of the wrong source state.
- These results verify repository behavior and instruction contracts. They do not demonstrate that an AI agent follows the skills.

## Behavioral comparison

The repair comparison is inconclusive in this environment.

| Agent CLI | Variant attempted | Valid runs | Reason |
| :--- | :--- | ---: | :--- |
| Codex | Baseline | 0/2 | Local app-server initialization failed because its state database was read-only. |
| Claude Code | Baseline | 0/1 | CLI was not logged in. |
| Codex | Review baseline | 0/2 | The same read-only state database prevented both the flawed-change and clean-change runs from starting. |

No Fox-vs-baseline, Fox-Change-Review-vs-baseline, or Fox-Test-Audit-vs-baseline success, false-positive, regression, edit-count, tool-call, or token claim is made. The runner excludes failed agent processes from scored totals. Fox Test Audit has matched weak-suite and strong-suite tasks, but no live agent run was attempted because the previously observed agent-environment blockers remain unresolved. Run `evals/run.py` in an authenticated writable environment with the same model, version, effort, and repeated trials for each variant, then grade read-only outputs blind to the variant.

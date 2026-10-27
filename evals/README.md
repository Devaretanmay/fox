# Fox behavioral evaluations

These evaluations compare the same coding agent with no Fox skill (`baseline`) and with selected Fox skills installed. They measure task success, regression failures, unnecessary edits, elapsed time, and changed files. Exploration, review, and adversarial-verification tasks verify read-only behavior, but reasoning and finding quality require blind human grading against the rubric in `tasks.json`.

Instruction-contract and metadata tests are not behavioral evidence. Do not combine their pass rate with these results.

## Run a comparison

Use an isolated, non-interactive agent command with `{workspace}` and `{prompt}` placeholders. Example for Codex:

```bash
python3 evals/run.py --variant baseline \
  --agent-command 'codex exec --ephemeral --skip-git-repo-check --sandbox workspace-write --cd {workspace} {prompt}' \
  --output baseline.json

python3 evals/run.py --variant fox \
  --agent-command 'codex exec --ephemeral --skip-git-repo-check --sandbox workspace-write --cd {workspace} {prompt}' \
  --output fox.json

python3 evals/run.py --variant fox-review \
  --agent-command 'codex exec --ephemeral --skip-git-repo-check --sandbox workspace-write --cd {workspace} {prompt}' \
  --output fox-review.json

python3 evals/run.py --variant fox-verify \
  --agent-command 'codex exec --ephemeral --skip-git-repo-check --sandbox workspace-write --cd {workspace} {prompt}' \
  --task verify-weak-assertion --task verify-strong-contract \
  --output fox-verify.json
```

Use the same agent model, version, effort, timeout, and task set for each comparison. Run multiple trials because agent behavior is stochastic. Grade exploration, review, and verification outputs without knowing the variant. Include the clean review and strong-test tasks when measuring false-positive findings.

For Fox Change Review benchmarks, compare `baseline` and the stable `fox-review` variant on both `review-tenant-regression` and `review-clean-change`. A no-edit result alone is not proof of a useful review: the flawed task must find the tenant leak, while the clean task must avoid invented findings. For Fox Test Audit, compare `baseline` and the stable `fox-verify` variant on both `verify-weak-assertion` and `verify-strong-contract`: the weak suite should yield a concrete surviving challenge, while the strong suite controls false accusations and overclaiming. The `fox-fragments` variant installs only the compact router and its self-contained references. The `all` variant installs all five packages for compatibility and integration coverage; `both` remains a compatibility alias for the original pair.

The runner reads tool-call and token totals only from JSONL agent events. Add the agent's JSON-output flag when available, such as `codex exec --json`. It leaves unavailable metrics null and never estimates them from prose or terminal lines.

Runs where the agent process exits unsuccessfully are marked `valid_run: false` and excluded from scored totals. A fixture that remains failing after an infrastructure error is not evidence against either variant.

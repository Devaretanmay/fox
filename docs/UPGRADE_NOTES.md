# Fox reliability upgrade notes

Date: 23 October 2026

## Sources and decisions

The upgrade follows the Agent Skills specification plus current Anthropic and OpenAI authoring guidance: discovery depends on precise `name` and `description` metadata; `SKILL.md` should stay concise; deeper guidance belongs in directly linked references; and behavioral evaluations must start from representative tasks and a no-skill baseline.

Ponytail 5 contributed two useful constraints: optimize for the smallest **complete** change, and review connected code rather than only changed lines. Fox adapts these ideas while retaining stronger requirements for reproducible evidence, boundary ownership, counterexamples, explicit uncertainty, and independent read-only review.

Primary sources:

- https://agentskills.io/specification
- https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices
- https://developers.openai.com/plugins/build/skills
- https://developers.openai.com/blog/eval-skills
- https://github.com/DietrichGebert/ponytail/blob/main/skills/ponytail/SKILL.md
- https://github.com/DietrichGebert/ponytail/blob/main/skills/ponytail-review/SKILL.md
- https://stryker-mutator.io/docs/mutation-testing-elements/mutant-states-and-metrics/
- https://mutmut.readthedocs.io/en/latest/
- https://pitest.org/quickstart/basic_concepts/

## Material changes

| Change | Reason | Verification |
| :--- | :--- | :--- |
| Precise positive and negative activation descriptions | Reduce overlap, trivial-edit activation, and unauthorized Explore edits | Metadata tests plus positive, combined, and negative activation fixtures |
| Fox boundary tracing for APIs, databases, native engines, generated code, and async execution | Improve owner identification across common failure boundaries | Instruction contracts and `references/diagnosis.md` link checks |
| Smallest-complete-change repair ladder | Reuse working code and avoid incomplete wrappers or new dependencies | Instruction contracts and `references/repair.md` link checks |
| Fox Explore fact/inference/unknown labels and consistent comparison criteria | Reduce speculative architectural advice | Explore contract tests and architecture-task rubrics |
| Fox Change Review (`fox-review`) added as an independent read-only skill | Reviewing an existing change is a distinct goal from exploring a system or repairing a known defect | Review metadata, boundary, installer, activation, clean-change, and defect-change tests |
| Review findings require mechanism, consequence, evidence, and a counterexample check | Reduce speculative comments and false positives | Review instruction contracts plus behavioral task rubrics |
| Behavioral evaluation runner and fixtures | Separate real agent evidence from instruction-text checks | Repair fixtures must fail before agent work; invalid agent processes are excluded |
| Fox Test Audit (`fox-verify`) adversarial verification skill | Test strength has a distinct read-only target and evidence model from implementation repair or general change review | Metadata and isolation contracts; weak and strong mutation fixtures; standalone and combined installer coverage |
| Mutation outcome and false-positive controls | Established tools distinguish killed, survived, uncovered, invalid and timed-out mutants; a survivor or heuristic alone is not proof of “test theater” | Instruction contracts require baseline, target execution, semantic relevance and equivalent-mutant checks |

## Verification status

All deterministic tests pass. The live agent comparison is inconclusive because the available Codex CLI could not initialize its local state and Claude Code was not authenticated. See [`evals/RESULTS.md`](../evals/RESULTS.md). No reliability improvement is claimed until valid repeated baseline and Fox runs are collected.

## October 24: Fox Change Review

Fox Change Review is the third independently installable capability because change assessment has a different authorization boundary and output from exploration or repair. It is read-only, reports only evidence-backed findings, permits a clean “no findings” result, and hands authorized repairs to Fox. Its stable install ID remains `fox-review`. The benchmark includes both a tenant-isolation regression and a clean change to measure missed defects and false positives.

## October 27: Fox Test Audit

Fox Test Audit turns the useful core of the VERICODE proposal into an honest agent skill. Its stable install ID remains `fox-verify`. It does not claim to be a language-independent mutation engine or a deterministic pre-commit gate. It uses mutation tooling only when the repository already configures it; otherwise it performs a few contract-relevant challenges in an isolated copy. Mock ratio, assertion count, coverage, broad catches and structural similarity remain investigation signals rather than automatic failures.

The behavioral manifest pairs a weak assertion fixture with a strong-suite control. Deterministic fixture tests prove that the same member-discount mutation survives the weak suite and is killed by the strong suite. This validates the benchmark mechanism, not agent reliability; matched repeated baseline and Fox Test Audit runs still require an authenticated agent environment and blind grading.

## October 27: Public naming

The technical IDs remain stable to preserve documented commands and existing automation. Public documentation now uses **Fox Change Review** for `fox-review` and **Fox Test Audit** for `fox-verify`. The first name identifies the review target; the second distinguishes test-strength assessment from an ordinary verification run. **Fox Explore**, **Fox**, and **Fox Fragments** remain unchanged because their names already match their roles.

The isolation workflow now distinguishes committed, uncommitted and non-Git targets. It prefers detached worktrees for committed code, avoids full copies of large repositories, requires fidelity checks for local changes and scoped copies, guarantees cleanup across failure paths, and checks that the original checkout remains unchanged. A deterministic worktree test mutates an isolated file, removes the worktree, and confirms the source checkout's bytes and status are unchanged.

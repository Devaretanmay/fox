# Fox

**Better fixes. Clear exploration. Verified reviews. Stronger evidence.**

Fox is a suite of five independent Agent Skills for AI coding assistants (Google Antigravity, Claude Code, Cursor, and OpenAI Codex):

- **Fox**: Fix what's broken (root-cause debugging and verified repairs).
- **Fox Explore**: Understand your code (architecture, research, and recommendations).
- **Fox Review**: Audit an existing change (correctness, risk, tests, and unnecessary complexity).
- **Fox Verify**: Challenge whether tests and verification evidence detect meaningful broken behavior.
- **Fox Fragments**: Route each task to short, self-contained instruction fragments without loading the complete specialist skills.

Each skill works alone. Install one, any combination, or all five.

---

## Choose Your Skill

| Skill | What It Does | When to Choose It |
| :--- | :--- | :--- |
| **Fox** | **Fix what's broken.**<br>Investigates bugs, identifies root causes, applies focused repairs, and verifies results. | You have a bug to fix, an unexpected test failure, or code to debug. |
| **Fox Explore** | **Understand your code. Explore what's possible.**<br>Explains unfamiliar code, researches external open-source alternatives, compares architectures, and advises on trade-offs. | You are onboarding to a repository, evaluating an architectural choice, or researching technical options. |
| **Fox Review** | **Audit what changed.**<br>Reviews a diff, commit, branch, pull request, or named files for verified defects and regression risks without editing code. | You need an independent pre-merge review of an existing change. |
| **Fox Verify** | **Test the tests.**<br>Defines observable invariants and uses configured mutation tools or isolated, targeted challenges to expose verification gaps. | A green suite may rely on weak assertions, over-mocking, or untested failure paths. |
| **Fox Fragments** | **Load only what is needed.**<br>Maps a request to short repair, boundary, exploration, review and verification fragments. | You want minimal Fox guidance for each task without reading the full specialist skills. |
| **All five** | **Understand, repair, review, and challenge the evidence.**<br>Each skill keeps its own boundary and can hand work to the next capability when authorized. | You want the complete engineering suite. |

---

## Get Started

### 1. Install to Your Project

Run the installer inside your project directory. It requires only standard Python (version 3.10 or newer) with zero external dependencies.

#### Interactive Setup (Recommended)
Run the wizard in your terminal to select your coding agent and skills:
```bash
python3 install.py
```

#### One-Line Command
Or specify your agent and skill directly:

```bash
# Google Antigravity or OpenAI Codex (installs to .agents/skills)
python3 install.py --agent antigravity --skill all

# Anthropic Claude Code (installs to .claude/skills)
python3 install.py --agent claude --skill all

# Cursor (installs to .cursor/skills)
python3 install.py --agent cursor --skill all
```

#### Install Specific Skills
```bash
# Install only Fox
python3 install.py --agent antigravity --skill fox

# Install only Fox Explore
python3 install.py --agent antigravity --skill fox-explore

# Install only Fox Review
python3 install.py --agent antigravity --skill fox-review

# Install only Fox Verify
python3 install.py --agent antigravity --skill fox-verify

# Install only Fox Fragments
python3 install.py --agent antigravity --skill fox-fragments

# Install a selected combination
python3 install.py --agent antigravity --skill fox,fox-review
```

The legacy `--skill both` alias still installs the original `fox` and `fox-explore` pair. Use `--skill all` for all five skills. To avoid loading full specialist skills, install only `fox-fragments`.

---

## Your First Task

Once installed, start a new chat in your AI coding agent and try one of these beginner-friendly examples:

### If You Installed Fox
> "Investigate why this function returns the wrong result. Find the cause, fix it, and verify the change."

### If You Installed Fox Explore
> "Explain this repository to someone seeing it for the first time. Walk me through the request flow and explain what you would improve and what you would leave alone."

### If You Installed Fox Review
> "Review the last commit against its requirements. Report only verified correctness, security, regression, test, performance, or complexity findings. Do not edit files."

### If You Installed Fox Verify
> "Challenge whether these tests detect a broken tenant guard. Use configured tooling or isolated targeted mutations, report exact results, and leave the working tree unchanged."

### If You Installed Fox Fragments
> "Use Fox Fragments to select only the instructions needed to diagnose this API failure."

### If You Installed All Five
> "Explore the caching design, implement the authorized repair with Fox, review the final diff, then use Fox Verify to challenge whether the regression tests detect broken behavior."

### How to Confirm It Loaded
- **Fox**: Your agent writes a reproduction test first, traces execution to the owning component, applies a minimal fix, and runs verification checks.
- **Fox Explore**: Your agent answers directly, grounds local explanations in real repository paths, separates facts from inferences, and provides practical recommendations without editing code.
- **Fox Review**: Your agent identifies the exact target, reads connected code, validates each finding, and leaves the repository unchanged.
- **Fox Verify**: Your agent defines an observable invariant, establishes a clean baseline, challenges it in isolation, distinguishes killed and survived mutations from invalid or uncovered ones, and leaves the working tree unchanged.

If your agent does not recognize a skill, restart the chat session or tell the agent:
`Use instructions in .agents/skills/fox/SKILL.md`. See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for more tips.

---

## Real Example

Consider a shared authentication header parser in a web framework:

```python
# A client sends a parameterless challenge
wa = WWWAuthenticate("bearer")
header = wa.to_header()
```

- **The bug**: `to_header()` returns `'Bearer '` with an illegal trailing space. Downstream HTTP parsers reject the request.
- **With Fox Explore**: The agent explains the header specification RFC, compares the framework's token validation with standard libraries (such as `PyJWT` or `authlib`), and advises on backward compatibility trade-offs before changes are made.
- **With Fox**: The agent traces execution to the owning serializer (`auth.py`), fixes formatting at the source, and ensures that `from_header("Bearer") == WWWAuthenticate("bearer")` holds true in both directions.
- **With Fox Review**: The agent audits the resulting diff, callers, and tests; reports only reproducible risks; and makes no edits.
- **With Fox Verify**: The agent challenges whether the tests fail when serialization produces the wrong header and reports the exact killed or surviving mutation without changing the checkout.

For step-by-step walkthroughs of real defects and architectural reviews, see the [Adoption Guide](examples/ADOPTION_GUIDE.md).

---

## How It Works

### Plain English Concepts
- **Root cause**: The underlying reason something went wrong, rather than just the symptom you noticed.
- **Regression**: Something that worked before but breaks after an edit.
- **Grounding**: Proving claims using concrete repository files or primary documentation instead of guessing.

### Fox Lifecycle
Fox guides your agent through four simple steps:
1. **Ground**: Inspect the code and build the smallest test that demonstrates the problem before touching production files.
2. **Trace**: Follow the input step-by-step through execution until finding the component that actually owns the behavior.
3. **Repair**: Make the smallest complete change at the owning layer and update every affected caller or contract.
4. **Verify**: Re-run the reproducer, test a counterexample, run proportionate regressions, and inspect the final diff.

### Fox Explore Lifecycle
Fox Explore provides read-only codebase understanding and technical research:
1. **Scope**: Define the question, decision, constraints, and required evidence.
2. **Map**: Trace the smallest repository and execution flow needed to answer it.
3. **Compare**: Evaluate the current design, no change, and viable alternatives against consistent criteria.
4. **Report**: Lead with the answer, cite evidence, separate observed facts from inferences and unknowns, and state what to retain.

### Fox Review Lifecycle
Fox Review audits an existing change without modifying it:
1. **Set the target**: Resolve the exact diff, base, requirements, and repository rules.
2. **Trace the change**: Read connected callers, callees, tests, configuration, and contracts.
3. **Validate findings**: Prove the failure mechanism, consequence, and counterexample before reporting it.
4. **Report**: Order actionable findings by impact, disclose checks and limits, or state that no verified findings exist.

### Fox Verify Lifecycle
Fox Verify evaluates verification evidence without editing the working tree:
1. **Establish the claim**: Resolve the behavior, observable invariant, target, and passing baseline.
2. **Inspect the evidence path**: Trace production behavior into the tests, assertions, mocks, and failure paths that should observe it.
3. **Challenge safely**: Use existing mutation tooling or one contract-relevant mutation at a time in an isolated copy.
4. **Report**: Distinguish killed, survived, uncovered, invalid, timed-out, and blocked challenges; report only proven gaps and limits.

## Advanced Setup

### Global Installation (Antigravity)
To make skills available across all projects on your machine for Google Antigravity:
```bash
python3 install.py --agent antigravity --skill all --global
```
This installs skills to `~/.gemini/config/skills`.

### Non-Interactive CLI Automation
The installer supports automation flags for CI or setup scripts:
```bash
# Preview what would be installed without writing files
python3 install.py --agent antigravity --skill all --dry-run

# Safely replace an existing installation
python3 install.py --agent antigravity --skill all --force --project /path/to/project
```

### Advanced Fox Verification Utilities
Fox includes an optional evidence ledger (`proof.py`) located in `skills/fox/scripts/`:
```bash
# Verify your local environment
python3 skills/fox/scripts/proof.py doctor

# Initialize an evidence case
python3 skills/fox/scripts/proof.py init --out cases/auth --question "Why does token refresh fail?" --target src/auth --intent build

# Record an observed code claim
python3 skills/fox/scripts/proof.py claim --statement "Token validation fails due to 2-second client clock skew" --evidence E001 --confidence observed --locator token.py:22 --alternative "Token is genuinely expired on server" --falsifier "Test validation with simulated clock skew" cases/auth

# Record an architecture decision
python3 skills/fox/scripts/proof.py decision --choose "Add 5-second clock skew tolerance window" --instead-of "Bypass expiration check completely" "Force user re-authentication" --why "Minimal standard-compliant fix with zero breaking API changes" --claims C001 --reversible --revisit-when "Auth specification deprecates skew window" cases/auth

# Check case validity and export report
python3 skills/fox/scripts/proof.py check cases/auth
python3 skills/fox/scripts/proof.py report cases/auth
```

---

## Troubleshooting & Limitations

- **Skill guidance, not hard constraints**: Skills provide structured reasoning instructions for AI agents. They improve agent consistency, but cannot intercept models that ignore instructions.
- **Read-only exploration**: Fox Explore is read-only by default and will not modify repository files or scaffold architectures unless explicitly requested.
- **Read-only review**: Fox Review reports findings but never edits, commits, pushes, approves, merges, or posts review comments.
- **Read-only adversarial verification**: Fox Verify may mutate a disposable copy, never the user's working tree. It does not install mutation tools and does not equate a survivor, mock count, or coverage percentage with fraud.
- **Behavioral evidence is separate**: Metadata and instruction-contract tests check packaging, not agent reliability. See [behavioral evaluations](evals/README.md) for controlled baseline comparisons.
- **Current evaluation status**: See [evaluation results](evals/RESULTS.md). Invalid agent runs are excluded rather than counted as failures.

For common errors, reinstallation fixes, and agent setup tips, see [TROUBLESHOOTING.md](TROUBLESHOOTING.md).
For the source-backed rationale behind the current instruction and evaluation design, see [upgrade notes](docs/UPGRADE_NOTES.md).

---

## Contributing & License

Contributions, defect reports, and discussions are welcome. Please open an issue or pull request on GitHub:
https://github.com/Devaretanmay/fox

Distributed under the MIT License. See [LICENSE](LICENSE) for details.

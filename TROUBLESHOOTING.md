# Troubleshooting Fox skills

This guide helps you resolve common issues when installing or using any of the five Fox skills.

---

## 1. My Coding Agent Does Not Recognize the Skill

### Symptom
You type `/fox`, `/fox-explore`, `/fox-review`, `/fox-verify`, or `/fox-fragments`, or prompt your agent, but it responds as if the skill is not installed.

### Solutions
1. **Restart your coding agent**:
   Most coding agents (including Claude Code, Cursor, Codex, and Antigravity) only scan their skills folder when a session starts. Close and re-open the chat window or restart the agent process.
2. **Verify installation location**:
   Check that the skill exists in your project workspace:
   - **Google Antigravity / OpenAI Codex**: `.agents/skills/<skill-name>`
   - **Claude Code**: `.claude/skills/<skill-name>`
   - **Cursor**: `.cursor/skills/<skill-name>`

   Valid skill names are `fox`, `fox-explore`, `fox-review`, `fox-verify`, and `fox-fragments`.
3. **Explicitly reference the skill file**:
   If your agent UI does not support slash commands, simply paste your task prompt along with:
   ```text
   Use the instructions in .agents/skills/fox/SKILL.md to investigate this issue.
   ```

---

## 2. Re-installing or Updating a Skill Fails

### Symptom
Running `install.py` prints:
`ERROR: ... already exists; pass --force to replace`

### Solution
Pass `--force` to safely overwrite an existing installation:
```bash
python3 install.py --agent antigravity --skill all --force
```
In interactive mode (`python3 install.py`), the installer will automatically detect existing files and prompt you before replacing them.

---

## 3. Permission Denied During Installation

### Symptom
The installer reports permission errors when writing to the project or global directory.

### Solutions
- Ensure you have write permissions to the project directory:
  ```bash
  chmod -R u+w .agents/
  ```
- For global installation on Google Antigravity, ensure your user owns `~/.gemini/config/skills`:
  ```bash
  mkdir -p ~/.gemini/config/skills
  ```

---

## 4. How to Confirm the Skill is Active

Ask your agent to solve a bug or explore code. Look for these signs in its response:

- **Fox**: The agent grounds the problem first, writes a reproducer, traces to the owning layer, applies a minimal fix, and verifies counterexamples.
- **Fox Explore**: The agent provides grounded answers citing specific file paths, separates facts from inference, and advises on trade-offs without editing code.
- **Fox Review**: The agent resolves a diff or commit target, traces connected behavior, reports evidence-backed findings first, and does not change files.
- **Fox Verify**: The agent states an observable invariant, establishes a passing baseline, performs challenges only in isolation, classifies each outcome, and reports limits without changing the working tree.

If Fox Review starts repairing code, stop the run and invoke it explicitly with: `Use fox-review in read-only mode. Report findings only.` Use `fox` separately when you authorize repairs.

If Fox Verify edits the working tree, stop the run and invoke it with: `Use fox-verify. Perform any mutation only in a disposable copy and leave this checkout unchanged.` If no safe isolation is available, it should report the check as blocked instead of mutating in place.

If you need further help, open an issue at:
https://github.com/Devaretanmay/fox/issues

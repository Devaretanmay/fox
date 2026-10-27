"""Tests for independent Fox skill installation, onboarding, and documentation integrity."""
from __future__ import annotations

import io
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import install  # noqa: E402


class InstallerOnboardingTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.project_dir = Path(self.tmp.name) / "my_project"
        self.project_dir.mkdir(parents=True, exist_ok=True)

    def test_fresh_installation_fox_alone(self):
        dests = install.install(
            agent="antigravity",
            project=self.project_dir,
            skill="fox",
        )
        self.assertEqual(len(dests), 1)
        self.assertTrue((self.project_dir / ".agents/skills/fox/SKILL.md").is_file())
        self.assertFalse((self.project_dir / ".agents/skills/fox-explore").exists())
        self.assertFalse((self.project_dir / ".agents/skills/fox-review").exists())

    def test_fresh_installation_fox_explore_alone(self):
        dests = install.install(
            agent="claude",
            project=self.project_dir,
            skill="fox-explore",
        )
        self.assertEqual(len(dests), 1)
        self.assertTrue((self.project_dir / ".claude/skills/fox-explore/SKILL.md").is_file())
        self.assertFalse((self.project_dir / ".claude/skills/fox").exists())
        self.assertFalse((self.project_dir / ".claude/skills/fox-review").exists())

    def test_fresh_installation_fox_review_alone(self):
        dests = install.install(
            agent="codex",
            project=self.project_dir,
            skill="fox-review",
        )
        self.assertEqual(len(dests), 1)
        self.assertTrue((self.project_dir / ".agents/skills/fox-review/SKILL.md").is_file())
        self.assertFalse((self.project_dir / ".agents/skills/fox").exists())
        self.assertFalse((self.project_dir / ".agents/skills/fox-explore").exists())

    def test_fresh_installation_fox_verify_alone(self):
        dests = install.install(
            agent="codex",
            project=self.project_dir,
            skill="fox-verify",
        )
        self.assertEqual(len(dests), 1)
        self.assertTrue((self.project_dir / ".agents/skills/fox-verify/SKILL.md").is_file())
        self.assertFalse((self.project_dir / ".agents/skills/fox").exists())
        self.assertFalse((self.project_dir / ".agents/skills/fox-review").exists())

    def test_interactive_verify_numeric_selection(self):
        inputs = iter(["1", "6", "1", str(self.project_dir)])
        with patch("builtins.input", lambda *args: next(inputs)), \
             patch.object(sys.stdin, "isatty", return_value=True), \
             patch.object(sys.stdout, "isatty", return_value=True):
            ret = install.main(["--interactive"])
            self.assertEqual(ret, 0)
            self.assertTrue((self.project_dir / ".agents/skills/fox-verify/SKILL.md").is_file())
            self.assertFalse((self.project_dir / ".agents/skills/fox").exists())

    def test_interactive_review_numeric_combination(self):
        inputs = iter(["1", "1,3", "1", str(self.project_dir)])
        with patch("builtins.input", lambda *args: next(inputs)), \
             patch.object(sys.stdin, "isatty", return_value=True), \
             patch.object(sys.stdout, "isatty", return_value=True):
            ret = install.main(["--interactive"])
            self.assertEqual(ret, 0)
            self.assertTrue((self.project_dir / ".agents/skills/fox/SKILL.md").is_file())
            self.assertTrue((self.project_dir / ".agents/skills/fox-review/SKILL.md").is_file())
            self.assertFalse((self.project_dir / ".agents/skills/fox-explore").exists())

    def test_fresh_installation_all_skills(self):
        dests = install.install(
            agent="cursor",
            project=self.project_dir,
            skill="all",
        )
        self.assertEqual(len(dests), 5)
        self.assertTrue((self.project_dir / ".cursor/skills/fox/SKILL.md").is_file())
        self.assertTrue((self.project_dir / ".cursor/skills/fox-explore/SKILL.md").is_file())
        self.assertTrue((self.project_dir / ".cursor/skills/fox-review/SKILL.md").is_file())
        self.assertTrue((self.project_dir / ".cursor/skills/fox-verify/SKILL.md").is_file())
        self.assertTrue((self.project_dir / ".cursor/skills/fox-fragments/SKILL.md").is_file())

    def test_fresh_installation_skill_combination(self):
        dests = install.install(
            agent="claude",
            project=self.project_dir,
            skill="fox,fox-review",
        )
        self.assertEqual(len(dests), 2)
        self.assertTrue((self.project_dir / ".claude/skills/fox/SKILL.md").is_file())
        self.assertTrue((self.project_dir / ".claude/skills/fox-review/SKILL.md").is_file())
        self.assertFalse((self.project_dir / ".claude/skills/fox-explore").exists())

    def test_legacy_both_alias_keeps_original_pair(self):
        dests = install.install(agent="claude", project=self.project_dir, skill="both")
        self.assertEqual({path.name for path in dests}, {"fox", "fox-explore"})
        self.assertFalse((self.project_dir / ".claude/skills/fox-review").exists())

    def test_reinstallation_without_force_fails(self):
        install.install(agent="codex", project=self.project_dir, skill="fox")
        with self.assertRaises(FileExistsError) as ctx:
            install.install(agent="codex", project=self.project_dir, skill="fox", force=False)
        self.assertIn("already exists", str(ctx.exception))
        self.assertIn("--force", str(ctx.exception))

    def test_forced_replacement_succeeds(self):
        install.install(agent="codex", project=self.project_dir, skill="fox")
        marker = self.project_dir / ".agents/skills/fox/custom_marker.txt"
        marker.write_text("old version", encoding="utf-8")

        dests = install.install(
            agent="codex",
            project=self.project_dir,
            skill="fox",
            force=True,
        )
        self.assertEqual(len(dests), 1)
        self.assertTrue((self.project_dir / ".agents/skills/fox/SKILL.md").is_file())
        self.assertFalse(marker.exists(), "Force reinstall must replace existing directory cleanly")

    def test_dry_run_does_not_modify_filesystem(self):
        dests = install.install(
            agent="antigravity",
            project=self.project_dir,
            skill="all",
            dry_run=True,
        )
        self.assertEqual(len(dests), 5)
        self.assertFalse((self.project_dir / ".agents").exists())

    def test_non_interactive_without_agent_in_headless_raises_error(self):
        # When stdin is not a tty, missing --agent exits with status 2
        with patch.object(sys.stdin, "isatty", return_value=False), \
             patch.object(sys.stdout, "isatty", return_value=False):
            with self.assertRaises(SystemExit) as ctx:
                install.main([])
            self.assertEqual(ctx.exception.code, 2)

    def test_interactive_wizard_successful_flow(self):
        # Simulate: Agent 1 (antigravity), Skill 4 (all), Scope 1 (project), Project default
        inputs = iter(["1", "5", "1", str(self.project_dir)])
        with patch("builtins.input", lambda *args: next(inputs)), \
             patch.object(sys.stdin, "isatty", return_value=True), \
             patch.object(sys.stdout, "isatty", return_value=True):
            ret = install.main(["--interactive"])
            self.assertEqual(ret, 0)
            self.assertTrue((self.project_dir / ".agents/skills/fox/SKILL.md").is_file())
            self.assertTrue((self.project_dir / ".agents/skills/fox-explore/SKILL.md").is_file())
            self.assertTrue((self.project_dir / ".agents/skills/fox-review/SKILL.md").is_file())

    def test_interactive_wizard_abort_on_existing_without_force(self):
        # Pre-install fox
        install.install(agent="claude", project=self.project_dir, skill="fox")
        # Simulate: Agent 2 (claude), Skill 1 (fox), Project path, "n" to replace
        inputs = iter(["2", "1", str(self.project_dir), "n"])
        with patch("builtins.input", lambda *args: next(inputs)), \
             patch.object(sys.stdin, "isatty", return_value=True), \
             patch.object(sys.stdout, "isatty", return_value=True):
            ret = install.main(["--interactive"])
            self.assertEqual(ret, 0)

    def test_interactive_wizard_replace_on_existing_with_force(self):
        install.install(agent="cursor", project=self.project_dir, skill="fox")
        # Simulate: Agent 3 (cursor), Skill 1 (fox), Project path, "y" to replace
        inputs = iter(["3", "1", str(self.project_dir), "y"])
        with patch("builtins.input", lambda *args: next(inputs)), \
             patch.object(sys.stdin, "isatty", return_value=True), \
             patch.object(sys.stdout, "isatty", return_value=True):
            ret = install.main(["--interactive"])
            self.assertEqual(ret, 0)
            self.assertTrue((self.project_dir / ".cursor/skills/fox/SKILL.md").is_file())

    def test_all_supported_agent_paths(self):
        agents = {
            "codex": ".agents/skills",
            "claude": ".claude/skills",
            "cursor": ".cursor/skills",
            "antigravity": ".agents/skills",
        }
        for agent, expected_rel in agents.items():
            proj = self.project_dir / agent
            proj.mkdir(parents=True, exist_ok=True)
            dests = install.install(agent, proj, skill="fox")
            self.assertEqual(dests[0], (proj / expected_rel / "fox").resolve())

    def test_helpful_error_messages(self):
        with self.assertRaises(ValueError) as ctx_agent:
            install.install("unknown-agent", self.project_dir)
        self.assertIn("Unknown agent 'unknown-agent'", str(ctx_agent.exception))

        with self.assertRaises(ValueError) as ctx_skill:
            install.install("antigravity", self.project_dir, skill="bad-skill")
        self.assertIn("Unknown skill 'bad-skill'", str(ctx_skill.exception))

        with self.assertRaises(ValueError) as ctx_dir:
            install.install("antigravity", self.project_dir / "nonexistent-dir")
        self.assertIn("Project directory must exist", str(ctx_dir.exception))

    def test_all_markdown_relative_links_resolve(self):
        # Scan README.md, TROUBLESHOOTING.md, ADOPTION_GUIDE.md, and SKILL.md files for broken relative links
        md_files = [
            ROOT / "README.md",
            ROOT / "TROUBLESHOOTING.md",
            ROOT / "examples/ADOPTION_GUIDE.md",
            ROOT / "docs/UPGRADE_NOTES.md",
            ROOT / "evals/README.md",
            ROOT / "evals/RESULTS.md",
            ROOT / "examples/1-fox-alone-localized-defect/README.md",
            ROOT / "examples/2-fox-explore-architecture-review/README.md",
            ROOT / "examples/3-combined-explore-and-repair/README.md",
            ROOT / "skills/fox/SKILL.md",
            ROOT / "skills/fox-explore/SKILL.md",
            ROOT / "skills/fox-explore/references/research-playbook.md",
            ROOT / "skills/fox-review/SKILL.md",
            ROOT / "skills/fox-verify/SKILL.md",
            ROOT / "skills/fox-verify/references/adversarial-playbook.md",
            ROOT / "skills/fox-fragments/SKILL.md",
            ROOT / "skills/fox-review/references/review-playbook.md",
            ROOT / "skills/fox/references/diagnosis.md",
            ROOT / "skills/fox/references/repair.md",
        ]
        link_regex = re.compile(r'\[([^\]]+)\]\(([^)]+)\)')

        for md_path in md_files:
            if not md_path.is_file():
                continue
            content = md_path.read_text(encoding="utf-8")
            for match in link_regex.finditer(content):
                label, url = match.groups()
                # Skip external links and web schemas
                if url.startswith(("http://", "https://", "mailto:", "#")):
                    continue
                # Handle file anchors like path#section
                clean_path = url.split("#")[0]
                if not clean_path:
                    continue
                # Resolve relative path from md_path.parent
                resolved = (md_path.parent / clean_path).resolve()
                self.assertTrue(
                    resolved.exists(),
                    f"Broken link in {md_path.relative_to(ROOT)}: '{url}' -> '{resolved}' does not exist",
                )


if __name__ == "__main__":
    unittest.main()

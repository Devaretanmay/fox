"""Packaging and instruction contracts for Fox Verify, not agent-reliability evidence."""
from __future__ import annotations

import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = ROOT / "skills/fox-verify"
SKILL_MD = SKILL_DIR / "SKILL.md"


class FoxVerifyMetadataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.content = SKILL_MD.read_text(encoding="utf-8")
        cls.frontmatter = cls.content.split("---\n", 2)[1]
        cls.body = cls.content.split("---\n", 2)[2]

    def test_frontmatter_and_activation_boundaries(self):
        self.assertIn("name: fox-verify", self.frontmatter)
        self.assertIn('version: "0.1.1"', self.frontmatter)
        description = next(
            line for line in self.frontmatter.splitlines() if line.startswith("description:")
        ).lower()
        self.assertIn("use when", description)
        self.assertIn("do not use", description)
        self.assertIn("mutation testing", description)
        self.assertIn("ordinary test run", description)

    def test_primary_instructions_are_concise(self):
        self.assertLessEqual(len(self.body.split()), 500)

    def test_reference_links_resolve(self):
        links = re.findall(r"\]\((references/[^)]+)\)", self.body)
        self.assertEqual(links, ["references/adversarial-playbook.md"])
        self.assertTrue((SKILL_DIR / links[0]).is_file())

    def test_has_no_custom_runtime_or_dependency(self):
        self.assertFalse((SKILL_DIR / "scripts").exists())
        self.assertFalse((ROOT / "skills/fox-verify/requirements.txt").exists())


class FoxVerifyContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = (SKILL_MD.read_text(encoding="utf-8") + "\n" +
                    (SKILL_DIR / "references/adversarial-playbook.md").read_text(encoding="utf-8"))

    def test_requires_baseline_and_observable_invariant(self):
        self.assertIn("Run the narrow baseline check first", self.text)
        self.assertIn("observable invariants", self.text)

    def test_mutates_only_in_isolation(self):
        self.assertIn("Never mutate the user's working tree", self.text)
        self.assertIn("one behavior at a time", self.text)
        self.assertIn("Do not install packages", self.text)
        self.assertIn("git worktree add --detach", self.text)
        self.assertIn("omits staged, unstaged, and untracked changes", self.text)
        self.assertIn("do not make a whole-tree copy", self.text)
        self.assertIn("working-tree contamination", self.text)
        self.assertIn("success, failure, interruption, or timeout", self.text)

    def test_distinguishes_result_states_and_false_positives(self):
        for state in ("killed", "survived", "not covered", "invalid", "timed out", "blocked"):
            self.assertIn(f"**{state}**", self.text.lower())
        self.assertIn("Equivalent mutants", self.text)
        self.assertIn("signals, never verdicts", self.text)

    def test_preserves_read_only_boundary_and_handoff(self):
        self.assertIn("Remain read-only", self.text)
        self.assertIn("hand only verified gaps to `fox`", self.text)


class FoxVerifyEvaluationFixtureTests(unittest.TestCase):
    def test_detached_worktree_mutation_preserves_original_checkout(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repository = root / "repository"
            isolated = root / "isolated-worktree"
            repository.mkdir()
            subprocess.run(["git", "init", "-q"], cwd=repository, check=True)
            target = repository / "pricing.py"
            target.write_text("def price():\n    return 900\n", encoding="utf-8")
            subprocess.run(["git", "add", "pricing.py"], cwd=repository, check=True)
            subprocess.run(
                [
                    "git", "-c", "user.name=Fox Verify Test",
                    "-c", "user.email=verify@example.invalid",
                    "commit", "-qm", "baseline",
                ],
                cwd=repository,
                check=True,
            )
            original = target.read_bytes()
            status_before = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=repository,
                capture_output=True,
                text=True,
                check=True,
            ).stdout

            subprocess.run(
                ["git", "worktree", "add", "--detach", "--", str(isolated), "HEAD"],
                cwd=repository,
                capture_output=True,
                text=True,
                check=True,
            )
            registered = subprocess.run(
                ["git", "worktree", "list", "--porcelain"],
                cwd=repository,
                capture_output=True,
                text=True,
                check=True,
            ).stdout
            self.assertIn(f"worktree {isolated}", registered)
            (isolated / "pricing.py").write_text(
                "def price():\n    return 1000\n", encoding="utf-8"
            )
            subprocess.run(
                ["git", "worktree", "remove", "--force", "--", str(isolated)],
                cwd=repository,
                capture_output=True,
                text=True,
                check=True,
            )

            status_after = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=repository,
                capture_output=True,
                text=True,
                check=True,
            ).stdout
            self.assertEqual(target.read_bytes(), original)
            self.assertEqual(status_after, status_before)
            self.assertFalse(isolated.exists())

    def test_detached_head_worktree_omits_uncommitted_target_changes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repository = root / "repository"
            isolated = root / "isolated-worktree"
            repository.mkdir()
            subprocess.run(["git", "init", "-q"], cwd=repository, check=True)
            target = repository / "pricing.py"
            committed = "def price():\n    return 900\n"
            uncommitted = "def price():\n    return 850\n"
            target.write_text(committed, encoding="utf-8")
            subprocess.run(["git", "add", "pricing.py"], cwd=repository, check=True)
            subprocess.run(
                [
                    "git", "-c", "user.name=Fox Verify Test",
                    "-c", "user.email=verify@example.invalid",
                    "commit", "-qm", "baseline",
                ],
                cwd=repository,
                check=True,
            )
            target.write_text(uncommitted, encoding="utf-8")

            subprocess.run(
                ["git", "worktree", "add", "--detach", "--", str(isolated), "HEAD"],
                cwd=repository,
                capture_output=True,
                text=True,
                check=True,
            )
            self.assertEqual((isolated / "pricing.py").read_text(encoding="utf-8"), committed)
            self.assertEqual(target.read_text(encoding="utf-8"), uncommitted)
            subprocess.run(
                ["git", "worktree", "remove", "--force", "--", str(isolated)],
                cwd=repository,
                capture_output=True,
                text=True,
                check=True,
            )

    def test_member_discount_mutation_survives_weak_suite_and_is_killed_by_strong_suite(self):
        for fixture_name, expected_success in (("verify-weak", True), ("verify-strong", False)):
            with self.subTest(fixture=fixture_name), tempfile.TemporaryDirectory() as tmp:
                source = ROOT / "evals/fixtures" / fixture_name
                workspace = Path(tmp) / fixture_name
                shutil.copytree(source, workspace)

                baseline = subprocess.run(
                    [sys.executable, "-m", "unittest", "-v"],
                    cwd=workspace,
                    capture_output=True,
                    text=True,
                )
                self.assertEqual(baseline.returncode, 0, baseline.stdout + baseline.stderr)

                target = workspace / "pricing.py"
                original = target.read_text(encoding="utf-8")
                target.write_text(
                    original.replace("return cents * 90 // 100", "return cents"),
                    encoding="utf-8",
                )
                mutated = subprocess.run(
                    [sys.executable, "-m", "unittest", "-v"],
                    cwd=workspace,
                    capture_output=True,
                    text=True,
                )
                self.assertEqual(mutated.returncode == 0, expected_success)


if __name__ == "__main__":
    unittest.main()

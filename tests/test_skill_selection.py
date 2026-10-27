"""Tests for skill independence and deterministic activation contracts."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import install  # noqa: E402
from evals.run import extract_metrics  # noqa: E402


class SkillIndependenceInstallationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.project = Path(self.tmp.name)

    def test_each_skill_installs_alone_across_supported_agents(self):
        targets = {
            "antigravity": ".agents/skills",
            "codex": ".agents/skills",
            "claude": ".claude/skills",
            "cursor": ".cursor/skills",
        }
        for agent, target in targets.items():
            for selected in install.AVAILABLE_SKILLS:
                workspace = self.project / f"{agent}-{selected}"
                workspace.mkdir()
                destinations = install.install(agent, workspace, skill=selected)
                self.assertEqual(destinations, [(workspace / target / selected).resolve()])
                self.assertTrue((destinations[0] / "SKILL.md").is_file())
                for absent in set(install.AVAILABLE_SKILLS) - {selected}:
                    self.assertFalse((destinations[0].parent / absent).exists())

    def test_all_and_explicit_complete_selection_install_five_skills(self):
        for selection in ("all", "fox,fox-explore,fox-review,fox-verify,fox-fragments"):
            workspace = self.project / selection.replace(",", "-")
            workspace.mkdir()
            destinations = install.install("codex", workspace, skill=selection)
            self.assertEqual({path.name for path in destinations}, set(install.AVAILABLE_SKILLS))

    def test_both_alias_preserves_original_two_skills(self):
        workspace = self.project / "legacy-both"
        workspace.mkdir()
        destinations = install.install("codex", workspace, skill="both")
        self.assertEqual({path.name for path in destinations}, {"fox", "fox-explore"})


class SkillIndependentExecutionTests(unittest.TestCase):
    def test_fox_optional_utility_runs_when_installed_alone(self):
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            fox_dir = install.install("claude", workspace, skill="fox")[0]
            result = subprocess.run(
                [sys.executable, str(fox_dir / "scripts/proof.py"), "doctor"],
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertFalse((fox_dir.parent / "fox-explore").exists())

    def test_fox_explore_has_no_runtime_dependency(self):
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            explore_dir = install.install("claude", workspace, skill="fox-explore")[0]
            self.assertTrue((explore_dir / "references/research-playbook.md").is_file())
            self.assertFalse((explore_dir / "scripts").exists())
            self.assertFalse((explore_dir.parent / "fox").exists())

    def test_fox_review_has_no_runtime_dependency(self):
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            review_dir = install.install("claude", workspace, skill="fox-review")[0]
            self.assertTrue((review_dir / "references/review-playbook.md").is_file())
            self.assertFalse((review_dir / "scripts").exists())
            self.assertFalse((review_dir.parent / "fox").exists())
            self.assertFalse((review_dir.parent / "fox-explore").exists())

    def test_fox_verify_has_no_runtime_dependency(self):
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            verify_dir = install.install("claude", workspace, skill="fox-verify")[0]
            self.assertTrue((verify_dir / "references/adversarial-playbook.md").is_file())
            self.assertFalse((verify_dir / "scripts").exists())
            self.assertFalse((verify_dir.parent / "fox").exists())
            self.assertFalse((verify_dir.parent / "fox-review").exists())


class ActivationContractTests(unittest.TestCase):
    """Check benchmark labels and metadata coverage, not model selection behavior."""

    @classmethod
    def setUpClass(cls):
        cls.tasks = json.loads((ROOT / "evals/tasks.json").read_text(encoding="utf-8"))
        cls.fox = (ROOT / "skills/fox/SKILL.md").read_text(encoding="utf-8").lower()
        cls.explore = (ROOT / "skills/fox-explore/SKILL.md").read_text(encoding="utf-8").lower()
        cls.fragments = (ROOT / "skills/fox-fragments/SKILL.md").read_text(encoding="utf-8").lower()
        cls.review = (ROOT / "skills/fox-review/SKILL.md").read_text(encoding="utf-8").lower()
        cls.verify = (ROOT / "skills/fox-verify/SKILL.md").read_text(encoding="utf-8").lower()

    def test_positive_and_negative_activation_cases_exist(self):
        labels = [set(task["expected_activation"]) for task in self.tasks]
        self.assertIn({"fox"}, labels)
        self.assertIn({"fox-explore"}, labels)
        self.assertIn({"fox-review"}, labels)
        self.assertIn({"fox-verify"}, labels)
        self.assertIn({"fox", "fox-explore"}, labels)
        self.assertIn({"fox", "fox-review"}, labels)
        self.assertIn({"fox-review", "fox-verify"}, labels)
        self.assertIn(set(), labels)

    def test_descriptions_contain_positive_and_negative_triggers(self):
        self.assertIn("use for", self.fox)
        self.assertIn("do not use", self.fox)
        self.assertIn("use for", self.explore)
        self.assertIn("do not use", self.explore)
        self.assertIn("use for", self.review)
        self.assertIn("do not use", self.review)
        self.assertIn("use when", self.verify)
        self.assertIn("do not use", self.verify)
        self.assertIn("trivial edits", self.fox)
        self.assertIn("repair defects", self.explore)
        self.assertIn("do not use to repair defects", self.review)
        self.assertIn("ordinary test run", self.verify)

    def test_activation_cases_reference_only_supported_skills(self):
        supported = set(install.AVAILABLE_SKILLS)
        for task in self.tasks:
            self.assertLessEqual(set(task["expected_activation"]), supported)


class EvaluationFixtureTests(unittest.TestCase):
    def test_jsonl_usage_metrics_are_measured_without_parsing_prose(self):
        output = "\n".join([
            '{"type":"item.completed","item":{"type":"command_execution"}}',
            '{"type":"turn.completed","usage":{"input_tokens":120,"output_tokens":30}}',
            "input_tokens=999 is only prose",
        ])
        self.assertEqual(extract_metrics(output), (1, 120, 30))

    def test_repair_fixtures_fail_before_agent_changes(self):
        tasks = json.loads((ROOT / "evals/tasks.json").read_text(encoding="utf-8"))
        for task in (item for item in tasks if item["kind"] == "repair"):
            fixture = ROOT / "evals" / task["fixture"]
            result = subprocess.run(task["test_command"], cwd=fixture, capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0, f"{task['id']} is not a failing baseline")

    def test_evaluation_runner_lists_manifest(self):
        result = subprocess.run(
            [sys.executable, str(ROOT / "evals/run.py"), "--variant", "baseline", "--list"],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("repair-wrapper-timeout: repair", result.stdout)
        self.assertIn("explore-request-flow: explore", result.stdout)
        self.assertIn("review-tenant-regression: review", result.stdout)
        self.assertIn("verify-weak-assertion: verify", result.stdout)

    def test_review_fixtures_prepare_clean_candidate_commits(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "review-results.json"
            result = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "evals/run.py"),
                    "--variant", "fox-review",
                    "--agent-command", "true",
                    "--task", "review-tenant-regression",
                    "--task", "review-clean-change",
                    "--output", str(output),
                ],
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            records = json.loads(output.read_text(encoding="utf-8"))["results"]
            self.assertEqual(len(records), 2)
            self.assertTrue(all(record["human_review_required"] for record in records))
            self.assertTrue(all(record["changed_files"] == [] for record in records))

    def test_verify_evaluation_keeps_human_grading_and_read_only_scoring(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "verify-results.json"
            result = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "evals/run.py"),
                    "--variant", "fox-verify",
                    "--agent-command", "true",
                    "--task", "verify-weak-assertion",
                    "--task", "verify-strong-contract",
                    "--output", str(output),
                ],
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            records = json.loads(output.read_text(encoding="utf-8"))["results"]
            self.assertEqual(len(records), 2)
            self.assertTrue(all(record["human_review_required"] for record in records))
            self.assertTrue(all(record["changed_files"] == [] for record in records))


if __name__ == "__main__":
    unittest.main()

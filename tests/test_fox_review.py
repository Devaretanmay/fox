"""Tests for Fox Review metadata, boundaries, and instruction contracts."""
from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = ROOT / "skills/fox-review"
SKILL_MD = SKILL_DIR / "SKILL.md"


class FoxReviewMetadataTests(unittest.TestCase):
    def test_frontmatter_and_version(self):
        content = SKILL_MD.read_text(encoding="utf-8")
        self.assertTrue(content.startswith("---\n"))
        frontmatter = content.split("---\n", 2)[1]
        self.assertIn("name: fox-review", frontmatter)
        self.assertIn('version: "0.1.1"', frontmatter)
        self.assertIn("license: MIT", frontmatter)
        self.assertIn("Use for", frontmatter)
        self.assertIn("Do not use", frontmatter)
        self.assertIn("# Fox Change Review", content)

    def test_primary_instructions_are_concise(self):
        body = SKILL_MD.read_text(encoding="utf-8").split("---\n", 2)[2]
        self.assertGreaterEqual(len(body.split()), 300)
        self.assertLessEqual(len(body.split()), 500)

    def test_reference_links_resolve(self):
        content = SKILL_MD.read_text(encoding="utf-8")
        links = re.findall(r"\[.*?\]\((references/[^)]+)\)", content)
        self.assertTrue(links)
        for link in links:
            self.assertTrue((SKILL_DIR / link).is_file(), link)

    def test_has_no_custom_runtime(self):
        self.assertFalse((SKILL_DIR / "scripts").exists())


class FoxReviewContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.content = SKILL_MD.read_text(encoding="utf-8")
        cls.playbook = (SKILL_DIR / "references/review-playbook.md").read_text(encoding="utf-8")

    def test_uses_four_stage_workflow(self):
        for number, name in enumerate(("Set the target", "Trace the change", "Validate findings", "Report"), 1):
            self.assertRegex(self.content, rf"## {number}\. {name}")

    def test_reviews_connected_code_not_only_diff(self):
        self.assertIn("callers, callees, tests, fixtures, configuration", self.content)
        self.assertIn("A change can break code it does not touch", self.playbook)

    def test_requires_reproducible_actionable_findings(self):
        self.assertIn("exact location, failure mechanism", self.content)
        self.assertIn("Test a competing interpretation", self.content)
        self.assertIn("smallest repair direction", self.content)

    def test_controls_false_positives(self):
        self.assertIn("Do not report style preferences", self.content)
        self.assertIn("Never invent a finding", self.content)
        self.assertIn("No verified findings", self.playbook)

    def test_is_read_only_and_hands_repairs_to_fox(self):
        self.assertIn("Remain read-only", self.content)
        self.assertIn("Do not edit files, apply fixes, commit, push, approve, merge, or post comments", self.content)
        self.assertIn("hand the verified findings to `fox`", self.content)

    def test_severity_is_impact_based(self):
        self.assertIn("Severity measures impact and reach, not confidence", self.playbook)
        for severity in ("Critical", "High", "Medium", "Low"):
            self.assertIn(f"**{severity}:**", self.playbook)


if __name__ == "__main__":
    unittest.main()

import unittest
import os
import re

from scripts.create_new_mc_version import bump_version_string, get_latest_version_dir
from scripts.test_mc_version import validate_version_files, validate_mrpack_artifact

class TestScriptsAndSkills(unittest.TestCase):
    """Test helper automation scripts and skills definitions."""

    def test_bump_version_string(self):
        self.assertEqual(bump_version_string("1.2.4"), "1.2.5")
        self.assertEqual(bump_version_string("1.0.0"), "1.0.1")
        self.assertEqual(bump_version_string("2.0"), "2.1")

    def test_get_latest_version_dir(self):
        vdir, vname = get_latest_version_dir()
        self.assertEqual(vname, "26.3")
        self.assertTrue(os.path.isdir(vdir))

    def test_validate_version_files_for_26_3(self):
        self.assertTrue(validate_version_files("26.3"))

    def test_validate_mrpack_artifact_for_26_3(self):
        self.assertTrue(validate_mrpack_artifact("26.3"))

    def test_skills_frontmatter(self):
        skills = [
            ".agents/skills/create-new-mc-version/SKILL.md",
            ".agents/skills/test-mc-version/SKILL.md",
        ]
        for skill_path in skills:
            with self.subTest(skill=skill_path):
                self.assertTrue(os.path.exists(skill_path), f"Skill file {skill_path} missing")
                with open(skill_path, "r", encoding="utf-8") as f:
                    content = f.read()
                
                # Check YAML frontmatter presence
                match = re.match(r"^---\n(.*?)\n---\n", content, re.DOTALL)
                self.assertIsNotNone(match, f"Missing YAML frontmatter in {skill_path}")
                frontmatter = match.group(1)
                self.assertIn("name:", frontmatter)
                self.assertIn("description:", frontmatter)

if __name__ == "__main__":
    unittest.main()

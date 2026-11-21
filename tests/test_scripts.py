import unittest
import os
import re

from scripts.create_new_mc_version import bump_version_string, get_latest_version_dir
from scripts.test_mc_version import (
    get_expected_mrpack_candidates,
    validate_mrpack_artifact,
    validate_mrpack_entries,
    validate_version_files,
)

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
        import shutil
        if not shutil.which("packwiz") and not os.path.exists("builds/Mac OS Optimized-26.3.mrpack"):
            self.skipTest("'packwiz' executable not found in PATH and no pre-built .mrpack in builds/")
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

    def test_get_expected_mrpack_candidates(self):
        self.assertEqual(
            get_expected_mrpack_candidates("26.2")[0],
            "builds/Mac OS Optimized-1.3.0+mc26.2.mrpack",
        )
        self.assertEqual(
            get_expected_mrpack_candidates("26.1")[0],
            "builds/Mac OS Optimized-1.3.0+mc26.1.2.mrpack",
        )
        self.assertEqual(
            get_expected_mrpack_candidates("1.21.7-8")[0],
            "builds/Mac OS Optimized-1.3.0+mc1.21.8.mrpack",
        )
        self.assertIn(
            "builds/Mac OS Optimized-26.3.mrpack",
            get_expected_mrpack_candidates("26.3"),
        )

    def test_validate_version_files_v1_3_0_targets(self):
        targets = ["1.21.1", "1.21.4", "1.21.5", "1.21.7-8", "1.21.9-10", "1.21.11", "26.1", "26.2"]
        for ver in targets:
            with self.subTest(version=ver):
                self.assertTrue(validate_version_files(ver))

    def test_validate_mrpack_entries_accepts_unique_paths(self):
        index_json = {
            "files": [
                {
                    "path": "mods/sodium.jar",
                    "downloads": ["https://cdn.modrinth.com/data/AANobbMI/versions/1/sodium.jar"],
                    "hashes": {"sha1": "abc", "sha512": "def"},
                },
                {
                    "path": "shaderpacks/RenderPearl.zip",
                    "downloads": ["https://cdn.modrinth.com/data/BrRak9pu/versions/1/RenderPearl.zip"],
                    "hashes": {"sha1": "ghi", "sha512": "jkl"},
                },
            ]
        }
        ok, errs = validate_mrpack_entries(index_json, ["modrinth.index.json", "overrides/options.txt"])
        self.assertTrue(ok, errs)
        self.assertEqual(errs, [])

    def test_validate_mrpack_entries_rejects_duplicates_and_collisions(self):
        dup_index = {
            "files": [
                {
                    "path": "shaderpacks/RenderPearl v2.2.0-beta.3.zip",
                    "downloads": ["https://example.com/a.zip"],
                    "hashes": {"sha1": "a", "sha512": "b"},
                },
                {
                    "path": "shaderpacks/renderpearl v2.2.0-beta.3.zip",
                    "downloads": ["https://example.com/b.zip"],
                    "hashes": {"sha1": "c", "sha512": "d"},
                },
            ]
        }
        ok, errs = validate_mrpack_entries(dup_index, ["modrinth.index.json"])
        self.assertFalse(ok)
        self.assertTrue(any("Duplicate modpack content path" in e for e in errs))

        collision_index = {
            "files": [
                {
                    "path": "config/iris.properties",
                    "downloads": ["https://example.com/iris.properties"],
                    "hashes": {"sha1": "a", "sha512": "b"},
                }
            ]
        }
        ok2, errs2 = validate_mrpack_entries(
            collision_index,
            ["modrinth.index.json", "overrides/config/iris.properties"],
        )
        self.assertFalse(ok2)
        self.assertTrue(any("collides with index path" in e for e in errs2))

if __name__ == "__main__":
    unittest.main()

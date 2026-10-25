import unittest
import os
import re
import glob
import tomllib

class TestChangelog(unittest.TestCase):
    """Validates CHANGELOG.md adherence to Keep a Changelog and version alignment."""

    CHANGELOG_PATH = "CHANGELOG.md"

    def test_changelog_exists(self):
        """Verify that CHANGELOG.md exists at the repository root."""
        self.assertTrue(os.path.exists(self.CHANGELOG_PATH), "CHANGELOG.md does not exist")

    def test_changelog_structure(self):
        """Verify standard Keep a Changelog sections."""
        with open(self.CHANGELOG_PATH, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("# Changelog", content)
        self.assertIn("## [Unreleased]", content)

        # Ensure semantic version headers exist: e.g. ## [1.2.4] - 2026-10-25
        version_headers = re.findall(r"## \[(\d+\.\d+\.\d+(?:\.\d+)?)\] - (\d{4}-\d{2}-\d{2})", content)
        self.assertGreater(len(version_headers), 0, "No valid version headers found in CHANGELOG.md")

    def test_all_pack_versions_in_changelog(self):
        """Verify that all version pack.toml versions have an entry in CHANGELOG.md."""
        with open(self.CHANGELOG_PATH, "r", encoding="utf-8") as f:
            content = f.read()

        version_files = glob.glob("versions/*/pack.toml")
        for vf in version_files:
            with open(vf, "rb") as pf:
                data = tomllib.load(pf)
            version = data.get("version")
            if version:
                with self.subTest(pack_version=version, path=vf):
                    self.assertIn(
                        f"[{version}]",
                        content,
                        f"Version {version} from {vf} is missing in CHANGELOG.md"
                    )

if __name__ == "__main__":
    unittest.main()

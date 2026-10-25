import unittest
import tomllib
import hashlib
import glob
import os

class TestPackIntegrity(unittest.TestCase):
    """Validates packwiz configuration, TOML syntax, and file hash integrity across all versions."""

    def test_toml_syntax_all_versions(self):
        """Ensure all TOML files in the versions directory are syntactically valid."""
        toml_files = glob.glob("versions/**/*.toml", recursive=True)
        self.assertGreater(len(toml_files), 0, "No TOML files found in versions/")
        
        for path in toml_files:
            with self.subTest(file=path):
                with open(path, "rb") as f:
                    try:
                        data = tomllib.load(f)
                        self.assertIsInstance(data, dict)
                    except Exception as e:
                        self.fail(f"Failed to parse TOML at {path}: {e}")

    def test_pack_and_index_hash_consistency(self):
        """Ensure index.toml sha256 matches the hash declared in pack.toml for each version."""
        version_dirs = [
            d for d in glob.glob("versions/*")
            if os.path.isdir(d) and os.path.exists(os.path.join(d, "pack.toml"))
        ]
        self.assertGreater(len(version_dirs), 0, "No version directories found")

        for vdir in version_dirs:
            with self.subTest(version=vdir):
                pack_file = os.path.join(vdir, "pack.toml")
                index_file = os.path.join(vdir, "index.toml")
                
                self.assertTrue(os.path.exists(index_file), f"index.toml missing in {vdir}")

                with open(pack_file, "rb") as f:
                    pack_data = tomllib.load(f)

                with open(index_file, "rb") as f:
                    actual_index_hash = hashlib.sha256(f.read()).hexdigest()

                declared_index_hash = pack_data.get("index", {}).get("hash")
                self.assertEqual(
                    actual_index_hash,
                    declared_index_hash,
                    f"Hash mismatch in {vdir}/pack.toml: declared {declared_index_hash}, actual {actual_index_hash}"
                )

    def test_index_file_references_and_hashes(self):
        """Ensure every file declared in index.toml exists and matches its expected sha256 hash."""
        version_dirs = [
            d for d in glob.glob("versions/*")
            if os.path.isdir(d) and os.path.exists(os.path.join(d, "index.toml"))
        ]

        for vdir in version_dirs:
            index_file = os.path.join(vdir, "index.toml")
            with open(index_file, "rb") as f:
                index_data = tomllib.load(f)

            files = index_data.get("files", [])
            for entry in files:
                rel_path = entry["file"]
                full_path = os.path.join(vdir, rel_path)
                expected_hash = entry["hash"]

                with self.subTest(version=vdir, file=rel_path):
                    self.assertTrue(os.path.exists(full_path), f"File {rel_path} declared in {index_file} does not exist")
                    with open(full_path, "rb") as f:
                        actual_hash = hashlib.sha256(f.read()).hexdigest()
                    self.assertEqual(
                        actual_hash,
                        expected_hash,
                        f"Hash mismatch for {rel_path} in {vdir}"
                    )

if __name__ == "__main__":
    unittest.main()

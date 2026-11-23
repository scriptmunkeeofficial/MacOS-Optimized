import unittest
import tomllib
import hashlib
import glob
import os
import re

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

    def test_fabric_loader_version_format(self):
        """Ensure every pack.toml declares a valid SemVer Fabric Loader version."""
        pack_files = sorted(glob.glob("versions/*/pack.toml"))
        self.assertGreater(len(pack_files), 0, "No pack.toml files found")

        for pack_file in pack_files:
            with self.subTest(pack=pack_file):
                with open(pack_file, "rb") as f:
                    pack_data = tomllib.load(f)
                fabric_ver = pack_data.get("versions", {}).get("fabric", "")
                self.assertRegex(
                    fabric_ver,
                    r"^\d+\.\d+\.\d+$",
                    f"Invalid Fabric Loader version '{fabric_ver}' in {pack_file}",
                )

    def test_no_duplicate_mod_ids(self):
        """Ensure no Modrinth mod-id is declared twice inside the same version directory."""
        version_dirs = [
            d for d in sorted(glob.glob("versions/*"))
            if os.path.isdir(d) and os.path.exists(os.path.join(d, "pack.toml"))
        ]
        self.assertGreater(len(version_dirs), 0, "No version directories found")

        for vdir in version_dirs:
            seen = {}
            for category in ("mods", "resourcepacks", "shaderpacks"):
                for pw_toml in sorted(glob.glob(os.path.join(vdir, category, "*.pw.toml"))):
                    with open(pw_toml, "rb") as f:
                        data = tomllib.load(f)
                    mod_id = data.get("update", {}).get("modrinth", {}).get("mod-id")
                    if not mod_id:
                        continue
                    rel_toml = os.path.relpath(pw_toml, vdir)
                    with self.subTest(version=vdir, mod_id=mod_id):
                        self.assertNotIn(
                            mod_id,
                            seen,
                            f"Duplicate Modrinth mod-id '{mod_id}' in {vdir}: {seen.get(mod_id)} and {rel_toml}",
                        )
                        seen[mod_id] = rel_toml

    def test_no_duplicate_target_filenames(self):
        """Ensure no two manifests inside a version target the same destination file path."""
        version_dirs = [
            d for d in sorted(glob.glob("versions/*"))
            if os.path.isdir(d) and os.path.exists(os.path.join(d, "pack.toml"))
        ]
        self.assertGreater(len(version_dirs), 0, "No version directories found")

        for vdir in version_dirs:
            seen_targets = {}
            for category in ("mods", "resourcepacks", "shaderpacks"):
                for pw_toml in sorted(glob.glob(os.path.join(vdir, category, "*.pw.toml"))):
                    with open(pw_toml, "rb") as f:
                        data = tomllib.load(f)
                    filename = data.get("filename", "")
                    if not filename:
                        continue
                    target = f"{category}/{filename}".lower()
                    rel_toml = os.path.relpath(pw_toml, vdir)
                    with self.subTest(version=vdir, target=target):
                        self.assertNotIn(
                            target,
                            seen_targets,
                            f"Duplicate target file '{target}' in {vdir}: {seen_targets.get(target)} and {rel_toml}",
                        )
                        seen_targets[target] = rel_toml

    def test_iris_properties_shaderpack_exists(self):
        """Ensure any active shaderPack in config/iris.properties matches an installed shaderpack manifest."""
        iris_files = sorted(glob.glob("versions/*/config/iris.properties"))
        self.assertGreater(len(iris_files), 0, "No iris.properties files found")

        for iris_file in iris_files:
            vdir = os.path.dirname(os.path.dirname(iris_file))
            installed_shaders = set()
            for sp_toml in glob.glob(os.path.join(vdir, "shaderpacks", "*.pw.toml")):
                with open(sp_toml, "rb") as f:
                    data = tomllib.load(f)
                if data.get("filename"):
                    installed_shaders.add(data["filename"])

            shader_pack = None
            with open(iris_file, "r", encoding="utf-8") as f:
                for line in f:
                    if line.startswith("shaderPack="):
                        shader_pack = line.strip().split("=", 1)[1]
                        break

            if shader_pack and shader_pack not in {"(internal)", "(off)"}:
                with self.subTest(version=vdir, shader_pack=shader_pack):
                    self.assertIn(
                        shader_pack,
                        installed_shaders,
                        f"shaderPack '{shader_pack}' in {iris_file} does not match any shaderpack in {vdir}/shaderpacks/",
                    )

if __name__ == "__main__":
    unittest.main()

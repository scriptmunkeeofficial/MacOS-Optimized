#!/usr/bin/env python3
"""Script to test and validate a Minecraft modpack version without loading the Modrinth App UI."""

import os
import sys
import argparse
import glob
import subprocess
import tomllib
import hashlib
import zipfile
import json
import shutil

def validate_version_files(mc_version):
    """Validate TOML syntax and hash integrity of all version files."""
    vdir = os.path.join("versions", mc_version)
    if not os.path.exists(vdir):
        print(f"Error: Version directory '{vdir}' does not exist!", file=sys.stderr)
        return False

    pack_file = os.path.join(vdir, "pack.toml")
    index_file = os.path.join(vdir, "index.toml")
    
    if not os.path.exists(pack_file) or not os.path.exists(index_file):
        print(f"Error: pack.toml or index.toml missing in {vdir}", file=sys.stderr)
        return False

    print(f"1. Validating TOML syntax in {vdir}...")
    for root, _, files in os.walk(vdir):
        for f in files:
            if f.endswith(".toml"):
                fpath = os.path.join(root, f)
                try:
                    with open(fpath, "rb") as fp:
                        tomllib.load(fp)
                except Exception as e:
                    print(f"   [FAIL] {fpath}: {e}", file=sys.stderr)
                    return False
    print("   [OK] All TOML files are syntactically valid.")

    print("2. Validating pack.toml and index.toml hash integrity...")
    with open(pack_file, "rb") as fp:
        pack_data = tomllib.load(fp)
    with open(index_file, "rb") as fp:
        actual_index_hash = hashlib.sha256(fp.read()).hexdigest()
    declared_index_hash = pack_data.get("index", {}).get("hash")
    if actual_index_hash != declared_index_hash:
        print(f"   [FAIL] index.toml hash mismatch: declared {declared_index_hash}, actual {actual_index_hash}", file=sys.stderr)
        return False
    print("   [OK] pack.toml matches index.toml SHA-256.")

    print("3. Validating external file references and hashes...")
    with open(index_file, "rb") as fp:
        index_data = tomllib.load(fp)
    for entry in index_data.get("files", []):
        rel = entry["file"]
        fpath = os.path.join(vdir, rel)
        if not os.path.exists(fpath):
            print(f"   [FAIL] Missing file declared in index: {rel}", file=sys.stderr)
            return False
        with open(fpath, "rb") as fp:
            fhash = hashlib.sha256(fp.read()).hexdigest()
        if fhash != entry["hash"]:
            print(f"   [FAIL] Hash mismatch for {rel}", file=sys.stderr)
            return False
    print(f"   [OK] All {len(index_data.get('files', []))} files exist with matching SHA-256 hashes.")
    return True

def get_expected_mrpack_candidates(mc_version):
    """Return ordered, deduplicated .mrpack candidate paths for a version directory."""
    pack_file = os.path.join("versions", mc_version, "pack.toml")
    pack_ver = None
    game_ver = None
    if os.path.exists(pack_file):
        with open(pack_file, "rb") as fp:
            pack_data = tomllib.load(fp)
        pack_ver = pack_data.get("version")
        game_ver = pack_data.get("versions", {}).get("minecraft")

    raw_candidates = []
    if pack_ver and game_ver:
        raw_candidates.append(f"builds/Mac OS Optimized-{pack_ver}+mc{game_ver}.mrpack")
    if pack_ver:
        raw_candidates.append(f"builds/Mac OS Optimized-{pack_ver}+mc{mc_version}.mrpack")
    if game_ver:
        raw_candidates.append(f"builds/Mac OS Optimized-{game_ver}.mrpack")
    raw_candidates.append(f"builds/Mac OS Optimized-{mc_version}.mrpack")

    candidates = []
    for cand in raw_candidates:
        if cand not in candidates:
            candidates.append(cand)
    return candidates

def validate_mrpack_entries(index_json, namelist):
    """Validate modrinth.index.json file entries and archive override paths for collisions."""
    errors = []
    seen_paths = {}
    for entry in index_json.get("files", []):
        path = entry.get("path", "")
        if not path:
            errors.append("Empty file path in modrinth.index.json")
            continue

        norm_path = path.lower()
        if norm_path in seen_paths:
            errors.append(
                f"Duplicate modpack content path: '{seen_paths[norm_path]}' and '{path}'"
            )
        else:
            seen_paths[norm_path] = path

        downloads = entry.get("downloads")
        if not isinstance(downloads, list) or len(downloads) == 0:
            errors.append(f"Missing downloads list for '{path}'")

        hashes = entry.get("hashes", {})
        if not hashes.get("sha1") or not hashes.get("sha512"):
            errors.append(f"Missing sha1/sha512 hashes for '{path}'")

    for name in namelist:
        if name.startswith("overrides/") and not name.endswith("/"):
            rel = name[len("overrides/"):]
            if rel.lower() in seen_paths:
                errors.append(
                    f"Override '{name}' collides with index path '{seen_paths[rel.lower()]}'"
                )

    return len(errors) == 0, errors

def validate_mrpack_artifact(mc_version):
    """Validate exported .mrpack artifact structure and modrinth.index.json."""
    pack_file = os.path.join("versions", mc_version, "pack.toml")
    if not os.path.exists(pack_file):
        print(f"   [FAIL] Missing pack.toml in versions/{mc_version}", file=sys.stderr)
        return False
    with open(pack_file, "rb") as fp:
        pack_data = tomllib.load(fp)

    mrpack_candidates = get_expected_mrpack_candidates(mc_version)
    mrpack_path = None
    for cand in mrpack_candidates:
        if os.path.exists(cand):
            mrpack_path = cand
            break

    if not mrpack_path:
        if not shutil.which("packwiz"):
            print("   [WARN] 'packwiz' executable not found in PATH and no pre-built .mrpack in builds/.", file=sys.stderr)
            return False
        print(f"   [INFO] No pre-existing .mrpack found in builds/ for {mc_version}. Exporting dry-run...")
        vdir = os.path.join("versions", mc_version)
        tmp_mrpack = f"/tmp/test-{mc_version}.mrpack"
        res = subprocess.run(["packwiz", "modrinth", "export", "-o", tmp_mrpack], cwd=vdir, capture_output=True, text=True)
        if res.returncode != 0:
            print(f"   [FAIL] packwiz modrinth export failed:\n{res.stderr}", file=sys.stderr)
            return False
        mrpack_path = tmp_mrpack

    print(f"4. Validating .mrpack archive structure ({mrpack_path})...")
    try:
        with zipfile.ZipFile(mrpack_path, "r") as zf:
            namelist = zf.namelist()
            if "modrinth.index.json" not in namelist:
                print("   [FAIL] modrinth.index.json missing from .mrpack archive", file=sys.stderr)
                return False
            index_bytes = zf.read("modrinth.index.json")
            index_json = json.loads(index_bytes.decode("utf-8"))
            game = index_json.get("game")
            files = index_json.get("files")
            if game != "minecraft" or not isinstance(files, list):
                print(f"   [FAIL] Invalid modrinth.index.json fields (game={game}, files={type(files).__name__})", file=sys.stderr)
                return False

            expected_ver = pack_data.get("version")
            actual_ver = index_json.get("versionId")
            if actual_ver != expected_ver:
                print(f"   [FAIL] versionId mismatch in {mrpack_path}: expected {expected_ver}, got {actual_ver}", file=sys.stderr)
                return False

            deps = index_json.get("dependencies", {})
            expected_mc = pack_data.get("versions", {}).get("minecraft")
            expected_fl = pack_data.get("versions", {}).get("fabric")
            if deps.get("minecraft") != expected_mc:
                print(f"   [FAIL] minecraft dependency mismatch: expected {expected_mc}, got {deps.get('minecraft')}", file=sys.stderr)
                return False
            if deps.get("fabric-loader") != expected_fl:
                print(f"   [FAIL] fabric-loader dependency mismatch: expected {expected_fl}, got {deps.get('fabric-loader')}", file=sys.stderr)
                return False

            entries_ok, entry_errors = validate_mrpack_entries(index_json, namelist)
            if not entries_ok:
                for err in entry_errors:
                    print(f"   [FAIL] {err}", file=sys.stderr)
                return False

            print(f"   [OK] Valid Modrinth pack (Version: {actual_ver}, Game: {game} {expected_mc}, Fabric: {expected_fl}, Files: {len(files)}, Format: {index_json.get('formatVersion')})")
    except Exception as e:
        print(f"   [FAIL] Invalid .mrpack archive: {e}", file=sys.stderr)
        return False
    return True

def discover_version_dirs():
    """Return sorted version directory names under versions/ that contain pack.toml."""
    return sorted(
        os.path.basename(d)
        for d in glob.glob("versions/*")
        if os.path.isdir(d) and os.path.exists(os.path.join(d, "pack.toml"))
    )

def serve_modpack(mc_version, port=8080):
    """Run packwiz serve for live client testing via packwiz-installer / Prism / MultiMC."""
    vdir = os.path.join("versions", mc_version)
    if not os.path.exists(vdir):
        print(f"Error: Version directory '{vdir}' does not exist!", file=sys.stderr)
        sys.exit(1)

    print(f"\n🚀 Starting live development server for Minecraft {mc_version}...")
    print(f"   URL: http://localhost:{port}/pack.toml")
    print("   To test in-game without Modrinth App:")
    print("   1. Create an instance in Prism Launcher or MultiMC with Fabric Loader.")
    print(f"   2. Install packwiz-installer or use packwiz URL: http://localhost:{port}/pack.toml")
    print("   Press Ctrl+C to stop the server.\n")
    try:
        subprocess.run(["packwiz", "serve", "--port", str(port)], cwd=vdir)
    except KeyboardInterrupt:
        print("\nDevelopment server stopped.")

def main():
    parser = argparse.ArgumentParser(description="Test and validate packwiz modpack versions.")
    parser.add_argument("versions", nargs="*", help="Minecraft version(s) (e.g. 26.2 26.3)")
    parser.add_argument("--all", action="store_true", help="Validate all version directories under versions/")
    parser.add_argument("--serve", action="store_true", help="Launch local HTTP development server for live testing")
    parser.add_argument("--port", type=int, default=8080, help="Port for development server (default: 8080)")

    args = parser.parse_args()
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    os.chdir(repo_root)

    if args.serve:
        if args.all or len(args.versions) != 1:
            parser.error("--serve requires exactly one version argument.")
        serve_modpack(args.versions[0], args.port)
        return

    target_versions = discover_version_dirs() if args.all else args.versions
    if not target_versions:
        parser.error("Provide at least one version or pass --all.")

    all_ok = True
    for ver in target_versions:
        print(f"=== Testing Minecraft Modpack Version: {ver} ===\n")
        ok1 = validate_version_files(ver)
        ok2 = validate_mrpack_artifact(ver)

        if ok1 and ok2:
            print(f"\n✅ All tests passed for Minecraft {ver}!\n")
        else:
            print(f"\n❌ Validation failed for Minecraft {ver}.\n", file=sys.stderr)
            all_ok = False

    if not all_ok:
        sys.exit(1)
    print("Tip: Run with --serve to test with a live client without importing into Modrinth.")

if __name__ == "__main__":
    main()

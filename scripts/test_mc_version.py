#!/usr/bin/env python3
"""Script to test and validate a Minecraft modpack version without loading the Modrinth App UI."""

import os
import sys
import argparse
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

def validate_mrpack_artifact(mc_version):
    """Validate exported .mrpack artifact structure and modrinth.index.json."""
    mrpack_candidates = [
        f"builds/Mac OS Optimized-{mc_version}.mrpack",
        f"builds/Mac OS Optimized-{mc_version}.mrpack",
    ]
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
            files = index_json.get("files", [])
            print(f"   [OK] Valid Modrinth pack (Game: {game}, Files: {len(files)}, Format: {index_json.get('formatVersion')})")
    except Exception as e:
        print(f"   [FAIL] Invalid .mrpack archive: {e}", file=sys.stderr)
        return False
    return True

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
    parser.add_argument("version", help="Minecraft version (e.g. 26.3)")
    parser.add_argument("--serve", action="store_true", help="Launch local HTTP development server for live testing")
    parser.add_argument("--port", type=int, default=8080, help="Port for development server (default: 8080)")

    args = parser.parse_args()
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    os.chdir(repo_root)

    if args.serve:
        serve_modpack(args.version, args.port)
        return

    print(f"=== Testing Minecraft Modpack Version: {args.version} ===\n")
    ok1 = validate_version_files(args.version)
    ok2 = validate_mrpack_artifact(args.version)

    if ok1 and ok2:
        print(f"\n✅ All tests passed for Minecraft {args.version}!")
        print("Tip: Run with --serve to test with a live client without importing into Modrinth.")
    else:
        print(f"\n❌ Validation failed for Minecraft {args.version}.", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()

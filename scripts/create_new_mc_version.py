#!/usr/bin/env python3
"""Script to automate the creation and packaging of a new Minecraft modpack version."""

import os
import sys
import shutil
import subprocess
import tomllib
import glob
import re

def run_cmd(cmd, cwd=None, check=True):
    """Run shell command with output echoing."""
    print(f"==> Running: {' '.join(cmd) if isinstance(cmd, list) else cmd}")
    res = subprocess.run(cmd, cwd=cwd, shell=isinstance(cmd, str), check=check, text=True, capture_output=True)
    if res.stdout:
        print(res.stdout.strip())
    if res.stderr:
        print(res.stderr.strip(), file=sys.stderr)
    return res

def get_latest_version_dir():
    """Find the most recent version directory in versions/."""
    candidates = []
    for p in glob.glob("versions/*"):
        if os.path.isdir(p) and os.path.exists(os.path.join(p, "pack.toml")):
            name = os.path.basename(p)
            candidates.append((p, name))
    
    # Sort with preference for major version numbers (e.g., 26.3 > 26.2 > 1.21.11)
    def parse_key(item):
        parts = re.findall(r"\d+", item[1])
        return [int(x) for x in parts]

    candidates.sort(key=parse_key)
    if not candidates:
        raise RuntimeError("No version directories found in versions/")
    return candidates[-1]

def bump_version_string(ver_str):
    """Bump patch version string: e.g. 1.2.4 -> 1.2.5."""
    parts = ver_str.strip().split(".")
    if parts:
        try:
            parts[-1] = str(int(parts[-1]) + 1)
            return ".".join(parts)
        except ValueError:
            pass
    return ver_str + ".1"

def create_new_version(target_mc_version):
    """Execute complete workflow for generating the new Minecraft version."""
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    os.chdir(repo_root)

    target_dir = os.path.join("versions", target_mc_version)
    if os.path.exists(target_dir):
        print(f"Error: Target version directory '{target_dir}' already exists!", file=sys.stderr)
        sys.exit(1)

    prev_path, prev_name = get_latest_version_dir()
    print(f"Baseline version selected: {prev_name} ({prev_path})")

    # Step 1: Create a new branch
    branch_name = f"feat/{target_mc_version}"
    print(f"\n[Step 1] Creating feature branch: {branch_name}")
    run_cmd(["git", "checkout", "-b", branch_name])

    # Step 2: Copy previous version directory to new version directory
    print(f"\n[Step 2] Copying {prev_path} to {target_dir}")
    shutil.copytree(prev_path, target_dir)

    # Step 3: Commit the copy change into the new branch
    print(f"\n[Step 3] Staging and committing baseline copy for {target_mc_version}")
    run_cmd(["git", "add", target_dir])
    run_cmd(["git", "commit", "-m", f"Baseline copy from {prev_name} for Minecraft {target_mc_version}"])

    # Step 4: Option 1 - Automated Migration
    print(f"\n[Step 4] Updating pack.toml version and migrating via packwiz")
    pack_toml_path = os.path.join(target_dir, "pack.toml")
    with open(pack_toml_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Bump version
    current_pack_ver = re.search(r'version\s*=\s*"([^"]+)"', content)
    if current_pack_ver:
        new_pack_ver = bump_version_string(current_pack_ver.group(1))
        content = re.sub(r'version\s*=\s*"[^"]+"', f'version = "{new_pack_ver}"', content, count=1)
        with open(pack_toml_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Bumped modpack version: {current_pack_ver.group(1)} -> {new_pack_ver}")

    # Pipeline requirement: packwiz refresh must run immediately after pack.toml update
    print("\nRefreshing pack index after pack.toml update...")
    run_cmd(["packwiz", "refresh"], cwd=target_dir)

    # Run packwiz migrate minecraft <version> -y
    print("\nRunning packwiz migrate...")
    run_cmd(["packwiz", "migrate", "minecraft", target_mc_version, "-y"], cwd=target_dir)

    # Run packwiz update --all -y
    print("\nRunning packwiz update --all...")
    run_cmd(["packwiz", "update", "--all", "-y"], cwd=target_dir)

    # Run packwiz refresh
    print("\nRunning packwiz refresh...")
    run_cmd(["packwiz", "refresh"], cwd=target_dir)

    # Commit the migration changes
    print("\nCommitting migration changes...")
    run_cmd(["git", "add", target_dir])
    run_cmd(["git", "commit", "-m", f"Migrate to Minecraft {target_mc_version} and update dependencies"])

    # Step 5: Testing & Validation (MUST run before packaging)
    print(f"\n[Step 5] Running automated test suite before packaging")
    test_res = run_cmd([sys.executable, "-m", "unittest", "discover", "tests", "-v"])

    # Step 6: Packaging (Only after tests pass)
    os.makedirs("builds", exist_ok=True)
    export_path = f"../../builds/Mac OS Optimized-{target_mc_version}.mrpack"
    print(f"\n[Step 6] Exporting Modrinth pack to {export_path}")
    run_cmd(["packwiz", "modrinth", "export", "-o", export_path], cwd=target_dir)
    
    print(f"\n🎉 Successfully created and verified Minecraft {target_mc_version} on branch '{branch_name}'!")
    print(f"Modpack artifact generated at: builds/Mac OS Optimized-{target_mc_version}.mrpack")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 scripts/create_new_mc_version.py <mc_version>", file=sys.stderr)
        print("Example: python3 scripts/create_new_mc_version.py 26.4", file=sys.stderr)
        sys.exit(1)
    create_new_version(sys.argv[1].strip())

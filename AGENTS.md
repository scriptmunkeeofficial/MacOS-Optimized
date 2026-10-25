# Context: MacOS Optimized Modpack

## Identity

You are a senior software engineer and systems architect specializing in Minecraft modding, performance optimization, and packwiz packaging. You do not do anything half-assed; you ensure high quality, deterministic verification, and clean implementations.

---

## Project Overview

**MacOS Optimized** is a curated, high-performance Fabric-based Minecraft modpack tailored specifically for Apple Silicon and macOS platforms. Its goal is to maximize framerates, eliminate macOS-specific input quirks (e.g., Retina display scaling, Command-key navigation, window management), and deliver pre-configured shaders and visual quality out of the box.

* **Modpack Format:** [packwiz](https://packwiz.infra.link/) (`pack.toml`, `index.toml`, and `.pw.toml` manifests).
* **Target Loaders:** Fabric Loader.
* **Packaging Target:** Modrinth (`.mrpack`) and CurseForge compatibility.
* **Testing Tooling:** Python 3 `unittest` suite (`tests/`).

---

## Repository Structure

```
MacOS-Optimized/
├── AGENTS.md                          # This document (AI operational guidelines & rules)
├── CHANGELOG.md                       # Repository-wide changelog (Keep a Changelog standard)
├── README.md                          # Project documentation and manual build instructions
├── icon.png                           # Pack icon
├── LICENSE                            # License file
├── .gitignore                         # Git ignore rules
├── .packwizignore                     # Packwiz build exclusion rules
├── .github/
│   ├── pull_request_template.md       # PR template enforcing changelog structure
│   └── workflows/
│       └── test.yml                   # CI workflow validating TOML and hash integrity
├── builds/                            # Exported .mrpack artifacts (git-ignored)
├── tests/                             # Automated test suite
│   ├── test_packs.py                  # Validates TOML syntax, pack hashes, and index files
│   └── test_changelog.py              # Validates CHANGELOG.md format and version tracking
└── versions/                          # Multi-version modpack manifests
    ├── 1.21.1/ ... 1.21.11/           # Historical Minecraft 1.21 releases
    ├── 26.1/                          # Minecraft 26.1 / 26.1.2 releases
    ├── 26.2/                          # Minecraft 26.2 releases
    └── 26.3/                          # Minecraft 26.3 releases
        ├── pack.toml                  # Version root manifest
        ├── index.toml                 # File index with SHA-256 hashes
        ├── options.txt                # Curated default client options
        ├── config/                    # Mod configurations (Iris, EntityCulling, Zoomify, etc.)
        ├── mods/                      # *.pw.toml manifests for each mod
        ├── resourcepacks/             # *.pw.toml manifests for resource packs
        └── shaderpacks/               # *.pw.toml manifests for shaderpacks
```

---

## Development Rules

1. **Branching Strategy:**
   - All new work must be created on an isolated branch branched off the default branch (`main`) or a dependent feature branch (e.g., `feat/<name>` or `feat/<version>`).
   - No direct commits to default branches (`main`, `dev`).
   - No pushes may happen if the active branch is `main`.
   - All Pull Requests must target the repository default branch (`main`).

2. **Autonomous Implementation & Pre-PR Review Checkpoint:**
   - Agents have full autonomy to implement features, update manifests, run tests, fix lint errors, and create atomic git commits on the isolated feature branch without pausing for step-by-step developer approval.
   - **Human Checkpoint:** Explicit developer approval is strictly required **before** opening or merging a Pull Request into default branches (`main`), or if an unresolvable blocker or critical architectural ambiguity arises.

3. **Mandatory Testing:**
   - All modifications to pack manifests, index files, or repository structure must be validated via the automated test suite.
   - Run `python3 -m unittest discover tests` before any commit or PR creation. All tests must pass with zero errors.

4. **Mandatory Changelog Maintenance:**
   - Every version release or pack update must update `CHANGELOG.md` adhering to [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
   - Every Pull Request description must include a `## Changelog` section formatted in accordance with `.github/pull_request_template.md` (mimicking PR #22 / PR #24).

5. **Production Deployment Guard:**
   - No direct changes to production distribution channels or releases outside of GitHub pull request reviews and CI workflows.

---

## Control Panel & Build Commands

* **Run Test Suite:**
  ```bash
  python3 -m unittest discover tests -v
  ```
* **Run Version Integrity Check (Without Modrinth App):**
  ```bash
  python3 scripts/test_mc_version.py <version>
  ```
* **Run Live Development Server (for live client testing without Modrinth App):**
  ```bash
  python3 scripts/test_mc_version.py <version> --serve
  ```
* **Refresh Pack Index (inside `versions/<target>`):**
  ```bash
  packwiz refresh
  ```
* **Update All Mods (Non-interactive):**
  ```bash
  packwiz update --all -y
  ```
* **Export Modrinth Pack:**
  ```bash
  packwiz modrinth export -o ../../builds/Mac\ OS\ Optimized-<version>.mrpack
  ```

---

## Agent Slash Commands

The repository provides two native agent skills (slash commands):

1. **`/create-new-mc-version <mc_version>`**:
   Automates creating a new feature branch, copying baseline files, committing the baseline copy, running non-interactive `packwiz migrate minecraft <version> -y`, updating mods with `-y`, packaging the `.mrpack` archive, and running verification tests.
   Defined in [`.agents/skills/create-new-mc-version/SKILL.md`](.agents/skills/create-new-mc-version/SKILL.md).

2. **`/test-mc-version <mc_version> [--serve]`**:
   Tests and validates modpack manifests, checksums, and `.mrpack` archive structure without launching or importing through the Modrinth App. Supports `--serve` to run a local HTTP server for Prism / MultiMC live client testing.
   Defined in [`.agents/skills/test-mc-version/SKILL.md`](.agents/skills/test-mc-version/SKILL.md).

---

## Minecraft Version Upgrade Protocol (AI Agent Execution)

When tasked with adding or updating support for a new Minecraft version (`<mc_ver>`):

You may execute the automated helper `python3 scripts/create_new_mc_version.py <mc_ver>` or follow the step-by-step developer protocol below:

### Step 1: Branch Setup
Create a dedicated feature branch from the latest `main`:
```bash
git checkout main && git pull origin main
git checkout -b feat/<mc_ver>
```

### Step 2: Create Version Directory
Copy the previous version directory as the baseline:
```bash
cp -r versions/<prev_ver> versions/<mc_ver>
```

### Step 3: Commit Baseline Copy
Stage and commit the copy into the new feature branch:
```bash
git add versions/<mc_ver>
git commit -m "Baseline copy from <prev_ver> for Minecraft <mc_ver>"
```

### Step 4: Update Manifests (Option 1 Automated)
Within `versions/<mc_ver>`:
1. Increment modpack `version` in `pack.toml` (e.g. `1.2.4` -> `1.2.5`).
2. Run `packwiz migrate minecraft <mc_ver> -y` to auto-accept Fabric loader and mod migrations.
3. Run `packwiz update --all -y` to update all remaining components non-interactively.
4. Run `packwiz refresh` to regenerate `index.toml`.
5. Commit the migration changes:
   ```bash
   git add versions/<mc_ver>
   git commit -m "Migrate to Minecraft <mc_ver> and update dependencies"
   ```

### Step 5: Package Artifact
Export Modrinth pack:
```bash
packwiz modrinth export -o ../../builds/Mac\ OS\ Optimized-<mc_ver>.mrpack
```

### Step 6: Verification & Testing
Execute the test suite without loading Modrinth:
```bash
python3 scripts/test_mc_version.py <mc_ver>
python3 -m unittest discover tests -v
```
Ensure all TOML files parse, all declared files exist, and SHA-256 hashes match.

### Step 7: Changelog & Pre-PR Review
1. Add the new version block in `CHANGELOG.md` under `[Unreleased]`.
2. Push the feature branch to origin: `git push -u origin feat/<mc_ver>`.
3. Draft a PR description mimicking the format in `.github/pull_request_template.md`.
4. Pause at the **Human Checkpoint** to obtain developer approval before opening and merging the Pull Request.

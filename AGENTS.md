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
* **Refresh Pack Index (inside `versions/<target>`):**
  ```bash
  packwiz refresh
  ```
* **Update All Mods (inside `versions/<target>`):**
  ```bash
  packwiz update --all
  ```
* **Export Modrinth Pack:**
  ```bash
  packwiz modrinth export -o ../../builds/Mac\ OS\ Optimized-<version>.mrpack
  ```

---

## Minecraft Version Upgrade Protocol (AI Agent Execution)

When tasked with adding or updating support for a new Minecraft version (`<mc_ver>`):

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

### Step 3: Update `pack.toml`
Update `versions/<mc_ver>/pack.toml`:
* Increment the modpack `version` (e.g. `1.2.4` -> `1.2.5`).
* Update `[versions].minecraft` to `<mc_ver>`.
* Update `[versions].fabric` to the latest target Fabric loader.

### Step 4: Refresh and Update Manifests
Run `packwiz refresh` and `packwiz update --all` within `versions/<mc_ver>/` to pull updated `.pw.toml` definitions for all mods, shaders, and resource packs.

### Step 5: Verification & Testing
Execute the test suite from the repository root:
```bash
python3 -m unittest discover tests
```
Ensure all TOML files parse, all declared files exist, and SHA-256 hashes match.

### Step 6: Changelog & Pre-PR Review
1. Add the new version block in `CHANGELOG.md`.
2. Commit the changes atomically with descriptive commit messages.
3. Push the feature branch to origin: `git push -u origin feat/<mc_ver>`.
4. Draft a PR description mimicking the format in `.github/pull_request_template.md`.
5. Pause at the **Human Checkpoint** to obtain developer approval before opening and merging the Pull Request.

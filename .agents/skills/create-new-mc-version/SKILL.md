---
name: create-new-mc-version
description: >-
  Automates creating, updating, and packaging a new Minecraft modpack version using packwiz.
  Use when the user invokes the slash command '/create-new-mc-version {mc_version}' or asks to add support for a new Minecraft version.
---

# Create New Minecraft Modpack Version (`/create-new-mc-version`)

This skill automates the complete developer workflow for creating, migrating, updating, packaging, and verifying a new Minecraft version for the MacOS-Optimized modpack.

## Usage Syntax

```text
/create-new-mc-version <mc_version_number>
```
*Example:* `/create-new-mc-version 26.4`

---

## Workflow Steps

When this skill is invoked with `<mc_version>`:

### Step 1: Branch Creation
Create a dedicated feature branch based on the latest default branch:
```bash
git checkout main && git pull origin main
git checkout -b feat/<mc_version>
```

### Step 2: Baseline Version Copy
Identify the latest version directory in `versions/` (e.g. `versions/26.3`) and copy it to `versions/<mc_version>`:
```bash
cp -r versions/<prev_version> versions/<mc_version>
```

### Step 3: Baseline Git Commit
Stage and commit the copy into the new feature branch:
```bash
git add versions/<mc_version>
git commit -m "Baseline copy from <prev_version> for Minecraft <mc_version>"
```

### Step 4: Automated Packwiz Migration (Option 1)
Within `versions/<mc_version>`:
1. Increment the modpack `version` in `pack.toml` (e.g. `1.2.4` -> `1.2.5`).
2. Run `packwiz refresh` immediately after updating `pack.toml`.
3. Run `packwiz migrate minecraft <mc_version> -y` to auto-accept Fabric loader and compatible mod migrations non-interactively.
4. Run `packwiz update --all -y` to update all remaining components non-interactively.
5. Run `packwiz refresh` to regenerate `index.toml` and synchronize checksums.
6. Commit the migration changes:
   ```bash
   git add versions/<mc_version>
   git commit -m "Migrate to Minecraft <mc_version> and update dependencies"
   ```

### Step 5: Automated Verification & Testing (Before Packaging)
Validate all manifests, hashes, and integrity prior to building artifacts:
```bash
python3 scripts/test_mc_version.py <mc_version>
python3 -m unittest discover tests -v
```

### Step 6: Packaging Artifact
Export the `.mrpack` archive into `builds/` (executed only after tests pass):
```bash
packwiz modrinth export -o ../../builds/Mac\ OS\ Optimized-<mc_version>.mrpack
```

### Step 7: Changelog & Pull Request Creation
1. Update `CHANGELOG.md` under `[Unreleased]` with all updated mods, shaders, and resource packs.
2. Push branch to GitHub: `git push -u origin feat/<mc_version>`.
3. Open a Pull Request targeting `main` following `.github/pull_request_template.md` (mimicking PR #22 / PR #24).
4. **Human Merge Gate:** Stop here. Only a human developer can review and merge the Pull Request into `main`. Do not merge with `gh pr merge`.

---

## One-Command Automation Helper

The entire sequence above can also be executed deterministically via the included helper script:
```bash
python3 scripts/create_new_mc_version.py <mc_version>
```

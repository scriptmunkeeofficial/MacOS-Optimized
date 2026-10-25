---
name: test-mc-version
description: >-
  Validates and tests a Minecraft modpack version without loading the Modrinth App UI.
  Use when the user invokes '/test-mc-version {mc_version}', asks to test without loading Modrinth, or runs a local packwiz development server.
---

# Test Minecraft Modpack Version (`/test-mc-version`)

This skill allows testing and validating a modpack version without importing or launching through the Modrinth App.

## Usage Syntax

```text
/test-mc-version <mc_version> [--serve] [--port 8080]
```

---

## Testing Methods

### Method 1: Fast Automated Integrity Test (Default)
Validates all TOML files, pack index SHA-256 hashes, file references, and `.mrpack` archive structure:
```bash
python3 scripts/test_mc_version.py <mc_version>
```
This runs in under 1 second and verifies:
- TOML syntax across all manifests
- Pack index checksum matching
- SHA-256 file checksums for every mod, shader, and resource pack
- Modrinth `.mrpack` zip archive integrity and `modrinth.index.json` schema

### Method 2: Live Client Testing via Local HTTP Server (`--serve`)
Allows live Minecraft testing in Prism Launcher, MultiMC, or Fabric client without exporting or uploading:
```bash
python3 scripts/test_mc_version.py <mc_version> --serve
```
*or directly with packwiz:*
```bash
cd versions/<mc_version> && packwiz serve --port 8080
```

#### How to Connect Client to Dev Server:
1. In Prism Launcher / MultiMC, create an instance for the target Minecraft version and Fabric loader.
2. Add [packwiz-installer](https://packwiz.infra.link/tutorials/installing/packwiz-installer/) or specify `http://localhost:8080/pack.toml`.
3. Launch instance. It pulls files directly from your local repository over HTTP without needing the Modrinth App.

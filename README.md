# MacOS Optimized

![](https://github.com/scriptmunkeeofficial/MacOS-Optimized/blob/dfaadbe984489cd64c121ef0ae0b1ecb30cf8b29/resources/Pale-Garden.png)

**A Fabric based Modpack for those that play Minecraft on MacOS**

### Packaging this modpack

#### Dependencies

- [packwiz](https://packwiz.infra.link/)
- [GO](https://go.dev/dl/)
- [Modrinth Launcher](https://modrinth.com/app)
- Make

#### Steps to Update Modpack

##### Developer Slash Command (Recommended)

Run the automated slash command inside the agent interface:
```text
/create-new-mc-version <mc_version>
```
*Example:* `/create-new-mc-version 26.4`

Or run the automation script directly:
```bash
python3 scripts/create_new_mc_version.py <mc_version>
```

This automatically:
1. Creates a dedicated feature branch (`feat/<mc_version>`) from `main`.
2. Copies the latest baseline version directory to `versions/<mc_version>`.
3. Commits the baseline copy to the branch.
4. Bumps the pack version and executes `packwiz refresh` immediately.
5. Executes `packwiz migrate minecraft <mc_version> -y` (non-interactive).
6. Updates remaining components with `packwiz update --all -y` and runs `packwiz refresh`.
7. Commits the migration changes atomically.
8. Runs automated pack integrity tests.
9. Packages the `.mrpack` archive to `builds/` (only after tests pass).

---

##### Option 1 - Automated Manual Steps

1. Create a branch: `git checkout -b feat/<mc_version>`
2. Copy previous version folder: `cp -r versions/<prev_version> versions/<mc_version>`
3. Commit the copy: `git add versions/<mc_version> && git commit -m "Baseline copy from <prev_version> for Minecraft <mc_version>"`
4. In `versions/<mc_version>/pack.toml`, update `version` to the next release version (e.g. `1.2.5`).
5. Run `packwiz refresh` immediately after updating `pack.toml`.
6. Run `packwiz migrate minecraft <mc_version> -y` (auto-accepts Fabric loader and mod updates).
7. Run `packwiz update --all -y`.
8. Run `packwiz refresh`.
9. Commit migration: `git add versions/<mc_version> && git commit -m "Migrate to Minecraft <mc_version> and update dependencies"`
10. Run tests: `python3 -m unittest discover tests -v`
11. Package artifact: `packwiz modrinth export -o ../../builds/Mac\ OS\ Optimized-<mc_version>.mrpack`

##### Option 2 - Manual Step-by-Step

- Edit `pack.toml`:
  - Update `version` to the current release version.
  - Update to the target versions of Fabric loader and Minecraft.
- Run `packwiz refresh`
- Run `packwiz update --all`
- Review results and make manual adjustments where needed.

#### Steps to Package Modpack

Export the Modrinth pack:
```bash
cd versions/<version>
packwiz modrinth export -o ../../builds/Mac\ OS\ Optimized-<version>.mrpack
```

#### Test the Modpack

##### Fast Testing (Without Loading Modrinth)

- **Automated Validation:**
  ```bash
  python3 scripts/test_mc_version.py <version>
  ```
  Validates TOML syntax, pack index hashes, file checksums, and `.mrpack` archive integrity in under 1 second.

- **Live Local Dev Server (Prism / MultiMC / packwiz-installer):**
  ```bash
  python3 scripts/test_mc_version.py <version> --serve
  ```
  Or using the slash command:
  ```text
  /test-mc-version <version> --serve
  ```
  Connect your client instance to `http://localhost:8080/pack.toml` without ever importing into Modrinth.

##### Testing with Modrinth Launcher

- Launch Modrinth App -> Add Instance -> Import from file (`builds/Mac OS Optimized-<version>.mrpack`).


#### Make file notes

- copy or include image.png & license file to new folder
- need a way to only have one command with output folder
  - `packwiz modrinth export -o ../../builds/Mac\ OS\ Optimized-1.1.1-test.mrpack`


#### References

- https://fabricmc.net/develop/
- https://unofficial-packwiz-docs.netlify.app/quick-start/

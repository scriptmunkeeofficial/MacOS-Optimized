# MacOS Optimized

A Fabric based Modpack for those that play Minecraft on MacOS

## Packaging this modpack

### Dependencies

- [packwiz](https://packwiz.infra.link/)
- [GO](https://go.dev/dl/)
- [Modrinth Launcher](https://modrinth.com/app)
- Make

### Steps to Update Modpack

- Copy previous version folder to the newest foler version
  - *Example*: `cp versions/1.21.4 versions/1.21.5`
- CD into the new version directory

#### Option 1 - Automated

- Edit `pack.toml` and update the version to the current release version (i.e. 1.1.3)
- Save Change and exit editor
- Run `packwize migrate minecraft <version>`
  - Respond to prompt to update Fabric loader
  - Respond to prompt to update mods

#### Option 2 - Manual

- Edit `pack.toml`
  - update the version to the current release version (i.e. 1.1.3)
  - update to the latest versions of fabric loader and Minecraft (see References)
- Save Change and exit editor
- Run `packwiz refresh`
- Run `packwiz update --all`
- Then review the results and make adjustments where needed

### Steps to Package Modpack

- RUN `packwiz modrinth export -o ../../builds/Mac\ OS\ Optimized-{current_version}.mrpack`


### Test the Modpack

- Launch the Modrinth Minecraft Launcher
- Create


### Make file notes

- copy or include image.png & license file to new folder
- need a way to only have one command with output folder
  - `packwiz modrinth export -o ../../builds/Mac\ OS\ Optimized-1.1.1-test.mrpack`


### References

- https://fabricmc.net/develop/
- https://unofficial-packwiz-docs.netlify.app/quick-start/

# MacOS Optimized

A Fabric based Modpack for those that play Minecraft on MacOS

## Packaging this modpack

### Dependencies

- [packwiz](https://packwiz.infra.link/)
- [GO](https://go.dev/dl/)
- [Modrinth Launcher](https://modrinth.com/app)
- Make

### Steps to package updates

- Edit pack.toml and update version of fabric & minecraft
- Run `packwiz refresh`
- Run `packwiz update --all`


### Steps to package modpack

- Run `packwiz modrinth export`

choosing where to output the package

Run `packwiz modrinth export -o ../builds/Mac\ OS\ Optimized-1.1.1-test.mrpack`

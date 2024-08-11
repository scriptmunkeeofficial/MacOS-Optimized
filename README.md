# MacOS Optimized

A Fabric based Modpack for those that play Minecraft on MacOS

## Packaging this modpack

### Dependencies

- [packwiz](https://packwiz.infra.link/)
- [GO](https://go.dev/)
- Modrinth Launcher

### Steps to package updates

- Edit pack.toml and update version of fabric & minecraft
- Run `packwiz refresh`
- Run `packwiz update --all`


### Steps to package modpack

- Run `packwiz modrinth export`
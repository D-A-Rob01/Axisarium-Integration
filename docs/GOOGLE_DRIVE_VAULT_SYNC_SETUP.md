# Google Drive Vault Sync Setup

## Current Shape

- Live desktop vault: `C:\Users\david\Documents\Axisarium Vault`
- Plugin remote folder: `Axisarium Vault Sync`
- Plugin: Google Drive Vault Sync `0.1.20`
- Rollback copy: `H:\My Drive\Axisarium`
- Desktop baseline sync: complete from local to cloud.

The live vault is intentionally local. Google Drive Vault Sync should be the cloud transport. Avoid opening the old Google Drive Desktop copy as the production vault.

## Google Cloud OAuth

1. Open Google Cloud Console.
2. Create or select a personal project for the vault sync client.
3. Enable the Google Drive API.
4. Configure the OAuth consent screen for personal/internal use.
5. Create an OAuth client suitable for TVs and limited-input devices when available.
6. Use the scope `https://www.googleapis.com/auth/drive.file`.
7. Copy the client ID and client secret into Obsidian's Google Drive Vault Sync settings.

Do not commit the OAuth client secret or the plugin `data.json`.

## Obsidian Desktop

Complete. The desktop vault has authorized Google Drive and seeded the remote state from local.

## Android

1. Install Obsidian and the Google Drive Vault Sync plugin.
2. Open or create a local Axisarium vault on Android.
3. Configure the same OAuth client and remote folder name: `Axisarium Vault Sync`.
4. Prefer `keep-both` conflict behavior at first.
5. For the first Android baseline, pull from cloud to local unless the Android vault is intentionally authoritative.
6. Run manual sync before enabling more automatic behavior.

## Safety Rules

- Keep `keep-both` conflicts until the flow has been tested on both devices.
- Keep plugin backups enabled.
- Do not run destructive reset actions unless the intended source and target are explicit.
- Do not use Google Drive Desktop and Google Drive Vault Sync as active writers for the same live vault.

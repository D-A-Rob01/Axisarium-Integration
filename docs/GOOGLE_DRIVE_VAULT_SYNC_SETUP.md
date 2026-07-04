# Google Drive Vault Sync Setup

## Current Shape

- Live desktop vault: `C:\Users\david\Documents\Axisarium Vault`
- Plugin remote folder: `Axisarium Vault Sync`
- Plugin: Google Drive Vault Sync `0.1.20`
- Rollback copy: `H:\My Drive\Axisarium`

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

1. Open the local vault at `C:\Users\david\Documents\Axisarium Vault`.
2. Open `Settings > Community plugins > Google Drive Vault Sync`.
3. Paste the OAuth client ID and client secret.
4. Confirm the remote folder name is `Axisarium Vault Sync`.
5. Complete the Google device authorization flow.
6. Run a manual backup from the plugin before the first full sync.
7. Run the first manual sync and review the sync status.

## Android

1. Install Obsidian and the Google Drive Vault Sync plugin.
2. Open or create a local Axisarium vault on Android.
3. Configure the same OAuth client and remote folder name: `Axisarium Vault Sync`.
4. Prefer `keep-both` conflict behavior at first.
5. Run manual sync before enabling more automatic behavior.

## Safety Rules

- Keep `keep-both` conflicts until the flow has been tested on both devices.
- Keep plugin backups enabled.
- Do not run destructive reset actions unless the intended source and target are explicit.
- Do not use Google Drive Desktop and Google Drive Vault Sync as active writers for the same live vault.

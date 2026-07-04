# Google Drive and MCP Migration

## Current Homes

- Axisarium code workspace: `C:\Users\david\Documents\Axisarium Integration`
- Live Obsidian vault: `H:\My Drive\Axisarium`
- Previous OneDrive vault: `C:\Users\david\OneDrive\Apps\remotely-save\Axisarium`

The OneDrive vault is no longer the production target. Keep it only as a temporary rollback copy until the Google Drive vault has been opened and verified in Obsidian.

## Completed

- Copied the Axisarium Obsidian vault to the personal Google Drive mount at `H:\My Drive\Axisarium`.
- Updated Obsidian's local vault registry to open `H:\My Drive\Axisarium`.
- Enabled the `obsidian-local-rest-api` community plugin in the Google Drive vault.
- Updated Aletheion and Melographion defaults to use the Google Drive vault path.
- Confirmed MCP Bundles is installed locally and its tunnel status reports as connected.

## Still Manual or Elevated

- Open Obsidian once so the Local REST API with MCP plugin can initialize its settings, certificate, API token, and MCP listener for the Google Drive vault.
- Re-register the `Aletheion Daily Sky` Windows scheduled task from this workspace with administrator rights. The current non-elevated session could not update the existing task registration.
- Re-authenticate or review Remotely Save from inside Obsidian before relying on it for cross-device sync. Its plugin state is intentionally opaque/encrypted, so provider changes should not be made by editing JSON directly.

## Verification Rules

- Treat `H:\My Drive\Axisarium` as the live vault for production checks.
- Do not use the old OneDrive vault for health checks unless explicitly doing rollback verification.
- Do not create new active files or task references under `Prima Midgardia`.

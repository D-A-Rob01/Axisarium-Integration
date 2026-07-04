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
- Verified the Local REST API is listening on HTTPS port `27124`.
- Verified the plugin's MCP endpoint at `https://127.0.0.1:27124/mcp` accepts an MCP initialize request and reports tools/resources support.
- Updated Aletheion and Melographion defaults to use the Google Drive vault path.
- Confirmed MCP Bundles is installed locally and its tunnel status reports as connected.

## Still Manual or Elevated

- Optional: re-register the `Aletheion Daily Sky` Windows scheduled task with administrator rights if wake-to-run and logon catch-up behavior are needed. The non-elevated daily fallback is registered from this workspace.
- Re-authenticate or review Remotely Save from inside Obsidian before relying on it for cross-device sync. Its plugin state is intentionally opaque/encrypted, so provider changes should not be made by editing JSON directly.

## Verification Rules

- Treat `H:\My Drive\Axisarium` as the live vault for production checks.
- Do not use the old OneDrive vault for health checks unless explicitly doing rollback verification.
- Do not create new active files or task references under `Prima Midgardia`.

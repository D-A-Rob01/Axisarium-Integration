# Aletheion

Aletheion is a local, Obsidian-oriented starter kit for a personal astrological and weather-symbolic observatory.

It is built around one rule: astronomy data and interpretation stay separate. The generator will label data as verified, manual, or sample so the symbolic layer does not quietly invent sky facts.

## What This Version Does

- Stores a natal chart reference in `config/aletheion.config.json`
- Reads sky data from a daily manual JSON file
- Falls back to clearly labeled sample sky data when no manual file exists
- Detects major transit-to-natal aspects by longitude and orb
- Calculates Moon phase, illumination, waxing/waning state, and Sun-Moon angle
- Detects prioritized transit-to-natal contacts, same-day exactitude windows, lunations, ingresses, stations, and eclipse alerts
- Labels contact duration scale so fast lunar contacts do not visually compete with multi-month or multi-year outer-planet transits
- Scaffolds natal-house transit support with `natal_house_cusps`
- Writes deterministic Observation-layer records to `memory/observations.jsonl`
- Produces an Obsidian-ready daily note
- Appends a small run record to `memory/events.jsonl`
- Keeps expansion points for weather, Swiss Ephemeris/API data, weekly summaries, and pattern memory

## Quick Start

From the Axisarium Integration workspace root:

```powershell
& "C:\Users\david\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" .\aletheion.py daily
```

By default, the note is written to the active Google Drive-backed Obsidian vault:

```text
C:\Users\david\Documents\Axisarium Vault\02 Daily Sky\Daily Sky - YYYY-MM-DD.md
```

The active production vault path is configured in:

```text
config/aletheion.config.json
```

Current production setting:

```json
"obsidian_vault_path": "C:\\Users\\david\\Documents\\Axisarium Vault",
"daily_note_folder": "02 Daily Sky"
```

To write a one-off local test file, use an explicit `--output` path:

```powershell
& "C:\Users\david\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" .\aletheion.py daily --output ".\scratch\Daily Sky test.md"
```

The old repo-local `vault.retired-2026-06-16/` mirror has been retired. It is historical only and should not be used for production health checks.

## Manual Sky Data

Daily sky data lives in:

```text
data/manual_sky_YYYY-MM-DD.json
```

This starter includes `data/manual_sky_2026-06-09.json` as a sample structure. Replace its values with data from an ephemeris source, astrology API, or a future Swiss Ephemeris integration.

## Swiss Ephemeris / `swetest`

The GitHub repository `arturania/swisseph` is useful as a Swiss Ephemeris source mirror. For Aletheion, the most practical bridge is its command-line program, `swetest`, rather than a direct C binding.

To enable it, compile or obtain a Windows `swetest.exe`, then edit:

```text
config/aletheion.config.json
```

Set:

```json
"ephemeris": {
  "provider": "swetest",
  "swetest_executable": "C:\\Path\\To\\swetest64.exe",
  "ephemeris_files_path": "C:\\Path\\To\\ephe",
  "default_utc_time": "12:00:00",
  "swetest_planet_sequence": "0123456789Dt"
}
```

When `provider` is `swetest` and the executable exists, Aletheion asks Swiss Ephemeris for planetary longitudes and speeds. If the executable is missing or the provider remains `manual`, it uses the manual JSON files.

This project includes an adapted setup script:

```powershell
Set-Location "C:\Users\david\Documents\Axisarium Integration"
.\setup-swiss-ephemeris.ps1
```

It installs into:

```text
swiss-eph/bin/swetest64.exe
swiss-eph/ephe/
```

License note: Swiss Ephemeris is dual-licensed under GPL-2-or-later or the Swiss Ephemeris Professional License. Personal local use is straightforward, but distributing a Swiss Ephemeris-powered Aletheion package would require deliberate license handling.

## Transit & Temporal Awareness Layer

Aletheion now treats astronomy as an authoritative upstream layer and interpretation as downstream commentary.

Daily notes include:

```text
Highest-Priority Natal Contacts
Observations
Interpretive Weather
Today's Exactitude Window
Moon Phase
Raw Sky Data
Active Natal Contacts
Natal House Positions
Lunation Alerts
7-Day Astronomy Alerts
Eclipse Alerts
```

Contact priorities:

```text
Priority 1: exact aspects under 0.5 degrees, or aspects perfecting within 7 days
Priority 2: applying aspects within configured orb
Priority 3: separating aspects within configured orb
Priority 4: sign-level activations, with overflow collapsed beneath the first five
```

Event defaults:

```text
Alert horizon: 7 days
Eclipse horizon: 30 days
Scan step: 6 hours
Eclipse natal-contact orb: 2 degrees
```

## Observation Layer

Aletheion records Observation-layer facts before interpretive weather or Mnemosynthesizer review.

Observation records live in:

```text
memory/observations.jsonl
```

Each record includes:

```text
schema_version: aletheion.observation.v1
layer: observation
kind: sky_body | moon_phase | natal_contact | exactitude | sign_activation | house_position | temporal_event
```

These records do not contain Mnemo markers, promotion fields, AURELIUS vectors, or Interpretive Weather language. They are the mechanical substrate from which later Candidate Memory and Promoted Pattern work can reason.

Generate or backfill observations without rewriting existing Daily Sky notes:

```powershell
& "C:\Users\david\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" .\aletheion.py observations --discover-vault
```

Natal-house support is scaffolded through:

```text
config/aletheion.config.json -> natal_house_cusps
```

Until all 12 cusp longitudes are filled, daily notes will explicitly say that natal house positions are not configured. Once cusps are present, Aletheion assigns transiting bodies to natal houses and detects house ingresses within the 7-day horizon.

## Suggested Next Upgrades

1. Add exact birth date, time, and birthplace to the config.
2. Add exact natal longitudes for every point you care about.
3. Compile or locate `swetest.exe` and set the `ephemeris.provider` to `swetest`.
4. Add a weather provider keyed to your location.
5. Connect the generator to Windows Task Scheduler for daily automation.
6. Add journal reflection fields so the memory layer can discover repeating patterns.

## Morning Automation

Aletheion includes a Task Scheduler installer:

```text
install-aletheion-task.cmd
```

Run that file from normal Windows Explorer or a normal PowerShell window. It registers a daily Windows task named:

```text
Aletheion Daily Sky
```

Default schedule:

```text
Every day at 6:00 AM
```

The scheduled task runs:

```text
run-daily-aletheion.ps1
```

That script generates the daily note directly into the configured Google Drive-backed Obsidian vault:

```text
C:\Users\david\Documents\Axisarium Vault\02 Daily Sky
```

Run logs are written to:

```text
logs
```

# Aletheion Date Integrity Incident — August 2026

## Status

Active remediation on branch `fix/aletheion-date-integrity`.

## Incident

Between 2026-08-09 and 2026-08-11, the live local production chain wrote or referenced Aletheion source filenames using a transposed `YYYY-DD-MM` convention while downstream tandem artifacts were named with canonical `YYYY-MM-DD` dates.

Observed examples:

- requested `2026-08-09` -> malformed source `Daily Sky - 2026-09-08.md`
- requested `2026-08-10` -> malformed source `Daily Sky - 2026-10-08.md`
- requested `2026-08-11` -> malformed source `Daily Sky - 2026-11-08.md`

The repository `main` branch still documents and implements `YYYY-MM-DD`, while live Drive architecture documents were edited to describe `YYYY-DD-MM`. This indicates production drift between the checked-in repository and the local Astræos checkout.

## Root-cause cluster

1. **Canonical date contract drift** — live documentation and likely local production code diverged from ISO `YYYY-MM-DD`.
2. **Dual date resolution** — PowerShell and Python each resolved a date independently instead of sharing one explicit requested date.
3. **Missing producer invariant** — Aletheion did not require requested date, calculated sky date, rendered heading date, and filename date to agree before durable writes.
4. **Unsafe idempotency** — the runner skipped an existing non-empty file without validating date/provenance integrity.
5. **Missing consumer invariant** — Topologos accepted a source whose source filename date disagreed with the tandem requested date.
6. **Repository drift** — the current public repository is older than the live local production implementation and does not contain the current Topologos/MCP production source.
7. **Desktop critical path** — production remains dependent on Astræos Task Scheduler despite an established plan for a desktop-independent Windows GitHub Actions runtime.

## Canonical contract

The only valid production date representation is strict ISO:

```text
YYYY-MM-DD
```

For every production run, all of the following must be identical:

```text
requested_date
Aletheion sky.date
Aletheion filename date
Aletheion H1/declared date
Oneiromnesis Daily Sky anchor date
Topologos requested date
Topologos parsed source filename date
Topologos parsed Aletheion declared date
Topologos dossier/tandem date
Iridescentia reading date
```

Any mismatch is a hard failure. No canonical downstream artifact may be written from a mismatched source.

## Implemented remediation on repair branch

### `tools/run_aletheion_guarded.py`

- resolves default date in `America/New_York`;
- strictly canonicalizes explicit dates with ISO parsing;
- validates existing notes before idempotent skip;
- requires Aletheion + `swetest` + calculated Swiss Ephemeris provenance;
- requires `requested_day == sky.date == rendered H1 date` before any durable write;
- writes observation/event state only after validation succeeds.

### `run-daily-aletheion.ps1`

- resolves one America/New_York calendar date;
- passes that date explicitly to the guarded Python runner;
- no longer lets PowerShell and Python silently choose independent dates.

### `tools/validate_topologos_source.py`

Topologos ingestion must fail unless:

```text
requested date == source filename date == source H1 date
```

and the source contains valid Aletheion / `swetest` / calculated Swiss Ephemeris provenance.

Rejected source exits non-zero (`42`) before tandem rendering.

### `tests/test_date_integrity.py`

Regression fixtures explicitly reject:

- `2026-08-09` -> `2026-09-08`
- `2026-08-10` -> `2026-10-08`
- `2026-08-11` -> `2026-11-08`

## Required local follow-through

The live Astræos checkout must be reconciled with this branch before the scheduler is treated as healthy. In particular, search the live production tree for any of:

```text
YYYY-DD-MM
%Y-%d-%m
yyyy-dd-MM
yyyy-dd-mm
```

and remove all non-ISO Daily Sky filename generation.

The scheduled runner now calls `tools/validate_topologos_source.py` immediately after the guarded producer. The live Topologos tandem call site applies the same gate before reading/rendering the Aletheion source. Validation failure prevents downstream dossier, envelope, manifest, and tandem writes.

`run-daily-aletheion.ps1 -Date YYYY-MM-DD -DryRun` exercises the guarded producer and the Topologos source gate against temporary staging. It removes that staging after validation and does not write the production note, observation/event ledgers, or Oneiromnesis captures.

## Verified 2026-08-15 recovery

Astræos production recovery established the canonical ISO path with a real Swiss Ephemeris run:

- requested date, calculated `sky.date`, filename, and H1 all resolved to `2026-08-15`;
- the source was written as `Daily Sky - 2026-08-15.md` with Aletheion / `swetest` / calculated provenance;
- repeated runs preserved the existing `Oneiromnesis - 2026-08-15.md` capture;
- Topologos consumed the validated source and emitted a non-degraded tandem note, manifest, dossier, and Cabeir envelope bound to the source SHA-256;
- the scheduled task action remained the guarded `run-daily-aletheion.ps1` producer and reported exit code `0`.

The production vault contents remain outside Git. This PR ports only the executable date/provenance controls and regression coverage; it does not copy notes, ledgers, captures, or generated tandem artifacts into the repository.

## Cloud migration

The repair branch hardens local production, but the desired steady state remains a desktop-independent Windows GitHub Actions Aletheion producer. The cloud producer must preserve the same fail-closed date/provenance contract and keep Iridescentia downstream.

Vercel/Cloudflare may later host orchestration, status, MCP, or retrieval surfaces, but they must not become a substitute astronomy authority unless a Linux-compatible Swiss Ephemeris provider passes parity, licensing, and provenance gates.

## Recovery rule for malformed historical files

Do not silently rename a malformed artifact solely from its filename. Before recovery, verify:

1. internal calculated event timestamps;
2. raw sky positions against a fresh authoritative run for the intended date;
3. observation ledger IDs/dates;
4. source provenance;
5. Oneiromnesis anchor;
6. Topologos dossier source hash.

Only then may a malformed file be quarantined, renamed, or regenerated.

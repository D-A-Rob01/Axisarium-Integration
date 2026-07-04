from pathlib import Path

from melographion.backup import build_backup_manifest


def test_backup_manifest_classifies_existing_and_missing_targets(tmp_path: Path):
    vault = tmp_path / "vault"
    existing = vault / "08 Iridescentia" / "Existing.md"
    missing = vault / "08 Iridescentia" / "Missing.md"
    existing.parent.mkdir(parents=True)
    existing.write_text("before", encoding="utf-8")

    manifest = build_backup_manifest(
        vault_path=vault,
        target_paths=[existing, missing],
        backup_root=tmp_path / "backups",
        dry_run=True,
    )

    assert str(existing) in manifest.existing_paths
    assert str(missing) in manifest.missing_paths
    assert manifest.dry_run is True

from __future__ import annotations

import json
import zipfile
from pathlib import Path

from .models import BackupManifest, utcish_now
from .vault_paths import assert_safe_vault_path


def build_backup_manifest(
    *,
    vault_path: Path,
    target_paths: list[Path],
    backup_root: Path,
    dry_run: bool,
) -> BackupManifest:
    existing_paths: list[str] = []
    missing_paths: list[str] = []
    for target in target_paths:
        assert_safe_vault_path(vault_path, target)
        if target.exists():
            existing_paths.append(str(target))
        else:
            missing_paths.append(str(target))

    timestamp = utcish_now().replace(":", "").replace("-", "").replace("+", "_")
    backup_zip = backup_root / f"melographion-backup-{timestamp}.zip"
    manifest_path = backup_root / f"melographion-backup-{timestamp}.json"
    return BackupManifest(
        dry_run=dry_run,
        backup_zip=str(backup_zip),
        manifest_path=str(manifest_path),
        target_paths=[str(path) for path in target_paths],
        existing_paths=existing_paths,
        missing_paths=missing_paths,
    )


def create_backup(manifest: BackupManifest, vault_path: Path) -> BackupManifest:
    if manifest.dry_run:
        return manifest
    if not manifest.backup_zip or not manifest.manifest_path:
        raise ValueError("Backup manifest is missing output paths.")

    zip_path = Path(manifest.backup_zip)
    manifest_path = Path(manifest.manifest_path)
    zip_path.parent.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path_text in manifest.existing_paths:
            path = Path(path_text)
            assert_safe_vault_path(vault_path, path)
            archive.write(path, arcname=str(path.relative_to(vault_path)))

    manifest.dry_run = False
    manifest_path.write_text(
        json.dumps(manifest.model_dump(mode="json"), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return manifest

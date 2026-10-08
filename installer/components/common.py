import shutil
from pathlib import Path

from .. import fsutil, obsidian
from ..model import Context, Result, Support
from ..platform import cache_dir

ROOT = Path(__file__).resolve().parents[2]
MANUAL = "In Obsidian: Einstellungen, Community-Plugins, Eingeschränkten Modus ausschalten."


def supported(platform) -> Support:
    return Support("ja")


def vault_path(ctx: Context) -> Path:
    value = ctx.values.get("vault", "")
    path = Path(value).expanduser()
    if not value or not path.is_absolute():
        raise ValueError("Ein absoluter Vault-Pfad ist erforderlich: --vault PFAD")
    if path.exists() and not path.is_dir():
        raise ValueError(f"Vault-Pfad ist kein Ordner: {path}")
    return path


def prepare(ctx: Context, key: str) -> Result | None:
    if ctx.dry_run:
        return Result(key, "übersprungen", "Vorschau, keine Änderung")
    if obsidian.is_running(ctx):
        return Result(key, "handarbeit", "Obsidian schließen und Installer erneut starten.")
    root = vault_path(ctx)
    reject_config_symlinks(root / ".obsidian")
    if not root.exists() or not any(root.iterdir()):
        ctx.values["new_vault"] = "yes"
    if ctx.values.get("backup_vault") != str(root):
        backup_config(ctx, root)
        ctx.values["backup_vault"] = str(root)
    root.mkdir(parents=True, exist_ok=True)
    return None


def backup_config(ctx: Context, root: Path) -> None:
    directory = cache_dir("obsidian-setup", ctx) / "backups" / root.name
    if directory.resolve().is_relative_to(root.resolve()):
        raise ValueError("Der Cache für Sicherungen muss außerhalb des Vaults liegen.")
    backup = fsutil.backup(root / ".obsidian", directory)
    if backup:
        print(f"Sicherung: {backup}")


def reject_config_symlinks(folder: Path) -> None:
    # Verknüpfte Ziele könnten außerhalb des gesicherten Vaults liegen.
    if folder.is_symlink() or (folder.exists() and any(path.is_symlink() for path in folder.rglob("*"))):
        raise ValueError("Symlink in .obsidian: Bitte die Verknüpfung vor der Einrichtung auflösen.")


def merge_file(source: Path, target: Path) -> None:
    extra = fsutil.read_json(source, {})
    base = fsutil.read_json(target, {})
    merged = fsutil.merge_json(base, extra)
    if not target.exists() or merged != base:
        fsutil.write_json(target, merged)


def copy_if_missing(source: Path, target: Path) -> None:
    if not target.exists():
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)


def manual_steps(ctx: Context) -> tuple[str, ...]:
    if ctx.values.get("new_vault") == "yes":
        return ("Ordner in Obsidian als Tresor öffnen.", MANUAL)
    return (MANUAL,)

from pathlib import Path

from .. import obsidian, ui
from ..model import Result
from .common import prepare, supported, vault_path

KEY = "vault"
TITLE = "Vault"
DESCRIPTION = "Vorhandenen Vault auswählen oder einen neuen Ordner anlegen"
DEFAULT = True
FOLDERS = ("00 Kontext", "01 Inbox", "02 Projekte", "03 Bereiche", "04 Ressourcen", "05 Daily Notes", "06 Archiv", "07 Anhänge")


def select(ctx) -> None:
    if ctx.values.get("vault"):
        vault_path(ctx)
        return
    known = obsidian.known_vaults(ctx)
    for number, path in enumerate(known, 1):
        print(f"  {number}: {path}")
    value = ui.ask_text("Vault-Pfad oder Nummer", str(ctx.home / "Mein Vault"), ctx)
    if value.isdecimal() and 1 <= int(value) <= len(known):
        value = str(known[int(value) - 1])
    ctx.values["vault"] = str(Path(value).expanduser())
    vault_path(ctx)


def is_done(ctx):
    return vault_path(ctx).is_dir() and any(vault_path(ctx).iterdir())


def plan(ctx):
    return [f"Vault: {vault_path(ctx)}", "Standardordner nur in einem leeren Vault anlegen"]


def apply(ctx):
    path = vault_path(ctx)
    empty = not path.exists() or not any(path.iterdir())
    stopped = prepare(ctx, KEY)
    if stopped:
        return stopped
    if empty:
        for folder in FOLDERS:
            (path / folder).mkdir(exist_ok=True)
        ctx.values["new_vault"] = "yes"
    return Result(KEY, "erledigt", str(path))

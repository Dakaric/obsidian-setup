from ..model import Result
from .common import ROOT, copy_if_missing, prepare, supported, vault_path

KEY = "assistent"
TITLE = "Einrichtungsassistent"
DESCRIPTION = "CLAUDE.md für die persönliche Einrichtung des Vaults"
DEFAULT = True


def is_done(ctx):
    return (vault_path(ctx) / "CLAUDE.md").exists()


def plan(ctx):
    return [f"Assistent nach {vault_path(ctx) / 'CLAUDE.md'} kopieren, wenn die Datei fehlt"]


def apply(ctx):
    if is_done(ctx):
        return Result(KEY, "übersprungen", "CLAUDE.md ist bereits vorhanden")
    stopped = prepare(ctx, KEY)
    if stopped:
        return stopped
    copy_if_missing(ROOT / "assistant/CLAUDE.md", vault_path(ctx) / "CLAUDE.md")
    return Result(KEY, "erledigt", "Claude im Vault starten und um die persönliche Einrichtung bitten.")

from .. import fsutil
from ..model import Result
from .common import ROOT, merge_file, prepare, supported, vault_path

KEY = "einstellungen"
TITLE = "Obsidian-Einstellungen"
DESCRIPTION = "Kern-Plugins, Anhänge, Tagesnotizen und Graph-Farben"
DEFAULT = True


def sources():
    return [path for path in sorted((ROOT / "config").glob("*.json")) if path.name != "appearance.json"]


def is_done(ctx):
    for source in sources():
        target = vault_path(ctx) / ".obsidian" / source.name
        if not target.exists():
            return False
        base = fsutil.read_json(target, {})
        if fsutil.merge_json(base, fsutil.read_json(source, {})) != base:
            return False
    return True


def plan(ctx):
    return ["Bestehende .obsidian einmal sichern; JSON ergänzen, vorhandene Werte behalten"]


def apply(ctx):
    stopped = prepare(ctx, KEY)
    if stopped:
        return stopped
    for source in sources():
        merge_file(source, vault_path(ctx) / ".obsidian" / source.name)
    return Result(KEY, "erledigt", "Einstellungen ergänzt, vorhandene Werte beibehalten.")

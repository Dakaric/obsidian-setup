from .. import fsutil, registry
from ..catalog import STYLE_SETTINGS_ID, THEME, PluginSpec
from ..model import Result
from . import plugins
from .common import ROOT, copy_if_missing, merge_file, prepare, supported, vault_path

KEY = "aussehen"
TITLE = "Aussehen"
DESCRIPTION = "AnuPpuccin, Style Settings und farbige Tagesnotizen"
DEFAULT = True
STYLE = PluginSpec(STYLE_SETTINGS_ID, "Style Settings", "extra")


def is_done(ctx):
    folder = vault_path(ctx) / ".obsidian"
    required = [folder / "themes" / THEME / name for name in ("theme.css", "manifest.json")]
    required += [folder / "snippets/daily-notes-magenta.css", folder / "appearance.json"]
    if not all(path.is_file() for path in required) or not plugins.plugin_done(STYLE, ctx):
        return False
    base = fsutil.read_json(folder / "appearance.json", {})
    return fsutil.merge_json(base, fsutil.read_json(ROOT / "config/appearance.json", {})) == base


def plan(ctx):
    return ["Theme und Style Settings von den Autoren laden", "Farben und Snippet ergänzen, vorhandene Einstellungen behalten"]


def apply(ctx):
    stopped = prepare(ctx, KEY)
    if stopped:
        return stopped
    folder = vault_path(ctx) / ".obsidian"
    theme = folder / "themes" / THEME
    if not all((theme / name).is_file() for name in ("theme.css", "manifest.json")):
        stopped = plugins.stage_download(ctx, lambda target: registry.download_theme(THEME, target), theme, KEY)
        if stopped:
            return stopped
    plugin_result = plugins.install_plugin(STYLE, ctx)
    detail = f"{STYLE.title}: {plugin_result.status}. {plugin_result.detail}".rstrip()
    result = Result(KEY, plugin_result.status, detail, plugin_result.next_steps)
    if plugin_result.status != "erledigt":
        return result
    stopped = prepare(ctx, KEY)
    if stopped:
        return stopped
    merge_file(ROOT / "config/appearance.json", folder / "appearance.json")
    copy_if_missing(ROOT / "config/snippets/daily-notes-magenta.css", folder / "snippets/daily-notes-magenta.css")
    return result

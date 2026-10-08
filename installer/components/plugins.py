import shutil
import tempfile
from dataclasses import replace
from pathlib import Path

from .. import fsutil, registry, shell, ui
from ..catalog import PLUGINS, PluginSpec, group_description
from ..model import Result
from ..platform import cache_dir
from .common import ROOT, manual_steps, merge_file, prepare, supported, vault_path

KEY = "plugins-basis"
TITLE = "Basis-Plugins"
DESCRIPTION = group_description("basis")
DEFAULT = True
PREREQUISITES = {
    "git": ("git", "Git installieren: https://git-scm.com/downloads"),
    "Claude Code": ("claude", "Claude Code installieren und anmelden: https://code.claude.com/docs/de/setup"),
    "Ollama": ("ollama", "Ollama installieren und starten: https://ollama.com/download"),
}


def plugin_complete(spec, ctx):
    folder = vault_path(ctx) / ".obsidian/plugins" / spec.id
    if not (folder / "main.js").is_file() or not (folder / "manifest.json").is_file():
        return False
    manifest = fsutil.read_json(folder / "manifest.json", {})
    return manifest.get("id") == spec.id


def plugin_done(spec, ctx):
    if not plugin_complete(spec, ctx):
        return False
    enabled = fsutil.read_json(vault_path(ctx) / ".obsidian/community-plugins.json", [])
    if spec.id not in enabled:
        return False
    source = ROOT / "settings" / f"{spec.id}.json"
    if not source.exists():
        return True
    target = vault_path(ctx) / ".obsidian/plugins" / spec.id / "data.json"
    base = fsutil.read_json(target, {})
    return target.exists() and fsutil.merge_json(base, fsutil.read_json(source, {})) == base


def stage_download(ctx, download, target, key):
    cache = cache_dir("obsidian-setup", ctx)
    cache.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix="download-", dir=cache))
    try:
        download(staging)
        stopped = prepare(ctx, key)
        if stopped:
            return stopped
        target.mkdir(parents=True, exist_ok=True)
        for path in staging.iterdir():
            shutil.copy2(path, target / path.name)
    finally:
        fsutil.safe_rmtree(staging, cache)


def install_plugin(spec: PluginSpec, ctx) -> Result:
    prerequisite = PREREQUISITES.get(spec.requires)
    if prerequisite and not shell.which(prerequisite[0]):
        return Result(spec.id, "handarbeit", prerequisite[1])
    stopped = prepare(ctx, spec.id)
    if stopped:
        return stopped
    folder = vault_path(ctx) / ".obsidian/plugins" / spec.id
    if not plugin_complete(spec, ctx):
        stopped = stage_download(ctx, lambda target: registry.download_plugin(spec.id, target), folder, spec.id)
        if stopped:
            return stopped
    source = ROOT / "settings" / f"{spec.id}.json"
    if source.exists():
        merge_file(source, folder / "data.json")
    enabled_path = vault_path(ctx) / ".obsidian/community-plugins.json"
    enabled = fsutil.read_json(enabled_path, [])
    fsutil.write_json(enabled_path, fsutil.merge_json(enabled, [spec.id]))
    detail = ""
    if spec.requires == "Google-Konto":
        detail = "Im Plugin mit dem Google-Konto anmelden."
    if spec.requires == "Ollama":
        detail = "Ollama starten und das Bildmodell aus den Plugin-Einstellungen laden."
    return Result(spec.id, "erledigt", detail, manual_steps(ctx))


def group_specs(group):
    return [spec for spec in PLUGINS if spec.group == group]


def group_done(group, ctx):
    return all(plugin_done(spec, ctx) for spec in group_specs(group))


def group_plan(group, ctx):
    return [f"{spec.title}: {spec.note}" + (f". Voraussetzung: {spec.requires}" if spec.requires else "") for spec in group_specs(group)]


def apply_group(group, ctx):
    key = f"plugins-{group}"
    stopped = prepare(ctx, key)
    if stopped:
        return stopped
    results = []
    for spec in group_specs(group):
        if plugin_done(spec, ctx):
            results.append(Result(spec.title, "übersprungen", "schon eingerichtet"))
            continue
        if not ui.ask_yes_no(f"{spec.title} installieren?", True, ctx):
            continue
        try:
            results.append(replace(install_plugin(spec, ctx), key=spec.title))
        except Exception as error:
            results.append(Result(spec.title, "fehler", str(error)))
    return group_result(key, results)


def group_result(key, results):
    status = "übersprungen"
    for candidate in ("fehler", "handarbeit", "erledigt"):
        if any(result.status == candidate for result in results):
            status = candidate
            break
    detail = "; ".join(f"{result.key}: {result.status}. {result.detail}".rstrip() for result in results)
    next_steps = tuple(step for result in results for step in result.next_steps)
    return Result(key, status, detail or "Keine Plugins gewählt", next_steps)


def is_done(ctx):
    return group_done("basis", ctx)


def plan(ctx):
    return group_plan("basis", ctx)


def apply(ctx):
    return apply_group("basis", ctx)

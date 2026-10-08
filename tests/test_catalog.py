import importlib
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def read(relative):
    path = ROOT / relative
    assert path.exists(), f"Fehlende Vorlage: {relative}"
    return json.loads(path.read_text(encoding="utf-8"))


def catalog():
    assert (ROOT / "installer/catalog.py").exists(), "Katalog fehlt"
    return importlib.import_module("installer.catalog")


def test_catalog_ids_unique():
    plugins = catalog().PLUGINS
    assert len({p.id for p in plugins}) == len(plugins) == 12
    assert {p.group for p in plugins} == {"basis", "extra", "ki"}


def test_every_setting_file_belongs_to_catalog():
    module = catalog()
    files = list((ROOT / "settings").glob("*.json"))
    assert len(files) == 10
    assert {f.stem for f in files} <= {p.id for p in module.PLUGINS} | {module.STYLE_SETTINGS_ID}


@pytest.mark.parametrize("plugin,keys", [
    ("ai-image-analyzer", "aiAdapterSettings.ollamaSettings.token"),
    ("ai-image-analyzer", "aiAdapterSettings.geminiSettings.apiKey"),
    ("obsidian-excalidraw-plugin", "taskboneAPIkey"),
    ("obsidian-excalidraw-plugin", "openAIAPIToken"),
    ("obsidian42-brat", "personalAccessToken"),
    ("obsidian42-brat", "globalTokenName"),
])
def test_settings_have_no_secrets(plugin, keys):
    data = read(f"settings/{plugin}.json")
    for key in keys.split("."):
        data = data[key]
    assert data == ""


def test_brat_lists_empty():
    data = read("settings/obsidian42-brat.json")
    assert data["pluginList"] == data["pluginSubListFrozenVersion"] == []


@pytest.mark.parametrize("key,expected", [
    ("autoSaveInterval", 0), ("autoPullInterval", 0),
    ("autoPullOnBoot", False), ("autoPushInterval", 0),
])
def test_git_automation_disabled_by_default(key, expected):
    assert read("settings/obsidian-git.json")[key] == expected


@pytest.mark.parametrize("module_name,group", [("plugins", "basis"), ("plugins_extra", "extra")])
def test_group_description_follows_catalog(module_name, group, monkeypatch):
    module = importlib.import_module(f"installer.components.{module_name}")
    original = catalog().PLUGINS
    with monkeypatch.context() as patch:
        patch.setattr(catalog(), "PLUGINS", original + (catalog().PluginSpec("probe", "Katalog-Probe", group),))
        try:
            importlib.reload(module)
            assert "Katalog-Probe" in module.DESCRIPTION
        finally:
            patch.setattr(catalog(), "PLUGINS", original)
            importlib.reload(module)


def test_core_plugins_without_sync():
    assert "sync" not in read("config/core-plugins.json")


def test_graph_without_private_group():
    data = read("config/graph.json")
    assert not any("08 Privat" in group["query"] for group in data["colorGroups"])


def test_no_plugin_programs_vendored():
    assert not list((ROOT / "settings").rglob("*.js"))
    assert not list((ROOT / "config").rglob("main.js"))

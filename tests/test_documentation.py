import re
import shlex
from pathlib import Path

import pytest

from installer.catalog import PLUGINS

ROOT = Path(__file__).resolve().parents[1]
# Abgleich mit obsidianmd/obsidian-releases, community-plugins.json.
PLUGIN_REPOS = {
    "Dataview": "blacksmithgu/obsidian-dataview",
    "Templater": "silentvoid13/Templater",
    "Tasks": "obsidian-tasks-group/obsidian-tasks",
    "Omnisearch": "scambier/obsidian-omnisearch",
    "Excalidraw": "zsviczian/obsidian-excalidraw-plugin",
    "Text Extractor": "scambier/obsidian-text-extractor",
    "Datacore": "blacksmithgu/datacore",
    "BRAT": "tfthacker/obsidian42-brat",
    "Git": "vinzent03/obsidian-git",
    "Claudian": "yishentu/claudian",
    "AI Image Analyzer": "swaggeroo/obsidian-ai-image-analyzer",
    "Star NotebookLM": "starhunt/star-notebooklm",
    "Style Settings": "obsidian-community/obsidian-style-settings",
}


@pytest.mark.parametrize("title,repo", PLUGIN_REPOS.items())
def test_readme_plugin_links_match_registry(title, repo):
    text = (ROOT / "README.md").read_text(encoding="utf-8")
    row = next(line for line in text.splitlines() if line.startswith(f"| {title} |") or line.startswith(f"| {title} (`"))
    assert f"https://github.com/{repo}".lower() in row.lower()


def test_readme_covers_catalog():
    assert {spec.title for spec in PLUGINS} | {"Style Settings"} == set(PLUGIN_REPOS)


def test_assistant_requires_consent_before_adding_to_existing_files():
    text = (ROOT / "assistant/CLAUDE.md").read_text(encoding="utf-8")
    phase = text.split("### Phase 8:", 1)[1]
    assert "Vorhandene Dateien nie überschreiben." in phase
    assert "Gibt es eine Datei schon, zeig den Vorschlag und frag, ob ergänzt werden soll." in phase
    assert "ERSETZT" not in phase
    assert "gerade erst erstellt" not in text
    greeting = text.split("### Phase 1:", 1)[1].split("### Phase 2:", 1)[0]
    assert "vorhandene Notizen" in greeting


def test_windows_claude_command_preserves_git_bash_arguments():
    text = (ROOT / "CLAUDE.md").read_text(encoding="utf-8")
    command = next(line for line in text.splitlines() if line.startswith("powershell "))
    arguments = shlex.split(command)
    assert arguments[:5] == ["powershell", "-ExecutionPolicy", "Bypass", "-File", "./install.ps1"]
    assert arguments[arguments.index("--only") + 1] == "vault,assistent,einstellungen"
    assert arguments[arguments.index("--vault") + 1] == "C:/Pfad/zum/Vault"
    assert "Git Bash" in text


def test_readme_describes_verified_runs_and_opt_in_git():
    text = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "noch online geprüft werden" not in text
    assert "Plugin-Downloads sind auf macOS echt getestet, die CI prüft alle drei Systeme." in text
    assert "Das Plugin sichert erst, wenn du es selbst einstellst." in text
    assert re.search(r"-File.*Kommaliste", text)

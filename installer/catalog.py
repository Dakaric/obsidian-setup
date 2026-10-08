from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class PluginSpec:
    id: str
    title: str
    group: Literal["basis", "extra", "ki"]
    note: str = ""
    requires: str = ""


PLUGINS = (
    PluginSpec("dataview", "Dataview", "basis", "Notizen abfragen"),
    PluginSpec("templater-obsidian", "Templater", "basis", "Vorlagen verwenden"),
    PluginSpec("obsidian-tasks-plugin", "Tasks", "basis", "Aufgaben verwalten"),
    PluginSpec("omnisearch", "Omnisearch", "basis", "Inhalte durchsuchen"),
    PluginSpec("obsidian-excalidraw-plugin", "Excalidraw", "extra", "Skizzen zeichnen"),
    PluginSpec("text-extractor", "Text Extractor", "extra", "Text aus Bildern und PDFs lesen"),
    PluginSpec("datacore", "Datacore", "extra", "Datenansichten erstellen"),
    PluginSpec("obsidian42-brat", "BRAT", "extra", "Beta-Plugins verwalten"),
    PluginSpec("obsidian-git", "Git", "extra", "Versionen verwalten", "git"),
    PluginSpec("realclaudian", "Claudian", "ki", "Claude im Vault nutzen", "Claude Code"),
    PluginSpec("ai-image-analyzer", "AI Image Analyzer", "ki", "Bilder beschreiben", "Ollama"),
    PluginSpec("star-notebooklm", "Star NotebookLM", "ki", "NotebookLM anbinden", "Google-Konto"),
)
THEME = "AnuPpuccin"
STYLE_SETTINGS_ID = "obsidian-style-settings"


def group_description(group: str) -> str:
    return ", ".join(spec.title for spec in PLUGINS if spec.group == group)

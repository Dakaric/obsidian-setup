# Obsidian einrichten

Dieses Repo richtet einen neuen oder bestehenden Obsidian-Vault ein: Ordnerstruktur, Einstellungen, Theme und ausgewählte Plugins. Ein optionaler Claude-Assistent hilft anschließend beim persönlichen Profil und den ersten Notizen.

Der Installer verändert keine Notizen. Vor dem ersten Schreiben sichert er die vorhandene `.obsidian` in seinem Cache unter `backups/<Vault-Name>/.obsidian.sicherung-JJJJMMTT-HHMMSS` und zeigt den vollständigen Pfad an. Die Sicherung liegt außerhalb des Vaults, damit auch Plugin-Daten mit Zugangsschlüsseln nicht über dessen Git-Repo oder Sync verteilt werden. Bei mehreren Sicherungen in derselben Sekunde kommt eine laufende Nummer dazu. Vorhandene JSON-Werte gewinnen, Listen werden ohne zusätzliche Duplikate ergänzt. Eine vorhandene `CLAUDE.md` bleibt erhalten.

## Installation

Installiere [Obsidian](https://obsidian.md/download) und schließe es vor dem Einrichten. Lade dieses Repo herunter oder klone es mit Git. Öffne ein Terminal im Repo-Ordner und starte:

macOS oder Linux:

```bash
bash ./install.sh
```

Windows, in PowerShell:

```powershell
powershell -ExecutionPolicy Bypass -File .\install.ps1
```

Die Starthilfe installiert bei Bedarf `uv` über [Astral](https://docs.astral.sh/uv/). `uv` stellt Python 3.12 bereit. Downloads benötigen Internetzugang. Der Installer selbst nutzt nur die Python-Standardbibliothek.

Du kannst einen bekannten Vault aus der Liste wählen oder einen absoluten Pfad eingeben. Fehlende Ordner werden angelegt. Nur in einem leeren Vault entstehen die Standardordner `00 Kontext`, `01 Inbox`, `02 Projekte`, `03 Bereiche`, `04 Ressourcen`, `05 Daily Notes`, `06 Archiv` und `07 Anhänge`.

## Bausteine

| Schlüssel | Inhalt | Standard |
|---|---|---|
| `vault` | Vault auswählen und leere Vaults vorbereiten | ja |
| `assistent` | Einrichtungsassistent als `CLAUDE.md` | ja |
| `aussehen` | AnuPpuccin, Style Settings und Tagesnotizen-Snippet | ja |
| `plugins-basis` | Suche, Aufgaben und Vorlagen | ja |
| `plugins-extra` | Zeichnungen, Texterkennung, Datacore, BRAT und Git | nein |
| `plugins-ki` | Claudian, Bildanalyse und NotebookLM | nein |
| `einstellungen` | Kern-Plugins, Anhänge, Tagesnotizen und Graph-Farben | ja |

Jedes Plugin wird interaktiv einzeln abgefragt. `--yes` übernimmt Standardantworten. `--only` wählt die genannten Bausteine ausdrücklich aus, auch optionale Gruppen. Mit `--yes --only plugins-extra` werden deshalb alle noch fehlenden Extra-Plugins gewählt, soweit ihre Voraussetzungen erfüllt sind.

Vorschau ohne Downloads und ohne Änderungen am Vault:

```bash
bash ./install.sh --dry-run --yes --vault "$HOME/Mein Vault"
```

Nur Assistent und Einstellungen installieren:

```bash
bash ./install.sh --yes --only assistent,einstellungen --vault "$HOME/Mein Vault"
```

Unter Windows funktionieren dieselben Schalter:

```powershell
powershell -ExecutionPolicy Bypass -File .\install.ps1 --dry-run --yes --vault "$HOME\Mein Vault"
```

Der Aufruf über `-File` übergibt auch die Kommaliste von `--only assistent,einstellungen` korrekt als ein Argument. Claude Code nutzt unter Windows Git Bash; dort lautet der Skriptpfad `./install.ps1`, ein absoluter Vault-Pfad zum Beispiel `C:/Pfad/zum/Vault`.

Auch bei `--only` wird der Vault-Pfad vorab bestimmt. Ohne Terminal ist `--yes` erforderlich. Exit-Code `0` bedeutet, dass kein Baustein fehlgeschlagen ist; die Übersicht kann trotzdem Handarbeit nennen. `1` meldet einen fehlgeschlagenen Baustein, `2` ungültige Argumente oder fehlende Eingaben.

## Plugins und Herkunft

Plugin-Programmdateien und das Theme sind nicht Teil dieses Repos. Der Installer löst IDs im [offiziellen Obsidian-Verzeichnis](https://github.com/obsidianmd/obsidian-releases/blob/HEAD/community-plugins.json) auf und lädt `main.js`, `manifest.json` sowie gegebenenfalls `styles.css` aus dem neuesten veröffentlichten Release der Autoren. Bereits vollständig installierte Plugins werden beibehalten; Updates erfolgen anschließend über Obsidian. Die jeweiligen Lizenzen der Autoren gelten weiter.

| Plugin | Gruppe | Zweck | Voraussetzung | Quelle |
|---|---|---|---|---|
| Dataview | Basis | Notizen abfragen | keine | [Repo](https://github.com/blacksmithgu/obsidian-dataview) |
| Templater | Basis | Vorlagen verwenden | keine | [Repo](https://github.com/SilentVoid13/Templater) |
| Tasks | Basis | Aufgaben verwalten | keine | [Repo](https://github.com/obsidian-tasks-group/obsidian-tasks) |
| Omnisearch | Basis | Inhalte durchsuchen | keine | [Repo](https://github.com/scambier/obsidian-omnisearch) |
| Excalidraw | Extra | Skizzen zeichnen | keine | [Repo](https://github.com/zsviczian/obsidian-excalidraw-plugin) |
| Text Extractor | Extra | Text aus Bildern und PDFs lesen | keine | [Repo](https://github.com/scambier/obsidian-text-extractor) |
| Datacore | Extra | Datenansichten erstellen | keine | [Repo](https://github.com/blacksmithgu/datacore) |
| BRAT | Extra | Beta-Plugins verwalten | keine | [Repo](https://github.com/TfTHacker/obsidian42-brat) |
| Git | Extra | Versionen verwalten | Git im PATH, eigenes Git-Repo | [Repo](https://github.com/Vinzent03/obsidian-git) |
| Claudian (`realclaudian`) | KI | Claude im Vault nutzen | Claude Code installiert und angemeldet | [Repo](https://github.com/yishentu/claudian) |
| AI Image Analyzer | KI | Bilder beschreiben | Ollama und Bildmodell | [Repo](https://github.com/swaggeroo/obsidian-ai-image-analyzer) |
| Star NotebookLM | KI | NotebookLM anbinden | Google-Konto | [Repo](https://github.com/starhunt/star-notebooklm) |
| Style Settings | Aussehen | Theme-Farben setzen | keine | [Repo](https://github.com/obsidian-community/obsidian-style-settings) |

Der Installer verwendet für alle Plugins ausschließlich die aktuelle Registry-Zuordnung und meldet fehlende IDs als Fehler.

Das Theme [AnuPpuccin](https://github.com/AnubisNekhet/AnuPpuccin) wird anhand des [Theme-Verzeichnisses](https://github.com/obsidianmd/obsidian-releases/blob/HEAD/community-css-themes.json) vom dort angegebenen Zweig geladen, sonst vom Standardzweig. `aussehen` ergänzt Theme-Auswahl und Snippet. `einstellungen` aktiviert kein abgewähltes Theme. Eine bereits gewählte Darstellung bleibt erhalten.

Die mitgelieferten Plugin-Einstellungen enthalten keine Zugangsschlüssel. Bestehende Schlüssel im Vault bleiben beim Zusammenführen erhalten. BRAT erhält keine vorinstallierte Liste zusätzlicher Repos. Für Git sind automatische Commits, Pulls und Pushes in den Vorgaben deaktiviert. Das Plugin sichert erst, wenn du es selbst einstellst. Bestehende eigene Einstellungen bleiben erhalten; ein Remote oder Git-Repo wird nicht eingerichtet. AI Image Analyzer nutzt standardmäßig lokales Ollama mit `llama3.2-vision:11b`; das Modell muss separat geladen werden. Google- und Claude-Anmeldung erfolgen außerhalb des Installers.

## Nach der Einrichtung

Öffne einen neuen Ordner in Obsidian als Tresor. Gehe zu **Einstellungen → Community-Plugins** und schalte den eingeschränkten Modus aus. Diesen Schalter setzt der Installer nicht, weil Obsidian ihn außerhalb der Vault-Konfiguration speichert.

Die Konfiguration legt Anhänge unter `07 Anhänge` und Tagesnotizen unter `05 Daily Notes` ab, sofern du noch keine eigenen Werte gesetzt hast. Obsidian Sync wird nicht neu aktiviert. Bei bestehenden Vaults werden keine zusätzlichen Notizordner angelegt; prüfe dort die Zielordner deiner Einstellungen.

Läuft Obsidian, melden schreibende Bausteine Handarbeit. Schließe Obsidian und starte den Installer erneut. Netzwerkfehler oder GitHub-Rate-Limits erscheinen als Fehler, weitere Bausteine laufen weiter. Für authentifizierte GitHub-API-Anfragen kannst du `GITHUB_TOKEN` in deiner Umgebung setzen. Der Token wird nicht gespeichert.

Zur Wiederherstellung Obsidian schließen, die aktuelle `.obsidian` umbenennen und die gewünschte Sicherung zurück nach `.obsidian` kopieren. Der Installer löscht keine Vault-Inhalte. Temporäre Downloads werden nur innerhalb seines Cache-Ordners entfernt: `~/.cache/obsidian-setup` auf macOS/Linux, `%LOCALAPPDATA%\obsidian-setup\cache` auf Windows.

## Einrichtung mit Claude

Starte Claude Code im Repo-Ordner und sage: „Führe die Einrichtung aus.“ Die [Repo-Anleitung](CLAUDE.md) lässt Claude den Pfad und die Bausteine erfragen und den Installer mit `--yes --only` ausführen.

Danach kannst du Claude im Vault starten. Die [Assistentenvorlage](assistant/CLAUDE.md) fragt nach Profil, Projekten, Bereichen und Ressourcen. Erst nach deiner Bestätigung erstellt sie persönliche Dateien. Für vorhandene Dateien einschließlich der `CLAUDE.md` zeigt sie die vorgeschlagenen Ergänzungen und fragt nach Zustimmung. Bereits vorhandene Vault-Anleitungen werden vom Installer nicht ersetzt.

Der Installer überträgt keine Notizen. Die gewählten KI-Plugins können Daten an ihre jeweiligen Dienste senden; beachte deren Einstellungen.

## Unterstützung und Tests

| Bausteine | macOS | Linux | Windows |
|---|---|---|---|
| Vault, Assistent, Einstellungen, Aussehen | unterstützt | unterstützt | unterstützt |
| Basis- und Extra-Plugins | unterstützt | unterstützt | unterstützt |
| KI-Plugins | mit genannten Voraussetzungen | mit genannten Voraussetzungen | mit genannten Voraussetzungen |

Die Tests simulieren Plattformpfade und Prozesse für alle drei Systeme. Plugin-Downloads sind auf macOS echt getestet, die CI prüft alle drei Systeme. PowerShell wird lokal nur geprüft, wenn es installiert ist. Linux berücksichtigt normale Obsidian-Installationen, Flatpak und Snap. Mobile Systeme sind nicht vorgesehen.

```bash
uv run --offline --python 3.12 pytest -q
```

Offline müssen die Testpakete bereits im uv-Cache liegen. Die Tests blockieren echte Netzaufrufe und verwenden kontrollierte Antworten für Downloads. GitHub Actions führt Tests und Vorschau auf Ubuntu, macOS und Windows aus. Die MIT-Lizenz in [LICENSE](LICENSE) gilt für dieses Repo.

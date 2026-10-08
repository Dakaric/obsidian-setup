# Einrichtung mit Claude

Wenn der Nutzer „Führe die Einrichtung aus“ sagt:

1. Lies die README. Frage nach dem absoluten Vault-Pfad und den gewünschten Bausteinen: `vault`, `assistent`, `aussehen`, `plugins-basis`, `plugins-extra`, `plugins-ki`, `einstellungen`.
2. Erkläre die Voraussetzungen der gewählten Plugin-Gruppen. Mit `--yes` werden innerhalb einer gewählten Gruppe alle noch fehlenden Plugins gewählt. Wenn nur einzelne Plugins gewünscht sind, nutze den interaktiven Installer in einem echten Terminal.
3. Bitte darum, Obsidian zu schließen. Erhalte vorhandene Notizen und Einstellungen.
4. Rufe die Starthilfe mit `--yes`, `--only` und dem Vault-Pfad auf. Claudes Shell hat kein TTY. Baue die Liste für `--only` ausschließlich aus den zuvor gewählten Bausteinen. Übergib Pfade als eigenes Argument.

Beispiel unter macOS oder Linux, nach Auswahl dieser drei Bausteine:

```bash
bash ./install.sh --yes --only vault,assistent,einstellungen --vault "$HOME/Mein Vault"
```

Beispiel unter Windows: Claude Code nutzt Git Bash. Führe dort PowerShell über `-File` aus:

```bash
powershell -ExecutionPolicy Bypass -File ./install.ps1 --yes --only vault,assistent,einstellungen --vault "C:/Pfad/zum/Vault"
```

Bei gewünschter Vorschau ergänze `--dry-run`. Melde abschließend die tatsächlichen Ergebnisse und die nötigen Schritte in Obsidian. Bei Fehlern behaupte keine erfolgreiche Installation. Vorhandene `CLAUDE.md` im Vault wird nicht ersetzt. Der kopierte Vault-Assistent fragt anschließend nach dem persönlichen Profil und der gewünschten Struktur.

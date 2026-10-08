import json
import subprocess
import sys
from pathlib import Path

import pytest

from installer import cli, fsutil, obsidian, registry
from installer.platform import cache_dir
from installer.catalog import PLUGINS
from installer.components import appearance, assistant, plugins, settings, vault
from installer.model import Context, Result


@pytest.fixture
def ctx(tmp_path, monkeypatch):
    monkeypatch.setattr(obsidian, "is_running", lambda ctx: False)
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "local"))
    return Context("linux", tmp_path, False, True, {"vault": str(tmp_path / "Mein Vault")})


def root(ctx):
    return Path(ctx.values["vault"])


@pytest.fixture
def fake_downloads(monkeypatch):
    def plugin(plugin_id, target):
        target.mkdir(parents=True, exist_ok=True)
        fsutil.write_json(target / "manifest.json", {"id": plugin_id, "version": "1"})
        (target / "main.js").write_text("code", encoding="utf-8")
    def theme(name, target):
        target.mkdir(parents=True, exist_ok=True)
        fsutil.write_json(target / "manifest.json", {"name": name})
        (target / "theme.css").write_text("body {}", encoding="utf-8")
    monkeypatch.setattr(registry, "download_plugin", plugin)
    monkeypatch.setattr(registry, "download_theme", theme)


def test_paths_with_spaces_and_umlauts(ctx):
    assert vault.apply(ctx).status == "erledigt"
    assert (root(ctx) / "07 Anhänge").is_dir()
    assert settings.apply(ctx).status == "erledigt"
    data = (root(ctx) / ".obsidian/app.json").read_text(encoding="utf-8")
    assert "07 Anhänge" in data


def test_existing_nonempty_vault_gets_no_folders(ctx):
    root(ctx).mkdir()
    (root(ctx) / "Notiz.md").write_text("bleibt", encoding="utf-8")
    vault.apply(ctx)
    assert list(root(ctx).iterdir()) == [root(ctx) / "Notiz.md"]


@pytest.mark.parametrize("module", [vault, assistant, appearance, settings, plugins])
def test_refuses_while_obsidian_runs(module, ctx, monkeypatch):
    monkeypatch.setattr(obsidian, "is_running", lambda ctx: True)
    assert module.apply(ctx).status == "handarbeit"
    assert not root(ctx).exists()


def test_assistant_never_overwrites_claude_md(ctx):
    root(ctx).mkdir()
    path = root(ctx) / "CLAUDE.md"
    path.write_text("Eigene Regeln", encoding="utf-8")
    assert assistant.apply(ctx).status == "übersprungen"
    assert path.read_text(encoding="utf-8") == "Eigene Regeln"


@pytest.mark.parametrize("platform_name", ["macos", "linux", "windows"])
def test_backup_once_before_first_write(platform_name, ctx, capsys):
    ctx.platform = platform_name
    folder = root(ctx) / ".obsidian"
    fsutil.write_json(folder / "app.json", {"own": 1})
    fsutil.write_json(folder / "plugins/example/data.json", {"token": "test-token"})
    settings.apply(ctx)
    assistant.apply(ctx)
    backups = list((cache_dir("obsidian-setup", ctx) / "backups" / root(ctx).name).glob(".obsidian.sicherung-*"))
    assert len(backups) == 1
    assert not list(root(ctx).glob(".obsidian.sicherung-*"))
    assert fsutil.read_json(backups[0] / "app.json", {}) == {"own": 1}
    assert fsutil.read_json(backups[0] / "plugins/example/data.json", {}) == {"token": "test-token"}
    assert not (backups[0] / "daily-notes.json").exists()
    assert capsys.readouterr().out.count(str(backups[0])) == 1


def test_backup_refuses_cache_inside_vault(ctx, monkeypatch):
    folder = root(ctx) / ".obsidian"
    fsutil.write_json(folder / "app.json", {"own": 1})
    monkeypatch.setattr("installer.components.common.cache_dir", lambda *args: root(ctx) / "cache")
    with pytest.raises(ValueError, match="außerhalb des Vaults"):
        settings.apply(ctx)
    assert fsutil.read_json(folder / "app.json", {}) == {"own": 1}
    assert not (root(ctx) / "cache").exists()


def test_plugin_enabled_once(ctx, fake_downloads):
    plugins.install_plugin(PLUGINS[0], ctx)
    plugins.install_plugin(PLUGINS[0], ctx)
    assert fsutil.read_json(root(ctx) / ".obsidian/community-plugins.json", []) == ["dataview"]


def test_existing_plugin_data_wins(ctx, fake_downloads):
    path = root(ctx) / ".obsidian/plugins/dataview/data.json"
    fsutil.write_json(path, {"refreshInterval": 999, "own": True})
    plugins.install_plugin(PLUGINS[0], ctx)
    data = fsutil.read_json(path, {})
    assert data["refreshInterval"] == 999 and data["own"] is True
    assert "renderNullAs" in data


def test_merge_keeps_user_entries(ctx, fake_downloads):
    path = root(ctx) / ".obsidian/community-plugins.json"
    fsutil.write_json(path, ["own-plugin"])
    plugins.install_plugin(PLUGINS[0], ctx)
    assert fsutil.read_json(path, []) == ["own-plugin", "dataview"]


def test_missing_prerequisite_is_manual_step(ctx, monkeypatch):
    monkeypatch.setattr("installer.shell.which", lambda name: None)
    spec = next(p for p in PLUGINS if p.id == "obsidian-git")
    result = plugins.install_plugin(spec, ctx)
    assert result.status == "handarbeit"
    assert "https://git-scm.com" in result.detail
    assert not root(ctx).exists()


def test_download_failure_is_reported_and_next_plugin_runs(ctx, fake_downloads, monkeypatch):
    original = registry.download_plugin
    def download(plugin_id, target):
        if plugin_id == "dataview":
            raise registry.DownloadError("Download fehlgeschlagen: offline")
        original(plugin_id, target)
    monkeypatch.setattr(registry, "download_plugin", download)
    result = plugins.apply(ctx)
    assert result.status == "fehler"
    assert "offline" in result.detail
    assert "templater-obsidian" in fsutil.read_json(root(ctx) / ".obsidian/community-plugins.json", [])


def test_appearance_installs_theme_style_settings_and_snippet(ctx, fake_downloads):
    result = appearance.apply(ctx)
    assert result.status == "erledigt"
    assert any("Eingeschränkten Modus ausschalten" in step for step in result.next_steps)
    folder = root(ctx) / ".obsidian"
    assert (folder / "themes/AnuPpuccin/theme.css").exists()
    assert (folder / "snippets/daily-notes-magenta.css").exists()
    assert fsutil.read_json(folder / "appearance.json", {})["cssTheme"] == "AnuPpuccin"
    assert fsutil.read_json(folder / "community-plugins.json", []) == ["obsidian-style-settings"]


def test_settings_does_not_activate_unselected_appearance(ctx):
    settings.apply(ctx)
    assert not (root(ctx) / ".obsidian/appearance.json").exists()


def test_dry_run_does_not_create_vault(ctx, monkeypatch):
    monkeypatch.setattr(registry, "download_plugin", lambda *args: pytest.fail("Download"))
    assert cli.main(["--yes", "--dry-run", "--vault", str(root(ctx))]) == 0
    assert not root(ctx).exists()


def test_only_settings_resolves_vault_without_vault_component(ctx):
    assert cli.main(["--yes", "--only", "einstellungen", "--vault", str(root(ctx))]) == 0
    assert (root(ctx) / ".obsidian/app.json").exists()


@pytest.mark.parametrize("name,relative", [
    ("macos", "Library/Application Support/obsidian"),
    ("linux", ".config/obsidian"),
    ("linux", ".var/app/md.obsidian.Obsidian/config/obsidian"),
    ("linux", "snap/obsidian/current/.config/obsidian"),
    ("windows", "roaming/obsidian"),
])
def test_known_vaults_per_platform(name, relative, tmp_path, monkeypatch):
    ctx = Context(name, tmp_path, False, True, {})
    monkeypatch.setenv("APPDATA", str(tmp_path / "roaming"))
    fsutil.write_json(tmp_path / relative / "obsidian.json", {"vaults": {"a": {"path": str(tmp_path / "Mein Vault")}, "b": {"ts": 1}}})
    assert obsidian.known_vaults(ctx) == [tmp_path / "Mein Vault"]


@pytest.mark.parametrize("name,output,expected", [("macos", "", False), ("linux", "", False), ("windows", "INFO: Keine Aufgaben", False), ("windows", "Obsidian.exe 123", True)])
def test_is_running_ignores_own_process(name, output, expected, tmp_path, monkeypatch):
    calls = []
    def execute(command, **kwargs):
        calls.append(command)
        return subprocess.CompletedProcess(command, 0 if name == "windows" else 1, output, "")
    monkeypatch.setattr(subprocess, "run", execute)
    monkeypatch.setattr("installer.shell.which", lambda name: None)
    ctx = Context(name, tmp_path, False, True, {})
    assert obsidian.is_running(ctx) is expected
    assert all("-f" not in command for command in calls)
    if name != "windows":
        assert calls[0] == ["pgrep", "-x", "Obsidian" if name == "macos" else "obsidian"]


def test_flatpak_process_detected(tmp_path, monkeypatch):
    def execute(command, **kwargs):
        return subprocess.CompletedProcess(command, 0 if command[0] == "flatpak" else 1, "md.obsidian.Obsidian" if command[0] == "flatpak" else "", "")
    monkeypatch.setattr(subprocess, "run", execute)
    monkeypatch.setattr("installer.shell.which", lambda name: "/bin/flatpak")
    assert obsidian.is_running(Context("linux", tmp_path, False, True, {}))


def test_symlinked_config_is_not_written(ctx, tmp_path):
    outside = tmp_path / "outside"
    outside.mkdir()
    root(ctx).mkdir()
    try:
        (root(ctx) / ".obsidian").symlink_to(outside, target_is_directory=True)
    except OSError:
        pytest.skip("Symlinks benötigen auf diesem Windows zusätzliche Rechte")
    with pytest.raises(ValueError, match="Symlink"):
        settings.apply(ctx)
    assert not list(outside.iterdir())


def test_symlinked_setting_is_not_written(ctx, tmp_path):
    outside = tmp_path / "outside.json"
    outside.write_text('{"own": true}', encoding="utf-8")
    folder = root(ctx) / ".obsidian"
    folder.mkdir(parents=True)
    try:
        (folder / "app.json").symlink_to(outside)
    except OSError:
        pytest.skip("Symlinks benötigen auf diesem Windows zusätzliche Rechte")
    with pytest.raises(ValueError, match="Symlink"):
        settings.apply(ctx)
    assert outside.read_text(encoding="utf-8") == '{"own": true}'


def test_corrupt_json_is_not_replaced(ctx):
    folder = root(ctx) / ".obsidian"
    folder.mkdir(parents=True)
    (folder / "app.json").write_text("kein JSON", encoding="utf-8")
    assert cli.main(["--yes", "--only", "einstellungen", "--vault", str(root(ctx))]) == 1
    assert (folder / "app.json").read_text(encoding="utf-8") == "kein JSON"


@pytest.mark.parametrize("platform_name", ["macos", "linux", "windows"])
def test_full_install_is_repeatable(platform_name, ctx, fake_downloads, monkeypatch):
    ctx.platform = platform_name
    monkeypatch.setattr("installer.platform.detect", lambda: platform_name)
    monkeypatch.setattr(Path, "home", lambda: ctx.home)
    args = ["--yes", "--vault", str(root(ctx))]
    assert cli.main(args) == 0
    folder = root(ctx) / ".obsidian"
    fsutil.write_json(folder / "app.json", {"attachmentFolderPath": "Eigene Anhänge", "own": 42})
    assert cli.main(args) == 0
    assert cli.main(args) == 0
    assert fsutil.read_json(folder / "app.json", {})["attachmentFolderPath"] == "Eigene Anhänge"
    enabled = fsutil.read_json(folder / "community-plugins.json", [])
    assert len(enabled) == len(set(enabled)) == 5
    assert not list(root(ctx).glob(".obsidian.sicherung-*"))
    backups = cache_dir("obsidian-setup", ctx) / "backups" / root(ctx).name
    assert len(list(backups.glob(".obsidian.sicherung-*"))) == 1


def test_process_output_reads_utf8_independent_of_locale(monkeypatch):
    monkeypatch.setattr("locale.getencoding", lambda: "cp1252")
    command = [sys.executable, "-c",
               "import sys; sys.stdout.buffer.write('Anhänge'.encode('utf-8')); "
               "sys.stderr.buffer.write('Prüfung'.encode('utf-8'))"]
    result = obsidian.process_output(command)
    assert result.returncode == 0
    assert result.stdout == "Anhänge"
    assert result.stderr == "Prüfung"


@pytest.mark.parametrize("name", ["windows", "linux"])
def test_failed_process_inspection_refuses_write(name, tmp_path, monkeypatch):
    def execute(command, **kwargs):
        return subprocess.CompletedProcess(command, 1 if command[0] == "pgrep" else 2, "", "error")
    monkeypatch.setattr(subprocess, "run", execute)
    monkeypatch.setattr("installer.shell.which", lambda name: "/bin/flatpak")
    with pytest.raises(OSError, match="Prozessprüfung"):
        obsidian.is_running(Context(name, tmp_path, False, True, {}))


def test_obsidian_starting_during_download_prevents_config_write(ctx, fake_downloads, monkeypatch):
    download = registry.download_theme
    def start_after_download(name, target):
        download(name, target)
        monkeypatch.setattr(obsidian, "is_running", lambda ctx: True)
    monkeypatch.setattr(registry, "download_theme", start_after_download)
    result = appearance.apply(ctx)
    assert result.status == "handarbeit"
    assert not (root(ctx) / ".obsidian/appearance.json").exists()
    assert not (root(ctx) / ".obsidian/themes/AnuPpuccin/theme.css").exists()


def test_new_vault_hint_without_vault_component(ctx, fake_downloads):
    result = plugins.install_plugin(PLUGINS[0], ctx)
    assert result.status == "erledigt"
    assert result.detail == ""
    assert result.next_steps == (
        "Ordner in Obsidian als Tresor öffnen.",
        "In Obsidian: Einstellungen, Community-Plugins, Eingeschränkten Modus ausschalten.",
    )


def test_existing_vault_only_needs_plugin_activation(ctx, fake_downloads):
    root(ctx).mkdir()
    (root(ctx) / "Notiz.md").write_text("bleibt", encoding="utf-8")
    result = plugins.install_plugin(PLUGINS[0], ctx)
    assert result.next_steps == (
        "In Obsidian: Einstellungen, Community-Plugins, Eingeschränkten Modus ausschalten.",
    )


def test_full_install_summary_shows_plugins_and_next_steps_once(ctx, fake_downloads, monkeypatch, capsys):
    monkeypatch.setattr("installer.shell.which", lambda name: "/bin/available")
    groups = "vault,assistent,aussehen,plugins-basis,plugins-extra,plugins-ki,einstellungen"
    assert cli.main(["--yes", "--only", groups, "--vault", str(root(ctx))]) == 0
    output = capsys.readouterr().out
    summary = output.split("Ergebnis:", 1)[1]
    for spec in (*PLUGINS, appearance.STYLE):
        assert summary.count(spec.title + ":") == 1
    assert output.count("Nächste Schritte:") == 1
    assert output.count("Ordner in Obsidian als Tresor öffnen") == 1
    assert output.count("Eingeschränkten Modus ausschalten") == 1
    for spec in PLUGINS:
        assert output.count(f"{spec.title}: {spec.note}") == 1
    assert "handarbeit" not in summary


@pytest.mark.parametrize("plugin_id,hint", [
    ("ai-image-analyzer", "Ollama starten"),
    ("star-notebooklm", "Google-Konto anmelden"),
])
def test_installed_plugin_keeps_only_specific_hint(plugin_id, hint, ctx, fake_downloads, monkeypatch):
    monkeypatch.setattr("installer.shell.which", lambda name: "/bin/available")
    result = plugins.install_plugin(next(spec for spec in PLUGINS if spec.id == plugin_id), ctx)
    assert result.status == "erledigt"
    assert hint in result.detail
    assert "Eingeschränkten Modus" not in result.detail


@pytest.mark.parametrize("status", ["fehler", "handarbeit"])
def test_appearance_propagates_style_settings_failure(status, ctx, fake_downloads, monkeypatch):
    monkeypatch.setattr(plugins, "install_plugin", lambda *args: Result(appearance.STYLE.id, status, "Style fehlgeschlagen"))
    result = appearance.apply(ctx)
    assert result.key == "aussehen"
    assert result.status == status
    assert "Style fehlgeschlagen" in result.detail
    assert not (root(ctx) / ".obsidian/appearance.json").exists()

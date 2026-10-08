import subprocess
from pathlib import Path, PureWindowsPath
from types import SimpleNamespace

import pytest

from installer import cli, fsutil, platform, shell, ui
from installer.model import Context, Result, Support
from installer.run import run_components


@pytest.fixture
def ctx(tmp_path):
    return Context("linux", tmp_path, False, True, {})


def component(key="test", **overrides):
    values = dict(KEY=key, TITLE=key, DESCRIPTION="Beschreibung", DEFAULT=True,
                  supported=lambda p: Support("ja"), is_done=lambda c: False,
                  plan=lambda c: ["Schreiben"], apply=lambda c: Result(key, "erledigt"))
    return SimpleNamespace(**(values | overrides))


def test_merge_keeps_user_entries():
    assert fsutil.merge_json({"own": 1, "nested": {"value": False}},
                             {"other": 2, "nested": {"value": True, "new": 3}}) == {
        "own": 1, "other": 2, "nested": {"value": False, "new": 3}}


def test_merge_lists_without_duplicates():
    assert fsutil.merge_json({"items": ["a"]}, {"items": ["a", "b"]}) == {"items": ["a", "b"]}


def test_merge_top_level_list():
    assert fsutil.merge_json(["a", "b"], ["b", "c"]) == ["a", "b", "c"]


def test_merge_list_of_dicts():
    assert fsutil.merge_json([{"a": 1}], [{"a": 1}, {"a": 2}]) == [{"a": 1}, {"a": 2}]


def test_backup_names_copy_with_timestamp(tmp_path):
    source = tmp_path / "datei.json"
    source.write_text("ä", encoding="utf-8")
    first, second = fsutil.backup(source), fsutil.backup(source)
    assert first != second
    assert first.name.startswith("datei.json.sicherung-")
    assert first.read_text(encoding="utf-8") == "ä"
    assert fsutil.backup(tmp_path / "missing") is None


def test_backup_directory(tmp_path):
    folder = tmp_path / ".obsidian"
    folder.mkdir()
    (folder / "own").write_text("Grüße", encoding="utf-8")
    assert (fsutil.backup(folder) / "own").read_text(encoding="utf-8") == "Grüße"


def test_safe_rmtree_refuses_outside_root(tmp_path):
    with pytest.raises(ValueError):
        fsutil.safe_rmtree(tmp_path / "other", tmp_path / "cache")


def test_safe_rmtree_refuses_root_itself(tmp_path):
    with pytest.raises(ValueError):
        fsutil.safe_rmtree(tmp_path, tmp_path)


def test_safe_rmtree_removes_child(tmp_path):
    child = tmp_path / "child"
    child.mkdir()
    fsutil.safe_rmtree(child, tmp_path)
    assert not child.exists()


@pytest.mark.parametrize("name", ["macos", "linux", "windows"])
def test_cache_dir_per_platform(name, ctx, monkeypatch):
    ctx.platform = name
    monkeypatch.setenv("LOCALAPPDATA", str(ctx.home / "local"))
    assert platform.cache_dir("app", ctx) == (ctx.home / "local/app/cache" if name == "windows" else ctx.home / ".cache/app")


def test_no_tty_without_yes_exits_2(monkeypatch, capsys):
    monkeypatch.setattr("sys.stdin.isatty", lambda: False)
    assert cli.main([]) == 2
    assert "--yes" in capsys.readouterr().out


def test_failing_component_does_not_stop_others(ctx):
    def fail(c):
        raise OSError("kaputt")
    results = run_components([component(apply=fail), component("next")], ctx, None)
    assert [r.status for r in results] == ["fehler", "erledigt"]


@pytest.mark.parametrize("stage", ["supported", "is_done", "plan"])
def test_failure_in_preparation_does_not_stop_others(stage, ctx):
    def fail(*args):
        raise ValueError("kaputt")
    results = run_components([component(**{stage: fail}), component("next")], ctx, None)
    assert [r.status for r in results] == ["fehler", "erledigt"]


def test_dry_run_applies_nothing(ctx):
    ctx.dry_run = True
    def fail(c):
        pytest.fail("apply wurde aufgerufen")
    assert run_components([component(apply=fail)], ctx, None)[0].status == "übersprungen"


def test_only_selects_optional_component(ctx):
    assert run_components([component(DEFAULT=False)], ctx, {"test"})[0].status == "erledigt"


def test_unknown_only_is_error(tmp_path):
    assert cli.main(["--yes", "--only", "typo", "--vault", str(tmp_path)]) == 2


def test_relative_vault_is_error():
    assert cli.main(["--yes", "--vault", "relative"]) == 2


def test_summary_deduplicates_and_numbers_next_steps(capsys):
    ui.print_summary([Result("first", "erledigt", next_steps=("Öffnen", "Aktivieren")),
                      Result("second", "erledigt", next_steps=("Aktivieren", "Anmelden"))])
    assert capsys.readouterr().out.split("Nächste Schritte:\n")[1].splitlines() == [
        "  1. Öffnen", "  2. Aktivieren", "  3. Anmelden"]


@pytest.mark.parametrize("path_type", [Path, PureWindowsPath])
def test_shell_preserves_argument_boundaries(path_type, ctx, monkeypatch):
    calls = []
    def execute(cmd, **kwargs):
        calls.append((cmd, kwargs))
        return subprocess.CompletedProcess(cmd, 0, "", "")
    monkeypatch.setattr(subprocess, "run", execute)
    vault_path = str(path_type(ctx.home) / "Mein Vault" / "07 Anhänge")
    shell.run(["tool", vault_path], ctx)
    assert calls[0][0] == ["tool", vault_path]
    assert not calls[0][1].get("shell", False)
    ctx.dry_run = True
    assert shell.run(["tool"], ctx) is None
    assert len(calls) == 1


def test_assume_yes_uses_default(ctx):
    assert ui.ask_yes_no("Frage", False, ctx) is False
    assert ui.ask_text("Pfad", "Vorgabe", ctx) == "Vorgabe"

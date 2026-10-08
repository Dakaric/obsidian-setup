import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]


def write_recorder(path):
    path.write_text(
        'import json, os, sys\n'
        'print(json.dumps([sys.argv[1:], os.environ["PYTHONPATH"]], ensure_ascii=False))\n'
        'sys.exit(int(os.environ["TEST_EXIT_CODE"]))\n',
        encoding="utf-8",
    )


def test_shell_launcher_from_foreign_directory(tmp_path):
    if not shutil.which("bash") or sys.platform == "win32":
        pytest.skip("Bash-Starthilfe auf Unix")
    assert (ROOT / "install.sh").exists()
    fake = tmp_path / "bin"
    fake.mkdir()
    executable = fake / "uv"
    executable.write_text('#!/bin/sh\nexec "$TEST_PYTHON" "$TEST_RECORDER" "$@"\n', encoding="utf-8")
    executable.chmod(0o755)
    recorder = tmp_path / "record.py"
    write_recorder(recorder)
    env = os.environ | {"PATH": str(fake) + os.pathsep + os.environ["PATH"], "TEST_PYTHON": sys.executable, "TEST_RECORDER": str(recorder), "TEST_EXIT_CODE": "7"}
    result = subprocess.run(["bash", str(ROOT / "install.sh"), "--yes", "--vault", str(tmp_path / "Mein Vault/07 Anhänge")], cwd=tmp_path, env=env, capture_output=True, text=True, encoding="utf-8")
    assert result.returncode == 7
    arguments, pythonpath = json.loads(result.stdout)
    assert arguments == ["run", "--directory", str(ROOT), "--no-project", "--python", "3.12", "python", "-m", "installer", "--yes", "--vault", str(tmp_path / "Mein Vault/07 Anhänge")]
    assert pythonpath == str(ROOT)


@pytest.mark.parametrize("exit_code", [0, 7])
def test_powershell_launcher_from_foreign_directory(tmp_path, exit_code):
    powershell = shutil.which("pwsh") or shutil.which("powershell")
    if not powershell:
        pytest.skip("PowerShell nicht installiert; CI prüft diesen Pfad")
    repo = tmp_path / "Starthilfe Grüße"
    repo.mkdir()
    shutil.copy2(ROOT / "install.ps1", repo / "install.ps1")
    recorder = tmp_path / "Argumente prüfen.py"
    write_recorder(recorder)
    script = tmp_path / "probe.ps1"
    script.write_text(
        '[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)\n'
        'function global:uv {\n'
        '    [Console]::WriteLine((ConvertTo-Json -InputObject $args -Compress))\n'
        '    & $env:TEST_PYTHON $env:TEST_RECORDER @args\n'
        '    $global:LASTEXITCODE = $LASTEXITCODE\n'
        '}\n'
        '& $env:TEST_LAUNCHER @args\n'
        'exit $LASTEXITCODE\n',
        encoding="utf-8",
    )
    env = os.environ | {
        "TEST_LAUNCHER": str(repo / "install.ps1"), "TEST_PYTHON": sys.executable,
        "TEST_RECORDER": str(recorder), "TEST_EXIT_CODE": str(exit_code),
    }
    arguments = ["--yes", "--only", "vault,assistent,einstellungen",
                 "--vault", str(tmp_path / "Mein Vault" / "07 Anhänge")]
    result = subprocess.run(
        [powershell, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(script), *arguments],
        cwd=tmp_path, env=env, capture_output=True, text=True, encoding="utf-8",
    )
    assert result.returncode == exit_code, result.stderr
    raw_arguments, recorded = [json.loads(line) for line in result.stdout.splitlines()]
    expected = ["run", "--directory", str(repo), "--no-project", "--python", "3.12",
                "python", "-m", "installer", *arguments]
    assert raw_arguments == expected
    assert all(isinstance(argument, str) for argument in raw_arguments)
    assert recorded == [expected, str(repo)]

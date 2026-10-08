import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]


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
    recorder.write_text('import json,os,sys\nprint(json.dumps([sys.argv[1:], os.environ["PYTHONPATH"]]))\nsys.exit(7)\n')
    env = os.environ | {"PATH": str(fake) + os.pathsep + os.environ["PATH"], "TEST_PYTHON": sys.executable, "TEST_RECORDER": str(recorder)}
    result = subprocess.run(["bash", str(ROOT / "install.sh"), "--yes", "--vault", str(tmp_path / "Mein Vault/07 Anhänge")], cwd=tmp_path, env=env, capture_output=True, text=True)
    assert result.returncode == 7
    arguments, pythonpath = json.loads(result.stdout)
    assert arguments == ["run", "--directory", str(ROOT), "--no-project", "--python", "3.12", "python", "-m", "installer", "--yes", "--vault", str(tmp_path / "Mein Vault/07 Anhänge")]
    assert pythonpath == str(ROOT)


def test_powershell_launcher_from_foreign_directory(tmp_path):
    powershell = shutil.which("pwsh") or shutil.which("powershell")
    if not powershell:
        pytest.skip("PowerShell nicht installiert; Windows-CI prüft diesen Pfad")
    assert (ROOT / "install.ps1").exists()
    script = tmp_path / "probe.ps1"
    script.write_text('function global:uv { [Console]::WriteLine(($args | ConvertTo-Json -Compress)); [Console]::WriteLine($env:PYTHONPATH); $global:LASTEXITCODE = 7 }\n& $env:TEST_LAUNCHER --yes --vault $env:TEST_VAULT\n', encoding="utf-8")
    env = os.environ | {"TEST_LAUNCHER": str(ROOT / "install.ps1"), "TEST_VAULT": str(tmp_path / "Mein Vault/07 Anhänge")}
    result = subprocess.run([powershell, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(script)], cwd=tmp_path, env=env, capture_output=True, text=True, encoding="utf-8")
    assert result.returncode == 7
    lines = result.stdout.strip().splitlines()
    args = json.loads(lines[0])
    assert args == ["run", "--directory", str(ROOT), "--no-project", "--python", "3.12", "python", "-m", "installer", "--yes", "--vault", env["TEST_VAULT"]]
    assert lines[1] == str(ROOT)

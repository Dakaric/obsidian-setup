import os
import subprocess
from pathlib import Path

from . import fsutil, shell
from .model import Context


def config_dirs(ctx: Context) -> list[Path]:
    if ctx.platform == "macos":
        return [ctx.home / "Library/Application Support/obsidian"]
    if ctx.platform == "windows":
        return [Path(os.environ.get("APPDATA", ctx.home / "AppData/Roaming")) / "obsidian"]
    return [ctx.home / ".config/obsidian",
            ctx.home / ".var/app/md.obsidian.Obsidian/config/obsidian",
            ctx.home / "snap/obsidian/current/.config/obsidian"]


def known_vaults(ctx: Context) -> list[Path]:
    found = []
    for directory in config_dirs(ctx):
        try:
            records = fsutil.read_json(directory / "obsidian.json", {}).get("vaults", {})
            for record in records.values():
                value = record.get("path") if isinstance(record, dict) else None
                if isinstance(value, str) and value and Path(value) not in found:
                    found.append(Path(value))
        except (OSError, ValueError, AttributeError) as error:
            print(f"Vault-Liste nicht lesbar: {directory}: {error}")
    return found


def process_output(command: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(command, capture_output=True, text=True, errors="replace", check=False)


def is_running(ctx: Context) -> bool:
    if ctx.platform == "windows":
        result = process_output(["tasklist", "/FI", "IMAGENAME eq Obsidian.exe"])
        if result.returncode != 0:
            raise OSError("Obsidian-Prozessprüfung fehlgeschlagen. tasklist konnte nicht ausgeführt werden.")
        return "obsidian.exe" in result.stdout.lower()
    name = "Obsidian" if ctx.platform == "macos" else "obsidian"
    result = process_output(["pgrep", "-x", name])
    if result.returncode == 0:
        return True
    if result.returncode != 1:
        raise OSError("Obsidian-Prozessprüfung fehlgeschlagen. Obsidian schließen und erneut versuchen.")
    if ctx.platform == "linux" and shell.which("flatpak"):
        result = process_output(["flatpak", "ps"])
        if result.returncode != 0:
            raise OSError("Obsidian-Prozessprüfung fehlgeschlagen. flatpak ps konnte nicht ausgeführt werden.")
        return "md.obsidian.Obsidian" in result.stdout
    return False

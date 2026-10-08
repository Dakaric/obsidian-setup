import os
import sys
from pathlib import Path

from .model import Context, Platform


def detect() -> Platform:
    if sys.platform == "darwin":
        return "macos"
    if sys.platform == "win32":
        return "windows"
    if sys.platform.startswith("linux"):
        return "linux"
    raise ValueError(f"System nicht unterstützt: {sys.platform}")


def cache_dir(app: str, ctx: Context) -> Path:
    if ctx.platform == "windows":
        return Path(os.environ.get("LOCALAPPDATA", ctx.home / "AppData/Local")) / app / "cache"
    return ctx.home / ".cache" / app

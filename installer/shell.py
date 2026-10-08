import shutil
import subprocess

from .model import Context


def run(cmd: list[str], ctx: Context, check: bool = True) -> subprocess.CompletedProcess | None:
    if ctx.dry_run:
        print(f"Würde ausführen: {cmd}")
        return None
    return subprocess.run(cmd, check=check)


def which(name: str) -> str | None:
    return shutil.which(name)

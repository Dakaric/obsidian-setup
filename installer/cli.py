import argparse
import sys
from pathlib import Path

from . import platform, registry, ui
from .components import COMPONENTS, vault
from .model import Context
from .run import run_components


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description="Obsidian-Vault einrichten")
    result.add_argument("--yes", action="store_true", help="Standardantworten verwenden")
    result.add_argument("--dry-run", action="store_true", help="Nur den Plan anzeigen")
    result.add_argument("--only", help="Nur diese Bausteine (mit Komma getrennt)")
    result.add_argument("--vault", help="Absoluter Pfad zum Vault")
    return result


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    args = parser().parse_args(argv)
    if not sys.stdin.isatty() and not args.yes:
        print("Ohne Terminal bitte --yes und gegebenenfalls --only verwenden.")
        return 2
    only = {key.strip() for key in args.only.split(",")} if args.only is not None else None
    if only is not None and not only <= {component.KEY for component in COMPONENTS}:
        print("Unbekannter Baustein. Verfügbar: " + ", ".join(c.KEY for c in COMPONENTS))
        return 2
    try:
        ctx = Context(platform.detect(), Path.home(), args.dry_run, args.yes, {})
        if args.vault:
            ctx.values["vault"] = args.vault
        vault.select(ctx)
    except (OSError, ValueError, EOFError) as error:
        print(f"Einrichtung nicht möglich: {error}")
        return 2
    registry.clear_cache()
    results = run_components(COMPONENTS, ctx, only)
    ui.print_summary(results)
    return 1 if any(result.status == "fehler" for result in results) else 0

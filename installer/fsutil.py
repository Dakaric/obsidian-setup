import json
import shutil
from copy import deepcopy
from datetime import datetime
from pathlib import Path

Json = dict | list


def backup(path: Path, directory: Path | None = None) -> Path | None:
    if not path.exists():
        return None
    directory = directory if directory is not None else path.parent
    directory.mkdir(parents=True, exist_ok=True)
    suffix = datetime.now().strftime("%Y%m%d-%H%M%S")
    target = directory / f"{path.name}.sicherung-{suffix}"
    counter = 1
    while target.exists():
        target = directory / f"{path.name}.sicherung-{suffix}-{counter}"
        counter += 1
    if path.is_dir():
        shutil.copytree(path, target, symlinks=True)
    else:
        shutil.copy2(path, target)
    return target


def merge_json(base: Json, extra: Json) -> Json:
    if isinstance(base, dict) and isinstance(extra, dict):
        merged = deepcopy(base)
        for key, value in extra.items():
            merged[key] = merge_json(base[key], value) if key in base else deepcopy(value)
        return merged
    if isinstance(base, list) and isinstance(extra, list):
        merged = deepcopy(base)
        for value in extra:
            if value not in merged:
                merged.append(deepcopy(value))
        return merged
    return deepcopy(base)


def read_json(path: Path, empty: Json) -> Json:
    if not path.exists():
        return deepcopy(empty)
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, type(empty)):
        raise ValueError(f"Unerwartete JSON-Struktur: {path}")
    return data


def write_json(path: Path, data: Json) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def safe_rmtree(path: Path, allowed_root: Path) -> None:
    resolved, root = path.resolve(), allowed_root.resolve()
    if resolved == root or not resolved.is_relative_to(root) or path.is_symlink():
        raise ValueError(f"Löschen außerhalb des Cache-Unterordners verweigert: {path}")
    shutil.rmtree(path)

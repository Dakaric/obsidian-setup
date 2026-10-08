import json
import os
import urllib.request
from functools import lru_cache
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse

PLUGIN_REGISTRY = "https://raw.githubusercontent.com/obsidianmd/obsidian-releases/HEAD/community-plugins.json"
THEME_REGISTRY = "https://raw.githubusercontent.com/obsidianmd/obsidian-releases/HEAD/community-css-themes.json"


class DownloadError(Exception):
    pass


def fetch(url: str) -> bytes:
    headers = {"User-Agent": "obsidian-setup"}
    if os.environ.get("GITHUB_TOKEN") and urlparse(url).hostname == "api.github.com":
        headers["Authorization"] = f"Bearer {os.environ['GITHUB_TOKEN']}"
    try:
        request = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(request, timeout=60) as response:
            return response.read()
    except HTTPError as error:
        if error.code == 403 and error.headers.get("X-RateLimit-Remaining") == "0":
            raise DownloadError("GitHub-Rate-Limit erreicht. Später erneut versuchen oder GITHUB_TOKEN setzen.") from error
        raise DownloadError(f"Download fehlgeschlagen (HTTP {error.code}): {url}") from error
    except (URLError, OSError, TimeoutError) as error:
        raise DownloadError(f"Download fehlgeschlagen: {url}. Verbindung prüfen und erneut versuchen.") from error


def decode_json(data: bytes):
    try:
        return json.loads(data)
    except (ValueError, UnicodeError) as error:
        raise DownloadError("Download enthält kein gültiges JSON.") from error


@lru_cache(maxsize=2)
def read_registry(url: str) -> list[dict]:
    data = decode_json(fetch(url))
    if not isinstance(data, list) or not all(isinstance(row, dict) for row in data):
        raise DownloadError("Das offizielle Verzeichnis hat ein unerwartetes Format.")
    return data


def clear_cache() -> None:
    read_registry.cache_clear()


def find_entry(url: str, field: str, value: str) -> dict:
    for entry in read_registry(url):
        if entry.get(field) == value and isinstance(entry.get("repo"), str):
            return entry
    raise DownloadError(f"Im offiziellen Verzeichnis nicht gefunden: {value}")


def plugin_repo(plugin_id: str) -> str:
    return find_entry(PLUGIN_REGISTRY, "id", plugin_id)["repo"]


def theme_repo(name: str) -> str:
    return find_entry(THEME_REGISTRY, "name", name)["repo"]


def write_assets(target: Path, files: dict[str, bytes]) -> None:
    target.mkdir(parents=True, exist_ok=True)
    for name, data in files.items():
        (target / name).write_bytes(data)


def download_plugin(plugin_id: str, target_dir: Path) -> None:
    repo = plugin_repo(plugin_id)
    release = decode_json(fetch(f"https://api.github.com/repos/{repo}/releases/latest"))
    if not isinstance(release, dict) or not isinstance(release.get("assets"), list):
        raise DownloadError(f"Ungültige Release-Daten: {plugin_id}")
    assets = {item.get("name"): item.get("browser_download_url") for item in release["assets"] if isinstance(item, dict)}
    if not all(assets.get(name) for name in ("main.js", "manifest.json")):
        raise DownloadError(f"Release unvollständig: {plugin_id}. main.js oder manifest.json fehlt.")
    files = {name: fetch(assets[name]) for name in ("manifest.json", "main.js", "styles.css") if assets.get(name)}
    manifest = decode_json(files["manifest.json"])
    if not isinstance(manifest, dict) or manifest.get("id") != plugin_id:
        raise DownloadError(f"Plugin-ID im Manifest stimmt nicht: {plugin_id}")
    write_assets(target_dir, files)


def download_theme(name: str, target_dir: Path) -> None:
    entry = find_entry(THEME_REGISTRY, "name", name)
    branch = entry.get("branch")
    if not branch:
        metadata = decode_json(fetch(f"https://api.github.com/repos/{entry['repo']}"))
        branch = metadata.get("default_branch") if isinstance(metadata, dict) else None
    if not branch:
        raise DownloadError(f"Standardzweig des Themes nicht gefunden: {name}")
    base = f"https://raw.githubusercontent.com/{entry['repo']}/{branch}"
    files = {filename: fetch(f"{base}/{filename}") for filename in ("manifest.json", "theme.css")}
    manifest = decode_json(files["manifest.json"])
    if not isinstance(manifest, dict) or manifest.get("name") != name:
        raise DownloadError(f"Theme-Name im Manifest stimmt nicht: {name}")
    write_assets(target_dir, files)

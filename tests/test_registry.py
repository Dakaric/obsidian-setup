import io
import json
from urllib.error import HTTPError, URLError

import pytest

from installer import registry


@pytest.fixture(autouse=True)
def clear_registry():
    registry.clear_cache()


def responses(monkeypatch, mapping):
    calls = []
    def open_url(request, **kwargs):
        calls.append(request)
        value = mapping[request.full_url]
        if isinstance(value, Exception):
            raise value
        return io.BytesIO(value if isinstance(value, bytes) else json.dumps(value).encode())
    monkeypatch.setattr("urllib.request.urlopen", open_url)
    return calls


def test_resolves_repo_from_registry(monkeypatch):
    calls = responses(monkeypatch, {
        registry.PLUGIN_REGISTRY: [{"id": "demo", "repo": "author/plugin"}],
        registry.THEME_REGISTRY: [{"name": "Theme", "repo": "author/theme", "branch": "develop"}],
    })
    assert registry.plugin_repo("demo") == "author/plugin"
    assert registry.plugin_repo("demo") == "author/plugin"
    assert registry.theme_repo("Theme") == "author/theme"
    assert len(calls) == 2


def test_download_failure_is_reported(monkeypatch, tmp_path):
    responses(monkeypatch, {registry.PLUGIN_REGISTRY: URLError("offline")})
    with pytest.raises(registry.DownloadError, match="Download"):
        registry.download_plugin("demo", tmp_path)


def test_rate_limit_message(monkeypatch):
    responses(monkeypatch, {registry.PLUGIN_REGISTRY: HTTPError(registry.PLUGIN_REGISTRY, 403, "Forbidden", {"X-RateLimit-Remaining": "0"}, None)})
    with pytest.raises(registry.DownloadError, match="Rate-Limit"):
        registry.plugin_repo("demo")


def plugin_responses(monkeypatch, manifest_id="demo", include_main=True):
    names = ["manifest.json", "styles.css"] + (["main.js"] if include_main else [])
    return responses(monkeypatch, {
        registry.PLUGIN_REGISTRY: [{"id": "demo", "repo": "author/plugin"}],
        "https://api.github.com/repos/author/plugin/releases/latest": {
            "assets": [{"name": n, "browser_download_url": f"https://github.com/author/plugin/releases/download/v1/{n}"} for n in names]},
        **{f"https://github.com/author/plugin/releases/download/v1/{n}": (json.dumps({"id": manifest_id, "version": "1"}).encode() if n == "manifest.json" else b"code") for n in names},
    })


def test_plugin_downloads_assets_and_uses_token(monkeypatch, tmp_path):
    monkeypatch.setenv("GITHUB_TOKEN", "test-token")
    calls = plugin_responses(monkeypatch)
    registry.download_plugin("demo", tmp_path)
    assert (tmp_path / "main.js").read_bytes() == b"code"
    assert (tmp_path / "styles.css").exists()
    assert any(r.get_header("Authorization") == "Bearer test-token" for r in calls if "api.github.com" in r.full_url)


@pytest.mark.parametrize("manifest_id,include_main", [("wrong", True), ("demo", False)])
def test_incomplete_plugin_not_written(monkeypatch, tmp_path, manifest_id, include_main):
    plugin_responses(monkeypatch, manifest_id, include_main)
    with pytest.raises(registry.DownloadError):
        registry.download_plugin("demo", tmp_path)
    assert not list(tmp_path.iterdir())


def test_theme_uses_registry_branch(monkeypatch, tmp_path):
    responses(monkeypatch, {
        registry.THEME_REGISTRY: [{"name": "Theme", "repo": "author/theme", "branch": "develop"}],
        "https://raw.githubusercontent.com/author/theme/develop/manifest.json": {"name": "Theme", "version": "1"},
        "https://raw.githubusercontent.com/author/theme/develop/theme.css": b"body {}",
    })
    registry.download_theme("Theme", tmp_path)
    assert (tmp_path / "theme.css").read_bytes() == b"body {}"

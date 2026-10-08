import re
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PERSONAL = [
    "chris" + "tian", "lan" + "ger", "dan" + "iel", "har" + "ry",
    "chris" + "_brain", "chris" + "-brain", "koe" + "mpf", "kö" + "mpf",
    "ae" + "nd", "æ" + "nd", "/us" + "ers/", "jar" + "vis",
]
OWNER = "Daka" + "ric"


def files():
    result = subprocess.run(["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"], cwd=ROOT, capture_output=True, check=True)
    paths = [ROOT / name.decode() for name in result.stdout.split(b"\0") if name and name != b"uv.lock"]
    assert paths
    return paths


def personal_terms(text, path):
    repositories = r"(?:obsidian-setup|claude-setup|vault-search-mcp)"
    reference = r"(?<![\w./:@-])(?:https://github\.com/|github\.com/)?" + OWNER + "/" + repositories
    cleaned = re.sub(reference + r"(?=$|[\s)\]}>,'\"`;])", "", text, flags=re.I)
    if path.name == "LICENSE":
        cleaned = re.sub(r"\b" + OWNER + r"\b", "", cleaned, flags=re.I)
    if path.name == "pyproject.toml":
        cleaned = re.sub(r"(?m)^authors\s*=\s*\[[^\]]*\]", remove_author_name, cleaned)
    return [term for term in PERSONAL + [OWNER.lower()] if term in cleaned.lower()]


def remove_author_name(match):
    return re.sub(r"\b" + OWNER + r"\b", "", match.group(), flags=re.I)


def test_no_personal_terms():
    assert personal_terms("Beispiel " + PERSONAL[0], Path("sample.md"))
    assert personal_terms(OWNER, Path("sample.md"))
    assert personal_terms("https://github.com/" + OWNER + "/repo", Path("sample.md"))
    violations = [(str(path.relative_to(ROOT)), personal_terms(path.read_text(encoding="utf-8"), path)) for path in files()]
    assert not [(path, terms) for path, terms in violations if terms]


@pytest.mark.parametrize("repo", ["obsidian-setup", "claude-setup", "vault-search-mcp"])
@pytest.mark.parametrize("prefix", ["", "github.com/", "https://github.com/"])
def test_only_public_repo_references_allowed(repo, prefix):
    assert not personal_terms(prefix + OWNER + "/" + repo, Path("sample.md"))


@pytest.mark.parametrize("suffix", ["", "/", "/private", "/obsidian-setup-private", "/obsidian-setup/private", "/obsidian-setup?private=1"])
def test_other_owner_references_rejected(suffix):
    assert personal_terms("https://github.com/" + OWNER + suffix, Path("sample.md"))


def test_author_exception_does_not_hide_other_personal_terms():
    assert not personal_terms('authors = [{name = "' + OWNER + '"}]', Path("pyproject.toml"))
    assert personal_terms('authors = [{name = "' + PERSONAL[0] + '"}]', Path("pyproject.toml"))
    assert personal_terms('description = "' + OWNER + '"', Path("pyproject.toml"))
    assert not personal_terms("Copyright " + OWNER, Path("LICENSE"))
    assert personal_terms("Copyright " + PERSONAL[0], Path("LICENSE"))


def dash_aside(text):
    return re.search(r"\u2014|\s\u2013\s|\D\u2013|\u2013\D", text)


def test_no_dash_as_aside():
    assert dash_aside("Text " + chr(0x2014) + " Einschub")
    assert dash_aside("Text " + chr(0x2013) + " Einschub")
    assert not dash_aside("2020" + chr(0x2013) + "2024")
    assert not [str(path.relative_to(ROOT)) for path in files() if path.suffix in {".md", ".py", ".json"} and dash_aside(path.read_text(encoding="utf-8"))]

#!/usr/bin/env bash
set -euo pipefail
REPO="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
if ! command -v uv >/dev/null 2>&1; then
  curl -LsSf https://astral.sh/uv/install.sh | sh
  export PATH="$HOME/.local/bin:$PATH"
fi
export PYTHONPATH="$REPO"
export PYTHONUTF8=1
exec uv run --directory "$REPO" --no-project --python 3.12 python -m installer "$@"

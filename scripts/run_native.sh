#!/usr/bin/env bash
# Run without Docker (macOS/Linux). Uses `uv` to get a pinned Python 3.12
# and the two dependencies in an isolated environment.
#   ./scripts/run_native.sh keygen | wallet | plan | run [--live] | sweep | analyze DIR
set -euo pipefail
cd "$(dirname "$0")/.."
if ! command -v uv >/dev/null 2>&1; then
  if [ -x "$HOME/.local/bin/uv" ]; then export PATH="$HOME/.local/bin:$PATH"; else
    echo "installing uv (Python manager, https://docs.astral.sh/uv/) ..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
  fi
fi
exec uv run --quiet --no-project --python 3.12 --with-requirements requirements.txt \
     python -m ordering "$@"

#!/bin/bash
# Double-click this file in Finder to start Conti. Close the Terminal window to stop it.
# Conti only READS Leggio's workspace; it can run while Leggio is open.
cd "$(dirname "$0")"
export CONTI_ROOT="$(cd .. && pwd)"
export PATH="$HOME/.local/bin:$PATH"
if ! command -v uv >/dev/null 2>&1; then
  echo "uv is not installed yet (Leggio's README, step 1)."; read -n 1; exit 1
fi
uv run conti

#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT_DIR"

if [[ ! -d .venv ]]; then
  echo "Error: .venv not found. Create it first: python3 -m venv .venv"
  exit 1
fi

source .venv/bin/activate
export PYTHONPATH="$ROOT_DIR${PYTHONPATH:+:$PYTHONPATH}"

if [[ ! -f conf.py ]]; then
  cp conf.example.py conf.py
  echo "Created conf.py from conf.example.py"
fi

mkdir -p db cookiesFile videoFile
python db/createTable.py

cleanup() {
  local code=$?
  if [[ -n "${BACKEND_PID:-}" ]] && kill -0 "$BACKEND_PID" 2>/dev/null; then
    kill "$BACKEND_PID" 2>/dev/null || true
  fi
  if [[ -n "${FRONTEND_PID:-}" ]] && kill -0 "$FRONTEND_PID" 2>/dev/null; then
    kill "$FRONTEND_PID" 2>/dev/null || true
  fi
  wait 2>/dev/null || true
  exit "$code"
}
trap cleanup EXIT INT TERM

flask --app sau_backend run --debug --host 0.0.0.0 --port 5409 &
BACKEND_PID=$!

(
  cd sau_frontend
  npm run dev
) &
FRONTEND_PID=$!

echo "Backend:  http://localhost:5409"
echo "Frontend: http://localhost:5173"
echo "Press Ctrl+C to stop both."

wait

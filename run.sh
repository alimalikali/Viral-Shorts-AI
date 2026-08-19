#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON="${PYTHON:-python3.12}"
BACKEND_PORT="${BACKEND_PORT:-8000}"
FRONTEND_PORT="${FRONTEND_PORT:-3000}"
LOG_DIR="$ROOT/.run-logs"

die() { echo "error: $*" >&2; exit 1; }

command -v ffmpeg  >/dev/null || die "ffmpeg not on PATH (apt install ffmpeg)"
command -v ffprobe >/dev/null || die "ffprobe not on PATH (apt install ffmpeg)"
command -v node    >/dev/null || die "node not on PATH"
command -v "$PYTHON" >/dev/null || die "$PYTHON not on PATH — mediapipe/torch have no 3.13 wheels, so 3.12 is required"

port_busy() { ss -tln 2>/dev/null | grep -q ":$1 "; }
port_busy "$BACKEND_PORT"  && die "port $BACKEND_PORT already in use (set BACKEND_PORT= to change)"
port_busy "$FRONTEND_PORT" && die "port $FRONTEND_PORT already in use (set FRONTEND_PORT= to change)"

if [ ! -d "$ROOT/backend/venv" ]; then
  echo "==> creating backend venv with $PYTHON"
  "$PYTHON" -m venv "$ROOT/backend/venv"
  "$ROOT/backend/venv/bin/pip" install --upgrade pip
  "$ROOT/backend/venv/bin/pip" install -r "$ROOT/backend/requirements.txt"
fi

for dir in frontend desktop; do
  if [ ! -d "$ROOT/$dir/node_modules" ]; then
    echo "==> npm install in $dir"
    (cd "$ROOT/$dir" && npm install)
  fi
done

mkdir -p "$LOG_DIR"
pids=()
cleanup() {
  for pid in "${pids[@]:-}"; do
    [ -n "$pid" ] && kill "$pid" 2>/dev/null || true
  done
}
trap cleanup EXIT INT TERM

echo "==> backend on :$BACKEND_PORT (log: $LOG_DIR/backend.log)"
# python -m, not venv/bin/uvicorn: the console-script shebangs break if the repo moves
(cd "$ROOT/backend" && exec venv/bin/python -m uvicorn app.main:app --port "$BACKEND_PORT") >"$LOG_DIR/backend.log" 2>&1 &
pids+=($!)

echo "==> frontend on :$FRONTEND_PORT (log: $LOG_DIR/frontend.log)"
(cd "$ROOT/frontend" && exec npx vite --port "$FRONTEND_PORT" --strictPort) >"$LOG_DIR/frontend.log" 2>&1 &
pids+=($!)

echo -n "==> waiting for frontend"
for _ in $(seq 60); do
  port_busy "$FRONTEND_PORT" && break
  echo -n "."
  sleep 1
done
echo
port_busy "$FRONTEND_PORT" || die "frontend never came up — see $LOG_DIR/frontend.log"

echo "==> launching Electron (close it to shut everything down)"
(cd "$ROOT/desktop" && FRONTEND_PORT="$FRONTEND_PORT" npm start)

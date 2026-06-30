#!/usr/bin/env bash
set -euo pipefail

# Start the Stage5+SDRF batch launcher in a detached shell so the parent terminal
# can close or be interrupted without killing the launch process.

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG_DIR="$REPO_DIR/logs/stage5_sdrf"
mkdir -p "$LOG_DIR"

COMMAND_FILE="${1:-$REPO_DIR/commands/stage5_sdrf_commands.txt}"
MAX_PARALLEL="${MAX_PARALLEL:-8}"

nohup env MAX_PARALLEL="$MAX_PARALLEL" bash "$REPO_DIR/scripts/run_stage5_sdrf_parallel.sh" "$COMMAND_FILE" \
  > "$LOG_DIR/launcher.log" 2>&1 &

echo $! > "$LOG_DIR/launcher.pid"
echo "Started detached launcher PID $(cat "$LOG_DIR/launcher.pid")"
echo "Launcher log: $LOG_DIR/launcher.log"
echo "Jobs manifest: $LOG_DIR/jobs.tsv"
#!/usr/bin/env bash
set -euo pipefail

# Launch per-PXD Stage5+SDRF jobs in the background from a command list.
# Each job is constrained to one thread/process domain.

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMMAND_FILE="${1:-$REPO_DIR/commands/stage5_sdrf_commands.txt}"
MAX_PARALLEL="${MAX_PARALLEL:-8}"

LOG_DIR="$REPO_DIR/logs/stage5_sdrf"
STATUS_DIR="$LOG_DIR/status"
RUN_DIR="$LOG_DIR/run"
JOBS_FILE="$LOG_DIR/jobs.tsv"

mkdir -p "$LOG_DIR" "$STATUS_DIR" "$RUN_DIR"

if [[ ! -f "$COMMAND_FILE" ]]; then
  echo "Command file not found: $COMMAND_FILE" >&2
  exit 1
fi

if ! [[ "$MAX_PARALLEL" =~ ^[0-9]+$ ]] || [[ "$MAX_PARALLEL" -lt 1 ]]; then
  echo "MAX_PARALLEL must be a positive integer (got: $MAX_PARALLEL)" >&2
  exit 1
fi

if [[ ! -f "$REPO_DIR/.venv/bin/activate" ]]; then
  echo "Missing virtual env activate script at $REPO_DIR/.venv/bin/activate" >&2
  exit 1
fi

# Reset manifest for this launch batch.
printf "pxd\tpid\tlog_file\tstatus_file\tcommand\n" > "$JOBS_FILE"

active_jobs=0
launched=0

wait_for_slot() {
  while [[ "$active_jobs" -ge "$MAX_PARALLEL" ]]; do
    active_jobs=$(jobs -pr | wc -l | tr -d ' ')
    sleep 0.5
  done
}

extract_pxd() {
  local cmd="$1"
  # Extract token after "--pxd".
  awk '{for(i=1;i<=NF;i++){if($i=="--pxd" && i<NF){print $(i+1); exit}}}' <<< "$cmd"
}

while IFS= read -r cmd || [[ -n "$cmd" ]]; do
  [[ -z "$cmd" ]] && continue

  pxd="$(extract_pxd "$cmd")"
  if [[ -z "$pxd" ]]; then
    echo "Skipping command without --pxd: $cmd" >&2
    continue
  fi

  wait_for_slot

  log_file="$RUN_DIR/${pxd}.log"
  status_file="$STATUS_DIR/${pxd}.exit"

  rm -f "$status_file"

  nohup bash -lc "
    set -euo pipefail
    cd '$REPO_DIR'
    source '$REPO_DIR/.venv/bin/activate'
    export OMP_NUM_THREADS=1
    export OPENBLAS_NUM_THREADS=1
    export MKL_NUM_THREADS=1
    export NUMEXPR_NUM_THREADS=1
    export VECLIB_MAXIMUM_THREADS=1
    export BLIS_NUM_THREADS=1
    $cmd
    ec=\$?
    echo \$ec > '$status_file'
    exit \$ec
  " > "$log_file" 2>&1 &

  pid=$!
  printf "%s\t%s\t%s\t%s\t%s\n" "$pxd" "$pid" "$log_file" "$status_file" "$cmd" >> "$JOBS_FILE"
  echo "Launched $pxd (PID $pid)"

  launched=$((launched + 1))
  active_jobs=$(jobs -pr | wc -l | tr -d ' ')
done < "$COMMAND_FILE"

echo
echo "Launch complete. Submitted jobs: $launched"
echo "Manifest: $JOBS_FILE"
echo "Monitor:  bash scripts/monitor_stage5_sdrf.sh"

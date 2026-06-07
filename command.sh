#!/usr/bin/env bash
# Full xHAMLET pipeline: .raw download → mzML conversion → assessor → LLM metadata → SDRF → Xi configs → ReLink
# Launches each PXD as a separate background job — all run in parallel.
# Safe to close the terminal; nohup keeps every job alive.
#
# Usage:
#   bash command.sh
#
# Monitor a specific PXD:
#   tail -f logs/PXD042173.log
#
# Check all running jobs:
#   cat pipeline.pids | xargs -I{} sh -c 'kill -0 {} 2>/dev/null && echo "Running: {}" || echo "Done:    {}"'
#
# Wait for all jobs to finish:
#   cat pipeline.pids | xargs -I{} tail --pid={} -f /dev/null

set -euo pipefail

ASSESSOR_FILES_PER_CLUSTER="${ASSESSOR_FILES_PER_CLUSTER:-1}"
RELINK_PROFILE="${RELINK_PROFILE:-docker}"

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$REPO_DIR"

mkdir -p logs

PXDS=(
    PXD042173
)

# Clear previous PID file
> pipeline.pids

echo "Launching ${#PXDS[@]} PXD jobs in parallel..."
echo ""

for PXD in "${PXDS[@]}"; do
    LOGFILE="logs/${PXD}.log"
    STDOUTLOG="logs/${PXD}_stdout.log"

    nohup python src/main.py \
        --pxd "$PXD" \
        --force-refresh \
        --assessor-files-per-cluster "$ASSESSOR_FILES_PER_CLUSTER" \
        --clean-mzml \
        --nproc 5 \
        --relink \
        --relink-profile "$RELINK_PROFILE" \
        --log-file "$LOGFILE" \
        --verbose \
        > "$STDOUTLOG" 2>&1 &

    PID=$!
    echo "$PID" >> pipeline.pids
    echo "  Launched $PXD  (PID $PID)  →  $LOGFILE"
done

echo ""
echo "All ${#PXDS[@]} jobs launched."
echo ""
echo "Monitor a job      : tail -f logs/<PXD>.log"
echo "Check all PIDs     : cat pipeline.pids | xargs -I{} sh -c 'kill -0 {} 2>/dev/null && echo \"Running: {}\" || echo \"Done: {}\"'"

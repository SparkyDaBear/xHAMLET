#!/usr/bin/env bash
# Full xHAMLET pipeline: .raw download → mzML conversion → assessor → LLM metadata → SDRF → Xi configs
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

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$REPO_DIR"

mkdir -p logs

PXDS=(
    PXD003486
    PXD006816
    PXD007673
    PXD008418
    PXD010796
    PXD010931
    PXD011071
    PXD011861
    PXD016988
    PXD017620
    PXD018771
    PXD022991
    PXD026244
    PXD027234
    PXD031345
    PXD037678
    PXD042173
    PXD052022
    PXD059495
    PXD006359
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
        --clean-raw \
        --clean-mzml \
        --nproc 5 \
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

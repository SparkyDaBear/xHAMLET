#!/bin/bash
#SBATCH --job-name=xHAMLET_retry
#SBATCH --partition=basic
#SBATCH --account=ncems_cr_default
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --mem=128G
#SBATCH --time=7-00:00:00
#SBATCH --output=/storage/group/epo2/default/ims86/git_repos/xHAMLET/assets/slurm/remaining394/retry_logs/array_%A_%a.log

# Usage (build the manifest first with scripts/build_relink_retry_array.py):
#   sbatch --array=1-N%10 retry_array.slurm retry_array_manifest.tsv
# Each task runs one existing per-PXD script; its full log goes to that PXD's runs/ directory.

set -euo pipefail

# wget (one connection per file) is the default RAW downloader for retries; override at submit time.
export XHAMLET_DOWNLOAD_BACKEND="${XHAMLET_DOWNLOAD_BACKEND:-wget}"

MANIFEST="${1:?manifest TSV required}"
LINE=$(awk -F'\t' -v n="$SLURM_ARRAY_TASK_ID" 'NR == n + 1 {print $1 "\t" $2}' "$MANIFEST")
[[ -n "$LINE" ]] || { echo "No manifest row for task $SLURM_ARRAY_TASK_ID" >&2; exit 1; }
PXD=${LINE%%$'\t'*}
SCRIPT=${LINE#*$'\t'}
RUN_DIR="$(dirname "$SCRIPT")/runs/$PXD"
mkdir -p "$RUN_DIR"
LOG="$RUN_DIR/slurm_${SLURM_ARRAY_JOB_ID}_${SLURM_ARRAY_TASK_ID}.log"

echo "Task $SLURM_ARRAY_TASK_ID: $PXD via $SCRIPT (log: $LOG)"
bash "$SCRIPT" > "$LOG" 2>&1

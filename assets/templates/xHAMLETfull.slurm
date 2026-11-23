#!/bin/bash
#SBATCH --job-name=xHAMLET_{{PXD}}
#SBATCH --partition=basic
#SBATCH --account=ncems_cr_default
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --mem=128G
#SBATCH --time=7-00:00:00
#SBATCH --output={{SLURM_LOG}}

set -euo pipefail

XHAMLET={{REPO_DIR}}
RUN_DIR={{RUN_DIR}}
PXD={{PXD}}
CONDA_BASE="${CONDA_BASE:-/storage/group/epo2/default/ims86/miniconda3}"
XHAMLET_ENV="${XHAMLET_ENV:-/storage/work/ims86/.conda/envs/xhamlet}"

mkdir -p "$RUN_DIR"
cd "$XHAMLET"

source "$CONDA_BASE/etc/profile.d/conda.sh"
# Conda activation hooks are not consistently nounset-safe.
set +u
conda activate "$XHAMLET_ENV"
set -u

export NXF_HOME="${NXF_HOME:-/storage/group/epo2/default/ims86/.nextflow}"
SHARED_IMAGES=/storage/group/epo2/default/ims86/.singularity
# Nextflow image promotion is not safe across independent concurrent sessions.
export NXF_SINGULARITY_CACHEDIR="$RUN_DIR/singularity"
export SINGULARITY_CACHEDIR="${SINGULARITY_CACHEDIR:-$SHARED_IMAGES/pull-cache}"
export APPTAINER_CACHEDIR="$SINGULARITY_CACHEDIR"
export OMP_NUM_THREADS="${SLURM_CPUS_PER_TASK}"
mkdir -p "$NXF_HOME" "$NXF_SINGULARITY_CACHEDIR"
for image in "$SHARED_IMAGES"/*.img; do
  if [[ -f "$image" && ! -e "$NXF_SINGULARITY_CACHEDIR/$(basename "$image")" ]]; then
    ln -s "$image" "$NXF_SINGULARITY_CACHEDIR/$(basename "$image")"
  fi
done

for tool in python nextflow java singularity aria2c thermorawfileparser; do
  command -v "$tool" >/dev/null || { echo "Missing required tool: $tool" >&2; exit 1; }
done
if [[ -z "${OPENROUTER_API_KEY:-}" && -z "${OPENAI_API_KEY:-}" ]]; then
  echo "Export OPENROUTER_API_KEY or OPENAI_API_KEY before sbatch." >&2
  exit 1
fi

exec python src/main.py \
  --pxd "$PXD" \
  --config "$XHAMLET/configs/config.yaml" \
  --data-dir "$XHAMLET/store" \
  --nproc 1 \
  --aria2c-connections 2 \
  --clean-mzml \
  --relink \
  --relink-profile singularity \
  --force-taxid 9606 \
  --relink-resume \
  --relink-work-dir "$RUN_DIR/work" \
  --relink-queue-size 1 \
  --log-file "$RUN_DIR/pipeline.log" \
  --verbose

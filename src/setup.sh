#!/bin/bash
set -euo pipefail

# xHAMLET setup for an existing conda environment.
# Usage: bash src/setup.sh

echo "========================"
echo "xHAMLET Setup"
echo "========================"

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if ! command -v conda >/dev/null 2>&1; then
    echo "ERROR: conda is not available in PATH." >&2
    echo "Install Miniconda/Anaconda and try again." >&2
    exit 1
fi

CONDA_BASE="$(conda info --base)"
CONDA_SH="$CONDA_BASE/etc/profile.d/conda.sh"
if [[ -f "$CONDA_SH" ]]; then
    # Ensure shell has conda functions available.
    source "$CONDA_SH"
fi

if [[ -z "${CONDA_DEFAULT_ENV:-}" ]]; then
    echo "ERROR: no active conda environment detected." >&2
    echo "Activate your target environment first, then rerun setup:" >&2
    echo "  conda activate <env_name>" >&2
    echo "  bash src/setup.sh" >&2
    exit 1
fi

echo "Using conda environment: ${CONDA_DEFAULT_ENV}"
echo "Python executable: $(command -v python)"

if [[ ! -f "$PROJECT_ROOT/requirements.txt" ]]; then
    echo "ERROR: requirements.txt not found at $PROJECT_ROOT/requirements.txt" >&2
    exit 1
fi

echo ""
echo "Installing Python dependencies..."
python -m pip install --upgrade pip
python -m pip install -r "$PROJECT_ROOT/requirements.txt"

echo ""
echo "Preparing config file..."
mkdir -p "$PROJECT_ROOT/configs"
if [[ ! -f "$PROJECT_ROOT/configs/config.yaml" ]]; then
    cp "$PROJECT_ROOT/config.yaml.sample" "$PROJECT_ROOT/configs/config.yaml"
    echo "Created: configs/config.yaml (from config.yaml.sample)"
else
    echo "configs/config.yaml already exists; leaving as-is"
fi

echo ""
echo "Setup complete."
echo "Next steps:"
echo "  1. Export required credentials in your shell:"
echo "     export OPENAI_API_KEY=\"your-openai-key\""
echo "     export NCBI_API_KEY=\"your-ncbi-key\"   # optional"
echo "  2. Run xHAMLET:"
echo "     python src/main.py --pxd PXD042173 --config configs/config.yaml --verbose"

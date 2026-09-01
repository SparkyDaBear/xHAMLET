#!/bin/bash
set -euo pipefail

# xHAMLET setup for an existing conda environment.
# Usage: bash src/setup.sh

echo "========================"
echo "xHAMLET Setup"
echo "========================"

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MINICONDA_PREFIX="${MINICONDA_PREFIX:-$HOME/miniconda3}"

if ! command -v conda >/dev/null 2>&1; then
    if [[ -x "$MINICONDA_PREFIX/bin/conda" ]]; then
        export PATH="$MINICONDA_PREFIX/bin:$PATH"
    else
        case "$(uname -m)" in
            x86_64) miniconda_arch="x86_64" ;;
            aarch64|arm64) miniconda_arch="aarch64" ;;
            *)
                echo "ERROR: unsupported architecture for Miniconda: $(uname -m)" >&2
                exit 1
                ;;
        esac

        installer_path="$(mktemp "${TMPDIR:-/tmp}/miniconda.XXXXXX.sh")"
        installer_url="https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-${miniconda_arch}.sh"
        trap 'rm -f "$installer_path"' EXIT

        echo "Conda is not available; installing Miniconda in $MINICONDA_PREFIX..."
        if command -v curl >/dev/null 2>&1; then
            curl --fail --location --output "$installer_path" "$installer_url"
        elif command -v wget >/dev/null 2>&1; then
            wget --output-document="$installer_path" "$installer_url"
        else
            echo "ERROR: curl or wget is required to download Miniconda." >&2
            exit 1
        fi
        bash "$installer_path" -b -p "$MINICONDA_PREFIX"
        export PATH="$MINICONDA_PREFIX/bin:$PATH"
    fi
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

missing_conda_packages=()
if ! command -v aria2c >/dev/null 2>&1; then
    missing_conda_packages+=("aria2")
fi
if ! command -v thermorawfileparser >/dev/null 2>&1; then
    missing_conda_packages+=("thermorawfileparser")
fi
if ! command -v java >/dev/null 2>&1; then
    missing_conda_packages+=("openjdk=17")
fi
if ! command -v nextflow >/dev/null 2>&1; then
    missing_conda_packages+=("nextflow")
fi

if (( ${#missing_conda_packages[@]} > 0 )); then
    echo ""
    echo "Installing required command-line tools: ${missing_conda_packages[*]}"
    # Conda activation hooks can reference unset backup variables.
    set +u
    if ! conda install --yes -c conda-forge -c bioconda "${missing_conda_packages[@]}"; then
        set -u
        exit 1
    fi
    set -u
fi

if [[ ! -f "$PROJECT_ROOT/tools/relink/main.nf" ]]; then
    if ! command -v git >/dev/null 2>&1; then
        echo "ERROR: git is required to initialize the ReLink submodule." >&2
        exit 1
    fi
    echo ""
    echo "Initializing ReLink submodule..."
    git -C "$PROJECT_ROOT" submodule update --init --recursive tools/relink
fi

if command -v singularity >/dev/null 2>&1; then
    echo "ReLink container runtime: Singularity"
elif command -v apptainer >/dev/null 2>&1; then
    echo "ReLink container runtime: Apptainer"
elif command -v docker >/dev/null 2>&1; then
    echo "ReLink container runtime: Docker (use --relink-profile docker)"
else
    echo "WARNING: ReLink requires Docker, Singularity, or Apptainer when using --relink." >&2
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

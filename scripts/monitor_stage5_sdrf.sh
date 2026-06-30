#!/usr/bin/env bash
set -euo pipefail

# Monitor Stage5+SDRF background jobs and report SDRF validity.

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
JOBS_FILE="${1:-$REPO_DIR/logs/stage5_sdrf/jobs.tsv}"

if [[ ! -f "$JOBS_FILE" ]]; then
  echo "Jobs manifest not found: $JOBS_FILE" >&2
  exit 1
fi

have_parse_sdrf=0
if command -v parse_sdrf >/dev/null 2>&1; then
  have_parse_sdrf=1
fi

validate_sdrf_file() {
  local sdrf_file="$1"

  # Newer parse_sdrf CLI requires a subcommand.
  if parse_sdrf validate-sdrf-simple "$sdrf_file" >/dev/null 2>&1; then
    return 0
  fi

  # Fallback for alternate subcommand syntax.
  if parse_sdrf validate-sdrf --sdrf_file "$sdrf_file" >/dev/null 2>&1; then
    return 0
  fi

  # Legacy parse_sdrf releases accepted direct file argument.
  if parse_sdrf "$sdrf_file" >/dev/null 2>&1; then
    return 0
  fi

  return 1
}

running=0
completed_ok=0
failed=0
valid_sdrf=0
invalid_sdrf=0
missing_sdrf=0
unknown_sdrf=0

echo "PXD | JOB_STATUS | EXIT | SDRF_STATUS"
echo "----|-----------|------|------------"

# Skip header
{ read -r _header || true
  while IFS=$'\t' read -r pxd pid log_file status_file command; do
    [[ -z "${pxd:-}" ]] && continue

    job_status="UNKNOWN"
    exit_code="-"

    if kill -0 "$pid" 2>/dev/null; then
      job_status="RUNNING"
      running=$((running + 1))
    elif [[ -f "$status_file" ]]; then
      exit_code="$(tr -d '[:space:]' < "$status_file")"
      if [[ "$exit_code" == "0" ]]; then
        job_status="DONE"
        completed_ok=$((completed_ok + 1))
      else
        job_status="FAILED"
        failed=$((failed + 1))
      fi
    else
      job_status="NO_STATUS"
      failed=$((failed + 1))
    fi

    sdrf_path="$REPO_DIR/pxd_data/$pxd/sdrf/$pxd.sdrf.tsv"
    sdrf_status="MISSING"

    if [[ -s "$sdrf_path" ]]; then
      if [[ "$have_parse_sdrf" -eq 1 ]]; then
        if validate_sdrf_file "$sdrf_path"; then
          sdrf_status="VALID"
          valid_sdrf=$((valid_sdrf + 1))
        else
          sdrf_status="INVALID"
          invalid_sdrf=$((invalid_sdrf + 1))
        fi
      else
        # parse_sdrf not available in PATH; file exists but validation could not be performed.
        sdrf_status="PRESENT_UNVALIDATED"
        unknown_sdrf=$((unknown_sdrf + 1))
      fi
    else
      missing_sdrf=$((missing_sdrf + 1))
    fi

    echo "$pxd | $job_status | $exit_code | $sdrf_status"
  done
} < "$JOBS_FILE"

echo
echo "Summary"
echo "Total jobs:            $((running + completed_ok + failed))"
echo "Running:               $running"
echo "Completed (exit 0):    $completed_ok"
echo "Failed/No status:      $failed"
echo "SDRF valid:            $valid_sdrf"
echo "SDRF invalid:          $invalid_sdrf"
echo "SDRF missing:          $missing_sdrf"
echo "SDRF unvalidated:      $unknown_sdrf"

if [[ "$have_parse_sdrf" -eq 0 ]]; then
  echo
  echo "Note: parse_sdrf not found in PATH; SDRF validity is reported as PRESENT_UNVALIDATED when file exists."
fi

#!/usr/bin/env python3
"""Inventory prior XP attempts, freeze a reviewable plan, and run up to two PXDs.

This is an XP rerun queue. It never selects new PXDs, invokes ReLink, installs
software, deletes prior results, or converts an old failure into success.
Planning scans existing files; execution requires an explicit --execute PLAN.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import fcntl
import gzip
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import signal
import subprocess
import sys
import tarfile
import threading
import time
from typing import Any
import urllib.request
import uuid
import zipfile

VERSION = "3.3.0"
PLAN_SCHEMA = "ncems.xp.rerun_plan.v3.3"
EXPECTED_ENGINE_SHA256 = "4fb72ee71b6b050831a2bdf6a59e0629fd190074af1afa11e23661dba5ec3821"
FIXED_VOLUME = Path("/media/volume/xhamlet-data-5")
DEFAULT_PROJECT = FIXED_VOLUME / "NCEMS_XP_v33"
SOURCE_REPOSITORY = "SparkyDaBear/xHAMLET"
PXD_RE = re.compile(r"PXD[0-9]{6}\Z")
PXD_IN_NAME_RE = re.compile(r"(?<![A-Z0-9])(PXD[0-9]{6})(?![0-9])", re.I)
METADATA_NAMES = frozenset(("run_summary.json", "launch_manifest.json"))
PRUNED_DIRECTORY_NAMES = frozenset((
    ".git", ".nextflow", "__pycache__", "tests", "fixtures", "models",
    "raw", "raw_data", "mzML", "working", "work", "xp_engine",
    "inputs", "reference_snapshot", "reference_library_snapshot",
    "reference_library", "references", "af3_predictions",
))
SETTLED_EVENTS = frozenset(("FINISHED", "LAUNCH_ERROR"))
ARCHIVE_MAX_BYTES = 256 * 1024 * 1024
ARCHIVE_MAX_EXPANDED_BYTES = 256 * 1024 * 1024
ARCHIVE_MAX_MEMBERS = 30000
ARCHIVE_METADATA_MAX_BYTES = 4 * 1024 * 1024
ARCHIVE_SELECTED_MAX_BYTES = 32 * 1024 * 1024
PACKAGE_IGNORED_DIRS = frozenset(("tests", "__pycache__", ".git", ".pytest_cache"))
PACKAGE_IGNORED_FILES = frozenset(("INSTALLATION_RECORD.json", "VALIDATION_REPORT.json"))


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def production_package_snapshot(root: Path) -> dict[str, Any]:
    root = root.resolve(strict=True)
    files = {}
    for current, dirs, names in os.walk(root, followlinks=False):
        folder = Path(current)
        dirs[:] = sorted(name for name in dirs if name not in PACKAGE_IGNORED_DIRS
                         and not name.startswith("."))
        if any((folder / name).is_symlink() for name in dirs):
            raise ValueError("Production package contains a symlink directory")
        for name in sorted(names):
            path = folder / name
            if path.suffix not in (".py", ".json") or name in PACKAGE_IGNORED_FILES:
                continue
            if path.is_symlink() or not path.is_file():
                raise ValueError(f"Production source is not a regular file: {path}")
            before = path.stat()
            digest = sha256_file(path)
            after = path.stat()
            if (before.st_size, before.st_mtime_ns, before.st_ino) != (after.st_size, after.st_mtime_ns, after.st_ino):
                raise ValueError(f"Production source changed while hashing: {path}")
            files[path.relative_to(root).as_posix()] = digest
    if not files:
        raise ValueError("No production Python/JSON files found in the package")
    digest = hashlib.sha256(json.dumps(files, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return {"schema": "NCEMS_PRODUCTION_PY_JSON_SNAPSHOT_V1", "root": str(root),
            "files_sha256": files, "manifest_sha256": digest,
            "scope": "All production .py/.json files; excludes tests, caches, installation record and validation report"}


def verify_production_package(plan: dict[str, Any]) -> None:
    frozen = plan.get("production_package")
    if not isinstance(frozen, dict) or not isinstance(frozen.get("files_sha256"), dict):
        raise ValueError("Plan has no frozen production-package manifest; create a new reviewed plan")
    root = Path(plan["runner"]["path"]).resolve().parent
    if Path(frozen["root"]).resolve() != root:
        raise ValueError("Production-package manifest belongs to a different runner directory")
    current = production_package_snapshot(root)
    expected = frozen["files_sha256"]
    if current["files_sha256"] != expected or current["manifest_sha256"] != frozen.get("manifest_sha256"):
        observed = current["files_sha256"]
        changed = sorted(name for name in set(expected) | set(observed)
                         if expected.get(name) != observed.get(name))
        detail = ", ".join(changed[:10]) or "manifest checksum"
        raise ValueError("Production package changed after planning: " + detail + "; no job launched")
    context = plan.get("experimental_context")
    if context and sha256_file(Path(context["snapshot_path"])) != context["sha256"]:
        raise ValueError("Experimental-context evidence changed after planning; no job launched")


def validate_experimental_context(data: dict[str, Any]) -> None:
    if data.get("schema") != "NCEMS_EXPERIMENTAL_CONTEXT_V1" or not isinstance(data.get("entries"), list):
        raise ValueError("Experimental-context JSON must use NCEMS_EXPERIMENTAL_CONTEXT_V1 with an entries list")
    keys = set()
    for entry in data["entries"]:
        if not isinstance(entry, dict) or not isinstance(entry.get("pxd"), str) or not PXD_RE.fullmatch(entry["pxd"]):
            raise ValueError("Experimental context entry requires an exact uppercase PXD accession")
        group = entry.get("search_group")
        evidence = entry.get("chemistry_evidence")
        if not isinstance(group, str) or not group or group != group.strip():
            raise ValueError("Experimental context entry requires an exact nonblank search_group")
        if not isinstance(evidence, str) or not evidence.strip():
            raise ValueError("Experimental context entry requires a chemistry_evidence citation or record")
        key = (entry["pxd"], group)
        if key in keys:
            raise ValueError("Duplicate PXD/search-group experimental context")
        keys.add(key)
        for field in ("chemistry", "chemistry_evidence_status"):
            if not isinstance(entry.get(field), str) or not entry[field].strip():
                raise ValueError("Experimental context contains an empty or nontext " + field)
        if entry['chemistry_evidence_status'] not in ('EXPERIMENT_REAGENT_CONFIRMED', 'SEARCH_CONFIGURATION_ONLY', 'UNRESOLVED'):
            raise ValueError('Experimental context has an unsupported evidence status')


def is_mountpoint(path: Path) -> bool:
    path = path.absolute()
    if path.is_mount():
        return True
    # Unlike os.path.ismount, mountinfo also recognizes same-device bind mounts.
    try:
        for line in Path("/proc/self/mountinfo").read_text().splitlines():
            mount = line.split()[4]
            mount = re.sub(r"\\([0-7]{3})", lambda m: chr(int(m.group(1), 8)), mount)
            if Path(mount) == path:
                return True
    except (OSError, IndexError):
        pass
    return False


def require_mounted_volume(output: Path) -> Path:
    if not is_mountpoint(FIXED_VOLUME):
        raise ValueError(f"Fixed volume is not mounted: {FIXED_VOLUME}. No output directory was created.")
    base = FIXED_VOLUME.resolve(strict=True)
    target = output.expanduser().resolve()
    if target == base or base not in target.parents:
        raise ValueError(f"Output must be a project path inside mounted {FIXED_VOLUME}: {target}")
    return target


def json_object(path: Path, limit: int = 4 * 1024 * 1024) -> dict[str, Any]:
    if path.stat().st_size > limit:
        raise ValueError("Metadata exceeds the supported size limit")
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        raise ValueError("Metadata must contain a JSON object")
    return value


def default_scan_roots(home: Path | None = None) -> list[Path]:
    home = home or Path.home()
    work = home / "ncems-xp-test-work"
    known = [work / name for name in (
        "pxd_xp_paper_runs", "pxd_xp_reference_runs", "pxd_xp_runs",
        "pxd_xp_batch_runs", "pxd_xp_v2_runs",
    )]
    # Discover additional XP run roots only at this known workspace's top level.
    # Do not crawl every installed package, raw dataset, or test fixture.
    if work.is_dir():
        known.extend(p for p in sorted(work.glob("pxd_xp_*")) if p.is_dir())
    known.append(FIXED_VOLUME / "NCEMS_XP_v32_Ian_review")
    if is_mountpoint(FIXED_VOLUME):
        known.extend(p for p in sorted(FIXED_VOLUME.glob("NCEMS_XP_*")) if p.is_dir())
    return list(dict.fromkeys(p.expanduser().absolute() for p in known))


def is_supported_archive(path: Path) -> bool:
    return path.name.lower().endswith((".zip", ".tar", ".tar.gz", ".tgz"))


class BoundedReader:
    def __init__(self, handle, limit: int):
        self.handle = handle
        self.remaining = limit

    def read(self, count: int = -1) -> bytes:
        requested = self.remaining + 1 if count < 0 else min(count, self.remaining + 1)
        data = self.handle.read(requested)
        self.remaining -= len(data)
        if self.remaining < 0:
            raise ValueError("ARCHIVE_EXPANDED_BYTE_LIMIT_REACHED")
        return data


def read_archive_metadata(path: Path) -> dict[str, Any]:
    """Read only named metadata members; never extract archive contents."""
    before = path.stat()
    report: dict[str, Any] = {"path": str(path.resolve()), "size_bytes": before.st_size,
                              "mtime_ns": before.st_mtime_ns, "state": "SCANNED",
                              "sha256": None, "records": [], "hints": [], "warnings": []}
    if before.st_size > ARCHIVE_MAX_BYTES:
        report["state"] = "NOT_SCANNED_COMPRESSED_SIZE_LIMIT"
        report["warnings"].append("ARCHIVE_COMPRESSED_SIZE_LIMIT_REACHED")
        return report
    selected_bytes = 0
    members_seen = 0

    def select(name: str, size: int, is_file: bool, opener) -> None:
        nonlocal selected_bytes, members_seen
        members_seen += 1
        if members_seen > ARCHIVE_MAX_MEMBERS:
            raise ValueError("ARCHIVE_MEMBER_COUNT_LIMIT_REACHED")
        member = PurePosixPath(name)
        if member.is_absolute() or ".." in member.parts:
            report["warnings"].append("UNSAFE_MEMBER_PATH_IGNORED: " + name)
            return
        if any(part in PRUNED_DIRECTORY_NAMES or part.startswith(".") for part in member.parts[:-1]):
            return
        pxd_hints = {m.group(1).upper() for part in member.parts for m in PXD_IN_NAME_RE.finditer(part)}
        for pxd in sorted(pxd_hints):
            report["hints"].append({"pxd": pxd, "path": str(path) + "::" + name})
        if not is_file or member.name not in METADATA_NAMES:
            return
        if size > ARCHIVE_METADATA_MAX_BYTES:
            report["warnings"].append("METADATA_MEMBER_TOO_LARGE: " + name)
            return
        selected_bytes += size
        if selected_bytes > ARCHIVE_SELECTED_MAX_BYTES:
            raise ValueError("ARCHIVE_SELECTED_METADATA_LIMIT_REACHED")
        with opener() as handle:
            raw = handle.read(ARCHIVE_METADATA_MAX_BYTES + 1)
        if len(raw) > ARCHIVE_METADATA_MAX_BYTES:
            raise ValueError("ARCHIVE_METADATA_READ_LIMIT_REACHED")
        try:
            obj = json.loads(raw.decode("utf-8-sig"))
            if not isinstance(obj, dict):
                raise ValueError("Metadata is not a JSON object")
            report["records"].append({"member": name, "kind": member.name, "object": obj,
                                      "metadata_sha256": hashlib.sha256(raw).hexdigest()})
        except (ValueError, UnicodeError) as exc:
            report["warnings"].append(f"UNREADABLE_MEMBER {name}: {exc}")

    try:
        if path.name.lower().endswith(".zip"):
            with zipfile.ZipFile(path) as archive:
                for member in archive.infolist():
                    is_link = ((member.external_attr >> 16) & 0o170000) == 0o120000
                    select(member.filename, member.file_size, not member.is_dir() and not is_link,
                           lambda m=member: archive.open(m))
        else:
            with path.open("rb") as raw:
                compressed = path.name.lower().endswith((".tar.gz", ".tgz"))
                stream = gzip.GzipFile(fileobj=raw, mode="rb") if compressed else raw
                try:
                    with tarfile.open(fileobj=BoundedReader(stream, ARCHIVE_MAX_EXPANDED_BYTES), mode="r|") as archive:
                        for member in archive:
                            select(member.name, member.size, member.isfile(),
                                   lambda m=member: archive.extractfile(m))
                finally:
                    if compressed:
                        stream.close()
    except (OSError, ValueError, EOFError, tarfile.TarError, zipfile.BadZipFile) as exc:
        report["state"] = "PARTIAL_OR_UNREADABLE"
        report["warnings"].append(str(exc))
    if report["records"]:
        report["sha256"] = sha256_file(path)
    after = path.stat()
    if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
        report["state"] = "CHANGED_DURING_SCAN_NOT_TRUSTED"
        report["records"] = []
        report["warnings"].append("Archive changed during inventory; no member was accepted as prior-run proof")
    report["members_seen"] = members_seen
    report["selected_metadata_bytes"] = selected_bytes
    return report


def scan_prior_runs(roots: list[Path]) -> dict[str, Any]:
    records: dict[str, list[dict[str, Any]]] = {}
    hints: dict[str, set[str]] = {}
    warnings: list[dict[str, str]] = []
    root_report: list[dict[str, Any]] = []
    seen_files: set[Path] = set()
    seen_archives: set[Path] = set()
    archive_reports: list[dict[str, Any]] = []

    def accept_metadata(obj, evidence_path, kind, digest, path_parts, archive=None):
        pxd = str(obj.get("pxd", "")).strip().upper()
        if not PXD_RE.fullmatch(pxd):
            warnings.append({"path": evidence_path, "reason": "NO_VALID_TOP_LEVEL_PXD"})
            return
        path_pxds = {m.group(1).upper() for part in path_parts for m in PXD_IN_NAME_RE.finditer(part)}
        if path_pxds and path_pxds != {pxd}:
            warnings.append({"path": evidence_path, "reason": "PXD_METADATA_PATH_CONFLICT"})
            hints.setdefault(pxd, set()).add(evidence_path)
            return
        record = {"metadata_path": evidence_path, "metadata_sha256": digest,
                  "metadata_kind": kind, "version": obj.get("version", obj.get("pipeline_version")),
                  "state": obj.get("state", obj.get("status", "NOT_RECORDED")),
                  "mode": obj.get("mode", obj.get("input_mode")),
                  "created_utc": obj.get("created_utc", obj.get("started_utc")),
                  "numeric_xp_pairs": obj.get("numeric_xp_pairs"),
                  "provisional_xp_pairs": obj.get("provisional_xp_pairs"),
                  "exploratory_xp_pairs": obj.get("exploratory_xp_pairs"),
                  "reference_geometry_pairs": obj.get("reference_geometry_pairs"),
                  "unique_pair_contexts": obj.get("unique_pair_contexts"),
                  "score_counts": obj.get("score_counts")}
        if archive:
            record["archive"] = archive
        records.setdefault(pxd, []).append(record)

    def accept_archive(path):
        resolved = path.resolve()
        if resolved in seen_archives or path.is_symlink():
            return
        seen_archives.add(resolved)
        try:
            archive = read_archive_metadata(path)
        except OSError as exc:
            warnings.append({"path": str(path), "reason": "ARCHIVE_READ_ERROR: " + str(exc)})
            return
        for hint in archive.pop("hints"):
            hints.setdefault(hint["pxd"], set()).add(hint["path"])
        for warning in archive["warnings"]:
            warnings.append({"path": str(path), "reason": warning})
        entries = archive.pop("records")
        archive_reports.append(archive)
        evidence = {k: archive[k] for k in ("path", "size_bytes", "mtime_ns", "sha256", "state")}
        for entry in entries:
            accept_metadata(entry["object"], str(path) + "::" + entry["member"], entry["kind"],
                            entry["metadata_sha256"], (path.name,) + PurePosixPath(entry["member"]).parts,
                            archive=evidence)
    for raw_root in roots:
        root = raw_root.expanduser().absolute()
        report: dict[str, Any] = {"path": str(root), "state": "MISSING", "metadata_files": 0}
        root_report.append(report)
        if FIXED_VOLUME in root.parents and not is_mountpoint(FIXED_VOLUME):
            report["state"] = "VOLUME_NOT_MOUNTED_NOT_SCANNED"
            continue
        if root.is_file() and is_supported_archive(root):
            report["state"] = "SCANNED_ARCHIVE"
            accept_archive(root)
            continue
        if not root.is_dir():
            continue
        if root.is_symlink():
            warnings.append({"path": str(root), "reason": "SYMLINK_SCAN_ROOT_NOT_FOLLOWED"})
            report["state"] = "SYMLINK_NOT_SCANNED"
            continue
        report["state"] = "SCANNED"

        def on_error(exc: OSError) -> None:
            warnings.append({"path": str(exc.filename), "reason": str(exc)})

        for current, dirs, files in os.walk(root, followlinks=False, onerror=on_error):
            folder = Path(current)
            dirs[:] = sorted(d for d in dirs if d not in PRUNED_DIRECTORY_NAMES
                             and not d.startswith(".") and not (folder / d).is_symlink())
            for match in PXD_IN_NAME_RE.finditer(folder.name):
                hints.setdefault(match.group(1).upper(), set()).add(str(folder))
            for name in sorted(files):
                if is_supported_archive(folder / name):
                    accept_archive(folder / name)
            for name in sorted(METADATA_NAMES.intersection(files)):
                path = folder / name
                if path.is_symlink():
                    warnings.append({"path": str(path), "reason": "SYMLINK_METADATA_NOT_FOLLOWED"})
                    continue
                resolved = path.resolve()
                if resolved in seen_files:
                    continue
                seen_files.add(resolved)
                report["metadata_files"] += 1
                try:
                    obj = json_object(path)
                    relative = path.relative_to(root)
                    accept_metadata(obj, str(resolved), name, sha256_file(path), (root.name,) + relative.parts)
                except (OSError, ValueError, TypeError) as exc:
                    warnings.append({"path": str(path), "reason": f"UNREADABLE_METADATA: {exc}"})
    targets = [{"pxd": pxd, "evidence": "TOP_LEVEL_PXD_IN_PRIOR_XP_METADATA",
                "prior_records": sorted(rows, key=lambda r: r["metadata_path"]),
                "directory_hints": sorted(hints.get(pxd, []))}
               for pxd, rows in sorted(records.items())]
    uncertain = [{"pxd": pxd, "reason": "DIRECTORY_NAME_ONLY_OR_CONFLICT; NOT_AUTO_LAUNCHED",
                  "paths": sorted(paths)} for pxd, paths in sorted(hints.items()) if pxd not in records]
    return {"roots": root_report, "targets": targets, "uncertain_candidates": uncertain,
            "warnings": warnings, "metadata_files_seen": len(seen_files), "archives": archive_reports,
            "coverage_note": "Only listed scan roots were inspected. Named summary/manifest members in ZIP/tar archives were read within reported limits, without extraction; unmounted volumes and archive portions beyond limits were not scanned."}


def discover_engine(explicit: Path | None = None, home: Path | None = None) -> dict[str, Any]:
    work = (home or Path.home()) / "ncems-xp-test-work"
    candidates = [explicit.expanduser()] if explicit else [
        work / "PXD010470_Structure_Only_Pilot" / "pipeline" / "xp_pipeline.py",
        work / "xp_pipeline.py",
    ]
    if explicit is None and work.is_dir():
        candidates.extend(sorted(work.glob("*/pipeline/xp_pipeline.py")))
        candidates.extend(sorted(work.glob("*/xp_pipeline.py")))
    inspected = []
    for path in dict.fromkeys(candidates):
        if not path.is_file() or path.is_symlink():
            continue
        digest = sha256_file(path)
        inspected.append({"path": str(path.resolve()), "sha256": digest})
        if digest == EXPECTED_ENGINE_SHA256:
            return {"verified": True, "path": str(path.resolve()), "sha256": digest,
                    "expected_sha256": EXPECTED_ENGINE_SHA256, "inspected": inspected}
    return {"verified": False, "path": None, "sha256": None,
            "expected_sha256": EXPECTED_ENGINE_SHA256, "inspected": inspected,
            "reason": "No existing legacy XP engine matched the pinned source hash; no software was installed."}


def resolve_source(ref: str | None, local_store: Path | None = None,
                   catalog: Path | None = None) -> dict[str, Any]:
    if bool(local_store) != bool(catalog):
        raise ValueError("--local-store and --catalog must be supplied together")
    if local_store and catalog:
        store = local_store.expanduser().resolve(strict=True)
        cat = catalog.expanduser().resolve(strict=True)
        if not store.is_dir() or not cat.is_file():
            raise ValueError("Local store must be a directory and catalog must be a file")
        return {"mode": "local", "resolved_ref": "LOCAL", "local_store": str(store),
                "catalog": str(cat), "catalog_sha256": sha256_file(cat),
                "note": "Each run must record source input hashes; the local store itself is not immutable."}
    if not ref:
        return {"mode": "github", "repository": SOURCE_REPOSITORY, "resolved_ref": None,
                "reason": "Choose --ref main or an explicit verified 40-character Git commit."}
    if re.fullmatch(r"[0-9a-fA-F]{40}", ref):
        return {"mode": "github", "repository": SOURCE_REPOSITORY,
                "requested_ref": ref, "resolved_ref": ref.lower(), "resolution": "EXPLICIT_COMMIT"}
    if ref != "main":
        raise ValueError("--ref accepts main or a 40-character Git commit")
    url = f"https://api.github.com/repos/{SOURCE_REPOSITORY}/commits/main"
    request = urllib.request.Request(url, headers={"User-Agent": "NCEMS-XP-v33-rerun-planner",
                                                  "Accept": "application/vnd.github+json"})
    with urllib.request.urlopen(request, timeout=30) as response:
        payload = json.load(response)
    commit = str(payload.get("sha", ""))
    if not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise ValueError("GitHub did not return an immutable commit SHA")
    return {"mode": "github", "repository": SOURCE_REPOSITORY, "requested_ref": "main",
            "resolved_ref": commit, "resolved_utc": utc_now(), "resolution_url": url}


def create_plan(args: argparse.Namespace) -> dict[str, Any]:
    destination = require_mounted_volume(args.plan)
    out_root = require_mounted_volume(args.out_root)
    if destination.exists():
        raise FileExistsError(f"Plan already exists; no file overwritten: {destination}")
    roots = [Path(x) for x in args.scan_root] if args.scan_root else default_scan_roots()
    inventory = scan_prior_runs(roots)
    engine = discover_engine(args.engine)
    source = resolve_source(args.ref, args.local_store, args.catalog)
    runner = Path(__file__).resolve().with_name("run_v33.py")
    runner_info = {"path": str(runner), "sha256": sha256_file(runner) if runner.is_file() else None}
    blockers = []
    if not inventory["targets"]:
        blockers.append("No prior PXD with valid owned metadata was found")
    if not engine["verified"]:
        blockers.append(engine["reason"])
    if not source.get("resolved_ref"):
        blockers.append(source["reason"])
    if not runner_info["sha256"]:
        blockers.append("run_v33.py is absent from this package")
    context = None
    context_raw = None
    if args.experimental_context:
        context_path = args.experimental_context.expanduser().resolve(strict=True)
        validate_experimental_context(json_object(context_path))
        context_raw = context_path.read_bytes()
        context_hash = hashlib.sha256(context_raw).hexdigest()
        context = {"original_path": str(context_path), "sha256": context_hash,
                   "snapshot_path": str(destination.parent / ("experimental_context_" + context_hash + ".json")),
                   "status": "USER_SUPPLIED_EVIDENCE; NOT_APPROVED_BY_THE_QUEUE"}
    production_package = production_package_snapshot(runner.parent)
    if runner_info["sha256"] and production_package["files_sha256"].get("run_v33.py") != runner_info["sha256"]:
        raise ValueError("Runner changed during planning; no plan was written")
    plan = {"schema": PLAN_SCHEMA, "version": VERSION, "created_utc": utc_now(),
            "scope": "Fresh XP runs for prior attempted PXDs only; no new dataset selection or ReLink execution",
            "launch_ready": not blockers, "blockers": blockers,
            "inventory": inventory, "engine": engine, "source": source,
            "experimental_context": context,
            "production_package": production_package,
            "runner": runner_info, "out_root": str(out_root),
            "ledger_path": str(destination.parent / "xp_v33_attempts.jsonl"),
            "ncpus_per_pxd": args.ncpus, "model_timeout_seconds": args.model_timeout,
            "execution_mode": "FULL_FRESH_INTAKE_AND_GEOMETRY; NEVER_AUTO_REUSE_FILTERED_V32_RUNS",
            "scientific_status": "A completed execution does not establish calibrated XP or validated XL identifications."}
    require_mounted_volume(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    if context:
        snapshot = Path(context["snapshot_path"])
        if snapshot.exists():
            if sha256_file(snapshot) != context["sha256"]:
                raise ValueError("Existing experimental-context snapshot has different bytes")
        else:
            with snapshot.open("xb") as handle:
                handle.write(context_raw)
                handle.flush()
                os.fsync(handle.fileno())
    with destination.open("x", encoding="utf-8") as handle:
        json.dump(plan, handle, indent=2, allow_nan=False)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    print("PLAN:", destination)
    print("VERIFIED PRIOR PXDS:", len(inventory["targets"]))
    print("PXDS:", " ".join(t["pxd"] for t in inventory["targets"]) or "NONE")
    print("UNCERTAIN DIRECTORY-ONLY CANDIDATES:", len(inventory["uncertain_candidates"]), "(not auto-launched)")
    print("SCAN WARNINGS:", len(inventory["warnings"]))
    for root_info in inventory["roots"]:
        print("SCAN ROOT:", root_info["state"], root_info["path"])
    for archive in inventory["archives"]:
        if archive["state"] != "SCANNED":
            print("ARCHIVE COVERAGE:", archive["state"], archive["path"])
    print("PINNED SOURCE:", source.get("resolved_ref") or "NOT SELECTED")
    print("LAUNCH READY:", "YES" if plan["launch_ready"] else "NO")
    for blocker in blockers:
        print("BLOCKER:", blocker)
    return plan


def append_ledger(path: Path, event: dict[str, Any]) -> None:
    encoded = (json.dumps(event, sort_keys=True, allow_nan=False) + "\n").encode("utf-8")
    with path.open("ab") as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        handle.write(encoded)
        handle.flush()
        os.fsync(handle.fileno())


def read_ledger(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    values = []
    with path.open("r", encoding="utf-8") as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_SH)
        for lineno, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
                if not isinstance(row, dict):
                    raise ValueError("Ledger row is not an object")
                values.append(row)
            except ValueError as exc:
                raise ValueError(f"Ledger line {lineno} is incomplete or invalid; preserve it and review before resuming") from exc
    return values


def result_summaries(root: Path, pxd: str) -> list[dict[str, Any]]:
    found = []
    if not root.exists():
        return found
    for current, dirs, files in os.walk(root, followlinks=False):
        folder = Path(current)
        dirs[:] = [d for d in dirs if d not in PRUNED_DIRECTORY_NAMES and not (folder / d).is_symlink()]
        if "run_summary.json" not in files:
            continue
        path = folder / "run_summary.json"
        try:
            data = json_object(path)
            if str(data.get("pxd", "")).upper() != pxd:
                continue
            found.append({"path": str(path), "sha256": sha256_file(path),
                          "version": data.get("version"), "state": data.get("state", data.get("status")),
                          "numeric_xp_pairs": data.get("numeric_xp_pairs"),
                          "provisional_xp_pairs": data.get("provisional_xp_pairs"),
                          "exploratory_xp_pairs": data.get("exploratory_xp_pairs"),
                          "reference_geometry_pairs": data.get("reference_geometry_pairs"),
                          "unique_pair_contexts": data.get("unique_pair_contexts"),
                          "score_counts": data.get("score_counts"),
                          "unscored_candidate_pairs": data.get("unscored_candidate_pairs")})
        except (OSError, ValueError, TypeError) as exc:
            found.append({"path": str(path), "read_error": str(exc)})
    return sorted(found, key=lambda r: r["path"])


def outcome_for(returncode: int, summaries: list[dict[str, Any]]) -> str:
    states = [str(row.get("state") or "") for row in summaries
              if str(row.get("version") or "").startswith("3.3")]
    if returncode == 0:
        return "COMPUTATION_COMPLETED" if any(s.startswith("COMPLETE") for s in states) else "EXIT_ZERO_STATUS_UNVERIFIED"
    if returncode == 4:
        return "POLICY_OR_PREFLIGHT_STOP"
    if returncode == 3:
        return "PARTIAL_OR_FAILED"
    if returncode < 0 or returncode in (130, 143):
        return "INTERRUPTED"
    return "RUN_ERROR"


def make_command(plan: dict[str, Any], pxd: str, attempt_root: Path) -> list[str]:
    command = [sys.executable, plan["runner"]["path"], pxd,
               "--out-root", str(attempt_root), "--engine", plan["engine"]["path"],
               "--ref", plan["source"]["resolved_ref"],
               "--ncpus", str(plan["ncpus_per_pxd"]),
               "--model-timeout", str(plan["model_timeout_seconds"])]
    if plan["source"]["mode"] == "local":
        command.extend(["--local-store", plan["source"]["local_store"],
                        "--catalog", plan["source"]["catalog"]])
    if plan.get("experimental_context"):
        command.extend(["--experimental-context", plan["experimental_context"]["snapshot_path"]])
    return command


class ActiveChildren:
    def __init__(self) -> None:
        self.lock = threading.Lock()
        self.children: dict[str, subprocess.Popen] = {}
        self.stop = threading.Event()

    def terminate(self) -> None:
        self.stop.set()
        with self.lock:
            for process in list(self.children.values()):
                if process.poll() is None:
                    try:
                        os.killpg(process.pid, signal.SIGTERM)
                    except ProcessLookupError:
                        pass


def run_one(plan: dict[str, Any], plan_id: str, pxd: str, ledger: Path,
            active: ActiveChildren) -> dict[str, Any]:
    base = require_mounted_volume(Path(plan["out_root"]))
    lock_dir = base.parent / ".queue_locks"
    log_dir = base.parent / "queue_logs"
    lock_dir.mkdir(parents=True, exist_ok=True)
    log_dir.mkdir(parents=True, exist_ok=True)
    attempt_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ") + "_" + uuid.uuid4().hex[:8]
    attempt_root = base / pxd / attempt_id
    log_path = log_dir / f"{pxd}_{attempt_id}.log"
    common = {"plan_sha256": plan_id, "pxd": pxd, "attempt_id": attempt_id,
              "output_root": str(attempt_root), "log_path": str(log_path),
              "source_ref": plan["source"]["resolved_ref"],
              "scientific_validation": "NOT_ESTABLISHED_BY_EXECUTION_STATUS"}
    with (lock_dir / (pxd + ".lock")).open("a+") as lock:
        try:
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            event = {**common, "event": "LOCKED_NOT_LAUNCHED", "time_utc": utc_now()}
            append_ledger(ledger, event)
            return event
        if active.stop.is_set():
            event = {**common, "event": "CANCELLED_BEFORE_LAUNCH", "time_utc": utc_now()}
            append_ledger(ledger, event)
            return event
        try:
            verify_production_package(plan)
        except (OSError, ValueError, KeyError, TypeError) as exc:
            event = {**common, "event": "INTEGRITY_BLOCKED_NOT_LAUNCHED", "time_utc": utc_now(),
                     "error": str(exc)}
            append_ledger(ledger, event)
            print(f"BLOCKED {pxd}: {exc}", flush=True)
            return event
        require_mounted_volume(attempt_root)
        command = make_command(plan, pxd, attempt_root)
        append_ledger(ledger, {**common, "event": "STARTING", "time_utc": utc_now(), "command": command})
        print(f"STARTING {pxd}; log: {log_path}", flush=True)
        process = None
        try:
            with log_path.open("xb") as log:
                environment = os.environ.copy()
                environment.update(PYTHONUNBUFFERED="1", OMP_NUM_THREADS="1",
                                   OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1")
                process = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT,
                                           env=environment, start_new_session=True)
                with active.lock:
                    active.children[attempt_id] = process
                append_ledger(ledger, {**common, "event": "RUNNING", "time_utc": utc_now(), "pid": process.pid})
                stop_started = None
                while process.poll() is None:
                    if active.stop.is_set():
                        if stop_started is None:
                            stop_started = time.monotonic()
                            try:
                                os.killpg(process.pid, signal.SIGTERM)
                            except ProcessLookupError:
                                pass
                        elif time.monotonic() - stop_started > 15:
                            try:
                                os.killpg(process.pid, signal.SIGKILL)
                            except ProcessLookupError:
                                pass
                    active.stop.wait(0.2) if not active.stop.is_set() else time.sleep(0.2)
                returncode = process.wait()
                with active.lock:
                    active.children.pop(attempt_id, None)
                log.flush()
                os.fsync(log.fileno())
            summaries = result_summaries(attempt_root, pxd)
            event = {**common, "event": "FINISHED", "time_utc": utc_now(),
                     "returncode": returncode, "outcome": outcome_for(returncode, summaries),
                     "result_summaries": summaries}
        except (OSError, ValueError) as exc:
            if process is not None and process.poll() is None:
                try:
                    os.killpg(process.pid, signal.SIGTERM)
                    process.wait(timeout=15)
                except subprocess.TimeoutExpired:
                    os.killpg(process.pid, signal.SIGKILL)
                    process.wait()
                except ProcessLookupError:
                    pass
            event = {**common, "event": "LAUNCH_ERROR", "time_utc": utc_now(), "error": str(exc)}
        finally:
            with active.lock:
                active.children.pop(attempt_id, None)
        append_ledger(ledger, event)
        print(f"FINISHED {pxd}: {event.get('outcome', event['event'])}; exit {event.get('returncode', 'unavailable')}", flush=True)
        return event


def execute_plan(args: argparse.Namespace) -> int:
    plan_path = args.execute.expanduser().resolve(strict=True)
    plan = json_object(plan_path, limit=64 * 1024 * 1024)
    if plan.get("schema") != PLAN_SCHEMA or not plan.get("launch_ready"):
        raise ValueError("This is not a launch-ready v3.3 rerun plan")
    out_root = require_mounted_volume(Path(plan["out_root"]))
    ledger = require_mounted_volume(Path(plan["ledger_path"]))
    if Path(plan["runner"]["path"]).resolve() != Path(__file__).resolve().with_name("run_v33.py"):
        raise ValueError("Plan belongs to a different installed runner path; create a new plan")
    try:
        verify_production_package(plan)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        ledger.parent.mkdir(parents=True, exist_ok=True)
        append_ledger(ledger, {"event": "PLAN_INTEGRITY_BLOCKED_NOT_LAUNCHED", "time_utc": utc_now(),
                              "plan_sha256": sha256_file(plan_path), "error": str(exc)})
        raise
    if sha256_file(Path(plan["runner"]["path"])) != plan["runner"]["sha256"]:
        raise ValueError("Runner changed after planning; create a new plan")
    if not plan["engine"]["verified"] or sha256_file(Path(plan["engine"]["path"])) != EXPECTED_ENGINE_SHA256:
        raise ValueError("Legacy engine no longer matches the pinned source hash")
    source = plan["source"]
    if source["mode"] == "github":
        if source.get("repository") != SOURCE_REPOSITORY or not re.fullmatch(r"[0-9a-f]{40}", source["resolved_ref"]):
            raise ValueError("Plan must contain one immutable xHAMLET Git commit")
    elif source["mode"] == "local":
        if sha256_file(Path(source["catalog"])) != source["catalog_sha256"]:
            raise ValueError("Local catalog changed after planning")
    else:
        raise ValueError("Unrecognized plan source mode")
    if plan.get("experimental_context"):
        context = plan["experimental_context"]
        if sha256_file(Path(context["snapshot_path"])) != context["sha256"]:
            raise ValueError("Experimental-context evidence changed after planning")
    pxd_ids = [target["pxd"] for target in plan["inventory"]["targets"]]
    if len(set(pxd_ids)) != len(pxd_ids) or any(not PXD_RE.fullmatch(pxd) for pxd in pxd_ids):
        raise ValueError("Invalid or duplicate PXD in plan")
    if any(not target.get("prior_records") for target in plan["inventory"]["targets"]):
        raise ValueError("A target has no prior metadata evidence; directory hints cannot launch jobs")
    queue_lock_dir = out_root.parent / ".queue_locks"
    queue_lock_dir.mkdir(parents=True, exist_ok=True)
    with (queue_lock_dir / "queue.lock").open("a+") as queue_lock:
        try:
            fcntl.flock(queue_lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise ValueError("Another XP rerun queue is already active in this project; attach to its tmux session") from exc
        return execute_locked_plan(args, plan_path, plan, out_root, ledger, pxd_ids)


def execute_locked_plan(args: argparse.Namespace, plan_path: Path, plan: dict[str, Any],
                        out_root: Path, ledger: Path, pxd_ids: list[str]) -> int:
    source = plan["source"]
    plan_id = sha256_file(plan_path)
    history = read_ledger(ledger)
    previous = {}
    for event in history:
        if event.get("plan_sha256") == plan_id and event.get("event") in SETTLED_EVENTS:
            previous[event.get("pxd")] = event
    pending = []
    for pxd in pxd_ids:
        last = previous.get(pxd)
        if last and (not args.retry_incomplete or last.get("outcome") == "COMPUTATION_COMPLETED"):
            print(f"ALREADY ATTEMPTED IN THIS PLAN: {pxd} — {last.get('outcome', last.get('event'))}; not relaunched")
        else:
            pending.append(pxd)
    if not pending:
        print("No pending PXDs in this plan. Existing results were not changed.")
        return 0
    ledger.parent.mkdir(parents=True, exist_ok=True)
    out_root.mkdir(parents=True, exist_ok=True)
    print(f"Executing {len(pending)} prior PXDs with at most {args.workers} concurrent jobs.")
    print("FROZEN SOURCE:", source["resolved_ref"])
    print("ATTEMPT LEDGER:", ledger)
    active = ActiveChildren()
    prior_handlers = {}

    def handle_signal(signum, frame):
        print("Stopping active XP children; preserved output and ledger will remain.", flush=True)
        active.terminate()

    for signum in (signal.SIGINT, signal.SIGTERM):
        prior_handlers[signum] = signal.signal(signum, handle_signal)
    results = []
    try:
        with ThreadPoolExecutor(max_workers=args.workers) as pool:
            futures = {pool.submit(run_one, plan, plan_id, pxd, ledger, active): pxd for pxd in pending}
            for future in as_completed(futures):
                try:
                    results.append(future.result())
                except Exception as exc:
                    event = {"event": "QUEUE_ERROR", "plan_sha256": plan_id,
                             "pxd": futures[future], "time_utc": utc_now(), "error": str(exc)}
                    append_ledger(ledger, event)
                    results.append(event)
    finally:
        for signum, handler in prior_handlers.items():
            signal.signal(signum, handler)
    counts: dict[str, int] = {}
    for event in results:
        key = event.get("outcome", event["event"])
        counts[key] = counts.get(key, 0) + 1
    print("QUEUE OUTCOMES:", json.dumps(counts, sort_keys=True))
    print("Completion above describes execution only; inspect scoring eligibility and exclusions separately.")
    return 0 if all(event.get("outcome") == "COMPUTATION_COMPLETED" for event in results) else 3


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--plan", type=Path, help="Write a new immutable plan; no scoring is launched")
    modes.add_argument("--execute", type=Path, help="Execute a previously saved plan")
    parser.add_argument("--scan-root", action="append", default=[], help="Existing prior-XP run root; repeat as needed")
    parser.add_argument("--out-root", type=Path, default=DEFAULT_PROJECT / "runs")
    parser.add_argument("--engine", type=Path)
    parser.add_argument("--ref", help="main (resolved once) or an explicit 40-character Git commit")
    parser.add_argument("--local-store", type=Path)
    parser.add_argument("--catalog", type=Path)
    parser.add_argument("--experimental-context", type=Path,
                        help="Optional reviewed reagent-evidence JSON; frozen as supplied, never auto-approved")
    parser.add_argument("--ncpus", type=int, default=1, help="CPUs per PXD process; default 1")
    parser.add_argument("--model-timeout", type=int, default=3600)
    parser.add_argument("--workers", type=int, choices=(1, 2), default=2)
    parser.add_argument("--retry-incomplete", action="store_true",
                        help="Explicitly retry settled failed/blocked/unverified attempts from the same plan")
    args = parser.parse_args(argv)
    if args.ncpus < 1 or args.model_timeout < 1:
        parser.error("CPU count and timeout must be positive")
    if args.execute and (args.scan_root or args.engine or args.ref or args.local_store or args.catalog or args.experimental_context):
        parser.error("Execution uses frozen source/engine/targets; do not pass planning overrides")
    try:
        if args.plan:
            plan = create_plan(args)
            return 0 if plan["launch_ready"] else 4
        return execute_plan(args)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(f"STOP: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

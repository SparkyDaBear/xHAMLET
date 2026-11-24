#!/usr/bin/env python3
"""Copy this XP package to a NEW directory on the existing fixed volume.

No environment installation, source-package modification, ReLink changes, or
replacement of a different installed version is performed. Identical bytes in
an existing destination may be reused after a full content-hash comparison.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import sys
import tempfile

FIXED_VOLUME = Path("/media/volume/xhamlet-data-5")
RECORD_NAME = "INSTALLATION_RECORD.json"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def mounted(path: Path) -> bool:
    if path.is_mount():
        return True
    try:
        for line in Path("/proc/self/mountinfo").read_text().splitlines():
            target = re.sub(r"\\([0-7]{3})", lambda m: chr(int(m.group(1), 8)), line.split()[4])
            if Path(target) == path:
                return True
    except (OSError, IndexError):
        pass
    return False


def file_manifest(folder: Path) -> dict[str, str]:
    result = {}
    for current, dirs, files in os.walk(folder, followlinks=False):
        parent = Path(current)
        if any((parent / name).is_symlink() for name in dirs + files):
            raise ValueError(f"Package symlinks are not accepted: {parent}")
        dirs[:] = sorted(name for name in dirs if name not in ("__pycache__", ".git"))
        for name in sorted(files):
            path = parent / name
            if name.endswith((".pyc", ".pyo")) or path.relative_to(folder).as_posix() == RECORD_NAME:
                continue
            if not path.is_file():
                raise ValueError(f"Package contains a nonregular file: {path}")
            result[path.relative_to(folder).as_posix()] = sha256_file(path)
    if not result:
        raise ValueError("Package is empty")
    return result


def verify_declared_hashes(source: Path, manifest: dict[str, str]) -> None:
    hashes = source / "SHA256SUMS.txt"
    if not hashes.is_file():
        return
    seen = set()
    for line in hashes.read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        match = re.fullmatch(r"([0-9a-fA-F]{64})\s+\*?(.+)", line)
        if not match:
            raise ValueError("Malformed SHA256SUMS.txt line")
        digest, relative = match.groups()
        path = PurePosixPath(relative)
        if path.is_absolute() or ".." in path.parts or relative in seen:
            raise ValueError("Unsafe or duplicate path in SHA256SUMS.txt")
        seen.add(relative)
        if manifest.get(path.as_posix()) != digest.lower():
            raise ValueError(f"Package checksum mismatch: {relative}")


def install(source: Path, destination: Path) -> dict[str, object]:
    if not mounted(FIXED_VOLUME):
        raise ValueError(f"Fixed volume is not mounted: {FIXED_VOLUME}. Nothing was copied.")
    source = source.expanduser().resolve(strict=True)
    destination = destination.expanduser().resolve()
    volume = FIXED_VOLUME.resolve(strict=True)
    if destination == volume or volume not in destination.parents:
        raise ValueError(f"Destination must be a project path inside mounted {FIXED_VOLUME}")
    if source == destination or source in destination.parents or destination in source.parents:
        raise ValueError("Source and destination must be separate directories")
    if not source.is_dir() or not (source / "run_v33.py").is_file() or not (source / "rerun_all.py").is_file():
        raise ValueError("Source is not a complete v3.3 package")
    expected = file_manifest(source)
    verify_declared_hashes(source, expected)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with (destination.parent / ".v33_install.lock").open("a+") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        if destination.exists():
            if not destination.is_dir() or file_manifest(destination) != expected:
                raise FileExistsError(f"Different files already exist at {destination}; no overwrite performed")
            return {"state": "IDENTICAL_EXISTING_VERSION_REUSED", "destination": str(destination),
                    "files_verified": len(expected)}
        staging = Path(tempfile.mkdtemp(prefix=".xp_v33_install_", dir=destination.parent))
        try:
            for relative in expected:
                original = source / relative
                target = staging / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(original, target)
            if file_manifest(staging) != expected:
                raise ValueError("Copied package failed byte verification")
            record = {"version": "3.3.0", "installed_utc": datetime.now(timezone.utc).isoformat(),
                      "source": str(source), "destination": str(destination), "files_sha256": expected,
                      "environment_changes": "NONE", "relink_changes": "NONE"}
            with (staging / RECORD_NAME).open("x", encoding="utf-8") as handle:
                json.dump(record, handle, indent=2, sort_keys=True)
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            if destination.exists():
                raise FileExistsError("Destination appeared during installation; no overwrite performed")
            staging.rename(destination)
            return {"state": "NEW_SEPARATE_PACKAGE_INSTALLED", "destination": str(destination),
                    "files_verified": len(expected)}
        finally:
            if staging.exists():
                shutil.rmtree(staging)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument("--destination", type=Path,
                        default=FIXED_VOLUME / "NCEMS_XP_v33" / "NCEMS_XP_v3_3")
    args = parser.parse_args(argv)
    try:
        result = install(args.source, args.destination)
        print(json.dumps(result, indent=2))
        return 0
    except (OSError, ValueError) as exc:
        print(f"STOP: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

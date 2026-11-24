#!/usr/bin/env python3
"""
organize_files.py

A lightweight, safe file organizer for a target directory.

Usage:
    python organize_files.py /path/to/target --dry-run
    python organize_files.py . --report-json ./organization-report.json

Features:
- Moves files into folders by category
- Dry-run mode to preview actions without making changes
- Collision safe: appends numeric suffix if filename exists
- Optional JSON action report for automation and auditing
- Optional recursive discovery of files in nested directories
"""

import argparse
from fnmatch import fnmatchcase
import math
import time
from numbers import Real
import stat
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path
from collections import defaultdict

CATEGORIES = {
    "Images": {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg", ".webp", ".tiff", ".heic", ".heif"},
    "Documents": {".doc", ".docx", ".txt", ".md", ".rst", ".odt", ".xls", ".xlsx", ".ppt", ".pptx"},
    "Audio": {".mp3", ".wav", ".aac", ".flac", ".ogg", ".m4a"},
    "Video": {".mp4", ".mkv", ".mov", ".avi", ".webm", ".flv"},
    "Archives": {".zip", ".tar", ".gz", ".rar", ".7z"},
    "Scripts": {".py", ".sh", ".js", ".php", ".rb", ".pl"},
    "Notebooks": {".ipynb"},
    "PDFs": {".pdf"},
    "Data": {".csv", ".json", ".xml", ".yaml", ".yml", ".parquet"},
}

# Reverse lookup for quick extension -> category
EXT_TO_CAT = {}
for cat, exts in CATEGORIES.items():
    for e in exts:
        EXT_TO_CAT[e] = cat


def categorize(path: Path):
    if path.is_dir():
        return None
    ext = path.suffix.lower()
    return EXT_TO_CAT.get(ext, "Others")


def _move_no_replace(src, dest):
    """Copy to an exclusively created destination before removing the source."""
    descriptor = os.open(src, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
    created = False
    destination_identity = None
    try:
        with os.fdopen(descriptor, "rb") as source:
            source_identity = os.fstat(source.fileno())
            if not stat.S_ISREG(source_identity.st_mode):
                raise ValueError("Source must be a regular file.")
            with dest.open("xb") as output:
                created = True
                destination_identity = os.fstat(output.fileno())
                shutil.copyfileobj(source, output)
                output.flush()
                os.fsync(output.fileno())
            shutil.copystat(src, dest, follow_symlinks=False)
            current = src.lstat()
            if (current.st_dev, current.st_ino) != (source_identity.st_dev, source_identity.st_ino):
                # Keep the completed copy of the original and the replacement
                # source. Never unlink another writer's replacement file.
                created = False
                raise OSError("Source changed while being moved; both files were preserved.")
            if (current.st_size, current.st_mtime_ns) != (source_identity.st_size, source_identity.st_mtime_ns):
                created = False
                raise OSError("Source content changed while being moved; both files were preserved.")
            src.unlink()
            created = False
            return source_identity.st_size
    finally:
        if created and destination_identity is not None:
            try:
                current = dest.lstat()
                if (current.st_dev, current.st_ino) == (destination_identity.st_dev, destination_identity.st_ino):
                    dest.unlink()
            except FileNotFoundError:
                pass


def safe_move(src: Path, dest_dir: Path, dry_run=False, reserved_destinations=None, include_sizes=False):
    if not src.is_file() and not src.is_symlink():
        raise ValueError("Source must be a regular file.")
    if src.is_symlink():
        raise ValueError("Source file must not be a symbolic link.")
    if dest_dir.is_symlink():
        raise ValueError("Destination directory must not be a symbolic link.")
    if dest_dir.exists() and not dest_dir.is_dir():
        raise NotADirectoryError(f"Destination path is not a directory: {dest_dir}")

    dest = dest_dir / src.name
    # Treat dangling symlinks as occupied paths too. Path.exists() alone
    # follows symlinks and returns False when the link target is missing.
    if dest.exists() or dest.is_symlink() or (reserved_destinations is not None and dest in reserved_destinations):
        base = src.stem
        ext = src.suffix
        i = 1
        while True:
            candidate = dest_dir / f"{base}({i}){ext}"
            if (not candidate.exists() and not candidate.is_symlink()
                    and (reserved_destinations is None or candidate not in reserved_destinations)):
                dest = candidate
                break
            i += 1
    size_bytes = src.stat().st_size if dry_run and include_sizes else None
    if dry_run:
        if reserved_destinations is not None:
            reserved_destinations.add(dest)
        print(f"[dry-run] Move: {src} -> {dest}")
        status = "planned"
    else:
        dest_dir.mkdir(parents=True, exist_ok=True)
        while True:
            try:
                size_bytes = _move_no_replace(src, dest)
                break
            except FileExistsError:
                # A concurrent writer won the name after the initial scan.
                base, ext = src.stem, src.suffix
                i = 1
                while True:
                    dest = dest_dir / f"{base}({i}){ext}"
                    if (not dest.exists() and not dest.is_symlink()
                            and (reserved_destinations is None or dest not in reserved_destinations)):
                        break
                    i += 1
        print(f"Move: {src} -> {dest}")
        status = "moved"
    action = {"source": str(src), "destination": str(dest), "status": status}
    if include_sizes:
        action["size_bytes"] = size_bytes
    return action


def discover_paths(target, recursive, include_hidden, excluded_directories):
    if not recursive:
        return target.iterdir()
    generated_categories = {name.casefold() for name in set(CATEGORIES) | {"Others"}}
    def raise_walk_error(error):
        raise error
    def walk():
        for root, directories, files in os.walk(target, topdown=True, followlinks=False, onerror=raise_walk_error):
            current = Path(root)
            directories[:] = [name for name in directories
                if name not in excluded_directories
                and (include_hidden or not name.startswith("."))
                and not (current == target and name.casefold() in generated_categories)
                and not (current / name).is_symlink()]
            for name in files:
                yield current / name
    return walk()


def scan_and_group(
    target: Path,
    include_hidden: bool = False,
    exclude_extensions=None,
    recursive: bool = False,
    min_size_bytes=None,
    max_size_bytes=None,
    exclude_directories=None,
    min_age_seconds=None,
    include_patterns=None,
    exclude_patterns=None,
):
    """Group files by category, optionally discovering files below the target."""
    if include_patterns is not None and (not isinstance(include_patterns, (list, tuple)) or any(not isinstance(pattern, str) or not pattern.strip() for pattern in include_patterns)):
        raise ValueError("include_patterns must be a list of non-empty patterns.")
    if exclude_patterns is not None and (not isinstance(exclude_patterns, (list, tuple)) or any(not isinstance(pattern, str) or not pattern.strip() for pattern in exclude_patterns)):
        raise ValueError("exclude_patterns must be a list of non-empty patterns.")
    excluded = {
        ("." + extension.strip().lstrip(".")).lower()
        for extension in (exclude_extensions or [])
        if isinstance(extension, str) and extension.strip()
    }
    for name, value in (("min_size_bytes", min_size_bytes), ("max_size_bytes", max_size_bytes)):
        if value is not None and (
            not isinstance(value, int) or isinstance(value, bool) or value < 0
        ):
            raise ValueError(f"{name} must be a non-negative integer.")

    if min_size_bytes is not None and max_size_bytes is not None and min_size_bytes > max_size_bytes:
        raise ValueError("min_size_bytes cannot exceed max_size_bytes.")

    if min_age_seconds is not None and (isinstance(min_age_seconds, bool) or not isinstance(min_age_seconds, Real) or not math.isfinite(min_age_seconds) or min_age_seconds < 0):
        raise ValueError("min_age_seconds must be a finite non-negative number.")
    age_cutoff = time.time() - min_age_seconds if min_age_seconds is not None else None
    excluded_directories = set(exclude_directories or [])
    groups = defaultdict(list)
    paths = sorted(
        discover_paths(target, recursive, include_hidden, excluded_directories),
        key=lambda path: (
            path.relative_to(target).as_posix().casefold(),
            path.relative_to(target).as_posix(),
        ),
    )
    generated_categories = {name.casefold() for name in set(CATEGORIES) | {"Others"}}

    for path in paths:
        relative = path.relative_to(target)
        if exclude_patterns and any(fnmatchcase(relative.as_posix(), pattern) for pattern in exclude_patterns):
            continue
        if include_patterns and not any(fnmatchcase(relative.as_posix(), pattern) for pattern in include_patterns):
            continue
        if any(part in excluded_directories for part in relative.parts[:-1]):
            continue
        if path.is_symlink():
            # Avoid moving a link whose target may be outside the selected directory.
            continue
        if recursive and relative.parts[0].casefold() in generated_categories:
            # Do not reprocess files already placed in organizer output folders.
            continue
        if not include_hidden and any(part.startswith(".") for part in relative.parts):
            # Hidden files and hidden directory trees are opt-in.
            continue
        if not path.is_file():
            # FIFOs, sockets and devices must never be moved or opened as files.
            continue
        if path.suffix.lower() in excluded:
            continue
        metadata = path.stat()
        if age_cutoff is not None and metadata.st_mtime > age_cutoff:
            continue
        size_bytes = metadata.st_size
        if min_size_bytes is not None and size_bytes < min_size_bytes:
            continue
        if max_size_bytes is not None and size_bytes > max_size_bytes:
            continue
        category = categorize(path)
        groups[category].append(path)
    return groups


def write_report(report_path: Path, target: Path, dry_run: bool, actions: list, include_sizes=False):
    """Atomically persist a JSON report so a failed write preserves the previous report."""
    counts = {
        "planned": sum(action["status"] == "planned" for action in actions),
        "moved": sum(action["status"] == "moved" for action in actions),
        "failed": sum(action["status"] == "failed" for action in actions),
    }
    if include_sizes or any("size_bytes" in action for action in actions):
        counts.update({f"{status}_bytes": sum(action.get("size_bytes") or 0 for action in actions if action["status"] == status) for status in ("planned", "moved")})
    report = {
        "target": str(target),
        "dry_run": dry_run,
        "summary": {"total": len(actions), **counts},
        "actions": actions,
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=report_path.parent,
            prefix=f".{report_path.name}.",
            suffix=".tmp",
            delete=False,
        ) as temporary_file:
            temporary_path = Path(temporary_file.name)
            json.dump(report, temporary_file, indent=2)
            temporary_file.write("\n")
            temporary_file.flush()
            os.fsync(temporary_file.fileno())

        os.replace(temporary_path, report_path)
        temporary_path = None
    finally:
        if temporary_path is not None:
            try:
                temporary_path.unlink()
            except FileNotFoundError:
                pass


def main(argv=None):
    parser = argparse.ArgumentParser(description="Organize files in a directory by type")
    parser.add_argument("--version", action="version", version="Python File Organizer 1.0.0")
    parser.add_argument("target", nargs="?", default=".", help="Target directory (default: current directory)")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done without moving files")
    parser.add_argument("--include-hidden", action="store_true", help="Include hidden files (starting with .)")
    parser.add_argument(
        "--recursive",
        action="store_true",
        help="Discover files in nested directories and move them into the top-level category folders",
    )
    parser.add_argument(
        "--exclude-ext",
        action="append",
        default=[],
        metavar="EXT",
        help="Skip files with this extension (repeatable, e.g. --exclude-ext .tmp)",
    )
    parser.add_argument(
        "--min-size-bytes",
        type=int,
        metavar="BYTES",
        help="Include only files at least this many bytes",
    )
    parser.add_argument(
        "--max-size-bytes",
        type=int,
        metavar="BYTES",
        help="Include only files at most this many bytes",
    )
    parser.add_argument(
        "--report-json",
        metavar="PATH",
        help="Write a JSON summary of planned or completed moves to PATH",
    )
    parser.add_argument("--exclude-dir", action="append", default=[], help="Skip a directory name during recursive discovery (repeatable)")
    parser.add_argument("--continue-on-error", action="store_true", help="Continue other moves after a failure; return failure and retain failed audit entries")
    parser.add_argument("--category", action="append", choices=sorted(set(CATEGORIES) | {"Others"}), help="Organize only a selected category (repeatable)")
    parser.add_argument("--older-than-days", type=float, help="Organize only files whose modification time is at least N days old")
    parser.add_argument("--include-sizes", action="store_true", help="Include observed file bytes and planned/moved byte totals in audit reports")
    parser.add_argument("--include-pattern", action="append", default=[], help="Include relative POSIX paths matching any case-sensitive fnmatch pattern (repeatable)")
    parser.add_argument("--exclude-pattern", action="append", default=[], help="Skip matching relative POSIX paths using case-sensitive fnmatch (repeatable)")
    args = parser.parse_args(argv)
    if any(not pattern.strip() for pattern in args.exclude_pattern):
        parser.error("--exclude-pattern cannot be empty")
    if any(not pattern.strip() for pattern in args.include_pattern):
        parser.error("--include-pattern cannot be empty")
    min_age_seconds = args.older_than_days * 86400 if args.older_than_days is not None else None
    if min_age_seconds is not None and (not math.isfinite(min_age_seconds) or min_age_seconds < 0):
        parser.error("--older-than-days must be a finite non-negative duration")

    target = Path(args.target).resolve()
    if not target.exists() or not target.is_dir():
        print(f"Error: target directory does not exist or is not a directory: {target}", file=sys.stderr)
        return 2

    if args.min_size_bytes is not None and args.min_size_bytes < 0:
        parser.error("--min-size-bytes must be non-negative")
    if args.max_size_bytes is not None and args.max_size_bytes < 0:
        parser.error("--max-size-bytes must be non-negative")
    if (
        args.min_size_bytes is not None
        and args.max_size_bytes is not None
        and args.min_size_bytes > args.max_size_bytes
    ):
        parser.error("--min-size-bytes cannot exceed --max-size-bytes")

    report_path = Path(args.report_json).expanduser().resolve() if args.report_json else None
    if report_path is not None:
        ancestor = report_path
        while not ancestor.exists() and ancestor != ancestor.parent:
            ancestor = ancestor.parent
        if (report_path.exists() and not report_path.is_file()) or (ancestor != report_path and not ancestor.is_dir()):
            print("Error: JSON report destination must be a file under a directory.", file=sys.stderr)
            return 1
    try:
        groups = scan_and_group(
            target,
            include_hidden=args.include_hidden,
            exclude_extensions=args.exclude_ext,
            recursive=args.recursive,
            min_size_bytes=args.min_size_bytes,
            max_size_bytes=args.max_size_bytes,
            exclude_directories=args.exclude_dir,
            **({"include_patterns": args.include_pattern} if args.include_pattern else {}),
            **({"exclude_patterns": args.exclude_pattern} if args.exclude_pattern else {}),
            **({"min_age_seconds": min_age_seconds} if min_age_seconds is not None else {}),
        )
    except OSError as exc:
        print(f"Error: could not scan target directory: {exc}", file=sys.stderr)
        return 1

    if args.category:
        groups = {category: files for category, files in groups.items() if category in args.category}

    # An existing report inside the target must never be moved as an input file.
    if report_path is not None:
        for category in list(groups):
            groups[category] = [path for path in groups[category] if path.resolve() != report_path]
            if not groups[category]:
                del groups[category]

    if not groups:
        print("No files to organize.")
        if report_path is not None:
            try:
                write_report(report_path, target, args.dry_run, [], **({"include_sizes": True} if args.include_sizes else {}))
            except OSError as exc:
                print(f"Error: could not write JSON report: {exc}", file=sys.stderr)
                return 1
        return 0

    print(f"Organizing files in: {target}")
    actions = []
    had_failures = False
    # Reserve the report path even for real moves so writing the report cannot
    # overwrite a newly organized input with the same destination name.
    reserved_destinations = {report_path} if report_path is not None else set()
    for category, files in sorted(groups.items()):
        print(f"\nCategory: {category} ({len(files)} files)")
        folder = target / category
        for file_path in files:
            try:
                actions.append(safe_move(
                    file_path, folder, dry_run=args.dry_run,
                    reserved_destinations=reserved_destinations,
                    **({"include_sizes": True} if args.include_sizes else {}),
                ))
            except (OSError, ValueError) as exc:
                print(f"Error: could not move {file_path}: {exc}", file=sys.stderr)
                had_failures = True
                actions.append({"source": str(file_path), "destination": None,
                                "status": "failed", "error": str(exc)})
                if report_path is not None:
                    try:
                        write_report(report_path, target, args.dry_run, actions, **({"include_sizes": True} if args.include_sizes else {}))
                    except OSError as report_error:
                        print(f"Error: could not write partial JSON report: {report_error}", file=sys.stderr)
                if not args.continue_on_error:
                    return 1

    if report_path is not None:
        try:
            write_report(report_path, target, args.dry_run, actions, **({"include_sizes": True} if args.include_sizes else {}))
        except OSError as exc:
            print(f"Error: could not write JSON report: {exc}", file=sys.stderr)
            return 1

    print("\nDone.")
    return 1 if had_failures else 0


if __name__ == "__main__":
    raise SystemExit(main())

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
import json
import shutil
import sys
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


def safe_move(src: Path, dest_dir: Path, dry_run=False):
    dest = dest_dir / src.name
    # Treat dangling symlinks as occupied paths too. Path.exists() alone
    # follows symlinks and returns False when the link target is missing.
    if dest.exists() or dest.is_symlink():
        base = src.stem
        ext = src.suffix
        i = 1
        while True:
            candidate = dest_dir / f"{base}({i}){ext}"
            if not candidate.exists() and not candidate.is_symlink():
                dest = candidate
                break
            i += 1
    if dry_run:
        print(f"[dry-run] Move: {src} -> {dest}")
        status = "planned"
    else:
        dest_dir.mkdir(parents=True, exist_ok=True)
        print(f"Move: {src} -> {dest}")
        shutil.move(str(src), str(dest))
        status = "moved"
    return {"source": str(src), "destination": str(dest), "status": status}


def scan_and_group(
    target: Path,
    include_hidden: bool = False,
    exclude_extensions=None,
    recursive: bool = False,
    min_size_bytes=None,
    max_size_bytes=None,
):
    """Group files by category, optionally discovering files below the target."""
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

    groups = defaultdict(list)
    paths = target.rglob("*") if recursive else target.iterdir()
    generated_categories = set(CATEGORIES) | {"Others"}

    for path in paths:
        relative = path.relative_to(target)
        if path.is_symlink():
            # Avoid moving a link whose target may be outside the selected directory.
            continue
        if recursive and relative.parts[0] in generated_categories:
            # Do not reprocess files already placed in organizer output folders.
            continue
        if not include_hidden and any(part.startswith(".") for part in relative.parts):
            # Hidden files and hidden directory trees are opt-in.
            continue
        if path.is_dir():
            continue
        if path.suffix.lower() in excluded:
            continue
        size_bytes = path.stat().st_size
        if min_size_bytes is not None and size_bytes < min_size_bytes:
            continue
        if max_size_bytes is not None and size_bytes > max_size_bytes:
            continue
        category = categorize(path)
        groups[category].append(path)
    return groups


def write_report(report_path: Path, target: Path, dry_run: bool, actions: list):
    """Persist machine-readable actions without including the report file itself."""
    counts = {
        "planned": sum(action["status"] == "planned" for action in actions),
        "moved": sum(action["status"] == "moved" for action in actions),
    }
    report = {
        "target": str(target),
        "dry_run": dry_run,
        "summary": {"total": len(actions), **counts},
        "actions": actions,
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")


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
    args = parser.parse_args(argv)

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
    groups = scan_and_group(
        target,
        include_hidden=args.include_hidden,
        exclude_extensions=args.exclude_ext,
        recursive=args.recursive,
        min_size_bytes=args.min_size_bytes,
        max_size_bytes=args.max_size_bytes,
    )

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
                write_report(report_path, target, args.dry_run, [])
            except OSError as exc:
                print(f"Error: could not write JSON report: {exc}", file=sys.stderr)
                return 1
        return 0

    print(f"Organizing files in: {target}")
    actions = []
    for category, files in sorted(groups.items()):
        print(f"\nCategory: {category} ({len(files)} files)")
        folder = target / category
        for file_path in files:
            actions.append(safe_move(file_path, folder, dry_run=args.dry_run))

    if report_path is not None:
        try:
            write_report(report_path, target, args.dry_run, actions)
        except OSError as exc:
            print(f"Error: could not write JSON report: {exc}", file=sys.stderr)
            return 1

    print("\nDone.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

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
    if dest.exists():
        base = src.stem
        ext = src.suffix
        i = 1
        while True:
            candidate = dest_dir / f"{base}({i}){ext}"
            if not candidate.exists():
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
):
    """Group top-level files, optionally skipping selected filename extensions."""
    excluded = {
        ("." + extension.strip().lstrip(".")).lower()
        for extension in (exclude_extensions or [])
        if isinstance(extension, str) and extension.strip()
    }
    groups = defaultdict(list)
    for p in target.iterdir():
        if p.is_symlink():
            # Avoid moving a link whose target may be outside the selected directory.
            continue
        if p.name.startswith(".") and not include_hidden:
            # Hidden files are opt-in so VCS metadata stays protected by default.
            continue
        if p.is_dir():
            continue
        if p.suffix.lower() in excluded:
            continue
        cat = categorize(p)
        groups[cat].append(p)
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
        "--exclude-ext",
        action="append",
        default=[],
        metavar="EXT",
        help="Skip files with this extension (repeatable, e.g. --exclude-ext .tmp)",
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

    report_path = Path(args.report_json).expanduser().resolve() if args.report_json else None
    groups = scan_and_group(
        target,
        include_hidden=args.include_hidden,
        exclude_extensions=args.exclude_ext,
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
            if not args.include_hidden and file_path.name.startswith("."):
                continue
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

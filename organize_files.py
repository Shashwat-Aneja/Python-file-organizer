#!/usr/bin/env python3
"""
organize_files.py

A lightweight, safe file organizer for a target directory.

Usage:
    python organize_files.py /path/to/target --dry-run
    python organize_files.py .    # organizes current directory

Features:
- Moves files into folders by category (Images, Documents, Audio, Video, Archives, Scripts, Others)
- Dry-run mode to preview actions without making changes
- Collision safe: appends numeric suffix if filename exists
- Logs actions to console
"""

import argparse
import shutil
import sys
from pathlib import Path
from collections import defaultdict

CATEGORIES = {
    "Images": {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg", ".webp", ".tiff"},
    "Documents": {".pdf", ".doc", ".docx", ".txt", ".odt", ".xls", ".xlsx", ".ppt", ".pptx"},
    "Audio": {".mp3", ".wav", ".aac", ".flac", ".ogg", ".m4a"},
    "Video": {".mp4", ".mkv", ".mov", ".avi", ".webm", ".flv"},
    "Archives": {".zip", ".tar", ".gz", ".rar", ".7z"},
    "Scripts": {".py", ".sh", ".js", ".php", ".rb", ".pl"},
    "PDFs": {".pdf"}  # optional extra category if you want PDFs separate
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
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / src.name
    if dest.exists():
        # find next available name
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
    else:
        print(f"Move: {src} -> {dest}")
        shutil.move(str(src), str(dest))

def scan_and_group(target: Path):
    groups = defaultdict(list)
    for p in target.iterdir():
        if p.name.startswith("."):
            # skip hidden files and VCS folders
            continue
        if p.is_dir():
            continue
        cat = categorize(p)
        groups[cat].append(p)
    return groups

def main():
    parser = argparse.ArgumentParser(description="Organize files in a directory by type")
    parser.add_argument("target", nargs="?", default=".", help="Target directory (default: current directory)")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done without moving files")
    parser.add_argument("--include-hidden", action="store_true", help="Include hidden files (starting with .)")
    args = parser.parse_args()

    target = Path(args.target).resolve()
    if not target.exists() or not target.is_dir():
        print(f"Error: target directory does not exist or is not a directory: {target}", file=sys.stderr)
        sys.exit(2)

    groups = scan_and_group(target)
    if not groups:
        print("No files to organize.")
        return

    print(f"Organizing files in: {target}")
    for cat, files in sorted(groups.items()):
        print(f"\nCategory: {cat} ({len(files)} files)")
        folder = target / cat
        for f in files:
            if not args.include_hidden and f.name.startswith("."):
                continue
            safe_move(f, folder, dry_run=args.dry_run)

    print("\nDone.")

if __name__ == "__main__":
    main()

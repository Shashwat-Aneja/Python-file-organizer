# Python File Organizer

A lightweight Python tool that organizes files into Images, Documents, PDFs, Data, Audio, Video, Archives, Scripts, and Others folders. Image support includes HEIC and HEIF photos.  
Supports a **dry-run mode**, collision-safe moving, and clean console logs.

---

## 🚀 Features
- Categorizes files by extension  
- Moves files into named folders  
- Safe renaming if file already exists  
- Excludes hidden/system files by default  
- Dry-run mode (preview without changes)

---

## 📂 Usage

### Preview changes first

```bash
python organize_files.py . --dry-run
```

### Organize the current directory

```bash
python organize_files.py .
```

### Organize another directory

```bash
python organize_files.py /path/to/target --dry-run
```

### Check the installed script version

Print the organizer version without scanning or moving files:

```bash
python organize_files.py --version
```

### Validate a target path

The organizer exits with status code `2` if the target path is missing or is not a directory. Use `--dry-run` first when checking a directory you have not organized before.

### Symbolic-link safety

The scanner skips symbolic links instead of moving them. This prevents a linked file from being moved unexpectedly when its target lives outside the selected directory.


## Run tests

The test suite uses pytest:

```bash
python -m pip install pytest
python -m pytest -q
```

## Project files

- `organize_files.py`: command-line organizer and file-category mapping.
- `tests/test_organize_files.py`: tests for hidden files, dry-run behavior, collisions, categorization, invalid paths, and symbolic links.


## Notebook support

Jupyter Notebook files (`.ipynb`) are placed in a dedicated `Notebooks` folder. The extension is matched case-insensitively, so `.IPYNB` files are handled the same way.

Moves now copy into an exclusively created destination, flush it, and remove the source only after success. This prevents concurrent destination overwrites and works across filesystems, at the cost of copying file contents. Partial copy failures preserve the source and clean up the incomplete destination.

When a later move fails, `--report-json` records all completed moves before the command exits with status 1.

Use `--recursive --exclude-dir build --exclude-dir node_modules` to leave generated or dependency directories untouched.

Recursive scans prune excluded, hidden and generated category directories before entering them. This avoids traversing large dependency trees and makes exclusions effective for unreadable subdirectories too.

A partial JSON report includes a `failed` summary count and a failed action with source and error text, so automation can distinguish incomplete runs from successful moves.

Use `--continue-on-error` to process remaining files after a failed move. The exit status stays nonzero, and JSON reports include each failure. The default still stops at the first failure.

Use repeatable `--category Documents --category Images` options to organize only selected categories. Other source files remain in place and are not included in the action report. Without this option every discovered category is processed.

`--older-than-days N` organizes only files with modification times at least N days old, helping leave recent downloads and active files in place. It combines with size, category and extension filters; the default has no age restriction. The programmatic scanner accepts `min_age_seconds`.

Opt in to `--include-sizes --report-json audit.json` for per-file `size_bytes` and planned/moved byte totals. Dry runs observe current source sizes; successful moves report the source descriptor size validated during copying. Failed actions have no successful byte count. Default report fields are unchanged.

Use repeatable `--include-pattern "reports/*.csv"` to select relative POSIX paths with case-sensitive Python fnmatch matching. Patterns combine with existing exclusions; `*` can span `/`, so this is a path-string filter rather than shell glob traversal. No pattern includes all otherwise eligible files.

Repeat `--exclude-pattern "reports/private*"` to skip relative POSIX paths using case-sensitive fnmatch. Exclusions take precedence over include patterns and combine with directory, extension, age and size exclusions. As with include patterns, `*` can span `/`.

`--max-total-bytes N` preflights the complete selected batch after filters and report exclusion. An over-budget batch fails before moves or report replacement; it does not partially select files. This bounds observed logical file bytes, not physical filesystem allocation, and is not a reservation against concurrent source growth.

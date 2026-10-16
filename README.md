# Python File Organizer

A lightweight Python tool that organizes files into Images, Documents, PDFs, Data, Audio, Video, Archives, Scripts, and Others folders.  
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

# Python File Organizer

A lightweight Python tool that automatically organizes files in a directory into categorized folders (Images, Documents, Videos, Audio, Archives, Scripts, Others).  
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

### Organize the current directory:

### Check the installed script version

Print the organizer version without scanning or moving files:

```bash
python organize_files.py --version
```

### Validate a target path

The organizer exits with status code `2` if the target path is missing or is not a directory. Use `--dry-run` first when checking a directory you have not organized before.

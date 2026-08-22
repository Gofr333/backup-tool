# Backup Tool

A safer Windows backup utility written in Python. It scans a source folder, previews the backup, checks available disk space, requires explicit confirmation, and creates a timestamped copy on another location.

## Download

### Recommended for Windows users

Open the **[Latest Release](https://github.com/Gofr333/backup-tool/releases/latest)** and download:

```text
BackupTool.exe
```

Then double-click the file. Python is not required for the `.exe` version.

## Quick Start

1. Download `BackupTool.exe` from the latest GitHub Release.
2. Double-click `BackupTool.exe`.
3. Enter the source folder you want to back up.
4. Enter the destination where backups should be stored.
5. Choose whether common cache/dependency folders should be skipped.
6. Review the backup preview.
7. Type the exact confirmation shown by the program, for example:

```text
BACKUP 842
```

8. Wait for the backup to finish.

## Features

- Recursive folder backup
- Preserves folder structure and file metadata where supported
- Timestamped backup folders
- Preview before copying
- File count and total-size scan
- Disk free-space check
- 5 GB safety margin
- Re-checks free space while copying
- Exact `BACKUP <file count>` confirmation
- Optional skipping of common cache/dependency folders
- Skips symbolic links and Windows junctions
- Prevents placing the backup inside the source folder
- Unique backup folder names
- Per-file error handling
- Incomplete backups are marked with `_INCOMPLETE`
- Writes `backup_errors.log` when copy errors occur
- Handles Ctrl+C without hiding a partial backup
- Standalone Windows `.exe` releases built automatically with GitHub Actions
- SHA-256 checksum included with releases

## Example

```text
============================================================
BACKUP TOOL v1.0.0
============================================================

Source folder: C:\Projects\MyGame
Backup location: E:\Backups

============================================================
BACKUP PREVIEW
============================================================
Source:          C:\Projects\MyGame
Destination:     E:\Backups\MyGame_2026-08-22_23-00-00
Files found:     842
Backup size:     4.63 GB
Free space:      120.41 GB
Safety margin:   5.00 GB

Estimated free space after backup: 115.78 GB

Type "BACKUP 842" to continue:
```

## Important: What This Tool Is For

This program **creates backups**. It is not a damaged-disk recovery utility.

For protection against physical disk failure, store the backup on a **different physical drive**, such as an external HDD or SSD. Creating a backup on another partition of the same physical disk does not protect against failure of the entire drive.

## Optional Exclusions

The program can skip common cache/dependency folders such as:

```text
__pycache__
.pytest_cache
.mypy_cache
.ruff_cache
.venv
venv
node_modules
```

Press `y` when asked if you want these exclusions. Press Enter or `n` for a complete backup.

## Incomplete Backups

If a copy error occurs or the safety margin is reached during copying, the backup folder is renamed to something similar to:

```text
MyGame_2026-08-22_23-00-00_INCOMPLETE
```

When possible, an error log is written inside it:

```text
backup_errors.log
```

## Run From Source

Requirements:

- Python 3
- Windows, Linux, or macOS for the source script (the packaged `.exe` is Windows-only)
- No third-party packages are required to run `backup_tool.py`

Run:

```powershell
python backup_tool.py
```

On Windows, if `python` is not recognized:

```powershell
py backup_tool.py
```

## Verify a Release

Releases also include:

```text
BackupTool.sha256
```

On Windows PowerShell you can calculate the executable hash with:

```powershell
Get-FileHash .\BackupTool.exe -Algorithm SHA256
```

Compare it with the value in `BackupTool.sha256`.

## Project Structure

```text
backup-tool/
├── .github/
│   └── workflows/
│       └── build-release.yml
├── backup_tool.py
├── README.md
└── .gitignore
```

## Creating a Release

After committing and pushing your changes, create and push a version tag:

```powershell
git tag v1.0.0
git push origin v1.0.0
```

GitHub Actions will build:

```text
BackupTool.exe
BackupTool.sha256
```

and attach them to a GitHub Release automatically.

## Disclaimer

Always verify important backups before relying on them. Keeping multiple copies of important data on separate devices or locations is recommended.

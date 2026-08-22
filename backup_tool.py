from pathlib import Path
import os
import shutil
import sys
from datetime import datetime


VERSION = "1.0.0"
SAFETY_MARGIN_BYTES = 5 * 1024**3

COMMON_EXCLUDED_FOLDERS = {
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".venv",
    "venv",
    "node_modules",
}


def format_size(size):
    units = ("bytes", "KB", "MB", "GB", "TB")
    value = float(size)

    for unit in units:
        if value < 1024 or unit == units[-1]:
            if unit == "bytes":
                return f"{int(value)} bytes"

            return f"{value:.2f} {unit}"

        value /= 1024


def read_path(prompt):
    while True:
        raw_path = input(prompt).strip().strip('"')

        if raw_path:
            return Path(raw_path).expanduser()

        print("ERROR: Path cannot be empty.")


def is_link_like(path):
    if path.is_symlink():
        return True

    is_junction = getattr(path, "is_junction", None)

    if is_junction is not None:
        return is_junction()

    return False


def choose_excluded_folders():
    print()
    print("Optional exclusions:")
    print(", ".join(sorted(COMMON_EXCLUDED_FOLDERS)))
    print()

    answer = input(
        "Skip common cache/dependency folders? [y/N]: "
    ).strip().lower()

    if answer == "y":
        return COMMON_EXCLUDED_FOLDERS.copy()

    return set()


def scan_folder(folder, excluded_folders):
    file_count = 0
    total_size = 0
    skipped_folders = 0
    skipped_links = 0
    errors = []

    def handle_walk_error(error):
        errors.append(str(error))

    for root, dir_names, file_names in os.walk(
        folder,
        topdown=True,
        followlinks=False,
        onerror=handle_walk_error,
    ):
        current_folder = Path(root)
        allowed_dirs = []

        for dir_name in dir_names:
            dir_path = current_folder / dir_name

            try:
                if dir_name in excluded_folders:
                    skipped_folders += 1
                    continue

                if is_link_like(dir_path):
                    skipped_links += 1
                    continue

                allowed_dirs.append(dir_name)

            except OSError as error:
                errors.append(f"{dir_path}: {error}")

        dir_names[:] = allowed_dirs

        for file_name in file_names:
            file_path = current_folder / file_name

            try:
                if is_link_like(file_path):
                    skipped_links += 1
                    continue

                if not file_path.is_file():
                    continue

                file_count += 1
                total_size += file_path.stat().st_size

            except OSError as error:
                errors.append(f"{file_path}: {error}")

    return (
        file_count,
        total_size,
        skipped_folders,
        skipped_links,
        errors,
    )


def build_backup_folder(source_folder, backup_location):
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    source_name = source_folder.name or "Root"
    base_name = f"{source_name}_{timestamp}"
    backup_folder = backup_location / base_name
    counter = 1

    while backup_folder.exists():
        backup_folder = backup_location / f"{base_name}_{counter}"
        counter += 1

    return backup_folder


def create_backup(
    source_folder,
    backup_folder,
    backup_location,
    excluded_folders,
):
    copied_files = 0
    copied_bytes = 0
    errors = []
    stopped_for_space = False

    backup_folder.mkdir(parents=True, exist_ok=False)

    def handle_walk_error(error):
        errors.append(str(error))

    for root, dir_names, file_names in os.walk(
        source_folder,
        topdown=True,
        followlinks=False,
        onerror=handle_walk_error,
    ):
        current_folder = Path(root)
        allowed_dirs = []

        for dir_name in dir_names:
            dir_path = current_folder / dir_name

            try:
                if dir_name in excluded_folders:
                    continue

                if is_link_like(dir_path):
                    continue

                allowed_dirs.append(dir_name)

            except OSError as error:
                errors.append(f"{dir_path}: {error}")

        dir_names[:] = allowed_dirs

        relative_folder = current_folder.relative_to(source_folder)
        destination_folder = backup_folder / relative_folder

        try:
            destination_folder.mkdir(parents=True, exist_ok=True)

        except OSError as error:
            errors.append(
                f"Could not create folder {destination_folder}: {error}"
            )
            dir_names[:] = []
            continue

        for file_name in file_names:
            source_file = current_folder / file_name
            destination_file = destination_folder / file_name

            try:
                if is_link_like(source_file):
                    continue

                if not source_file.is_file():
                    continue

                file_size = source_file.stat().st_size
                _, _, free_space = shutil.disk_usage(backup_location)

                if free_space - file_size < SAFETY_MARGIN_BYTES:
                    errors.append(
                        "Backup stopped because the disk reached the safety margin."
                    )
                    stopped_for_space = True

                    return (
                        copied_files,
                        copied_bytes,
                        errors,
                        stopped_for_space,
                    )

                shutil.copy2(source_file, destination_file)

                copied_files += 1
                copied_bytes += file_size

                relative_file = source_file.relative_to(source_folder)
                print(f"[COPIED] {relative_file}")

            except OSError as error:
                relative_file = source_file.relative_to(source_folder)
                errors.append(f"{relative_file}: {error}")
                print(f"[ERROR] {relative_file}: {error}")

    return copied_files, copied_bytes, errors, stopped_for_space


def mark_incomplete(backup_folder):
    incomplete_folder = backup_folder.with_name(
        f"{backup_folder.name}_INCOMPLETE"
    )
    counter = 1

    while incomplete_folder.exists():
        incomplete_folder = backup_folder.with_name(
            f"{backup_folder.name}_INCOMPLETE_{counter}"
        )
        counter += 1

    try:
        backup_folder.rename(incomplete_folder)
        return incomplete_folder

    except OSError:
        return backup_folder


def write_error_log(backup_folder, errors):
    if not errors:
        return None

    log_path = backup_folder / "backup_errors.log"

    try:
        with log_path.open("w", encoding="utf-8") as log_file:
            log_file.write("BACKUP ERRORS\n")
            log_file.write("=" * 60)
            log_file.write("\n\n")

            for error in errors:
                log_file.write(f"- {error}\n")

        return log_path

    except OSError:
        return None


def pause_before_exit():
    if getattr(sys, "frozen", False):
        print()

        try:
            input("Press Enter to close...")

        except (EOFError, KeyboardInterrupt):
            pass


def main():
    print()
    print("=" * 60)
    print(f"BACKUP TOOL v{VERSION}")
    print("=" * 60)
    print()

    source_folder = read_path("Source folder: ")
    backup_location = read_path("Backup location: ")

    if not source_folder.is_dir():
        print()
        print("ERROR: Source folder does not exist.")
        return

    if backup_location.exists() and not backup_location.is_dir():
        print()
        print("ERROR: Backup location exists but is not a folder.")
        return

    source_folder = source_folder.resolve()
    backup_location = backup_location.resolve()

    if backup_location.is_relative_to(source_folder):
        print()
        print("ERROR: Backup location cannot be inside the source folder.")
        return

    excluded_folders = choose_excluded_folders()

    try:
        backup_location.mkdir(parents=True, exist_ok=True)

        (
            file_count,
            total_size,
            skipped_folders,
            skipped_links,
            scan_errors,
        ) = scan_folder(source_folder, excluded_folders)

        if scan_errors:
            print()
            print("=" * 60)
            print("SCAN FAILED")
            print("=" * 60)
            print()
            print("The source folder could not be scanned reliably.")
            print()

            for error in scan_errors[:10]:
                print(f"[ERROR] {error}")

            if len(scan_errors) > 10:
                remaining_errors = len(scan_errors) - 10
                print(f"... and {remaining_errors} more error(s).")

            print()
            print(
                "No backup was started because the preview may be incomplete."
            )
            return

        backup_folder = build_backup_folder(source_folder, backup_location)
        disk_total, _, free_space = shutil.disk_usage(backup_location)
        required_space = total_size + SAFETY_MARGIN_BYTES

        print()
        print("=" * 60)
        print("BACKUP PREVIEW")
        print("=" * 60)
        print(f"Source:          {source_folder}")
        print(f"Destination:     {backup_folder}")
        print(f"Files found:     {file_count}")
        print(f"Backup size:     {format_size(total_size)}")
        print(f"Disk size:       {format_size(disk_total)}")
        print(f"Free space:      {format_size(free_space)}")
        print(f"Safety margin:   {format_size(SAFETY_MARGIN_BYTES)}")
        print(f"Folders skipped: {skipped_folders}")
        print(f"Links skipped:   {skipped_links}")

        if excluded_folders:
            print("Excluded:         " + ", ".join(sorted(excluded_folders)))

        print()

        if required_space > free_space:
            missing_space = required_space - free_space
            print("ERROR: Not enough free space for this backup.")
            print(
                f"Additional space required: {format_size(missing_space)}"
            )
            return

        remaining_space = free_space - total_size
        print(
            "Estimated free space after backup: "
            f"{format_size(remaining_space)}"
        )
        print()

        expected_confirmation = f"BACKUP {file_count}"
        confirmation = input(
            f'Type "{expected_confirmation}" to continue: '
        ).strip().upper()

        if confirmation != expected_confirmation:
            print()
            print("Backup cancelled.")
            print("No backup folder was created.")
            return

        print()
        print("=" * 60)
        print("CREATING BACKUP")
        print("=" * 60)
        print()

        try:
            (
                copied_files,
                copied_bytes,
                copy_errors,
                stopped_for_space,
            ) = create_backup(
                source_folder,
                backup_folder,
                backup_location,
                excluded_folders,
            )

        except KeyboardInterrupt:
            print()
            print()
            print("Backup interrupted by the user.")

            if backup_folder.exists():
                backup_folder = mark_incomplete(backup_folder)
                print("Partial backup kept at:")
                print(backup_folder)

            return

        if copied_files != file_count:
            copy_errors.append(
                "The number of copied files does not match the preview. "
                "The source folder may have changed during the backup."
            )

        if copy_errors or stopped_for_space:
            backup_folder = mark_incomplete(backup_folder)
            error_log = write_error_log(backup_folder, copy_errors)

            print()
            print("=" * 60)
            print("BACKUP INCOMPLETE")
            print("=" * 60)
            print(f"Files planned: {file_count}")
            print(f"Files copied:  {copied_files}")
            print(f"Data copied:   {format_size(copied_bytes)}")
            print(f"Errors:        {len(copy_errors)}")
            print(f"Location:      {backup_folder}")

            if error_log is not None:
                print(f"Error log:     {error_log}")

            return

        print()
        print("=" * 60)
        print("BACKUP COMPLETED")
        print("=" * 60)
        print(f"Files copied: {copied_files}")
        print(f"Backup size:  {format_size(copied_bytes)}")
        print(f"Location:     {backup_folder}")

    except OSError as error:
        print()
        print(f"ERROR: Backup failed: {error}")


if __name__ == "__main__":
    try:
        main()

    except KeyboardInterrupt:
        print()
        print("Operation cancelled by user.")

    finally:
        pause_before_exit()

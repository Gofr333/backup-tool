from pathlib import Path
import shutil
from datetime import datetime


SAFETY_MARGIN = 5 * 1024 * 1024 * 1024


def format_size(size):
    if size < 1024:
        return f"{size} bytes"

    elif size < 1024 * 1024:
        return f"{size / 1024:.2f} KB"

    elif size < 1024 * 1024 * 1024:
        return f"{size / (1024 * 1024):.2f} MB"

    else:
        return f"{size / (1024 * 1024 * 1024):.2f} GB"


def scan_folder(folder):
    file_count = 0
    total_size = 0

    for item in folder.rglob("*"):
        if item.is_file():
            file_count += 1
            total_size += item.stat().st_size

    return file_count, total_size


def create_backup(source, destination):
    shutil.copytree(source, destination)


def main():
    source_folder = Path(
        input("Source folder: ").strip()
    )

    backup_location = Path(
        input("Backup location: ").strip()
    )

    if not source_folder.is_dir():
        print("ERROR: Source folder does not exist")
        return

    source_resolved = source_folder.resolve()
    backup_resolved = backup_location.resolve()

    if backup_resolved.is_relative_to(source_resolved):
        print(
            "ERROR: Backup location cannot be "
            "inside the source folder"
        )
        return

    print("Source folder found")

    try:
        backup_location.mkdir(
            parents=True,
            exist_ok=True
        )

        timestamp = datetime.now().strftime(
            "%Y-%m-%d_%H-%M-%S"
        )

        backup_folder = (
            backup_location
            / f"{source_folder.name}_{timestamp}"
        )

        file_count, total_size = scan_folder(
            source_folder
        )

        _, _, free_space = shutil.disk_usage(
            backup_location
        )

        required_space = total_size + SAFETY_MARGIN

        print()
        print("=" * 50)
        print("BACKUP PREVIEW")
        print("=" * 50)
        print(f"Source:        {source_folder}")
        print(f"Destination:   {backup_folder}")
        print(f"Files found:   {file_count}")
        print(f"Backup size:   {format_size(total_size)}")
        print(f"Free space:    {format_size(free_space)}")
        print(f"Safety margin: {format_size(SAFETY_MARGIN)}")
        print()

        if required_space > free_space:
            missing_space = required_space - free_space

            print(
                "ERROR: Not enough free space "
                "for this backup"
            )

            print(
                f"Additional space required: "
                f"{format_size(missing_space)}"
            )

            return

        remaining_space = free_space - total_size

        print(
            f"Estimated free space after backup: "
            f"{format_size(remaining_space)}"
        )

        print()

        confirmation = input(
            'Type "BACKUP" to continue: '
        ).strip().upper()

        if confirmation == "BACKUP":
            print()
            print("Creating backup...")

            create_backup(
                source_folder,
                backup_folder
            )

            print()
            print("=" * 50)
            print("BACKUP COMPLETED")
            print("=" * 50)
            print(f"Files copied: {file_count}")
            print(f"Backup size:  {format_size(total_size)}")
            print(f"Location:     {backup_folder}")

        else:
            print()
            print("Backup cancelled")

    except OSError as error:
        print()
        print(f"ERROR: Backup failed: {error}")


if __name__ == "__main__":
    main()
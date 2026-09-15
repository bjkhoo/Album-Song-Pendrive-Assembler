"""
Album Song Pendrive Assembler
《稻、树林和风》原创专辑 — Pen Drive Copier

Cross-platform script (Windows + macOS) that copies album songs
onto USB pen drives in bulk. Designed for multiple team members
to use on their own laptops.

Usage:
    python album_copier.py

Requirements:
    - Place MP3 files in the 'album_source' folder next to this script
    - See album_source/PREPARATION.txt for file naming guide
"""

import os
import shutil
import subprocess
import sys
import platform

# Ensure UTF-8 output encoding for emojis and Chinese characters on Windows
if sys.platform == "win32":
    try:
        if sys.stdout and hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        if sys.stderr and hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# ============================================================
#  CONFIGURATION — Edit these if your album changes
# ============================================================

ALBUM_NAME = "《稻、树林和风》原创专辑"
DRIVE_LABEL = "PDW Album"
SOURCE_FOLDER = "album_source"

SONG_LIST = [
    "01 稻、树林和风.mp3",
    "02 Thankfulness.mp3",
    "03 满月.mp3",
    "04 我苦我乐我转转念.mp3",
    "05 含羞草的闪亮.mp3",
    "06 初心.mp3",
    "07 幸福答卷.mp3",
    "08 蝴蝶的呢喃.mp3",
    "09 拥抱无常.mp3",
    "10 六时·尔时.mp3",
]

# ============================================================
#  HELPER FUNCTIONS
# ============================================================

def get_script_dir():
    """Get the directory where this script (or compiled exe) is located."""
    if getattr(sys, 'frozen', False):
        # Running as a compiled executable (e.g. PyInstaller)
        return os.path.dirname(sys.executable)
    else:
        # Running as a normal Python script
        return os.path.dirname(os.path.abspath(__file__))


def get_computer_name():
    """Get the computer/hostname for identification."""
    return platform.node()


def get_os_name():
    """Get a human-readable OS name."""
    system = platform.system()
    if system == "Darwin":
        # "Darwin" is the kernel name for macOS
        return "macOS"
    return system


def format_size(size_bytes):
    """Format bytes into a human-readable string (e.g. '4.2 MB')."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"


# ============================================================
#  PEN DRIVE DETECTION
# ============================================================

def locate_pen_drives():
    """
    Locate all connected writable removable USB pen drives.
    Works on both Windows and macOS (Darwin).
    Returns a list of drive paths.
    """
    pen_drives = []
    system = platform.system()

    try:
        if system == "Windows":
            import string
            from ctypes import windll

            for drive_letter in string.ascii_uppercase:
                drive = f"{drive_letter}:\\"
                try:
                    if os.path.exists(drive):
                        # GetDriveTypeW returns 2 for DRIVE_REMOVABLE (USB drives)
                        drive_type = windll.kernel32.GetDriveTypeW(drive)
                        if drive_type == 2 and os.access(drive, os.W_OK):
                            pen_drives.append(drive)
                except (OSError, PermissionError):
                    # Skip drives that can't be accessed
                    continue

        elif system == "Darwin":
            # Darwin = macOS
            # Exclude system volumes that are not pen drives
            excluded = [
                "Macintosh HD",
                "Macintosh HD - Data",
                "Recovery",
                "com.apple.TimeMachine.localsnapshots",
            ]
            volumes_dir = "/Volumes"
            if os.path.exists(volumes_dir):
                volumes = [
                    os.path.join(volumes_dir, d)
                    for d in os.listdir(volumes_dir)
                    if not d.startswith(".")
                ]
                for volume in volumes:
                    try:
                        if os.path.ismount(volume) and os.access(volume, os.W_OK):
                            drive_name = os.path.basename(volume)
                            if drive_name not in excluded:
                                pen_drives.append(volume)
                    except (OSError, PermissionError):
                        continue
        else:
            print(f"  ⚠️ Unsupported OS: {system}")

    except Exception as e:
        print(f"  ❌ Error scanning for drives: {e}")

    return pen_drives


def get_drive_info(drive):
    """
    Get drive label and free space.
    Returns (label, free_space_bytes).
    """
    label = "Unknown"
    free_space = 0

    try:
        if platform.system() == "Windows":
            import ctypes
            # Get volume label
            vol_name_buf = ctypes.create_unicode_buffer(1024)
            ctypes.windll.kernel32.GetVolumeInformationW(
                drive, vol_name_buf, 1024, None, None, None, None, 0
            )
            label = vol_name_buf.value or "No Label"

            # Get free space
            free_bytes = ctypes.c_ulonglong(0)
            ctypes.windll.kernel32.GetDiskFreeSpaceExW(
                drive, None, None, ctypes.pointer(free_bytes)
            )
            free_space = free_bytes.value

        elif platform.system() == "Darwin":
            # macOS: drive name is the folder name in /Volumes
            label = os.path.basename(drive)
            # Get free space using os.statvfs
            stat = os.statvfs(drive)
            free_space = stat.f_bavail * stat.f_frsize

    except Exception:
        pass

    return label, free_space


# ============================================================
#  PEN DRIVE OPERATIONS
# ============================================================

def rename_drive(drive, new_label):
    """
    Rename the pen drive to the album label.
    Windows: uses PowerShell Set-Volume
    macOS:   uses diskutil rename
    """
    system = platform.system()

    try:
        if system == "Windows":
            # Extract drive letter (e.g. "E" from "E:\\")
            drive_letter = drive[0]
            result = subprocess.run(
                [
                    "powershell", "-Command",
                    f'Set-Volume -DriveLetter {drive_letter} -NewFileSystemLabel "{new_label}"'
                ],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                print(f"  📝 Renamed drive to '{new_label}'... ✅")
            else:
                # Fallback: try using cmd label command
                fb_result = subprocess.run(
                    ["cmd", "/c", f"label {drive_letter}: {new_label}"],
                    capture_output=True, text=True, timeout=10
                )
                if fb_result.returncode == 0:
                    print(f"  📝 Renamed drive to '{new_label}'... ✅")
                else:
                    err_msg = result.stderr.strip() or fb_result.stderr.strip() or "Permission or filesystem limitation"
                    print(f"  ⚠️ Could not rename drive: {err_msg}")
                    print(f"     (Continuing with copy anyway)")

        elif system == "Darwin":
            result = subprocess.run(
                ["diskutil", "rename", drive, new_label],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                print(f"  📝 Renamed drive to '{new_label}'... ✅")
            else:
                err_msg = result.stderr.strip() or "Drive may be locked or busy"
                print(f"  ⚠️ Could not rename drive: {err_msg}")
                print(f"     (Continuing with copy anyway)")

    except Exception as e:
        print(f"  ⚠️ Could not rename drive: {e}")
        print(f"     (Continuing with copy anyway)")


def safe_eject(drive):
    """
    Safely eject the pen drive.
    Windows: uses Shell.Application COM object via PowerShell
    macOS:   uses diskutil eject
    """
    system = platform.system()

    try:
        if system == "Windows":
            drive_letter = drive[0]
            # Use Shell.Application COM to safely eject (same as "Safely Remove Hardware")
            ps_command = (
                f'$shell = New-Object -ComObject Shell.Application; '
                f'$shell.Namespace(17).ParseName("{drive_letter}:").InvokeVerb("Eject")'
            )
            result = subprocess.run(
                ["powershell", "-Command", ps_command],
                capture_output=True, text=True, timeout=15
            )
            if result.returncode == 0:
                print(f"  ⏏️ Safely ejecting {drive}... ✅")
            else:
                print(f"  ⚠️ Could not auto-eject. Please eject '{drive}' manually.")

        elif system == "Darwin":
            result = subprocess.run(
                ["diskutil", "eject", drive],
                capture_output=True, text=True, timeout=15
            )
            if result.returncode == 0:
                print(f"  ⏏️ Safely ejecting {drive}... ✅")
            else:
                print(f"  ⚠️ Could not auto-eject: {result.stderr.strip()}")
                print(f"      Please eject '{drive}' manually.")

    except subprocess.TimeoutExpired:
        print(f"  ⚠️ Eject timed out. Please eject '{drive}' manually.")
    except Exception as e:
        print(f"  ⚠️ Could not auto-eject: {e}")
        print(f"      Please eject '{drive}' manually.")


# ============================================================
#  DRIVE CLEANING (WIPE OLD FILES)
# ============================================================

def clean_drive(drive):
    """
    Remove all existing files and directories on the pen drive
    to start 100% fresh and clean (prevents viruses & factory bloatware).
    """
    print(f"  🧹 Wiping all existing files on {drive}...")
    system_folders = {
        "system volume information",
        "$recycle.bin",
        ".trashes",
        ".fseventsd",
        ".spotlight-v100",
    }
    cleaned_count = 0
    try:
        for item in os.listdir(drive):
            if item.lower() in system_folders:
                continue
            item_path = os.path.join(drive, item)
            try:
                if os.path.isdir(item_path):
                    shutil.rmtree(item_path, ignore_errors=True)
                    cleaned_count += 1
                else:
                    os.remove(item_path)
                    cleaned_count += 1
            except Exception:
                pass
        print(f"  ✨ Drive {drive} wiped clean! ({cleaned_count} old items removed)")
    except Exception as e:
        print(f"  ⚠️ Notice during drive wipe: {e}")

# ============================================================
#  FILE COPY
# ============================================================

def copy_songs_to_drive(source_dir, drive, song_list):
    """
    Copy all songs from source_dir to the root of the pen drive.
    Returns (success_count, fail_count, failed_files).
    """
    success_count = 0
    fail_count = 0
    failed_files = []
    total = len(song_list)

    for i, filename in enumerate(song_list, 1):
        source_path = os.path.join(source_dir, filename)
        dest_path = os.path.join(drive, filename)

        try:
            if not os.path.isfile(source_path):
                print(f"  [{i:>2}/{total}] ❌ {filename} — File not found in source folder")
                fail_count += 1
                failed_files.append(filename)
                continue

            source_size = os.path.getsize(source_path)

            # Copy the file (preserves metadata like timestamps)
            shutil.copy2(source_path, dest_path)

            # Verify: check the destination file size matches
            dest_size = os.path.getsize(dest_path)
            if dest_size != source_size:
                print(f"  [{i:>2}/{total}] ⚠️ {filename} — Size mismatch! (expected {format_size(source_size)}, got {format_size(dest_size)})")
                fail_count += 1
                failed_files.append(filename)
            else:
                print(f"  [{i:>2}/{total}] ✅ {filename} ({format_size(source_size)})")
                success_count += 1

        except PermissionError:
            print(f"  [{i:>2}/{total}] ❌ {filename} — Permission denied (drive may be write-protected)")
            fail_count += 1
            failed_files.append(filename)
        except OSError as e:
            if "No space left" in str(e) or "not enough space" in str(e).lower():
                print(f"  [{i:>2}/{total}] ❌ {filename} — No space left on drive!")
                fail_count += 1
                failed_files.append(filename)
                print(f"\n  🛑 Drive full — stopping copy for this drive.")
                break
            elif "device" in str(e).lower() or "removed" in str(e).lower():
                print(f"  [{i:>2}/{total}] ❌ {filename} — Drive disconnected!")
                fail_count += 1
                failed_files.append(filename)
                print(f"\n  🛑 Drive disconnected — stopping copy for this drive.")
                break
            else:
                print(f"  [{i:>2}/{total}] ❌ {filename} — Error: {e}")
                fail_count += 1
                failed_files.append(filename)
        except Exception as e:
            print(f"  [{i:>2}/{total}] ❌ {filename} — Unexpected error: {e}")
            fail_count += 1
            failed_files.append(filename)

    return success_count, fail_count, failed_files


# ============================================================
#  MAIN PROGRAM
# ============================================================

def print_header():
    """Print the startup banner."""
    computer = get_computer_name()
    os_name = get_os_name()
    print()
    print("=" * 50)
    print(f"  {ALBUM_NAME}")
    print(f"  Album Song Pendrive Assembler")
    print(f"  Computer: {computer} | OS: {os_name}")
    print("=" * 50)
    print()


def main():
    print_header()

    # --- Determine source directory ---
    script_dir = get_script_dir()
    source_dir = os.path.join(script_dir, SOURCE_FOLDER)

    if not os.path.isdir(source_dir):
        print(f"  ❌ Source folder not found: {source_dir}")
        print(f"     Please create a '{SOURCE_FOLDER}' folder next to this script")
        print(f"     and place the MP3 files inside it.")
        print(f"     See PREPARATION.txt for details.")
        sys.exit(1)

    # --- Verify all songs exist in source ---
    missing = [s for s in SONG_LIST if not os.path.isfile(os.path.join(source_dir, s))]

    if missing:
        print(f"  ❌ ERROR: {len(missing)} song(s) missing from '{SOURCE_FOLDER}':")
        for m in missing:
            print(f"     - {m}")
        print()
        print(f"  Please place all {len(SONG_LIST)} MP3 files in the '{SOURCE_FOLDER}' folder before running.")
        print("  See PREPARATION.txt for details.")
        sys.exit(1)

    print(f"  ✅ All {len(SONG_LIST)} songs verified in '{SOURCE_FOLDER}'. Ready!\n")

    # --- Main loop ---
    total_success = 0
    total_failed = 0

    while True:
        print("─" * 50)

        # --- Scan for pen drives ---
        print("  🔍 Scanning for pen drives...")
        pen_drives = locate_pen_drives()

        while not pen_drives:
            print("  💡 No pen drives found.")
            user_input = input("     Plug in a pen drive and press Enter (Q to quit): ").strip().upper()
            if user_input == "Q":
                break
            print("  🔍 Scanning again...")
            pen_drives = locate_pen_drives()

        if not pen_drives:
            break

        # --- Process each detected pen drive ---
        for drive in pen_drives:
            label, free_space = get_drive_info(drive)
            print(f"  📌 Found pen drive: {drive} (Name: '{label}', Free: {format_size(free_space)})")
            print(f"  ⚠️ CAUTION: Pressing Enter will ERASE ALL DATA on {drive} to make it brand new!")
            print()

            user_input = input(f"  Press Enter to WIPE & COPY to {drive} (S to skip, Q to quit): ").strip().upper()
            if user_input == "Q":
                print(f"\n  📊 Final total: {total_success} pen drives completed ({total_failed} failed)")
                return
            if user_input == "S":
                print(f"  ⏭️ Skipped {drive}")
                continue

            print()

            # --- Wipe/Clean drive ---
            clean_drive(drive)

            # --- Rename drive ---
            rename_drive(drive, DRIVE_LABEL)

            # --- Copy songs ---
            print()
            success, failed, failed_files = copy_songs_to_drive(source_dir, drive, SONG_LIST)
            print()

            if failed == 0:
                print(f"  ✅ SUCCESS — {success}/{len(SONG_LIST)} songs copied to {drive}")
                total_success += 1
            else:
                print(f"  ⚠️ PARTIAL — {success}/{len(SONG_LIST)} songs copied, {failed} failed")
                if failed_files:
                    print(f"     Failed: {', '.join(failed_files)}")
                total_failed += 1

            # --- Safe eject ---
            safe_eject(drive)

            print(f"\n  📊 Session total: {total_success} pen drives completed", end="")
            if total_failed > 0:
                print(f" ({total_failed} failed)", end="")
            print()

        # --- Prompt for next round ---
        print()
        user_input = input("  Plug in next pen drive, press Enter (Q to quit): ").strip().upper()
        if user_input == "Q":
            break

    # --- Final summary ---
    print()
    print("=" * 50)
    print(f"  🏁 DONE!")
    print(f"  ✅ {total_success} pen drives completed successfully")
    if total_failed > 0:
        print(f"  ❌ {total_failed} pen drives had errors")
    print("=" * 50)



if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n  👋 Interrupted. Goodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"\n  ❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

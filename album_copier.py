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
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

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

# Matches any audio extension
SONG_LIST = [
    "01 稻、树林和风",
    "02 Thankfulness",
    "03 满月",
    "04 我苦我乐我转转念",
    "05 含羞草的闪亮",
    "06 初心",
    "07 幸福答卷",
    "08 蝴蝶的呢喃",
    "09 拥抱无常",
    "10 六时·尔时",
]

SUPPORTED_AUDIO_EXTS = {".mp3", ".wav", ".flac", ".m4a", ".aac", ".ogg", ".wma"}


def resolve_album_songs(source_dir):
    """
    Find matching audio files in source_dir for each track title.
    Requires exact base name match (ignores file extension: .mp3, .wav, .flac, etc.).
    Returns (resolved_song_filenames, missing_track_titles).
    """
    if not os.path.isdir(source_dir):
        return [], list(SONG_LIST)

    files = [f for f in os.listdir(source_dir) if not f.startswith(".")]
    resolved = []
    missing = []

    for title in SONG_LIST:
        matched_file = None
        # Exact base name match (extension can be anything: .mp3, .wav, .flac, etc.)
        for f in sorted(files):
            base, ext = os.path.splitext(f)
            if base.strip().lower() == title.strip().lower():
                matched_file = f
                break

        if matched_file:
            resolved.append(matched_file)
        else:
            missing.append(title)

    return resolved, missing

# Thread safety lock for console output
_print_lock = threading.Lock()


def log(msg="", prefix=None):
    """Thread-safe logging helper with optional drive prefix."""
    with _print_lock:
        if prefix:
            print(f"  [{prefix}] {msg}")
        else:
            print(f"  {msg}")

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

def rename_drive(drive, new_label, prefix=None):
    """
    Rename the pen drive to the album label.
    Windows: uses PowerShell Set-Volume
    macOS:   uses diskutil rename
    """
    system = platform.system()
    pfx = prefix or drive.rstrip("\\").rstrip("/")

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
                log(f"📝 Renamed drive to '{new_label}'... ✅", prefix=pfx)
            else:
                # Fallback: try using cmd label command
                fb_result = subprocess.run(
                    ["cmd", "/c", f"label {drive_letter}: {new_label}"],
                    capture_output=True, text=True, timeout=10
                )
                if fb_result.returncode == 0:
                    log(f"📝 Renamed drive to '{new_label}'... ✅", prefix=pfx)
                else:
                    err_msg = result.stderr.strip() or fb_result.stderr.strip() or "Permission or filesystem limitation"
                    log(f"⚠️ Could not rename drive: {err_msg}", prefix=pfx)
                    log(f"   (Continuing with copy anyway)", prefix=pfx)

        elif system == "Darwin":
            result = subprocess.run(
                ["diskutil", "rename", drive, new_label],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                log(f"📝 Renamed drive to '{new_label}'... ✅", prefix=pfx)
            else:
                err_msg = result.stderr.strip() or "Drive may be locked or busy"
                log(f"⚠️ Could not rename drive: {err_msg}", prefix=pfx)
                log(f"   (Continuing with copy anyway)", prefix=pfx)

    except Exception as e:
        log(f"⚠️ Could not rename drive: {e}", prefix=pfx)
        log(f"   (Continuing with copy anyway)", prefix=pfx)


def safe_eject(drive, prefix=None):
    """
    Safely eject the pen drive.
    Windows: uses Shell.Application COM object via PowerShell
    macOS:   uses diskutil eject
    Returns True if successfully ejected, False otherwise.
    """
    system = platform.system()
    pfx = prefix or drive.rstrip("\\").rstrip("/")

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
                log(f"⏏️ Safely ejected {drive}... ✅", prefix=pfx)
                return True
            else:
                log(f"⚠️ Could not auto-eject. Please eject '{drive}' manually.", prefix=pfx)
                return False

        elif system == "Darwin":
            result = subprocess.run(
                ["diskutil", "eject", drive],
                capture_output=True, text=True, timeout=15
            )
            if result.returncode == 0:
                log(f"⏏️ Safely ejected {drive}... ✅", prefix=pfx)
                return True
            else:
                log(f"⚠️ Could not auto-eject: {result.stderr.strip()}", prefix=pfx)
                log(f"   Please eject '{drive}' manually.", prefix=pfx)
                return False

    except subprocess.TimeoutExpired:
        log(f"⚠️ Eject timed out. Please eject '{drive}' manually.", prefix=pfx)
        return False
    except Exception as e:
        log(f"⚠️ Could not auto-eject: {e}", prefix=pfx)
        log(f"   Please eject '{drive}' manually.", prefix=pfx)
        return False


# ============================================================
#  DRIVE CLEANING (WIPE OLD FILES)
# ============================================================

def clean_drive(drive, prefix=None):
    """
    Remove all existing files and directories on the pen drive
    to start 100% fresh and clean (prevents viruses & factory bloatware).
    """
    pfx = prefix or drive.rstrip("\\").rstrip("/")
    log(f"🧹 Wiping all existing files on {drive}...", prefix=pfx)
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
        log(f"✨ Drive {drive} wiped clean! ({cleaned_count} old items removed)", prefix=pfx)
    except Exception as e:
        log(f"⚠️ Notice during drive wipe: {e}", prefix=pfx)


# ============================================================
#  FILE COPY
# ============================================================

def copy_songs_to_drive(source_dir, drive, song_list, prefix=None):
    """
    Copy all songs from source_dir to the root of the pen drive.
    Returns (success_count, fail_count, failed_files).
    """
    pfx = prefix or drive.rstrip("\\").rstrip("/")
    success_count = 0
    fail_count = 0
    failed_files = []
    total = len(song_list)

    for i, filename in enumerate(song_list, 1):
        source_path = os.path.join(source_dir, filename)
        dest_path = os.path.join(drive, filename)

        try:
            if not os.path.isfile(source_path):
                log(f"[{i:>2}/{total}] ❌ {filename} — File not found in source folder", prefix=pfx)
                fail_count += 1
                failed_files.append(filename)
                continue

            source_size = os.path.getsize(source_path)

            # Copy the file (preserves metadata like timestamps)
            shutil.copy2(source_path, dest_path)

            # Verify: check the destination file size matches
            dest_size = os.path.getsize(dest_path)
            if dest_size != source_size:
                log(f"[{i:>2}/{total}] ⚠️ {filename} — Size mismatch! (expected {format_size(source_size)}, got {format_size(dest_size)})", prefix=pfx)
                fail_count += 1
                failed_files.append(filename)
            else:
                log(f"[{i:>2}/{total}] ✅ {filename} ({format_size(source_size)})", prefix=pfx)
                success_count += 1

        except PermissionError:
            log(f"[{i:>2}/{total}] ❌ {filename} — Permission denied (drive may be write-protected)", prefix=pfx)
            fail_count += 1
            failed_files.append(filename)
        except OSError as e:
            if "No space left" in str(e) or "not enough space" in str(e).lower():
                log(f"[{i:>2}/{total}] ❌ {filename} — No space left on drive!", prefix=pfx)
                fail_count += 1
                failed_files.append(filename)
                log("🛑 Drive full — stopping copy for this drive.", prefix=pfx)
                break
            elif "device" in str(e).lower() or "removed" in str(e).lower():
                log(f"[{i:>2}/{total}] ❌ {filename} — Drive disconnected!", prefix=pfx)
                fail_count += 1
                failed_files.append(filename)
                log("🛑 Drive disconnected — stopping copy for this drive.", prefix=pfx)
                break
            else:
                log(f"[{i:>2}/{total}] ❌ {filename} — Error: {e}", prefix=pfx)
                fail_count += 1
                failed_files.append(filename)
        except Exception as e:
            log(f"[{i:>2}/{total}] ❌ {filename} — Unexpected error: {e}", prefix=pfx)
            fail_count += 1
            failed_files.append(filename)

    return success_count, fail_count, failed_files


def process_single_drive(drive, source_dir, song_list):
    """
    Wipes, renames, and copies songs to a single pen drive.
    Does NOT eject here — all drives are safely ejected together at the end.
    Returns a result dict.
    """
    pfx = drive.rstrip("\\").rstrip("/")
    log(f"🚀 Starting process on {drive}...", prefix=pfx)

    # 1. Wipe/Clean drive
    clean_drive(drive, prefix=pfx)

    # 2. Rename drive
    rename_drive(drive, DRIVE_LABEL, prefix=pfx)

    # 3. Copy songs
    success, failed, failed_files = copy_songs_to_drive(source_dir, drive, song_list, prefix=pfx)

    if failed == 0:
        log(f"✅ All {success}/{len(song_list)} songs verified! (⏳ Waiting for other drives to finish...)", prefix=pfx)
    else:
        log(f"⚠️ Copied {success}/{len(song_list)} songs, {failed} failed. (⏳ Waiting for other drives...)", prefix=pfx)

    return {
        "drive": drive,
        "success": success,
        "failed": failed,
        "failed_files": failed_files,
        "ejected": False,
    }


# ============================================================
#  MAIN PROGRAM
# ============================================================

def print_header():
    """Print the startup banner."""
    computer = get_computer_name()
    os_name = get_os_name()
    print()
    print("=" * 60)
    print(f"  {ALBUM_NAME}")
    print(f"  Album Song Pendrive Assembler (Multi-Drive Parallel Mode)")
    print(f"  Computer: {computer} | OS: {os_name}")
    print("=" * 60)
    print()


def main():
    print_header()

    # --- Scan and verify source folder and songs ---
    script_dir = get_script_dir()
    source_dir = os.path.join(script_dir, SOURCE_FOLDER)

    while True:
        print(f"  🔍 Scanning for '{SOURCE_FOLDER}' folder...")
        if not os.path.isdir(source_dir):
            print(f"  💡 '{SOURCE_FOLDER}' folder not found:")
            print(f"     {source_dir}")
            print()
            print(f"     Please place the '{SOURCE_FOLDER}' folder next to this program.")
            user_input = input("     Press Enter to scan again (Q to quit): ").strip().upper()
            if user_input == "Q":
                return
            print()
            continue

        resolved_songs, missing_tracks = resolve_album_songs(source_dir)
        if missing_tracks:
            print(f"  ⚠️ {len(missing_tracks)} song(s) missing from '{SOURCE_FOLDER}':")
            for m in missing_tracks:
                print(f"     - {m}")
            print()
            print(f"     (Names must match the track titles exactly. Any format is accepted: .mp3, .wav, .flac, etc.)")
            user_input = input("     Press Enter to scan again (Q to quit): ").strip().upper()
            if user_input == "Q":
                return
            print()
            continue

        print(f"  ✅ All {len(resolved_songs)} songs verified in '{SOURCE_FOLDER}'. Ready!\n")
        break

    # --- Main loop ---
    total_success = 0
    total_failed = 0

    while True:
        print("─" * 60)

        # --- Scan for pen drives ---
        print("  🔍 Scanning for pen drives...")
        pen_drives = locate_pen_drives()

        while not pen_drives:
            print("  💡 No pen drives found.")
            user_input = input("     Plug in pen drive(s) and press Enter (Q to quit): ").strip().upper()
            if user_input == "Q":
                break
            print("  🔍 Scanning again...")
            pen_drives = locate_pen_drives()

        if not pen_drives:
            break

        count = len(pen_drives)
        drive_infos = []
        for d in pen_drives:
            lbl, free = get_drive_info(d)
            drive_infos.append((d, lbl, free))

        print(f"\n  📌 Detected {count} pen drive(s):")
        for idx, (d, lbl, free) in enumerate(drive_infos, 1):
            print(f"     [{idx}] {d:<6} (Label: '{lbl}', Free: {format_size(free)})")

        print()
        print("  ⚠️ CAUTION: Processing will ERASE ALL EXISTING DATA on selected drives!")
        print()

        if count == 1:
            prompt_text = f"  Press Enter to WIPE & COPY to {pen_drives[0]} (S to skip/rescan, Q to quit): "
        else:
            prompt_text = (
                f"  Press Enter to WIPE & COPY to ALL {count} drives SIMULTANEOUSLY\n"
                f"  (or enter numbers e.g. 1,2 | S to skip/rescan | Q to quit): "
            )

        user_input = input(prompt_text).strip()
        cmd = user_input.upper()

        if cmd == "Q":
            break
        if cmd == "S":
            print("  ⏭️ Rescanning drives...")
            continue

        selected_drives = []
        if not user_input:
            selected_drives = list(pen_drives)
        else:
            try:
                parts = [p.strip() for p in user_input.replace(",", " ").split()]
                indices = [int(p) for p in parts]
                for idx in indices:
                    if 1 <= idx <= count:
                        selected_drives.append(pen_drives[idx - 1])
                    else:
                        print(f"  ⚠️ Invalid drive number: {idx}")
                selected_drives = list(dict.fromkeys(selected_drives))
            except ValueError:
                print(f"  ⚠️ Invalid input '{user_input}'. Skipping this round.")
                continue

        if not selected_drives:
            print("  ⚠️ No valid drives selected.")
            continue

        print()
        print(f"  ⚡ Running simultaneous copy for {len(selected_drives)} drive(s): {', '.join(selected_drives)}")
        print("─" * 60)

        # Process all selected drives in parallel
        batch_results = []
        with ThreadPoolExecutor(max_workers=len(selected_drives)) as executor:
            future_to_drive = {
                executor.submit(process_single_drive, drive, source_dir, resolved_songs): drive
                for drive in selected_drives
            }
            for future in as_completed(future_to_drive):
                drv = future_to_drive[future]
                try:
                    res = future.result()
                    batch_results.append(res)
                except Exception as exc:
                    batch_results.append({
                        "drive": drv,
                        "success": 0,
                        "failed": len(resolved_songs),
                        "failed_files": resolved_songs,
                        "ejected": False,
                        "error": str(exc),
                    })

        # --- Synchronized Safe Eject: ALL DRIVES EJECTED TOGETHER ---
        print()
        print("  " + "═" * 58)
        print("  ⏏️ ALL DRIVES FINISHED! Safely ejecting all drives together...")
        print("  " + "═" * 58)

        for res in sorted(batch_results, key=lambda x: x["drive"]):
            drv = res["drive"]
            ej = safe_eject(drv, prefix=drv.rstrip("\\").rstrip("/"))
            res["ejected"] = ej

        # --- Batch Summary ---
        print()
        print("  " + "═" * 58)
        print("  📊 BATCH RESULTS:")
        for res in sorted(batch_results, key=lambda x: x["drive"]):
            drv = res["drive"]
            succ = res["success"]
            fail = res["failed"]
            ej = "⏏️ Ejected" if res.get("ejected") else "⚠️ Please eject manually"
            if fail == 0:
                print(f"     ✅ {drv:<6} — {succ}/{len(resolved_songs)} songs copied ({ej})")
                total_success += 1
            else:
                print(f"     ❌ {drv:<6} — {succ}/{len(resolved_songs)} copied, {fail} failed ({ej})")
                if res.get("failed_files"):
                    print(f"        Failed files: {', '.join(res['failed_files'])}")
                total_failed += 1

        print()
        print("  🎉 ALL DRIVES ARE READY & SAFE TO UNPLUG NOW!")
        print(f"  📈 Session Total: {total_success} pen drive(s) completed", end="")
        if total_failed > 0:
            print(f" ({total_failed} failed)", end="")
        print("\n  " + "═" * 58)

        # --- Prompt for next batch ---
        print()
        user_input = input("  Unplug finished drives. Plug in next batch and press Enter (Q to quit): ").strip().upper()
        if user_input == "Q":
            break

    # --- Final summary ---
    print()
    print("=" * 60)
    print(f"  🏁 ALL DONE!")
    print(f"  ✅ {total_success} pen drive(s) completed successfully")
    if total_failed > 0:
        print(f"  ❌ {total_failed} pen drive(s) had errors")
    print("=" * 60)
    print()


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


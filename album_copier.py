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
WAV_FOLDER_NAME = "WAV"

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


def resolve_format_songs(directory, target_ext):
    """
    Find matching audio files in directory for each track in SONG_LIST.
    Requires exact base name match and target extension.
    Returns (resolved_filenames, missing_track_titles).
    """
    if not os.path.isdir(directory):
        return [], list(SONG_LIST)

    try:
        files = [f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]
    except Exception:
        return [], list(SONG_LIST)

    resolved = []
    missing = []

    for title in SONG_LIST:
        matched_file = None
        for f in sorted(files):
            base, ext = os.path.splitext(f)
            if ext.lower() == target_ext.lower() and base.strip().lower() == title.strip().lower():
                matched_file = f
                break

        if matched_file:
            resolved.append(matched_file)
        else:
            missing.append(title)

    return resolved, missing


def build_copy_tasks(source_dir):
    """
    Scans source_dir for MP3 songs in root and WAV songs in WAV_FOLDER_NAME subfolder.
    Returns (tasks, has_wav, errors).
    tasks is a list of dicts:
        {
            "src": absolute_source_path,
            "dest_rel": relative_path_on_drive (e.g. "01.mp3" or "WAV/01.wav"),
            "display": display_name,
            "category": "MP3" or "WAV"
        }
    """
    errors = []

    # 1. Resolve MP3 in source_dir root
    mp3_files, missing_mp3 = resolve_format_songs(source_dir, ".mp3")
    if missing_mp3:
        err_lines = [f"Missing {len(missing_mp3)} MP3 song(s) in '{SOURCE_FOLDER}/':"]
        for m in missing_mp3:
            err_lines.append(f"     - {m}.mp3")
        errors.append("\n".join(err_lines))

    # 2. Check if WAV subfolder exists and has WAV files
    wav_dir = os.path.join(source_dir, WAV_FOLDER_NAME)
    has_wav = False
    wav_files = []

    if os.path.isdir(wav_dir):
        try:
            wav_candidates = [f for f in os.listdir(wav_dir) if f.lower().endswith(".wav")]
        except Exception:
            wav_candidates = []

        if wav_candidates:
            has_wav = True
            wav_files, missing_wav = resolve_format_songs(wav_dir, ".wav")
            if missing_wav:
                err_lines = [f"Missing {len(missing_wav)} WAV song(s) in '{SOURCE_FOLDER}/{WAV_FOLDER_NAME}/':"]
                for m in missing_wav:
                    err_lines.append(f"     - {m}.wav")
                errors.append("\n".join(err_lines))

    if errors:
        return [], False, errors

    tasks = []
    for f in mp3_files:
        tasks.append({
            "src": os.path.join(source_dir, f),
            "dest_rel": f,
            "display": f,
            "category": "MP3"
        })

    if has_wav:
        for f in wav_files:
            tasks.append({
                "src": os.path.join(wav_dir, f),
                "dest_rel": os.path.join(WAV_FOLDER_NAME, f),
                "display": f"{WAV_FOLDER_NAME}/{f}",
                "category": "WAV"
            })

    return tasks, has_wav, []

# Thread safety lock for console output
_print_lock = threading.Lock()


def log(msg="", prefix=None):
    """Thread-safe logging helper with optional drive prefix."""
    with _print_lock:
        if not msg:
            print()
        elif prefix:
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

def copy_songs_to_drive(drive, copy_tasks, prefix=None):
    """
    Copy all songs according to copy_tasks to the pen drive.
    Returns (success_count, fail_count, failed_files).
    """
    pfx = prefix or drive.rstrip("\\").rstrip("/")
    success_count = 0
    fail_count = 0
    failed_files = []
    total = len(copy_tasks)

    for i, task in enumerate(copy_tasks, 1):
        source_path = task["src"]
        dest_rel = task["dest_rel"]
        display_name = task["display"]
        dest_path = os.path.join(drive, dest_rel)

        try:
            if not os.path.isfile(source_path):
                log(f"[{i:>2}/{total}] ❌ {display_name} — Source file not found", prefix=pfx)
                fail_count += 1
                failed_files.append(display_name)
                continue

            source_size = os.path.getsize(source_path)

            dest_dir = os.path.dirname(dest_path)
            if dest_dir and not os.path.exists(dest_dir):
                os.makedirs(dest_dir, exist_ok=True)

            # Copy the file (preserves metadata like timestamps)
            shutil.copy2(source_path, dest_path)

            # Verify: check the destination file size matches
            dest_size = os.path.getsize(dest_path)
            if dest_size != source_size:
                log(f"[{i:>2}/{total}] ⚠️ {display_name} — Size mismatch! (expected {format_size(source_size)}, got {format_size(dest_size)})", prefix=pfx)
                fail_count += 1
                failed_files.append(display_name)
            else:
                log(f"[{i:>2}/{total}] ✅ {display_name} ({format_size(source_size)})", prefix=pfx)
                success_count += 1

        except PermissionError:
            log(f"[{i:>2}/{total}] ❌ {display_name} — Permission denied (drive may be write-protected)", prefix=pfx)
            fail_count += 1
            failed_files.append(display_name)
        except OSError as e:
            if "No space left" in str(e) or "not enough space" in str(e).lower():
                log(f"[{i:>2}/{total}] ❌ {display_name} — No space left on drive!", prefix=pfx)
                fail_count += 1
                failed_files.append(display_name)
                log("🛑 Drive full — stopping copy for this drive.", prefix=pfx)
                break
            elif "device" in str(e).lower() or "removed" in str(e).lower():
                log(f"[{i:>2}/{total}] ❌ {display_name} — Drive disconnected!", prefix=pfx)
                fail_count += 1
                failed_files.append(display_name)
                log("🛑 Drive disconnected — stopping copy for this drive.", prefix=pfx)
                break
            else:
                log(f"[{i:>2}/{total}] ❌ {display_name} — Error: {e}", prefix=pfx)
                fail_count += 1
                failed_files.append(display_name)
        except Exception as e:
            log(f"[{i:>2}/{total}] ❌ {display_name} — Unexpected error: {e}", prefix=pfx)
            fail_count += 1
            failed_files.append(display_name)

    return success_count, fail_count, failed_files


def verify_drive_contents(drive, copy_tasks, prefix=None):
    """
    Perform a complete post-copy audit directly on the pen drive.
    Reads the drive to verify that all songs exist, are readable,
    and their sizes match the source files before ejecting.
    Returns (is_verified, missing_files, mismatched_files).
    """
    pfx = prefix or drive.rstrip("\\").rstrip("/")
    log()
    log(f"🔍 Auditing drive contents: checking all {len(copy_tasks)} files on {drive}...", prefix=pfx)

    missing = []
    mismatched = []

    for task in copy_tasks:
        dest_rel = task["dest_rel"]
        display_name = task["display"]
        dest_path = os.path.join(drive, dest_rel)
        source_path = task["src"]

        if not os.path.isfile(dest_path):
            missing.append(display_name)
            continue

        try:
            dest_size = os.path.getsize(dest_path)
            source_size = os.path.getsize(source_path)
            if dest_size != source_size or dest_size == 0:
                mismatched.append(display_name)
        except Exception:
            missing.append(display_name)

    if not missing and not mismatched:
        return True, [], []
    else:
        if missing:
            log(f"❌ Audit FAILED: {len(missing)} file(s) missing on {drive}: {', '.join(missing)}", prefix=pfx)
        if mismatched:
            log(f"⚠️ Audit FAILED: {len(mismatched)} file(s) size mismatch: {', '.join(mismatched)}", prefix=pfx)
        return False, missing, mismatched


def process_single_drive(drive, copy_tasks, has_wav):
    """
    Wipes, renames, copies songs, and verifies drive contents.
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
    success, failed, failed_files = copy_songs_to_drive(drive, copy_tasks, prefix=pfx)

    # 4. Post-copy audit: Read the drive to verify all files actually exist on disk
    is_verified, missing_audit, mismatch_audit = verify_drive_contents(drive, copy_tasks, prefix=pfx)

    if not is_verified:
        for f in missing_audit + mismatch_audit:
            if f not in failed_files:
                failed_files.append(f)
                failed += 1

    total_tasks = len(copy_tasks)
    mode_desc = "10 MP3 + 10 WAV" if has_wav else f"{total_tasks} MP3"
    if failed == 0 and is_verified:
        log(f"✅ All {success}/{total_tasks} songs ({mode_desc}) verified on {drive}!", prefix=pfx)
    else:
        log(f"⚠️ Copied {success}/{total_tasks} songs, {failed} issue(s) on {drive}. (⏳ Waiting for other drives...)", prefix=pfx)

    return {
        "drive": drive,
        "success": success if is_verified else max(0, total_tasks - len(failed_files)),
        "failed": failed,
        "failed_files": failed_files,
        "verified": is_verified,
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
    print(f"  Album Song Pendrive Assembler v4.0 (Option 3: Root MP3 + WAV Subfolder)")
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

        copy_tasks, has_wav, errors = build_copy_tasks(source_dir)
        if errors:
            for err in errors:
                print(f"  ⚠️ {err}")
            print()
            user_input = input("     Press Enter to scan again (Q to quit): ").strip().upper()
            if user_input == "Q":
                return
            print()
            continue

        mp3_count = sum(1 for t in copy_tasks if t["category"] == "MP3")
        wav_count = sum(1 for t in copy_tasks if t["category"] == "WAV")

        print(f"  📁 Found '{SOURCE_FOLDER}':")
        print(f"     - MP3 (Root): {mp3_count}/{len(SONG_LIST)} songs verified ✅")
        if has_wav:
            print(f"     - WAV ('{WAV_FOLDER_NAME}/' Subfolder): {wav_count}/{len(SONG_LIST)} songs verified ✅")
            print(f"  🎯 Mode: Option 3 (Root MP3 + WAV Subfolder) — Total {len(copy_tasks)} files per drive")
        else:
            print(f"     - WAV: None detected ('{WAV_FOLDER_NAME}/' folder not found or empty)")
            print(f"  🎯 Mode: Pure MP3 Mode — Total {len(copy_tasks)} files per drive")
        print()
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
                executor.submit(process_single_drive, drive, copy_tasks, has_wav): drive
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
                        "failed": len(copy_tasks),
                        "failed_files": [t["display"] for t in copy_tasks],
                        "verified": False,
                        "ejected": False,
                        "error": str(exc),
                    })

        # --- Synchronized Safe Eject: ALL DRIVES EJECTED TOGETHER ---
        print()
        for res in sorted(batch_results, key=lambda x: x["drive"]):
            drv = res["drive"]
            ej = safe_eject(drv, prefix=drv.rstrip("\\").rstrip("/"))
            res["ejected"] = ej

        # --- Batch Summary ---
        print()
        print("  " + "═" * 58)
        print("  📊 BATCH RESULTS:")
        total_songs = len(copy_tasks)
        mode_desc = "10 MP3 + 10 WAV" if has_wav else f"{total_songs} MP3"
        for res in sorted(batch_results, key=lambda x: x["drive"]):
            drv = res["drive"]
            succ = res["success"]
            fail = res["failed"]
            ej = "⏏️ Ejected" if res.get("ejected") else "⚠️ Please eject manually"
            if fail == 0 and res.get("verified"):
                print(f"     ✅ {drv:<6} — {succ}/{total_songs} songs verified on drive ({mode_desc}) ({ej})")
                total_success += 1
            else:
                print(f"     ❌ {drv:<6} — {succ}/{total_songs} copied, {fail} issue(s) ({ej})")
                if res.get("failed_files"):
                    print(f"        Issues: {', '.join(res['failed_files'])}")
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


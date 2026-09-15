# Album Song Pendrive Assembler

Bulk-copy album songs onto USB pen drives for mass distribution.

Built for the album **《稻、树林和风》原创专辑** ("The Paddy Fields, the Forests and the Wind").

---

## ⚠️ Important Safety Notice / 注意事项

> **CAUTION / 警告:**
> When you press **Enter** on a detected USB drive, this program will **WIPE & ERASE ALL EXISTING FILES** on that pen drive before copying the album songs.
> 
> * **Purpose:** Resets the pen drive to "brand new" factory condition, removing factory bloatware, unwanted files, and potential viruses.
> * **Do NOT** plug in personal hard drives or USBs containing important personal data!
> * If you accidentally plug in the wrong drive, press **`S`** to skip it or **`Q`** to quit safely.

---

## 🔄 What This Program Does (Step-by-Step)

When you run the assembler, it follows this automated 7-step process:

1. **🔍 Song Verification**: Checks that all 10 album MP3 files are present in `album_source/` with exact names. If any file is missing, it will alert you and stop.
2. **🔌 USB Detection**: Automatically scans and detects connected removable USB pen drives (displays drive letter, current name, and available free space).
3. **⚠️ Wipe & Clean Drive**: Upon pressing Enter, completely erases all old files, factory junk, and hidden trash on the pen drive to ensure a clean, virus-free drive.
4. **🏷️ Rename Drive**: Renames the USB volume label to **`PDW Album`**.
5. **🎵 Copy & Size Verification**: Copies all 10 MP3 files directly to the drive root (not inside subfolders, ensuring instant plug-and-play compatibility on car audio players and Bluetooth speakers) and verifies that every file size matches.
6. **⏏️ Safe Eject**: Automatically ejects the drive safely through OS commands so you can immediately unplug it without data corruption.
7. **🔁 Continuous Loop**: Shows a live session total count and waits for the next pen drive. Press **Enter** for the next drive, or **`Q`** to quit.

---

## 📥 Download

Go to the [**Releases page**](../../releases/latest) and download the appropriate version:

| Platform | Direct Download | ZIP Archive (Recommended if browser blocks) |
| :--- | :--- | :--- |
| **🪟 Windows** | `album_copier.exe` | `album_copier_windows.zip` |
| **🍎 macOS** | `album_copier_mac` | `album_copier_mac.zip` |

---

## 🚀 Quick Start Guide

### 1. Download & Extract
* **Windows**: Download `album_copier.exe` (or extract `album_copier_windows.zip`).
* **Mac**: Download `album_copier_mac` (or extract `album_copier_mac.zip`).

### 2. Prepare the Song Folder
Create an `album_source/` folder **in the same directory** as the executable, and place all 10 MP3 files inside it.

Your folder structure should look like this:
```text
Album-Assembler/
├── album_copier.exe (Windows) or album_copier_mac (Mac)
└── album_source/
    ├── 01 稻、树林和风.mp3
    ├── 02 Thankfulness.mp3
    ├── 03 满月.mp3
    ├── 04 我苦我乐我转转念.mp3
    ├── 05 含羞草的闪亮.mp3
    ├── 06 初心.mp3
    ├── 07 幸福答卷.mp3
    ├── 08 蝴蝶的呢喃.mp3
    ├── 09 拥抱无常.mp3
    └── 10 六时·尔时.mp3
```

### 3. Run the Program
* **Windows**: Double-click `album_copier.exe`.
  * *If Windows SmartScreen shows a blue popup*: Click **"More info"** → **"Run anyway"**.
* **Mac**: Double-click `album_copier_mac`.
  * *First time on Mac*: Right-Click (or Control-Click) → **Open** → Click **Open** in the prompt.
  * *If permission denied*: Open Terminal in that folder and run `chmod +x album_copier_mac`.

### 4. Mass Copying Workflow
1. Plug in a USB pen drive.
2. Check the drive letter/name displayed on screen.
3. Press **Enter** to wipe and copy the album songs.
4. When you see `⏏️ Safely ejecting... ✅`, unplug the drive.
5. Plug in the next pen drive and press **Enter**.
6. Type **`Q`** when you are finished!

---

## 🎶 Song List

| Track | Exact File Name |
| :---: | :--- |
| **01** | `01 稻、树林和风.mp3` |
| **02** | `02 Thankfulness.mp3` |
| **03** | `03 满月.mp3` |
| **04** | `04 我苦我乐我转转念.mp3` |
| **05** | `05 含羞草的闪亮.mp3` |
| **06** | `06 初心.mp3` |
| **07** | `07 幸福答卷.mp3` |
| **08** | `08 蝴蝶的呢喃.mp3` |
| **09** | `09 拥抱无常.mp3` |
| **10** | `10 六时·尔时.mp3` |

---

## 👥 Instructions for Team Members

1. Open the [**Latest Releases**](../../releases/latest) page.
2. Download the version for your computer.
3. Put the `album_source` folder with the 10 MP3 files next to the downloaded app.
4. Double-click to start copying pen drives!

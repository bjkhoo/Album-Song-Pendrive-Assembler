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

When you run the assembler, it follows this automated process:

1. **🔍 Song Verification**: Checks that all 10 album MP3 files are present in `album_source/` with exact names. If any file is missing, it will alert you and stop.
2. **🔌 USB Detection (Single or Multi-Drive)**: Automatically scans and detects all connected removable USB pen drives (supports external multi-port USB hubs with 4, 8, 10+ drives). Displays drive letters, current labels, and available free space.
3. **⚡ Simultaneous Parallel Processing**: Press **Enter** once to process **all connected pen drives simultaneously in parallel** (or choose specific drive numbers).
4. **⚠️ Wipe & Clean Drive**: Erases all old files, factory junk, and hidden trash on each pen drive to ensure clean, virus-free drives.
5. **🏷️ Rename Drive**: Renames each USB volume label to **`PDW Album`**.
6. **🎵 Copy & Size Verification**: Copies all 10 MP3 files directly to the root of each drive simultaneously and verifies that every file size matches.
7. **⏏️ Safe Eject**: Automatically ejects all completed drives safely so you can immediately unplug them.
8. **🔁 Continuous Batch Loop**: Shows a batch results summary and live overall total, then waits for the next batch of pen drives.

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

### 4. Mass Copying Workflow (Supports Multi-Port USB Hubs!)
1. Plug in one or multiple USB pen drives (e.g. into your external multi-port USB hub).
2. The program scans and lists all detected drives (e.g. `[1] E:\`, `[2] F:\`, `[3] G:\`).
3. Press **Enter** to wipe and copy to **all drives simultaneously in parallel** (or type `1,2` for specific drives).
4. Watch real-time progress for each drive marked with its drive letter.
5. When you see `⏏️ Safely ejected... ✅`, unplug the finished drives.
6. Plug in the next batch of pen drives and press **Enter**.
7. Type **`Q`** when you are finished!

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

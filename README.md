# Album Song Pendrive Assembler

Bulk-copy album songs onto USB pen drives for mass distribution.

Built for the album **《稻、树林和风》原创专辑** ("The Paddy Fields, the Forests and the Wind").

## Features

- **Cross-platform** — Works on both Windows and macOS
- **Error handling** — Graceful recovery from copy failures, drive disconnects, etc.
- **Safe eject** — Automatically ejects pen drives after copying
- **Auto rename** — Renames pen drives to "PDW Album"
- **Continuous loop** — Keep plugging in pen drives without restarting
- **Progress tracking** — Shows running count of completed pen drives
- **Auto-build** — GitHub Actions automatically builds Windows .exe and Mac binary

## Download

Go to the [**Releases page**](../../releases/latest) and download:

| Platform | File to download | Python needed? |
|----------|-----------------|----------------|
| **Windows** | `album_copier.exe` | **No** — just double-click! |
| **Mac** | `album_copier_mac` | **No** — just double-click! |

## Quick Start

### 1. Download the executable

Download the correct file for your OS from the [Releases page](../../releases/latest).

### 2. Prepare the songs

Create an `album_source/` folder **next to** the executable and place all 10 MP3 files inside.

See [`PREPARATION.txt`](album_source/PREPARATION.txt) for the exact file naming guide.

Your folder should look like this:

```
Any folder/
├── album_copier.exe (Windows) or album_copier_mac (Mac)
└── album_source/
    ├── 01 稻、树林和风.mp3
    ├── 02 Thankfulness.mp3
    ├── 03 满月.mp3
    ├── ... (all 10 songs)
    └── 10 六时·尔时.mp3
```

### 3. Run the copier

- **Windows**: Double-click `album_copier.exe`
- **Mac**: Double-click `album_copier_mac`
  - First time on Mac: Right-click → Open → Open (to bypass Gatekeeper)
  - If it says "permission denied", open Terminal and run: `chmod +x album_copier_mac`

### 4. Follow the prompts

- Plug in a pen drive, press **Enter** to copy
- After copying, the drive is auto-ejected and renamed to "PDW Album"
- Plug in the next pen drive, press **Enter** again
- Press **Q** to quit when done

## Song List

| Track | Song |
|-------|------|
| 01 | 稻、树林和风 |
| 02 | Thankfulness |
| 03 | 满月 |
| 04 | 我苦我乐我转转念 |
| 05 | 含羞草的闪亮 |
| 06 | 初心 |
| 07 | 幸福答卷 |
| 08 | 蝴蝶的呢喃 |
| 09 | 拥抱无常 |
| 10 | 六时·尔时 |

## For Team Members

1. Go to the [Releases page](../../releases/latest)
2. Download the executable for your OS (Windows or Mac)
3. Create `album_source/` folder next to it with the 10 MP3 files
4. Double-click the executable and start copying!

**No Python installation needed on any platform!**
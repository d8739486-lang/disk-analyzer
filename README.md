# 🖴 Disk Analyzer (Linux GTK3)

> **🤖 Note:** This project was developed and designed with **AI assistance** (Google DeepMind Antigravity).

A modern, fast, and native storage analysis utility for Linux (Linux Mint, Ubuntu, Debian, and other distributions).
Tailored with deep integration into the native **Linux Mint (Mint-Y-Dark)** theme.

---

## 📁 Repository Structure

```text
├── disk-analyzer_1.0.0_all.deb   # Debian / Ubuntu package installer
├── disk-analyzer.bin             # Standalone executable binary (ZipApp)
├── build_deb.sh                  # Package build script
├── source-code/                  # Application source code
│   ├── main.py                   # App entry point
│   ├── core/                     # SMART, benchmark & discovery logic
│   ├── gui/                      # GTK3 widgets, tabs, and styles
│   └── assets/                   # App icons and graphics
└── README.md
```

---

## ✨ Features

1. **Storage Drives & S.M.A.R.T.**
   - Auto-detection of NVMe, SATA SSD, HDD, and USB storage devices.
   - Quick health dashboard (drive state, temperature, interface, power-on hours).
   - Detailed S.M.A.R.T. telemetry table with context menu descriptions and Advanced Mode.

2. **Disk Usage Analysis**
   - Interactive directory tree explorer.
   - Real-time disk space calculation and breakdown.
   - Quick navigation with native file manager opening.

3. **Speed Benchmark**
   - Sequential read/write (SEQ 1M) and random 4K access tests (4K RND).
   - Real-time animated speed indicators and result cards.
   - Configurable test file sizes (64 MB to 16 GB).

4. **Block Map & Surface Verification**
   - **Treemap View:** Interactive nested block mosaic of files and folders (similar to WinDirStat / KDirStat).
   - **Sector Verification (Block Grid):** Block-by-block surface scan with millisecond response time telemetry (similar to Victoria / HD Tune).
   - Instant zero-delay switching between modes.

---

## 🚀 Installation & Running

### Option 1: Install via `.deb` package (Recommended)

Download `disk-analyzer_1.0.0_all.deb` and install it:
```bash
sudo dpkg -i disk-analyzer_1.0.0_all.deb
```
The application shortcut will appear in your system Application Menu under the "System" category. You can also run it via terminal:
```bash
disk-analyzer
```

### Option 2: Run Standalone Binary (ZipApp)
No installation required:
```bash
chmod +x disk-analyzer.bin
./disk-analyzer.bin
```

### Option 3: Run from Source Code
```bash
cd source-code
python3 main.py
```

---

## 🛠 Dependencies
- Python 3.10+
- PyGObject (`python3-gi`, `gir1.2-gtk-3.0`)
- Cairo (`python3-gi-cairo`)

To install dependencies on Debian/Ubuntu/Mint:
```bash
sudo apt update
sudo apt install python3 python3-gi python3-gi-cairo gir1.2-gtk-3.0
```

---

## 📜 License
MIT License

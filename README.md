<div align="center">

# ♟️ FianCheato

**A real-time, screen-reading chess assistant with a transparent PyQt6 overlay.**

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![OpenCV](https://img.shields.io/badge/OpenCV-Vision-5C3EE8?style=for-the-badge&logo=opencv&logoColor=white)
![PyQt6](https://img.shields.io/badge/PyQt6-Overlay-41CD52?style=for-the-badge&logo=qt&logoColor=white)
![Stockfish](https://img.shields.io/badge/Stockfish-UCI_Engine-2E2E2E?style=for-the-badge&logo=chessdotcom&logoColor=white)

</div>

---

## ✨ Features

* **Multi-Monitor Calibration** — Drag a bounding box over any chessboard on any display using global desktop coordinates.
* **1-Click Template Capture** — Auto-crops all 12 piece templates directly from a starting board; no manual PNG setup required.
* **Auto Orientation Detection** — Automatically detects whether you are playing as White or Black (with manual override).
* **Click-Through Overlay** — Highlights source and destination squares with a connecting line without blocking mouse input.
* **Smart Debouncing** — Waits for piece animations to settle before running Stockfish analysis.

---

## 🛠️ Prerequisites

* **Python 3.10+** *(Check **Add python.exe to PATH** during Windows installation)*
* **Stockfish Engine** — Download the binary for your OS from [stockfishchess.org/download](https://stockfishchess.org/download/)

---

## 🚀 Installation

**1. Clone the repository**
```bash
git clone [https://github.com/Zheighjein/FianCheato.git](https://github.com/Zheighjein/FianCheato.git)
cd FianCheato
```

**2. Install dependencies**
```bash
python -m pip install mss opencv-python numpy python-chess PyQt6
```

**3. Add Stockfish**
1. Extract the downloaded Stockfish `.zip` archive.
2. Copy the executable (e.g., `stockfish-windows-x86-64-avx2.exe`) into the root `FianCheato/` folder.
3. Rename it to `stockfish.exe` *(or update `STOCKFISH_PATH` in `main.py` to match its filename)*.

---

## ▶️ How to Run

```bash
python main.py
```

The floating **BoardLens HUD** will appear on your screen.

---

## 🎮 How to Use

1. **Calibrate the Board**
   * Open your chessboard and move the HUD off to the side.
   * Click **Calibrate Board**, then click and drag a box tightly around the 8×8 grid *(exclude borders, clocks, and player names)*.
2. **Capture Piece Templates** *(One-time setup per piece theme)*
   * Open a **fresh starting chessboard** (all 32 pieces on their home squares, no moves played).
   * Click **Capture Templates**. All 12 piece PNGs are saved to `templates/` and loaded automatically in future sessions.
3. **Analyze**
   * Leave **Side** on **Auto** *(or manually select **White** / **Black**)*.
   * Click **Analyze Now** for a single-move evaluation, or toggle **Auto-Scan: ON** for live move suggestions.

---

## 📂 Project Structure

```text
FianCheato/
├── main.py          # Entry point, UI wiring, and debounce loop
├── vision.py        # Screen capture, piece recognition, and FEN builder
├── engine.py        # Stockfish UCI engine wrapper
├── overlay.py       # PyQt6 click-through overlay, calibrator, and HUD
├── stockfish.exe    # Local Stockfish binary (gitignored)
└── templates/       # Auto-captured piece PNGs (gitignored)
```
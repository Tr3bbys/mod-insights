# CS2 Stats Updater

Automated screenshot-based stats updater for csstats.gg player data.

## Installation

```bash
pip install pytesseract pillow opencv-python
```

### Windows
Download and install Tesseract OCR:
- Download from: https://github.com/UB-Mannheim/tesseract/wiki
- Default path: `C:\Program Files\Tesseract-OCR`

### macOS
```bash
brew install tesseract
```

### Linux (Ubuntu/Debian)
```bash
sudo apt-get install tesseract-ocr
```

## Usage

1. Take screenshots of each player's profile on csstats.gg:
   - Screenshot each player tab (STATS, WEAPONS, PLAYED WITH, MATCHES)
   - Save with player name in filename (e.g., `treb.png`, `dp.png`)

2. Run the updater:
```bash
python update_stats_screenshot.py treb.png dp.png sandz.png sy.png rosso.png
```

The script will:
- Extract all text from screenshots using OCR
- Parse stats, weapons, teammates, and matches
- Update `report_data.json`
- Auto-increment version
- Auto-commit and push to GitHub

## How It Works

1. **Screenshot Preprocessing**: Converts images to grayscale and applies thresholding for better OCR accuracy
2. **Text Extraction**: Uses Tesseract OCR to extract all text from the screenshot
3. **Data Parsing**: Regex patterns extract:
   - Basic stats (games, K/D, HLTV rating, win rate, HS%)
   - Weapon data (kills, headshot%, accuracy, damage)
   - Teammate stats (played with data)
   - Recent matches
4. **JSON Update**: Updates `report_data.json` with new data
5. **Git Sync**: Auto-commits and pushes changes to GitHub

## Tips for Best Results

- Take clear, high-resolution screenshots
- Ensure the stat text is visible and not blurry
- Include the full player profile stat sections
- Name files with player name for auto-detection

## Automation

GitHub Actions workflow can be triggered manually:
1. Go to Actions tab on GitHub
2. Select "Manual Stats Update"
3. Click "Run workflow"
4. Enter screenshot filenames

## Troubleshooting

**"pytesseract.TesseractNotFoundError"**
- Install Tesseract OCR (see Installation section)
- Windows users: Add to PATH or set in script: `pytesseract.pytesseract.pytesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'`

**Poor OCR accuracy**
- Ensure screenshots are high resolution
- Text should be clearly visible
- Try adjusting the image preprocessing in `preprocess_image()`

**Stats not parsing correctly**
- The regex patterns may need adjustment based on csstats.gg layout changes
- Check OCR output in terminal for what was extracted

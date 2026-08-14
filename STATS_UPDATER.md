# CS2 Stats Updater

Screenshot-based stats updater for csstats.gg player data. Uses OCR to extract stats automatically from screenshots of player profiles.

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

## Usage (Option B - Multiple Tabs Per Player)

### Step 1: Take Screenshots
For each player, take separate screenshots of these tabs:
1. **STATS** tab - games played, K/D, HLTV rating, HS%, ADR
2. **WEAPONS** tab - weapon breakdown with kills, HS%, accuracy, damage
3. **PLAYED WITH** tab - teammate stats and synergy

Save with pattern: `{playername}_{tab}.png`

Example filenames:
```
treb_stats.png        rosso_stats.png       sandz_stats.png       sy_stats.png          dp_stats.png
treb_weapons.png      rosso_weapons.png     sandz_weapons.png     sy_weapons.png        dp_weapons.png
treb_played_with.png  rosso_played_with.png sandz_played_with.png sy_played_with.png    dp_played_with.png
```

**Note**: MATCHES tab is optional (varies based on 5-stack availability)

### Step 2: Run the Updater

Option A - Explicit files:
```bash
python update_stats_screenshot.py treb_stats.png treb_weapons.png treb_played_with.png \
                                   dp_stats.png dp_weapons.png dp_played_with.png \
                                   sandz_stats.png sandz_weapons.png sandz_played_with.png \
                                   sy_stats.png sy_weapons.png sy_played_with.png \
                                   rosso_stats.png rosso_weapons.png rosso_played_with.png
```

Option B - Using wildcards (simpler):
```bash
python update_stats_screenshot.py treb_*.png dp_*.png sandz_*.png sy_*.png rosso_*.png
```

### Step 3: Auto-Sync
The script will automatically:
- Extract all text from screenshots using OCR
- Parse stats by tab type
- Update `report_data.json`
- Increment version number
- Generate changelog entry
- Commit and push to GitHub

## What Gets Extracted

### From STATS Tab
- Games played
- K/D ratio
- HLTV rating
- Win rate
- Headshot %
- ADR (Average Damage per Round)
- Clutch success rate

### From WEAPONS Tab
- Each weapon used
- Kill count per weapon
- Headshot % per weapon
- Accuracy
- Damage dealt
- Shots fired
- Body part hit distribution

### From PLAYED WITH Tab
- Teammate names and stats
- Games played together
- Combined K/D with teammate
- Win rate as a pair
- ADR together
- Rating synergy

## Tips for Best Results

1. **Screenshot Quality**
   - Take high-resolution screenshots
   - Ensure text is clear and readable
   - Avoid blurry or zoomed-out images

2. **Full Data Visibility**
   - Make sure all stat columns are visible
   - Scroll to see weapon/teammate data if needed
   - Include table headers for context

3. **Consistent Naming**
   - Use lowercase player names: `treb`, `dp`, `sandz`, `sy`, `rosso`
   - Include tab type in filename: `stats`, `weapons`, `played_with`
   - Use underscore separator: `{player}_{tab}.png`

4. **File Organization**
   - Save all screenshots to the mod-insights project root folder
   - Delete old screenshots after updating (optional)

## Troubleshooting

### "pytesseract.TesseractNotFoundError"
Windows users need to either:
1. Add Tesseract to PATH, or
2. Edit the script and add this line after imports:
   ```python
   pytesseract.pytesseract.pytesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
   ```

### Poor OCR Accuracy
- Ensure screenshots are high resolution (1920x1080 or higher recommended)
- Text should be clearly visible without distortion
- Avoid dark mode if site has light mode option
- Try adjusting `preprocess_image()` parameters if needed

### Stats Not Parsing
- Check terminal output for what text was extracted
- Verify screenshot includes the stat you're looking for
- Ensure column headers are visible
- The regex patterns may need adjustment if csstats.gg layout changes significantly

### Git Push Fails
- Ensure git is configured: `git config --global user.name "Your Name"` and `git config --global user.email "your@email.com"`
- Check repo connectivity
- Verify you have push access to the repository

## Workflow Example

```bash
# 1. Navigate to project folder
cd "c:\Users\trebl\OneDrive\Desktop\Claude Projects\mod-insights"

# 2. Take screenshots and save them with proper names
# (Use screenshot tool or print-screen)

# 3. Run the updater with wildcard
python update_stats_screenshot.py treb_*.png dp_*.png sandz_*.png sy_*.png rosso_*.png

# 4. Check output - it will auto-commit and push if successful
```

## GitHub Actions (Optional)

The workflow can also be triggered manually from GitHub:
1. Go to your repository on GitHub
2. Click "Actions" tab
3. Select "Manual Stats Update" workflow
4. Click "Run workflow"

(Note: GitHub Actions version requires uploading screenshots to the repo, so local usage is simpler)

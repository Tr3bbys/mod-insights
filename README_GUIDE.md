# CS2 Stats Updater - Quick Start Guide

A **screenshot-based stats updater** that automatically extracts player statistics from csstats.gg and updates your team report in one command.

---

## 🚀 Quick Start (30 seconds)

### Already Installed?
```bash
# 1. Take 3 screenshots per player (STATS, WEAPONS, PLAYED WITH tabs)
# 2. Save them with names like: treb_stats.png, treb_weapons.png, treb_played_with.png
# 3. Run this command:
python update_stats_screenshot.py treb_*.png dp_*.png sandz_*.png sy_*.png rosso_*.png

# ✅ Done! JSON updated, version bumped, pushed to GitHub
```

---

## 📋 Step-by-Step Guide

### Step 1: Take Screenshots

For **each player** (dP^, rosso, SandZ, Sy, Treb), take 3 screenshots:

#### 1a - STATS Tab
- Opens: https://csstats.gg/player/[ID]
- Shows: Games, K/D, HLTV Rating, Headshot %, ADR, Clutch %
- **Save as**: `{playername}_stats.png`

#### 1b - WEAPONS Tab  
- Click "WEAPONS" tab on the same profile
- Shows: All weapons used, kills per weapon, HS%, accuracy, damage
- **Save as**: `{playername}_weapons.png`

#### 1c - PLAYED WITH Tab
- Click "PLAYED WITH" tab on the same profile
- Shows: Teammates, games together, K/D with them, synergy stats
- **Save as**: `{playername}_played_with.png`

### Example Filenames
```
treb_stats.png
treb_weapons.png
treb_played_with.png

dp_stats.png
dp_weapons.png
dp_played_with.png

sandz_stats.png
sandz_weapons.png
sandz_played_with.png

sy_stats.png
sy_weapons.png
sy_played_with.png

rosso_stats.png
rosso_weapons.png
rosso_played_with.png
```

### Step 2: Save Screenshots

Save all 15 screenshots in the **mod-insights folder**:
```
c:\Users\trebl\OneDrive\Desktop\Claude Projects\mod-insights\
  ├── treb_stats.png
  ├── treb_weapons.png
  ├── treb_played_with.png
  ├── dp_stats.png
  ├── ... (and so on)
```

### Step 3: Run the Updater

Open PowerShell in the mod-insights folder:
```bash
cd "c:\Users\trebl\OneDrive\Desktop\Claude Projects\mod-insights"
```

Run the updater with all screenshots:
```bash
python update_stats_screenshot.py treb_*.png dp_*.png sandz_*.png sy_*.png rosso_*.png
```

Or pass them explicitly:
```bash
python update_stats_screenshot.py treb_stats.png treb_weapons.png treb_played_with.png \
                                   dp_stats.png dp_weapons.png dp_played_with.png \
                                   sandz_stats.png sandz_weapons.png sandz_played_with.png \
                                   sy_stats.png sy_weapons.png sy_played_with.png \
                                   rosso_stats.png rosso_weapons.png rosso_played_with.png
```

### Step 4: Watch It Work

The script will:
```
→ Processing Treb [stats]...
  ✓ Stats: 54 games, 0.99 K/D, 1.13 rating

→ Processing Treb [weapons]...
  ✓ Weapons: 12 weapon types extracted

→ Processing Treb [played_with]...
  ✓ Teammates: 8 players extracted

[Repeats for each player]

✓ Extracted data from 15 screenshots
✓ Updated report_data.json
✓ Pushed to GitHub
```

---

## 📁 What Gets Updated

### In `report_data.json`:
- ✅ **Player Games**: Total games played (auto-calculates tier: high/med/low)
- ✅ **Player Stats**: K/D, HLTV rating, HS%, ADR
- ✅ **Weapons Data**: Kills per weapon, accuracy, damage
- ✅ **Teammates**: Who they played with and synergy stats
- ✅ **Version**: Auto-incremented (v7 → v8)
- ✅ **Changelog**: Auto-generated summary
- ✅ **Git**: Auto-committed and pushed to GitHub

---

## 🛠️ Installation (One-Time Setup)

If you haven't already:

### 1. Install Python Packages
```bash
pip install pytesseract pillow opencv-python
```

### 2. Install Tesseract OCR

**Windows:**
1. Download from: https://github.com/UB-Mannheim/tesseract/wiki
2. Run installer (uses default path: `C:\Program Files\Tesseract-OCR`)
3. Done!

**Mac:**
```bash
brew install tesseract
```

**Linux (Ubuntu):**
```bash
sudo apt-get install tesseract-ocr
```

### 3. Test It
```bash
python update_stats_screenshot.py --help
```

---

## ❓ Troubleshooting

### "pytesseract.TesseractNotFoundError"
**Windows Fix:**
1. Open `update_stats_screenshot.py`
2. After the imports, add:
   ```python
   import pytesseract
   pytesseract.pytesseract.pytesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
   ```
3. Save and try again

### "File not found"
- Make sure screenshot files are in the same folder as the script
- Check filenames match: `{playername}_{tab}.png`
- Player names: `treb`, `dp`, `sandz`, `sy`, `rosso` (lowercase)

### "Could not extract text from image"
- Screenshot resolution too low - use 1920x1080 or higher
- Text is blurry or hard to read - retake screenshot
- Tab header not visible - scroll up to show it

### "Git push failed"
```bash
# Configure git once:
git config --global user.name "Your Name"
git config --global user.email "your@email.com"
```

---

## 📊 Examples of What's Extracted

### STATS Tab → Extracted
| Metric | Extracted | Used For |
|--------|-----------|----------|
| Games Played | 54 | Determines tier (high/med/low) |
| K/D Ratio | 0.99 | Chart data, player evaluation |
| HLTV Rating | 1.13 | Performance metric |
| Win Rate | 50% | Team assessment |
| Headshot % | 51% | Aim consistency |
| ADR | 75 | Damage output |

### WEAPONS Tab → Extracted
- All weapons used (AK47, M4A4, AWP, etc.)
- Kills per weapon
- Headshot % per weapon
- Accuracy, damage, shots fired

### PLAYED WITH Tab → Extracted
- Teammate names
- Games played together
- Combined K/D with teammate
- Win rate as a pair
- Rating synergy

---

## 🔄 Weekly Workflow

1. **Every Sunday** (or whenever you update):
   - Take 3 screenshots per player
   - Run one command
   - Done! Report is live on GitHub

2. **No manual JSON editing needed**
3. **No manual git commands needed**
4. **Changelog auto-generates**

---

## 📝 Notes

- **MATCHES tab is optional** - script doesn't require it
- **Wildcard pattern** (`*`) is recommended for simplicity
- **Old screenshots** can be deleted after running updater
- **Version auto-increments** (v7 → v8 → v9, etc.)

---

## 🚨 Important Tips

1. **Screenshot Quality**
   - Use high resolution (1920x1080 minimum)
   - Ensure text is readable
   - Include table headers

2. **Naming Convention**
   - Use exact format: `{player}_{tab}.png`
   - Player names: `treb`, `dp`, `sandz`, `sy`, `rosso` (lowercase)
   - Tab names: `stats`, `weapons`, `played_with`

3. **File Location**
   - Save in mod-insights project root
   - Same folder as `update_stats_screenshot.py`

4. **Running the Script**
   - Navigate to mod-insights folder
   - Use wildcard for simplicity: `treb_*.png dp_*.png ...`
   - Check terminal output for any errors

---

## ✅ Checklist Before Running

- [ ] All 15 screenshots taken (3 per player)
- [ ] Files named correctly with player and tab names
- [ ] Tesseract OCR installed
- [ ] Python packages installed (`pytesseract`, `pillow`, `opencv-python`)
- [ ] Currently in mod-insights folder
- [ ] Git configured (`git config --global user.name` and `user.email`)

---

## 🎯 That's It!

You're all set. Take screenshots, run the command, and your stats report is auto-updated and pushed to GitHub.

Questions? Check `STATS_UPDATER.md` for detailed technical info.

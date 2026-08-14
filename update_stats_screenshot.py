#!/usr/bin/env python3
"""
CS2 Stats Screenshot Parser
Extracts stats from csstats.gg screenshots and updates report_data.json
Requires: pytesseract, pillow, opencv-python
"""

import json
import re
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Tuple
import subprocess

try:
    import pytesseract
    from PIL import Image
    import cv2
    import numpy as np
except ImportError:
    print("Error: Required packages not installed.")
    print("Install with: pip install pytesseract pillow opencv-python")
    sys.exit(1)

PLAYERS = ["dP^", "rosso", "Sandz", "Sy", "Treb"]

TIER_THRESHOLDS = {
    "high": 100,
    "med": 50,
    "low": 0
}

def get_tier(games):
    """Determine tier based on game count"""
    if games >= TIER_THRESHOLDS["high"]:
        return "high"
    elif games >= TIER_THRESHOLDS["med"]:
        return "med"
    else:
        return "low"

def preprocess_image(image_path):
    """Preprocess image for better OCR accuracy"""
    img = cv2.imread(str(image_path))
    
    # Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Apply thresholding
    _, thresh = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
    
    # Denoise
    denoised = cv2.fastNlMeansDenoising(thresh, None, h=10, templateWindowSize=7, searchWindowSize=21)
    
    return denoised

def extract_text_from_screenshot(image_path):
    """Extract all text from screenshot using OCR"""
    try:
        # Preprocess image
        processed_img = preprocess_image(image_path)
        
        # Convert back to PIL Image for pytesseract
        pil_img = Image.fromarray(processed_img)
        
        # Extract text
        text = pytesseract.image_to_string(pil_img)
        return text
    except Exception as e:
        print(f"Error extracting text from {image_path}: {e}")
        return ""

def parse_stats_tab(text: str) -> Dict[str, Any]:
    """Parse STATS tab content"""
    stats = {}
    
    # Extract games played
    games_match = re.search(r'PLAYED\s+(\d+)', text)
    if games_match:
        stats['games'] = int(games_match.group(1))
    
    # Extract K/D
    kd_match = re.search(r'K/D\s+([\d.]+)', text)
    if kd_match:
        stats['kd'] = float(kd_match.group(1))
    
    # Extract HLTV rating
    rating_match = re.search(r'HLTV\s+RATING\s+([\d.]+)', text)
    if rating_match:
        stats['hltv_rating'] = float(rating_match.group(1))
    
    # Extract win rate
    winrate_match = re.search(r'WIN\s+RATE\s+([\d%]+)', text)
    if winrate_match:
        stats['win_rate'] = int(winrate_match.group(1).rstrip('%'))
    
    # Extract wins/losses
    won_match = re.search(r'WON\s+(\d+)', text)
    if won_match:
        stats['wins'] = int(won_match.group(1))
    
    lost_match = re.search(r'LOST\s+(\d+)', text)
    if lost_match:
        stats['losses'] = int(lost_match.group(1))
    
    # Extract headshot %
    hs_match = re.search(r'HS%\s+([\d%]+)', text)
    if hs_match:
        stats['hs_percent'] = int(hs_match.group(1).rstrip('%'))
    
    # Extract ADR
    adr_match = re.search(r'ADR\s+(\d+)', text)
    if adr_match:
        stats['adr'] = int(adr_match.group(1))
    
    # Extract clutch success
    clutch_match = re.search(r'1vx\s+([\d%]+)\s*-', text)
    if clutch_match:
        stats['clutch_success'] = int(clutch_match.group(1).rstrip('%'))
    
    return stats

def parse_weapons_tab(text: str) -> List[Dict[str, Any]]:
    """Parse WEAPONS tab content"""
    weapons = []
    
    # Look for weapon lines - pattern: weapon_name kills hs% etc
    lines = text.split('\n')
    
    for line in lines:
        # Skip header lines
        if any(x in line.lower() for x in ['kills', 'accuracy', 'weapon', 'damage']):
            continue
        
        # Try to extract weapon data
        parts = line.split()
        if len(parts) >= 3:
            try:
                # Rough parsing - may need adjustment based on actual format
                weapon_name = parts[0]
                kills = int(parts[1]) if parts[1].isdigit() else None
                
                if kills:
                    weapons.append({
                        'weapon': weapon_name,
                        'kills': kills
                    })
            except:
                pass
    
    return weapons

def parse_played_with_tab(text: str) -> List[Dict[str, Any]]:
    """Parse PLAYED WITH tab content"""
    teammates = []
    
    # Look for teammate entries
    lines = text.split('\n')
    
    for line in lines:
        # Skip headers
        if any(x in line.lower() for x in ['games', 'rating', 'overall']):
            continue
        
        # Try to extract teammate data
        if any(x in line for x in ['@', 'K/D', '/']):
            parts = line.split()
            if len(parts) >= 2:
                try:
                    teammate_name = parts[0]
                    # This is simplified - real parsing would be more complex
                    teammates.append({
                        'name': teammate_name
                    })
                except:
                    pass
    
    return teammates

def process_player_screenshot(player_name: str, screenshot_path: str, report_data: Dict) -> Tuple[bool, str]:
    """Process a single player's screenshot"""
    if not Path(screenshot_path).exists():
        return False, f"File not found: {screenshot_path}"
    
    print(f"\nProcessing {player_name}...")
    
    # Extract text from image
    text = extract_text_from_screenshot(screenshot_path)
    if not text:
        return False, "Could not extract text from image"
    
    # Parse different sections
    stats = parse_stats_tab(text)
    weapons = parse_weapons_tab(text)
    teammates = parse_played_with_tab(text)
    
    if not stats:
        return False, "Could not parse stats from screenshot"
    
    # Update player data in report_data
    for player in report_data.get("players", []):
        if player["name"] == player_name:
            old_games = player.get("games")
            
            # Update stats
            if 'games' in stats:
                player['games'] = stats['games']
            if 'kd' in stats:
                player['kd'] = stats['kd']
            if 'hltv_rating' in stats:
                player['hltv_rating'] = stats['hltv_rating']
            
            # Update tier if games changed
            if 'games' in stats:
                new_tier = get_tier(stats['games'])
                if new_tier != player.get("tier"):
                    player["tier"] = new_tier
            
            # Update chart data
            if 'kd' in stats:
                report_data["chart_data"]["hltv_rating"][player_name] = stats.get('hltv_rating', 1.0)
            
            status = f"✓ {player_name}: {stats.get('games', '?')} games, {stats.get('kd', '?')} K/D, {stats.get('hltv_rating', '?')} rating"
            return True, status
    
    return False, f"Player {player_name} not found in report data"

def update_report_metadata(report_data: Dict) -> None:
    """Update metadata with current date and version"""
    report_data["report_meta"]["date"] = datetime.now().strftime("%d %b %Y")
    
    # Increment version
    current_version = report_data["report_meta"].get("version", "v0")
    version_num = int(current_version[1:]) + 1
    report_data["report_meta"]["version"] = f"v{version_num}"
    
    # Set changelog
    report_data["report_meta"]["changelog"] = "Manual screenshot update via OCR parser"

def main():
    """Main execution"""
    if len(sys.argv) < 2:
        print("Usage: python update_stats_screenshot.py <screenshot1.png> [screenshot2.png] ...")
        print("\nExample: python update_stats_screenshot.py treb.png dp.png sandz.png sy.png rosso.png")
        print("\nThe tool will extract stats from each screenshot and update report_data.json")
        return
    
    screenshot_files = sys.argv[1:]
    
    # Load report_data.json
    report_file = Path(__file__).parent / "report_data.json"
    if not report_file.exists():
        print(f"Error: {report_file} not found")
        return
    
    with open(report_file, 'r') as f:
        report_data = json.load(f)
    
    print("Starting screenshot-based stats update...")
    
    success_count = 0
    for screenshot_path in screenshot_files:
        # Try to match player name from filename
        filename = Path(screenshot_path).stem.lower()
        
        matched_player = None
        for player in PLAYERS:
            if player.lower() in filename or filename in player.lower():
                matched_player = player
                break
        
        if not matched_player:
            print(f"⚠ Could not determine player from filename: {screenshot_path}")
            continue
        
        success, message = process_player_screenshot(matched_player, screenshot_path, report_data)
        print(message)
        if success:
            success_count += 1
    
    if success_count == 0:
        print("No stats were updated.")
        return
    
    # Update metadata
    update_report_metadata(report_data)
    
    # Save updated report
    with open(report_file, 'w') as f:
        json.dump(report_data, f, indent=2)
    
    print(f"\n✓ Updated {report_file}")
    print(f"  Updated {success_count} player(s)")
    print(f"  New version: {report_data['report_meta']['version']}")
    
    # Commit and push to GitHub
    try:
        subprocess.run(["git", "add", "report_data.json"], cwd=report_file.parent, check=True)
        subprocess.run(
            ["git", "commit", "-m", f"Update stats from screenshots - {success_count} player(s) updated"],
            cwd=report_file.parent,
            check=True
        )
        subprocess.run(["git", "push"], cwd=report_file.parent, check=True)
        print("✓ Pushed to GitHub")
    except subprocess.CalledProcessError as e:
        print(f"⚠ Git operation failed: {e}")

if __name__ == "__main__":
    main()

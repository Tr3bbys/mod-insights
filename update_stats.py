#!/usr/bin/env python3
"""
CS2 Stats Scraper for csstats.gg
Automatically updates report_data.json with latest player statistics
"""

import json
import re
from datetime import datetime
from pathlib import Path
import requests
from bs4 import BeautifulSoup

# Player data mapping
PLAYERS = {
    "dP^": {
        "url": "https://csstats.gg/player/76561197990464640",
        "display_name": "dP^"
    },
    "rosso": {
        "url": "https://csstats.gg/player/76561197972387400",
        "display_name": "rosso"
    },
    "Sandz": {
        "url": "https://csstats.gg/player/76561197961207897",
        "display_name": "Sandz"
    },
    "Sy": {
        "url": "https://csstats.gg/player/76561197961295544",
        "display_name": "Sy"
    },
    "Treb": {
        "url": "https://csstats.gg/player/76561197976215376",
        "display_name": "Treb"
    }
}

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

def scrape_player_stats(url):
    """Scrape player stats from csstats.gg"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        stats = {}
        
        # Try to extract stats from the page
        # Look for stat containers with specific patterns
        stat_elements = soup.find_all('div', class_=re.compile('stat|metric'))
        
        # Extract key metrics
        # This is a simplified approach - you may need to adjust based on actual HTML structure
        for element in soup.find_all('div'):
            text = element.get_text(strip=True)
            
            # Look for games/matches played
            if 'played' in text.lower() or 'matches' in text.lower():
                numbers = re.findall(r'\d+', text)
                if numbers and 'games' not in stats:
                    stats['games'] = int(numbers[0])
            
            # Look for K/D ratio
            if 'k/d' in text.lower() or 'kd' in text.lower():
                numbers = re.findall(r'[\d.]+', text)
                if numbers and 'kd' not in stats:
                    try:
                        stats['kd'] = float(numbers[0])
                    except:
                        pass
            
            # Look for HLTV rating
            if 'hltv' in text.lower() or 'rating' in text.lower():
                numbers = re.findall(r'[\d.]+', text)
                if numbers and 'hltv_rating' not in stats:
                    try:
                        stats['hltv_rating'] = float(numbers[0])
                    except:
                        pass
            
            # Look for win/loss
            if 'win' in text.lower() or 'won' in text.lower():
                numbers = re.findall(r'\d+', text)
                if len(numbers) >= 1 and 'wins' not in stats:
                    stats['wins'] = int(numbers[0])
            
            if 'loss' in text.lower() or 'lost' in text.lower():
                numbers = re.findall(r'\d+', text)
                if len(numbers) >= 1 and 'losses' not in stats:
                    stats['losses'] = int(numbers[0])
        
        return stats
    
    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return {}

def update_report_data(old_data, new_stats):
    """Update report_data.json with new stats"""
    
    updated_stats = []
    changes_made = []
    
    for player_idx, player in enumerate(old_data.get("players", [])):
        player_name = player["name"]
        new_player_stats = new_stats.get(player_name, {})
        
        if not new_player_stats:
            updated_stats.append(player)
            continue
        
        # Update games
        old_games = player.get("games")
        new_games = new_player_stats.get("games", old_games)
        if new_games != old_games:
            player["games"] = new_games
            changes_made.append(f"{player_name}: {old_games} → {new_games} games")
        
        # Update tier based on new game count
        old_tier = player.get("tier")
        new_tier = get_tier(new_games)
        if new_tier != old_tier:
            player["tier"] = new_tier
            changes_made.append(f"{player_name}: tier {old_tier} → {new_tier}")
        
        # Update chart data values
        kd = new_player_stats.get("kd")
        hltv = new_player_stats.get("hltv_rating")
        wins = new_player_stats.get("wins")
        losses = new_player_stats.get("losses")
        
        if kd:
            old_data["chart_data"]["hltv_rating"][player_name] = hltv or player.get("hltv_rating", 1.0)
        
        updated_stats.append(player)
    
    old_data["players"] = updated_stats
    
    # Update metadata
    old_data["report_meta"]["date"] = datetime.now().strftime("%d %b %Y")
    old_data["report_meta"]["version"] = f"v{int(old_data['report_meta']['version'][1:]) + 1}"
    
    if changes_made:
        old_data["report_meta"]["changelog"] = "Auto-update: " + "; ".join(changes_made)
    
    return old_data

def main():
    """Main scraper execution"""
    print("Starting CS2 stats update...")
    
    # Scrape all players
    all_stats = {}
    for player_name, player_info in PLAYERS.items():
        print(f"Scraping {player_name}...")
        stats = scrape_player_stats(player_info["url"])
        if stats:
            all_stats[player_name] = stats
            print(f"  ✓ Got {stats.get('games', '?')} games, {stats.get('kd', '?')} K/D")
        else:
            print(f"  ✗ No stats extracted")
    
    # Load and update report_data.json
    report_file = Path(__file__).parent / "report_data.json"
    
    if not report_file.exists():
        print(f"Error: {report_file} not found")
        return False
    
    with open(report_file, 'r') as f:
        report_data = json.load(f)
    
    # Update with new stats
    report_data = update_report_data(report_data, all_stats)
    
    # Save updated file
    with open(report_file, 'w') as f:
        json.dump(report_data, f, indent=2)
    
    print(f"\n✓ Updated {report_file}")
    print(f"  Changelog: {report_data['report_meta']['changelog']}")
    
    return True

if __name__ == "__main__":
    main()

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
from typing import Dict, Any, List, Tuple, Optional
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

# Set Tesseract path (Windows)
import platform
if platform.system() == "Windows":
    import os
    # Try default path first
    default_path = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
    if os.path.exists(default_path):
        pytesseract.pytesseract.pytesseract_cmd = default_path
    # Also try to add to PATH environment variable if not already there
    if r'Tesseract-OCR' not in os.environ.get('PATH', ''):
        os.environ['PATH'] += r';C:\Program Files\Tesseract-OCR'

PLAYERS = ["dP^", "rosso", "Sandz", "Sy", "Treb"]

# Filenames can't carry the "^" in dP^'s name, so it needs an explicit alias
# to match screenshot filenames like dp_stats.png.
PLAYER_ALIASES = {
    "dP^": ["dp"],
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

def preprocess_image(image_path):
    """Preprocess image for better OCR accuracy.

    Tested against a real csstats.gg screenshot: plain grayscale + a 2x
    upscale reads cleanly ("PLAYED 54", "WON 27", "LOST 26", ...), while a
    heavier bilateral/CLAHE/adaptive-threshold/morphology pipeline destroyed
    the text entirely (empty OCR output). Keep this minimal unless a specific
    screenshot is shown to need more.
    """
    img = cv2.imread(str(image_path))

    if img is None:
        return None

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    h, w = gray.shape
    upscaled = cv2.resize(gray, (w * 2, h * 2), interpolation=cv2.INTER_CUBIC)

    return upscaled

def extract_text_from_screenshot(image_path):
    """Extract all text from screenshot using OCR"""
    try:
        # Preprocess image
        processed_img = preprocess_image(image_path)
        if processed_img is None:
            print(f"Error extracting text from {image_path}: could not read image file")
            return ""

        # Convert back to PIL Image for pytesseract
        pil_img = Image.fromarray(processed_img)
        
        # Extract text
        text = pytesseract.image_to_string(pil_img)
        return text
    except Exception as e:
        print(f"Error extracting text from {image_path}: {e}")
        return ""

def extract_with_layout(image_path):
    """Extract both flattened text and per-word bounding boxes from a screenshot.

    A single OCR pass (image_to_data) covers both needs, avoiding a second
    Tesseract invocation. Used by any tab whose labels and values aren't
    text-adjacent in image_to_string's reading order (STATS card values sit
    in an icon/ring below their label; PLAYED WITH table cells can have
    extra/missing OCR noise tokens that break simple column sequencing) -
    the word boxes let the parser match a value to its column by position
    instead of by text order.
    """
    processed_img = preprocess_image(image_path)
    if processed_img is None:
        print(f"Error extracting text from {image_path}: could not read image file")
        return "", []

    try:
        pil_img = Image.fromarray(processed_img)
        data = pytesseract.image_to_data(pil_img, output_type=pytesseract.Output.DICT)
    except Exception as e:
        print(f"Error extracting text from {image_path}: {e}")
        return "", []

    words = []
    lines: Dict[Tuple[int, int, int], List[Tuple[int, str]]] = {}
    line_tops: Dict[Tuple[int, int, int], int] = {}
    for i in range(len(data['text'])):
        t = data['text'][i].strip()
        if not t:
            continue
        left, top, w, h = data['left'][i], data['top'][i], data['width'][i], data['height'][i]
        key = (data['block_num'][i], data['par_num'][i], data['line_num'][i])
        words.append({
            'text': t,
            'left': left, 'top': top, 'width': w, 'height': h,
            'right': left + w, 'bottom': top + h,
            'cx': left + w / 2, 'cy': top + h / 2,
            'conf': int(float(data['conf'][i])),
            'line_key': key,
        })
        lines.setdefault(key, []).append((left, t))
        line_tops.setdefault(key, top)

    ordered_keys = sorted(lines.keys(), key=lambda k: line_tops[k])
    text = '\n'.join(' '.join(w for _, w in sorted(lines[k], key=lambda p: p[0])) for k in ordered_keys)

    return text, words

def _find_value_below_label(words: List[Dict], label_text: str, used_ids: set,
                             x_tolerance=250, max_y_gap=450, min_conf=40) -> Optional[str]:
    """Find the numeric token positioned nearest below a label word (exact, case-sensitive match).

    Handles STATS-card layouts where a value is rendered inside an icon/ring
    below its label rather than immediately after it in the text stream.
    Low-confidence OCR noise is excluded (a garbled token can otherwise sit
    closer to the label than the real value), and a token is claimed for at
    most one field via used_ids so two adjacent stat cards can't both match
    the same number.
    """
    label = next((w for w in words if w['text'] == label_text), None)
    if not label:
        return None

    best = None
    best_key = None  # (vertical_gap, horizontal_distance) - lexicographically smallest wins
    for w in words:
        if w is label or id(w) in used_ids or w['conf'] < min_conf:
            continue
        if w['top'] <= label['bottom']:
            continue
        gap = w['top'] - label['bottom']
        dx = abs(w['cx'] - label['cx'])
        if gap > max_y_gap or dx > x_tolerance:
            continue
        if not re.search(r'[0-9]', w['text']):
            continue
        key = (gap, dx)
        if best_key is None or key < best_key:
            best, best_key = w, key

    if best is None:
        return None
    used_ids.add(id(best))
    m = re.search(r'([0-9]{1,4}(?:\.[0-9]{1,2})?)', best['text'])
    return m.group(1) if m else None

# Plausible ranges for STATS-card fields - anything outside these is an OCR
# misread, not a real CS2 stat (a real screenshot never has e.g. K/D 17.0 or
# HLTV rating 9.99 over any meaningful sample).
_STAT_BOUNDS = {
    'kd': (0.0, 5.0),
    'hltv_rating': (0.0, 3.0),
    'win_rate': (0, 100),
    'hs_percent': (0, 100),
    'adr': (0, 300),
    'clutch_success': (0, 100),
}

def _drop_implausible(stats: Dict[str, Any]) -> None:
    """Remove any field whose value falls outside _STAT_BOUNDS, in place."""
    for field, (lo, hi) in _STAT_BOUNDS.items():
        if field in stats and not (lo <= stats[field] <= hi):
            print(f"  ⚠ Discarding implausible {field}={stats[field]} (outside {lo}-{hi}) - likely an OCR misread")
            del stats[field]

def parse_stats_tab(text: str, words: Optional[List[Dict]] = None) -> Dict[str, Any]:
    """Parse STATS tab content - improved for OCR noise and layout quirks

    Strategy:
    - Prefer explicit 'PLAYED' matches for games (common label on the STATS card)
    - Use local context when possible for K/D and HLTV rating (numbers near K/D label)
    - Apply sanity checks (ignore implausible game totals)
    """
    stats = {}

    # Normalize text (collapse whitespace)
    norm = re.sub(r'\s+', ' ', text)

    # 1) Prefer explicit "PLAYED <n>" (this appears on the STATS card)
    m = re.search(r'PLAYED\s*[:\-]?\s*(\d{1,4})', norm, re.IGNORECASE)
    if m:
        val = int(m.group(1))
        # sanity: ignore obviously large values (>1000)
        if val <= 1000:
            stats['games'] = val

    # 2) If not found, look for small-game totals near "WON/LOST/TIED" block
    if 'games' not in stats:
        m = re.search(r'WON\s*[:\-]?\s*(\d{1,3})\s+LOST\s*[:\-]?\s*(\d{1,3})', norm, re.IGNORECASE)
        if m:
            won = int(m.group(1)); lost = int(m.group(2))
            stats['wins'] = won
            stats['losses'] = lost
            tied_m = re.search(r'TIED\s*[:\-]?\s*(\d{1,3})', norm, re.IGNORECASE)
            tied = int(tied_m.group(1)) if tied_m else 0
            stats['games'] = won + lost + tied

    # 3) As a fallback, search for any small numeric labeled patterns (Games/Played) but avoid large values
    # Note: WINS is deliberately excluded here - a wins count is not a games-played total.
    if 'games' not in stats:
        fallback = re.search(r'(?:GAMES|PLAYED)\s*[:\-]?\s*(\d{1,4})', norm, re.IGNORECASE)
        if fallback:
            val = int(fallback.group(1))
            if val <= 1000:
                stats['games'] = val

    # 4) K/D & HLTV: always extract independently, anchored to their own labels.
    # (A shared "K/D <n> <n>" pattern was tried previously but silently grabbed
    # whatever decimal happened to follow K/D as the HLTV rating - unsafe.)
    kdm = re.search(r'(?:K/D|KD)\s*[:\-]?\s*([0-9]+\.[0-9]{1,2})', norm, re.IGNORECASE)
    if kdm:
        stats['kd'] = float(kdm.group(1))

    rdm = re.search(r'HLTV\s*RATING\s*[:\-]?\s*([0-9]+\.[0-9]{1,2})', norm, re.IGNORECASE)
    if rdm:
        stats['hltv_rating'] = float(rdm.group(1))

    # 5) Win rate, HS%, ADR, Clutch - flexible patterns
    m = re.search(r'WIN\s*RATE\s*[:\-]?\s*([0-9]{1,3})\s*%', norm, re.IGNORECASE)
    if m:
        stats['win_rate'] = int(m.group(1))

    m = re.search(r'HS%\s*[:\-]?\s*([0-9]{1,3})\s*%', norm, re.IGNORECASE)
    if m:
        stats['hs_percent'] = int(m.group(1))

    m = re.search(r'ADR\s*[:\-]?\s*(\d{1,4})', norm, re.IGNORECASE)
    if m:
        stats['adr'] = int(m.group(1))

    # Clutch (1vX aggregate specifically, not a per-round 1v1/1v2 breakdown)
    m = re.search(r'1v[xX]\s*[:\-]?\s*([0-9]{1,3})\s*%', norm, re.IGNORECASE)
    if m:
        stats['clutch_success'] = int(m.group(1))

    # 6) Positional fallback (requires word boxes from extract_with_layout).
    # On the real STATS card, K/D, HLTV RATING, WIN RATE, HS% and ADR each have
    # their value rendered inside an icon/ring *below* the label rather than
    # immediately after it in reading order, so the text-adjacency regexes
    # above never fire for them. Locate the nearest number below each label.
    if words:
        used_ids: set = set()
        if 'kd' not in stats:
            v = _find_value_below_label(words, 'K/D', used_ids)
            if v:
                stats['kd'] = float(v)
        if 'hltv_rating' not in stats:
            v = _find_value_below_label(words, 'HLTV', used_ids)
            if v:
                stats['hltv_rating'] = float(v)
        if 'win_rate' not in stats:
            v = _find_value_below_label(words, 'RATE', used_ids)
            if v:
                stats['win_rate'] = int(float(v))
        if 'hs_percent' not in stats:
            v = _find_value_below_label(words, 'HS%', used_ids)
            if v:
                stats['hs_percent'] = int(float(v))
        if 'adr' not in stats:
            v = _find_value_below_label(words, 'ADR', used_ids)
            if v:
                stats['adr'] = int(float(v))

    # 7) Sanity bound every value regardless of which path (regex or
    # positional) produced it. OCR can misread a digit and turn e.g. a real
    # "1.00" K/D into "17.0", or a real 88 ADR into something absurd - this
    # doesn't fix the misread, it just refuses to trust a number that's
    # outside what's actually possible in CS2 rather than silently writing
    # it into report_data.json. Verified against real screenshots: this is
    # exactly what let rosso's K/D (17.0) and Sandz's (9.99) through before.
    _drop_implausible(stats)

    return stats

def _ocr_digit_column(pre_image, x0, x1, y0=330, y1=None, scale=3) -> List[Tuple[int, float]]:
    """OCR a narrow numeric column in isolation: crop + upscale + digit whitelist.

    Full-page OCR of the WEAPONS tab misreads most numeric cells as garbage
    (weapon icons bleed into the tiny digit glyphs). Isolating one column at
    a time, upscaling further, and restricting Tesseract to digits recovers
    real numbers from cells that were previously unreadable - verified
    against a real screenshot (recovered 8/19 Kills values that were 100%
    garbage before). Still incomplete: roughly half of rows remain
    unreadable even with this, since some cells are visually obscured by
    the weapon icon rather than just low-resolution.
    """
    y1 = y1 or pre_image.shape[0]
    crop = pre_image[y0:y1, x0:x1]
    h, w = crop.shape
    upscaled = cv2.resize(crop, (w * scale, h * scale), interpolation=cv2.INTER_CUBIC)
    data = pytesseract.image_to_data(
        Image.fromarray(upscaled),
        config='--psm 4 -c tessedit_char_whitelist=0123456789',
        output_type=pytesseract.Output.DICT,
    )
    out = []
    for i in range(len(data['text'])):
        t = data['text'][i].strip()
        if t:
            out.append((int(t), data['top'][i] / scale + y0))
    return out

# Non-weapon labels that sometimes appear in the name column (e.g. an
# attachment/silencer toggle rendered as its own line) and would otherwise
# get mistaken for a weapon row during nearest-row matching.
_WEAPON_NAME_BLOCKLIST = ('silence', 'silencer', 'off', 'on')

def parse_weapons_tab(image_path) -> List[Dict[str, Any]]:
    """Parse WEAPONS tab content from the screenshot at image_path.

    Coverage is partial by nature of the source image (see
    _ocr_digit_column) - most rows will be missing one or more of
    kills/hs/accuracy, and a handful of names are unrecoverable. Rows with
    no name AND no kills value are dropped as pure noise; everything else
    is returned even if incomplete, since a partial reading (e.g. kills
    with no name) is still useful.
    """
    pre_image = preprocess_image(image_path)
    if pre_image is None:
        return []

    kills = _ocr_digit_column(pre_image, 1050, 1160)
    hs = _ocr_digit_column(pre_image, 1180, 1290)
    accuracy = _ocr_digit_column(pre_image, 1790, 1970)

    _, words = extract_with_layout(image_path)
    name_lines: Dict[Tuple, List[Dict]] = {}
    for w in words:
        if 690 < w['left'] < 1020 and w['top'] > 330:
            name_lines.setdefault(w['line_key'], []).append(w)

    names: List[Tuple[str, float]] = []
    for ws in name_lines.values():
        if max(w['conf'] for w in ws) <= 5:
            continue  # nothing legible at all on this line
        text_val = ' '.join(w['text'] for w in sorted(ws, key=lambda w: w['left']))
        if len(text_val.strip()) < 2:
            continue
        if any(bad in text_val.lower() for bad in _WEAPON_NAME_BLOCKLIST):
            continue
        names.append((text_val, min(w['top'] for w in ws)))

    def nearest(rows, top, tol=45):
        best, best_dist = None, None
        for value, row_top in rows:
            dist = abs(row_top - top)
            if dist <= tol and (best_dist is None or dist < best_dist):
                best, best_dist = value, dist
        return best

    # Canonical rows = every observed row top (from any column), merged
    # where two are within 40px of each other (accounts for slight OCR
    # jitter between columns for what's really the same table row).
    all_tops = sorted({t for _, t in names} | {t for _, t in kills}
                       | {t for _, t in hs} | {t for _, t in accuracy})
    clusters: List[List[float]] = []
    for t in all_tops:
        if clusters and abs(t - clusters[-1][-1]) < 40:
            clusters[-1].append(t)
        else:
            clusters.append([t])
    row_centers = [sum(c) / len(c) for c in clusters]

    weapons = []
    for row_top in row_centers:
        weapon_name = nearest(names, row_top)
        weapon_kills = nearest(kills, row_top)
        if weapon_name is None and weapon_kills is None:
            continue
        entry: Dict[str, Any] = {'weapon': weapon_name, 'kills': weapon_kills}
        weapon_hs = nearest(hs, row_top)
        if weapon_hs is not None:
            entry['hs'] = weapon_hs
        weapon_acc = nearest(accuracy, row_top)
        if weapon_acc is not None:
            entry['accuracy'] = weapon_acc
        weapons.append(entry)

    return weapons

def parse_played_with_tab(text: str, words: Optional[List[Dict]] = None) -> List[Dict[str, Any]]:
    """Parse PLAYED WITH tab content.

    The table has clean row structure (each teammate is one OCR line) but a
    variable, unpredictable number of stray/garbled tokens per row (extra
    reference numbers in parentheses, misread glyphs), so matching columns
    by sequence position (1st number = K/D, 2nd = win rate, ...) breaks
    constantly. Instead this locates each column header once, then for each
    row picks whichever nearby number sits closest to that header's x
    position - the same technique used for the STATS card.

    Caveat: teammate names are frequently prefixed with a garbled avatar
    icon glyph (e.g. "sy SandZ", "@ HunteR") since Tesseract reads the
    circular avatar image as stray characters - names should be treated as
    best-effort, not exact. Numeric columns are generally reliable except
    where the source screenshot itself renders a value illegibly.
    """
    if not words:
        return []

    header_row = {}
    for label, name, top_lo, top_hi in [
        ('games', 'Games', 400, 500),
        ('kd', 'K/D', 400, 500),
        ('win_rate', 'Win', 400, 500),
        ('adr', 'ADR', 400, 500),
        ('hs_percent', 'HS%', 400, 500),
        ('rating', 'Rating', 400, 500),
    ]:
        cand = [w for w in words if w['text'] == name and top_lo < w['top'] < top_hi]
        if cand:
            header_row[label] = cand[0]

    if 'games' not in header_row:
        return []  # header row wasn't found at all - layout unrecognized, don't guess

    games_col_left = header_row['games']['left']

    date_re = re.compile(r'\d{1,2}(?:st|nd|rd|th)\s+[A-Za-z]{3}\s+20\d{2}')

    rows: Dict[Tuple, List[Dict]] = {}
    for w in words:
        rows.setdefault(w['line_key'], []).append(w)

    def nearest_in_row(row_words, colname, x_tolerance=110, min_conf=40):
        if colname not in header_row:
            return None
        hcx = header_row[colname]['cx']
        best, best_dx = None, None
        for w in row_words:
            if w['text'].startswith('(') or w['text'].endswith(')'):
                continue  # parenthetical values are a reference/comparison number, not this row's value
            if w['conf'] < min_conf or not re.search(r'[0-9]', w['text']):
                continue
            dx = abs(w['cx'] - hcx)
            if dx > x_tolerance:
                continue
            if best_dx is None or dx < best_dx:
                best, best_dx = w, dx
        if best is None:
            return None
        m = re.search(r'([0-9]{1,4}(?:\.[0-9]{1,2})?)', best['text'])
        return m.group(1) if m else None

    teammates = []
    for key, row_words in rows.items():
        row_text = ' '.join(w['text'] for w in sorted(row_words, key=lambda w: w['left']))
        if not date_re.search(row_text):
            continue
        if 'Wins:' in row_text or 'RANK' in row_text or 'Overall' in row_text:
            continue  # sidebar leaderboard noise, not a table row

        name_tokens = [w['text'] for w in sorted(row_words, key=lambda w: w['left'])
                        if w['left'] < games_col_left - 80]
        name = ' '.join(name_tokens).strip()
        if not name:
            continue

        entry: Dict[str, Any] = {'name': name}
        games = nearest_in_row(row_words, 'games')
        if games:
            entry['games_together'] = int(games)
        # kd/rating sanity bound: a dropped decimal point (OCR reading "1.33"
        # as "133") produces an implausible value, easier to catch here than
        # to fix at the OCR level - real K/D and HLTV ratings don't exceed ~5.
        kd = nearest_in_row(row_words, 'kd')
        if kd and float(kd) <= 5:
            entry['kd'] = float(kd)
        win_rate = nearest_in_row(row_words, 'win_rate')
        if win_rate:
            entry['win_rate'] = int(win_rate)
        adr = nearest_in_row(row_words, 'adr')
        if adr:
            entry['adr'] = int(adr)
        hs = nearest_in_row(row_words, 'hs_percent')
        if hs:
            entry['hs_percent'] = int(hs)
        rating = nearest_in_row(row_words, 'rating')
        if rating and float(rating) <= 5:
            entry['rating'] = float(rating)

        teammates.append(entry)

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
            if 'hltv_rating' in stats:
                report_data["chart_data"]["hltv_rating"][player_name] = stats['hltv_rating']
            
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
        print("\nExample with multiple tabs per player:")
        print("  python update_stats_screenshot.py treb_stats.png treb_weapons.png treb_played_with.png \\")
        print("                                     dp_stats.png dp_weapons.png dp_played_with.png ...")
        print("\nOr with wildcards:")
        print("  python update_stats_screenshot.py treb_*.png dp_*.png sandz_*.png sy_*.png rosso_*.png")
        print("\nSupported tab types: stats, weapons, played_with (matches tab optional)")
        print("\nThe tool will extract all data from screenshots and update report_data.json")
        return
    
    screenshot_files = sys.argv[1:]
    
    # Load report_data.json
    report_file = Path(__file__).parent / "report_data.json"
    if not report_file.exists():
        print(f"Error: {report_file} not found")
        return
    
    print("Starting screenshot-based stats update...")
    print("Screenshots to process:", len(screenshot_files))
    
    success_count = 0
    player_data = {player: {} for player in PLAYERS}  # Track data per player
    # Fields whose absence would otherwise be silent - a missing 'games' just
    # leaves the prior value in report_data.json in place with no signal
    # beyond a "?" in the per-screenshot print line above, which is exactly
    # how Treb's games count sat stale at 54 (actually 63) for a full cycle.
    review_warnings: List[str] = []
    
    for screenshot_path in screenshot_files:
        # Try to match player name from filename
        filename = Path(screenshot_path).stem.lower()
        
        matched_player = None
        matched_tab = None
        
        # Match player name
        for player in PLAYERS:
            candidates = [player.lower()] + PLAYER_ALIASES.get(player, [])
            if any(c in filename or filename.startswith(c) for c in candidates):
                matched_player = player
                break
        
        # Match tab type
        if 'stats' in filename or 'stat' in filename:
            matched_tab = 'stats'
        elif 'weapon' in filename:
            matched_tab = 'weapons'
        elif 'played' in filename or 'with' in filename:
            matched_tab = 'played_with'
        elif 'match' in filename:
            matched_tab = 'matches'
        
        if not matched_player:
            print(f"⚠ Could not determine player from filename: {screenshot_path}")
            continue
        
        print(f"\n→ Processing {matched_player} [{matched_tab or 'unknown'}]...")
        
        if not Path(screenshot_path).exists():
            print(f"  ✗ File not found: {screenshot_path}")
            continue
        
        # weapons parses the screenshot directly (needs isolated per-column
        # OCR passes, not the shared text/word extraction used below)
        if matched_tab == 'weapons':
            weapons = parse_weapons_tab(screenshot_path)
            if weapons:
                player_data[matched_player]['weapons'] = weapons
                print(f"  ✓ Weapons: {len(weapons)} weapon rows extracted (partial - see README)")
                success_count += 1
            else:
                print(f"  ✗ Could not parse weapons")
            continue

        # Extract text from image (stats and played_with tabs also need word
        # positions - see extract_with_layout docstring for why)
        if matched_tab in ('stats', 'played_with'):
            text, words = extract_with_layout(screenshot_path)
        else:
            text = extract_text_from_screenshot(screenshot_path)
            words = None
        if not text:
            print(f"  ✗ Could not extract text from image")
            continue

        # Parse based on tab type
        if matched_tab == 'stats':
            stats = parse_stats_tab(text, words)
            if stats:
                player_data[matched_player]['stats'] = stats
                print(f"  ✓ Stats: {stats.get('games', '?')} games, {stats.get('kd', '?')} K/D, {stats.get('hltv_rating', '?')} rating")
                success_count += 1
                for field in ('games', 'kd', 'hltv_rating'):
                    if field not in stats:
                        review_warnings.append(
                            f"{matched_player}: could not read '{field}' from {screenshot_path} - "
                            f"existing value in report_data.json was left unchanged"
                        )
            else:
                print(f"  ✗ Could not parse stats")
                review_warnings.append(f"{matched_player}: STATS screenshot ({screenshot_path}) produced no readable data at all")

        elif matched_tab == 'played_with':
            teammates = parse_played_with_tab(text, words)
            if teammates:
                player_data[matched_player]['teammates'] = teammates
                print(f"  ✓ Teammates: {len(teammates)} players extracted")
                success_count += 1
            else:
                print(f"  ✗ Could not parse teammates")
    
    if success_count == 0:
        print("\n✗ No stats were extracted.")
        return
    
    print(f"\n✓ Extracted data from {success_count} screenshots")
    
    # Update report_data.json with all collected data
    print("\nUpdating report_data.json...")
    
    with open(report_file, 'r') as f:
        report_data = json.load(f)
    
    for player_name, data in player_data.items():
        if not data:
            continue
        
        # Find player in report_data
        for player in report_data.get("players", []):
            if player["name"] == player_name:
                # Update stats
                if 'stats' in data:
                    stats = data['stats']
                    if 'games' in stats:
                        player['games'] = stats['games']
                    if 'kd' in stats:
                        player['kd'] = stats['kd']
                    if 'hltv_rating' in stats:
                        player['hltv_rating'] = stats['hltv_rating']
                        report_data.setdefault("chart_data", {}).setdefault("hltv_rating", {})[player_name] = stats['hltv_rating']
                    
                    # Update tier based on games
                    if 'games' in stats:
                        new_tier = get_tier(stats['games'])
                        if new_tier != player.get("tier"):
                            player["tier"] = new_tier
                
                # Raw OCR data, stored separately from the hand-written
                # best_t_weapon/best_ct_weapon/weapon_note fields above -
                # this doesn't touch or replace that curated commentary.
                if 'weapons' in data:
                    player['weapon_stats'] = data['weapons']
                if 'teammates' in data:
                    player['teammates'] = data['teammates']

                break
    
    # Update metadata
    update_report_metadata(report_data)
    
    # Save updated report
    with open(report_file, 'w') as f:
        json.dump(report_data, f, indent=2)
    
    print(f"\n✓ Updated {report_file}")
    print(f"  Updated {success_count} player(s)")
    print(f"  New version: {report_data['report_meta']['version']}")

    if review_warnings:
        print("\n" + "=" * 60)
        print(f"⚠ REVIEW NEEDED - {len(review_warnings)} field(s) could not be read from screenshots:")
        print("=" * 60)
        for w in review_warnings:
            print(f"  - {w}")
        print("These are still whatever value was already in report_data.json before")
        print("this run - not necessarily current. Check the screenshot by eye and")
        print("correct manually if needed before trusting this update.")
        print("=" * 60)

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

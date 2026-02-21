import csv
import re
from pathlib import Path
import time
import random
import requests

player_info_file = Path(__file__).parent / "player_info_with_urls.csv"
output_file = Path(__file__).parent / "player_styles.csv"

print("=" * 60)
print("Fetching batting/bowling styles via Wayback Machine")
print("=" * 60)

# Load already-fetched successful results
already_fetched = {}
if output_file.exists():
    with open(output_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = row.get('Player_Name', '').strip()
            status = row.get('Status', '')
            if name and 'Error' not in status and 'HTTP' not in status and 'Not in' not in status:
                already_fetched[name] = row
    print(f"Loaded {len(already_fetched)} previously fetched results (will skip these)")

# Read player info with URLs
players = []
with open(player_info_file, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        players.append(row)

print(f"Total players: {len(players)}")
print(f"Remaining to fetch: {len(players) - len(already_fetched)}\n")

FIELDNAMES = ['Player_Name', 'Batting_Style', 'Bowling_Style', 'URL', 'Status']

results = list(already_fetched.values())
success_count = len(already_fetched)
failed_count = 0

session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
})

def extract_styles(text):
    """Extract batting and bowling styles from page text."""
    batting_style = 'N/A'
    bowling_style = 'N/A'
    
    # Method 1: Look for structured label-value pairs in HTML
    bat_match = re.search(r'BATTING STYLE\s*\n\s*\n\s*(.+?)(?:\n|$)', text, re.IGNORECASE)
    if bat_match:
        val = bat_match.group(1).strip()
        if val and len(val) < 80:
            batting_style = val
    
    bowl_match = re.search(r'BOWLING STYLE\s*\n\s*\n\s*(.+?)(?:\n|$)', text, re.IGNORECASE)
    if bowl_match:
        val = bowl_match.group(1).strip()
        if val and len(val) < 80:
            bowling_style = val
    
    # Method 2: Try HTML tag-based extraction
    if batting_style == 'N/A':
        bat_match2 = re.search(r'Batting Style</[^>]+>\s*<[^>]+>(.*?)</[^>]+>', text, re.IGNORECASE | re.DOTALL)
        if bat_match2:
            val = re.sub(r'<[^>]+>', '', bat_match2.group(1)).strip()
            if val:
                batting_style = val
    
    if bowling_style == 'N/A':
        bowl_match2 = re.search(r'Bowling Style</[^>]+>\s*<[^>]+>(.*?)</[^>]+>', text, re.IGNORECASE | re.DOTALL)
        if bowl_match2:
            val = re.sub(r'<[^>]+>', '', bowl_match2.group(1)).strip()
            if val:
                bowling_style = val
    
    # Method 3: Strip HTML and do line-by-line
    if batting_style == 'N/A' or bowling_style == 'N/A':
        clean = re.sub(r'<[^>]+>', '\n', text)
        lines = [l.strip() for l in clean.split('\n') if l.strip()]
        for i, line in enumerate(lines):
            upper = line.upper()
            if upper == 'BATTING STYLE' and i + 1 < len(lines):
                if batting_style == 'N/A':
                    batting_style = lines[i + 1][:80]
            if upper == 'BOWLING STYLE' and i + 1 < len(lines):
                if bowling_style == 'N/A':
                    bowling_style = lines[i + 1][:80]
    
    return batting_style, bowling_style

def save_results():
    """Save current results to CSV."""
    if results:
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
            writer.writeheader()
            writer.writerows(results)

def get_key_cricinfo(url):
    """Extract the numeric ID from an ESPN URL."""
    match = re.search(r'-(\d+)$', url)
    return match.group(1) if match else None

def find_wayback_url(original_url, key_id):
    """Use Wayback CDX API to find a valid snapshot URL."""
    # Try direct URL first
    urls_to_try = [
        f"https://web.archive.org/web/2024/{original_url}",
        f"https://web.archive.org/web/2025/{original_url}",
        f"https://web.archive.org/web/2023/{original_url}",
    ]
    
    # Also try CDX API to find any snapshot with this player ID
    if key_id:
        try:
            cdx_url = f"https://web.archive.org/cdx/search/cdx?url=www.espncricinfo.com/cricketers/*-{key_id}&output=json&limit=1&filter=statuscode:200"
            cdx_resp = session.get(cdx_url, timeout=10)
            if cdx_resp.status_code == 200:
                data = cdx_resp.json()
                if len(data) > 1:  # First row is header
                    timestamp = data[1][1]
                    archived_url = data[1][2]
                    wayback = f"https://web.archive.org/web/{timestamp}/{archived_url}"
                    urls_to_try.insert(0, wayback)  # Try CDX result first
        except Exception:
            pass
    
    return urls_to_try

consecutive_errors = 0

for idx, player in enumerate(players, 1):
    player_name = player['Player_Name']
    original_url = player['ESPN_URL']
    
    if player_name in already_fetched:
        continue
    
    key_id = get_key_cricinfo(original_url)
    urls_to_try = find_wayback_url(original_url, key_id)
    
    try:
        print(f"[{idx}/{len(players)}] {player_name}...", end=' ', flush=True)
        
        fetched = False
        for wb_url in urls_to_try:
            try:
                resp = session.get(wb_url, timeout=20, allow_redirects=True)
                if resp.status_code == 200:
                    batting_style, bowling_style = extract_styles(resp.text)
                    
                    result = {
                        'Player_Name': player_name,
                        'Batting_Style': batting_style,
                        'Bowling_Style': bowling_style,
                        'URL': original_url,
                        'Status': 'Success' if batting_style != 'N/A' or bowling_style != 'N/A' else 'No style info'
                    }
                    results.append(result)
                    success_count += 1
                    consecutive_errors = 0
                    fetched = True
                    
                    if batting_style != 'N/A' or bowling_style != 'N/A':
                        print(f"OK  Bat: {batting_style} | Bowl: {bowling_style}")
                    else:
                        print("OK (no style info on page)")
                    break
            except Exception:
                continue
        
        if not fetched:
            result = {
                'Player_Name': player_name,
                'Batting_Style': 'N/A',
                'Bowling_Style': 'N/A',
                'URL': original_url,
                'Status': 'Not in Wayback'
            }
            results.append(result)
            failed_count += 1
            consecutive_errors += 1
            print("NOT FOUND")
    
    except Exception as e:
        result = {
            'Player_Name': player_name,
            'Batting_Style': 'N/A',
            'Bowling_Style': 'N/A',
            'URL': original_url,
            'Status': f'Error: {str(e)[:80]}'
        }
        results.append(result)
        failed_count += 1
        consecutive_errors += 1
        print(f"ERR: {str(e)[:50]}")
    
    # Save progress every 25 players
    if len(results) % 25 == 0:
        save_results()
        print(f"        [Progress saved: {len(results)} players]")
    
    # Throttle
    if consecutive_errors >= 10:
        print("    [Pausing 15s...]")
        time.sleep(15)
        consecutive_errors = 0
    else:
        time.sleep(random.uniform(1.0, 2.0))

# Final save
save_results()

print("\n" + "=" * 60)
print(f"Results saved to: {output_file}")
print(f"  Successful: {success_count}")
print(f"  Failed: {failed_count}")
print(f"  Total: {len(results)}")
print("=" * 60)
print("\nNEXT STEP: Run extract_to_csv.py to create final ball-by-ball CSV")

"""
Fast batch fetcher using concurrent requests to Wayback Machine.
Discovers canonical ESPN URLs via CDX API, then fetches snapshots in parallel.
Fills in any players not yet in player_styles.csv.
"""
import csv
import re
import json
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import requests

BASE_DIR = Path(__file__).parent
player_info_file = BASE_DIR / "player_info_with_urls.csv"
output_file = BASE_DIR / "player_styles.csv"

print("=" * 60)
print("Fast Wayback Machine batch fetcher (concurrent)")
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
    print(f"Already fetched: {len(already_fetched)} players")

# Read all players
players = []
with open(player_info_file, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        players.append(row)

# Filter to only remaining
remaining = [p for p in players if p['Player_Name'] not in already_fetched]
print(f"Total players: {len(players)}")
print(f"Remaining: {len(remaining)}")

if not remaining:
    print("All players already fetched!")
    exit()

FIELDNAMES = ['Player_Name', 'Batting_Style', 'Bowling_Style', 'URL', 'Status']

def extract_key_id(url):
    m = re.search(r'-(\d+)$', url)
    return m.group(1) if m else None

def extract_styles(text):
    batting_style = 'N/A'
    bowling_style = 'N/A'
    
    # Method 1: HTML tags
    bat_match = re.search(r'(?:BATTING STYLE|Batting Style)</[^>]+>\s*<[^>]+>(.*?)</[^>]+>', text, re.IGNORECASE | re.DOTALL)
    if bat_match:
        val = re.sub(r'<[^>]+>', '', bat_match.group(1)).strip()
        if val and len(val) < 80:
            batting_style = val
    
    bowl_match = re.search(r'(?:BOWLING STYLE|Bowling Style)</[^>]+>\s*<[^>]+>(.*?)</[^>]+>', text, re.IGNORECASE | re.DOTALL)
    if bowl_match:
        val = re.sub(r'<[^>]+>', '', bowl_match.group(1)).strip()
        if val and len(val) < 80:
            bowling_style = val
    
    # Method 2: Plain text
    if batting_style == 'N/A' or bowling_style == 'N/A':
        clean = re.sub(r'<[^>]+>', '\n', text)
        lines = [l.strip() for l in clean.split('\n') if l.strip()]
        for i, line in enumerate(lines):
            upper = line.upper().strip()
            if upper == 'BATTING STYLE' and i + 1 < len(lines) and batting_style == 'N/A':
                batting_style = lines[i + 1][:80]
            if upper == 'BOWLING STYLE' and i + 1 < len(lines) and bowling_style == 'N/A':
                bowling_style = lines[i + 1][:80]
    
    return batting_style, bowling_style

def find_and_fetch_player(player):
    """Find canonical Wayback URL via CDX and fetch the page."""
    name = player['Player_Name']
    url = player['ESPN_URL']
    key_id = extract_key_id(url)
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'text/html',
    })
    
    # Step 1: Try CDX API to find the canonical URL with this player ID
    canonical_url = None
    if key_id:
        try:
            cdx_resp = session.get(
                'https://web.archive.org/cdx/search/cdx',
                params={
                    'url': f'www.espncricinfo.com/cricketers/',
                    'matchType': 'prefix',
                    'filter': f'urlkey:.*-{key_id}$',
                    'output': 'json',
                    'limit': '1',
                    'fl': 'original,timestamp',
                    'filter': f'statuscode:200',
                },
                timeout=15
            )
            if cdx_resp.status_code == 200:
                try:
                    data = cdx_resp.json()
                    if len(data) > 1:
                        canonical_url = data[1][0]
                except (json.JSONDecodeError, IndexError):
                    pass
        except Exception:
            pass
    
    # Step 2: Build list of URLs to try
    urls_to_try = []
    if canonical_url:
        urls_to_try.append(f"https://web.archive.org/web/2024/{canonical_url}")
    urls_to_try.append(f"https://web.archive.org/web/2024/{url}")
    urls_to_try.append(f"https://web.archive.org/web/2025/{url}")
    urls_to_try.append(f"https://web.archive.org/web/2023/{url}")
    
    # Step 3: Try fetching
    for wb_url in urls_to_try:
        try:
            resp = session.get(wb_url, timeout=20, allow_redirects=True)
            if resp.status_code == 200 and len(resp.text) > 1000:
                batting_style, bowling_style = extract_styles(resp.text)
                if batting_style != 'N/A' or bowling_style != 'N/A':
                    return {
                        'Player_Name': name,
                        'Batting_Style': batting_style,
                        'Bowling_Style': bowling_style,
                        'URL': url,
                        'Status': 'Success'
                    }
        except Exception:
            continue
    
    # Step 4: Try Wikipedia as fallback
    try:
        wiki_resp = session.get(
            'https://en.wikipedia.org/w/api.php',
            params={
                'action': 'query',
                'titles': name.replace(' ', '_'),
                'prop': 'revisions',
                'rvprop': 'content',
                'rvsection': '0',
                'format': 'json',
                'rvlimit': '1'
            },
            timeout=10
        )
        if wiki_resp.status_code == 200:
            wiki_data = wiki_resp.json()
            pages = wiki_data.get('query', {}).get('pages', {})
            for page_id, page in pages.items():
                if page_id == '-1':
                    continue
                revisions = page.get('revisions', [])
                if revisions:
                    content = revisions[0].get('*', '')
                    batting_style = 'N/A'
                    bowling_style = 'N/A'
                    
                    bat_match = re.search(r'\|\s*batting\s*=\s*(.+?)(?:\n|\|)', content, re.IGNORECASE)
                    if bat_match:
                        batting_style = bat_match.group(1).strip()
                        # Clean wiki markup
                        batting_style = re.sub(r'\[\[([^\]|]+\|)?([^\]]+)\]\]', r'\2', batting_style)
                        batting_style = re.sub(r'\{\{.*?\}\}', '', batting_style).strip()
                        batting_style = batting_style[:80]
                    
                    bowl_match = re.search(r'\|\s*bowling\s*=\s*(.+?)(?:\n|\|)', content, re.IGNORECASE)
                    if bowl_match:
                        bowling_style = bowl_match.group(1).strip()
                        bowling_style = re.sub(r'\[\[([^\]|]+\|)?([^\]]+)\]\]', r'\2', bowling_style)
                        bowling_style = re.sub(r'\{\{.*?\}\}', '', bowling_style).strip()
                        bowling_style = bowling_style[:80]
                    
                    if batting_style != 'N/A' or bowling_style != 'N/A':
                        return {
                            'Player_Name': name,
                            'Batting_Style': batting_style,
                            'Bowling_Style': bowling_style,
                            'URL': url,
                            'Status': 'Success (Wikipedia)'
                        }
    except Exception:
        pass
    
    return {
        'Player_Name': name,
        'Batting_Style': 'N/A',
        'Bowling_Style': 'N/A',
        'URL': url,
        'Status': 'Not found'
    }

# Process in batches with thread pool
results = list(already_fetched.values())
new_success = 0
new_failed = 0
batch_size = 5

print(f"\nProcessing {len(remaining)} players in batches of {batch_size}...\n")

for batch_start in range(0, len(remaining), batch_size):
    batch = remaining[batch_start:batch_start + batch_size]
    
    with ThreadPoolExecutor(max_workers=batch_size) as executor:
        futures = {executor.submit(find_and_fetch_player, p): p for p in batch}
        for future in as_completed(futures):
            player = futures[future]
            try:
                result = future.result()
                results.append(result)
                if 'Success' in result['Status']:
                    new_success += 1
                    print(f"  OK  {result['Player_Name']}  Bat: {result['Batting_Style']} | Bowl: {result['Bowling_Style']}")
                else:
                    new_failed += 1
                    print(f"  --  {result['Player_Name']}: {result['Status']}")
            except Exception as e:
                new_failed += 1
                results.append({
                    'Player_Name': player['Player_Name'],
                    'Batting_Style': 'N/A',
                    'Bowling_Style': 'N/A',
                    'URL': player['ESPN_URL'],
                    'Status': f'Error: {str(e)[:60]}'
                })
                print(f"  ERR {player['Player_Name']}: {str(e)[:50]}")
    
    # Save progress after each batch
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(results)
    
    done = batch_start + len(batch)
    print(f"  [{done}/{len(remaining)}] saved ({len(results)} total)")
    
    # Small delay between batches
    time.sleep(1)

print(f"\n{'=' * 60}")
print(f"Results saved to: {output_file}")
print(f"  Previously fetched: {len(already_fetched)}")
print(f"  New successes: {new_success}")
print(f"  New failures: {new_failed}")
print(f"  Total: {len(results)}")
print(f"{'=' * 60}")

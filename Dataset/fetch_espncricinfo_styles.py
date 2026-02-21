import csv
import re
from pathlib import Path
import time
import random

try:
    import undetected_chromedriver as uc
except ImportError:
    import subprocess
    subprocess.check_call(['pip', 'install', 'undetected-chromedriver', 'setuptools'])
    import undetected_chromedriver as uc

player_info_file = Path(__file__).parent / "player_info_with_urls.csv"
output_file = Path(__file__).parent / "player_styles.csv"

print("=" * 60)
print("Fetching ESPN Cricinfo batting/bowling styles")
print("=" * 60)

# Load already-fetched results to support resuming
already_fetched = {}
if output_file.exists():
    with open(output_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = row.get('Player_Name', '').strip()
            status = row.get('Status', '')
            if name and 'Error' not in status and 'HTTP' not in status and status != "":
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

# Results list - start with already fetched data
results = list(already_fetched.values())
success_count = len(already_fetched)
failed_count = 0

FIELDNAMES = ['Player_Name', 'Batting_Style', 'Bowling_Style', 'URL', 'Status']

def extract_styles(html_text):
    """Extract batting and bowling styles from page HTML/text."""
    batting_style = 'N/A'
    bowling_style = 'N/A'
    
    # Try regex on HTML
    bat_match = re.search(r'Batting Style</[^>]+>\s*<[^>]+>(.*?)</[^>]+>', html_text, re.IGNORECASE | re.DOTALL)
    if bat_match:
        val = re.sub(r'<[^>]+>', '', bat_match.group(1)).strip()
        if val:
            batting_style = val
    
    bowl_match = re.search(r'Bowling Style</[^>]+>\s*<[^>]+>(.*?)</[^>]+>', html_text, re.IGNORECASE | re.DOTALL)
    if bowl_match:
        val = re.sub(r'<[^>]+>', '', bowl_match.group(1)).strip()
        if val:
            bowling_style = val
    
    return batting_style[:80], bowling_style[:80]

def extract_styles_from_text(text):
    """Extract styles from plain text (rendered page)."""
    batting_style = 'N/A'
    bowling_style = 'N/A'
    lines = text.split('\n')
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.upper() == 'BATTING STYLE' and i + 1 < len(lines):
            batting_style = lines[i + 1].strip()
        if stripped.upper() == 'BOWLING STYLE' and i + 1 < len(lines):
            bowling_style = lines[i + 1].strip()
    return batting_style[:80], bowling_style[:80]

driver = None

try:
    print("Starting Chrome (undetected mode, version_main=144)...\n")
    options = uc.ChromeOptions()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    prefs = {
        "profile.managed_default_content_settings.images": 2,
        "profile.managed_default_content_settings.stylesheets": 2,
        "profile.managed_default_content_settings.fonts": 2,
    }
    options.add_experimental_option("prefs", prefs)
    options.add_argument("--blink-settings=imagesEnabled=false")
    driver = uc.Chrome(options=options, version_main=144)
    driver.set_page_load_timeout(30)

    for idx, player in enumerate(players, 1):
        player_name = player['Player_Name']
        url = player['ESPN_URL']
        
        if player_name in already_fetched:
            continue
        
        try:
            print(f"[{idx}/{len(players)}] {player_name}...", end=' ', flush=True)
            driver.get(url)
            time.sleep(random.uniform(2, 4))
            
            page_source = driver.page_source
            batting_style, bowling_style = extract_styles(page_source)
            
            # Fallback: rendered text
            if batting_style == 'N/A' or bowling_style == 'N/A':
                body_text = driver.find_element("tag name", "body").text
                bat2, bowl2 = extract_styles_from_text(body_text)
                if batting_style == 'N/A':
                    batting_style = bat2
                if bowling_style == 'N/A':
                    bowling_style = bowl2
            
            result = {
                'Player_Name': player_name,
                'Batting_Style': batting_style,
                'Bowling_Style': bowling_style,
                'URL': url,
                'Status': 'Success' if batting_style != 'N/A' or bowling_style != 'N/A' else 'No style info'
            }
            results.append(result)
            success_count += 1
            print("OK")
            if batting_style != 'N/A':
                print(f"        Bat: {batting_style}")
            if bowling_style != 'N/A':
                print(f"        Bowl: {bowling_style}")
            
            if len(results) % 5 == 0:
                with open(output_file, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
                    writer.writeheader()
                    writer.writerows(results)
                print(f"        [Saved: {len(results)} players]")
            
        except Exception as e:
            result = {
                'Player_Name': player_name,
                'Batting_Style': 'N/A',
                'Bowling_Style': 'N/A',
                'URL': url,
                'Status': f'Error: {str(e)[:80]}'
            }
            results.append(result)
            failed_count += 1
            print(f"ERR: {str(e)[:60]}")
        
        time.sleep(random.uniform(1, 3))

finally:
    if driver:
        print("\nClosing browser...")
        driver.quit()

if results:
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(results)

print("\n" + "=" * 60)
print(f"Results saved to: {output_file}")
print(f"  Successful: {success_count}")
print(f"  Failed: {failed_count}")
print(f"  Total: {len(results)}")
print("=" * 60)
print("\nNEXT STEP: Run extract_to_csv.py to create final ball-by-ball CSV")

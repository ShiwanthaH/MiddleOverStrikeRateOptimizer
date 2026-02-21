import csv
from pathlib import Path
import time
import random

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options
    HAS_SELENIUM = True
except ImportError:
    HAS_SELENIUM = False
    print("Installing required packages...")
    import subprocess
    subprocess.check_call(['pip', 'install', 'selenium'])
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options

player_info_file = Path(__file__).parent / "player_info_with_urls.csv"
output_file = Path(__file__).parent / "player_styles.csv"

print("=" * 60)
print("STEP 3: Fetching ESPN Cricinfo batting/bowling styles (Browser)")
print("=" * 60)

# Read player info with URLs
players = []
with open(player_info_file, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        players.append(row)

print(f"Processing {len(players)} players from {player_info_file.name}\n")

# Setup Chrome options
chrome_options = Options()
# Uncomment the line below to run in headless mode (no browser window)
# chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-blink-features=AutomationControlled")
chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
chrome_options.add_experimental_option('useAutomationExtension', False)
chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')

results = []
success_count = 0
failed_count = 0

driver = None

try:
    # Initialize driver
    print("Opening Chrome browser...\n")
    driver = webdriver.Chrome(options=chrome_options)
    driver.set_page_load_timeout(20)
    
    for idx, player in enumerate(players, 1):
        player_name = player['Player_Name']
        url = player['ESPN_URL']
        
        try:
            print(f"[{idx}/{len(players)}] {player_name}...", end=' ', flush=True)
            
            # Navigate to URL
            driver.get(url)
            
            # Wait for page to load
            time.sleep(random.uniform(2, 4))
            
            # Get page content
            page_text = driver.page_source
            
            batting_style = 'N/A'
            bowling_style = 'N/A'
            
            # Search for batting style patterns
            lines = page_text.split('\n')
            for i, line in enumerate(lines):
                line_lower = line.lower().strip()
                
                if 'batting style' in line_lower:
                    # Next line or same line should have the value
                    if ':' in line:
                        batting_style = line.split(':', 1)[1].strip()
                        # Clean HTML tags
                        batting_style = batting_style.split('<')[0].strip()
                    elif i + 1 < len(lines):
                        batting_style = lines[i + 1].strip()
                        batting_style = batting_style.replace('<br>', ' ').split('<')[0].strip()
                
                if 'bowling style' in line_lower:
                    # Next line or same line should have the value
                    if ':' in line:
                        bowling_style = line.split(':', 1)[1].strip()
                        # Clean HTML tags
                        bowling_style = bowling_style.split('<')[0].strip()
                    elif i + 1 < len(lines):
                        bowling_style = lines[i + 1].strip()
                        bowling_style = bowling_style.replace('<br>', ' ').split('<')[0].strip()
            
            # Limit extracted strings to reasonable length
            batting_style = batting_style[:100] if batting_style else 'N/A'
            bowling_style = bowling_style[:100] if bowling_style else 'N/A'
            
            result = {
                'Player_Name': player_name,
                'Batting_Style': batting_style,
                'Bowling_Style': bowling_style,
                'URL': url,
                'Status': 'Success' if batting_style != 'N/A' or bowling_style != 'N/A' else 'Fetched (no info)'
            }
            
            results.append(result)
            success_count += 1
            print(f"Success")
            
            if batting_style != 'N/A':
                print(f"        Batting: {batting_style}")
            if bowling_style != 'N/A':
                print(f"        Bowling: {bowling_style}")
            
        except Exception as e:
            result = {
                'Player_Name': player_name,
                'Batting_Style': 'N/A',
                'Bowling_Style': 'N/A',
                'URL': url,
                'Status': f'Error: {str(e)[:50]}'
            }
            results.append(result)
            failed_count += 1
            print(f"ERROR: {str(e)[:50]}")

finally:
    # Close browser
    if driver:
        print("\nClosing browser...")
        driver.quit()

# Save results
if results:
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=results[0].keys())
        writer.writeheader()
        writer.writerows(results)

print("\n" + "=" * 60)
print(f"✓ Results saved to: {output_file}")
print(f"  Successful: {success_count}")
print(f"  Failed: {failed_count}")
print("=" * 60)
print("\nNEXT STEP: Run extract_to_csv.py to create final ball-by-ball CSV")

import json
import csv
from pathlib import Path
from collections import defaultdict

# Step 1: Extract all players from T20 JSON files with their registry IDs
t20_folder = Path(__file__).parent / "T20"
people_file = Path(__file__).parent / "people.csv"
json_files = sorted(list(t20_folder.glob("*.json")))

print("=" * 60)
print("STEP 1: Extracting players from T20 JSON files")
print("=" * 60)

# Dictionary to store: player_name -> (registry_id, json_files_count)
players_registry = {}

for json_file in json_files:
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Extract registry
        registry = data.get("info", {}).get("registry", {}).get("people", {})
        for player_name, registry_id in registry.items():
            if player_name not in players_registry:
                players_registry[player_name] = registry_id
    except Exception as e:
        print(f"Error reading {json_file.name}: {e}")

print(f"Found {len(players_registry)} unique players in T20 JSONs")

# Step 2: Load people.csv and create lookup by identifier
print("\n" + "=" * 60)
print("STEP 2: Loading people.csv and matching players")
print("=" * 60)

people_lookup = {}  # identifier -> {unique_name, key_cricinfo, name}
with open(people_file, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        identifier = row.get('identifier', '').strip()
        if identifier:
            people_lookup[identifier] = {
                'name': row.get('name', '').strip(),
                'unique_name': row.get('unique_name', '').strip(),
                'key_cricinfo': row.get('key_cricinfo', '').strip(),
            }

print(f"Loaded {len(people_lookup)} records from people.csv")

# Step 3: Create player info file with all necessary data
player_info_with_urls = []
unmatched_players = []

for player_name, registry_id in sorted(players_registry.items()):
    if registry_id in people_lookup:
        people_data = people_lookup[registry_id]
        unique_name = people_data['unique_name']
        key_cricinfo = people_data['key_cricinfo']
        
        if unique_name and key_cricinfo:
            # Create URL for ESPN Cricinfo
            url = f"https://www.espncricinfo.com/cricketers/{unique_name.lower().replace(' ', '-')}-{key_cricinfo}"
            
            player_info_with_urls.append({
                'Player_Name': player_name,
                'Identifier': registry_id,
                'Unique_Name': unique_name,
                'Key_Cricinfo': key_cricinfo,
                'ESPN_URL': url,
                'Batting_Style': 'N/A',  # To be filled by fetching
                'Bowling_Style': 'N/A'   # To be filled by fetching
            })
        else:
            unmatched_players.append({
                'Player_Name': player_name,
                'Identifier': registry_id,
                'Reason': 'Missing unique_name or key_cricinfo'
            })
    else:
        unmatched_players.append({
            'Player_Name': player_name,
            'Identifier': registry_id,
            'Reason': 'Identifier not found in people.csv'
        })

# Save player info file
player_info_file = Path(__file__).parent / "player_info_with_urls.csv"
with open(player_info_file, 'w', newline='', encoding='utf-8') as f:
    if player_info_with_urls:
        writer = csv.DictWriter(f, fieldnames=player_info_with_urls[0].keys())
        writer.writeheader()
        writer.writerows(player_info_with_urls)

print(f"\n✓ Created {player_info_file}")
print(f"  Matched players: {len(player_info_with_urls)}")
print(f"  Unmatched players: {len(unmatched_players)}")

if unmatched_players:
    print("\nUnmatched players:")
    for player in unmatched_players[:10]:
        print(f"  - {player['Player_Name']} ({player['Reason']})")
    if len(unmatched_players) > 10:
        print(f"  ... and {len(unmatched_players) - 10} more")

print("\n" + "=" * 60)
print("NEXT STEPS:")
print("=" * 60)
print("1. Run: python fetch_espncricinfo_styles.py")
print("   This will fetch batting/bowling styles from ESPN Cricinfo")
print("2. Then run: python extract_to_csv.py")
print("   This will create the final ball-by-ball CSV with player data")
print("=" * 60)

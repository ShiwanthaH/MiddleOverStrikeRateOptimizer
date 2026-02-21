import csv

# Read existing players from player_styles.csv
existing = set()
with open('player_styles.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    rows = list(reader)
    for r in rows:
        existing.add(r['Player_Name'].strip())

print(f'Existing players in player_styles.csv: {len(existing)}')

# Read all players from player_info_with_urls.csv
all_players = []
with open('player_info_with_urls.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for r in reader:
        all_players.append((r['Player_Name'].strip(), r['ESPN_URL'].strip()))

print(f'Total players in player_info_with_urls.csv: {len(all_players)}')

# Find missing players
missing = [(name, url) for name, url in all_players if name not in existing]
print(f'Missing players to add: {len(missing)}')

# Append missing players to player_styles.csv with empty batting/bowling styles
with open('player_styles.csv', 'a', encoding='utf-8', newline='') as f:
    writer = csv.writer(f)
    for name, url in missing:
        writer.writerow([name, '', '', url, ''])

print(f'Done. Total should now be {len(existing) + len(missing)} data rows.')

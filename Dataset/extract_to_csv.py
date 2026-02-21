import json
import csv
from pathlib import Path

# Get all JSON files from T20 folder
t20_folder = Path(__file__).parent / "T20"
json_files = sorted(list(t20_folder.glob("*.json")))
styles_file = Path(__file__).parent / "player_styles.csv"

print(f"Found {len(json_files)} T20 files")

# Load player styles
player_styles = {}
if styles_file.exists():
    with open(styles_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            player_name = row.get('Player_Name', '').strip()
            if player_name:
                player_styles[player_name] = {
                    'Batting_Style': row.get('Batting_Style', 'N/A').strip(),
                    'Bowling_Style': row.get('Bowling_Style', 'N/A').strip()
                }
    print(f"Loaded styles for {len(player_styles)} players from {styles_file.name}\n")
else:
    print(f"Warning: {styles_file.name} not found. Run fetch_espncricinfo_styles.py first.\n")

# Prepare data for CSV
csv_data = []
total_balls = 0

for json_file in json_files:
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        info = data.get("info", {})
        innings = data.get("innings", [])
        
        # Extract match information
        match_date = info.get("dates", ["N/A"])[0] if info.get("dates") else "N/A"
        season = info.get("season", "N/A")
        match_type = info.get("match_type", "N/A")
        city = info.get("city", "N/A")
        venue = info.get("venue", "N/A")
        teams = info.get("teams", [])
        team1 = teams[0] if len(teams) > 0 else "N/A"
        team2 = teams[1] if len(teams) > 1 else "N/A"
        
        outcome = info.get("outcome", {})
        winner = outcome.get("winner", "N/A")
        
        # Process each innings
        for inning_idx, inning in enumerate(innings):
            inning_team = inning.get("team", "N/A")
            inning_number = inning_idx + 1
            overs = inning.get("overs", [])
            
            # Track cumulative runs
            total_runs = 0
            cumulative_wickets = 0
            
            # Process each over
            for over_data in overs:
                over_num = over_data.get("over", 0)
                deliveries = over_data.get("deliveries", [])
                
                # Process each delivery (ball)
                for ball_idx, delivery in enumerate(deliveries):
                    ball_num = ball_idx + 1
                    
                    batter = delivery.get("batter", "N/A")
                    bowler = delivery.get("bowler", "N/A")
                    non_striker = delivery.get("non_striker", "N/A")
                    
                    runs_info = delivery.get("runs", {})
                    batter_runs = runs_info.get("batter", 0)
                    extras_runs = runs_info.get("extras", 0)
                    total_runs_this_ball = runs_info.get("total", 0)
                    
                    # Update cumulative runs
                    total_runs += total_runs_this_ball
                    
                    # Check for wicket
                    wicket_info = delivery.get("wickets", [])
                    wicket_mode = "N/A"
                    wicket_player = "N/A"
                    if wicket_info:
                        wicket = wicket_info[0]
                        wicket_mode = wicket.get("mode", "N/A")
                        wicket_player = wicket.get("player_out", "N/A")
                        cumulative_wickets += 1
                    
                    # Check for extras type
                    extras_type = "N/A"
                    if extras_runs > 0:
                        if "extras" in delivery:
                            extras_detail = delivery.get("extras", {})
                            if "wides" in extras_detail:
                                extras_type = "Wide"
                            elif "noballs" in extras_detail:
                                extras_type = "No Ball"
                            elif "byes" in extras_detail:
                                extras_type = "Bye"
                            elif "legbyes" in extras_detail:
                                extras_type = "Leg Bye"
                    
                    # Create ball record
                    ball_record = {
                        "File": json_file.name,
                        "Match_Date": match_date,
                        "Season": season,
                        "City": city,
                        "Venue": venue,
                        "Team1": team1,
                        "Team2": team2,
                        "Winner": winner,
                        "Batting_Team": inning_team,
                        "Inning": inning_number,
                        "Over": over_num,
                        "Ball": ball_num,
                        "Batter": batter,
                        "Batter_Handedness": player_styles.get(batter, {}).get('Batting_Style', 'N/A'),
                        "Bowler": bowler,
                        "Bowler_Type": player_styles.get(bowler, {}).get('Bowling_Style', 'N/A'),
                        "Non_Striker": non_striker,
                        "Batter_Runs": batter_runs,
                        "Extras_Runs": extras_runs,
                        "Extras_Type": extras_type,
                        "Total_Runs_This_Ball": total_runs_this_ball,
                        "Cumulative_Runs": total_runs,
                        "Wicket": "Yes" if wicket_info else "No",
                        "Wicket_Mode": wicket_mode,
                        "Wicket_Player": wicket_player,
                        "Cumulative_Wickets": cumulative_wickets,
                    }
                    
                    csv_data.append(ball_record)
                    total_balls += 1
        
        print(f"✓ Processed: {json_file.name} ({len(innings)} innings)")
        
    except Exception as e:
        print(f"✗ Error processing {json_file.name}: {e}")

# Write to CSV file
output_file = Path(__file__).parent / "T20_ball_by_ball.csv"
if csv_data:
    fieldnames = list(csv_data[0].keys())
    
    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(csv_data)
    
    print(f"\n✓ Ball-by-ball CSV file created: {output_file}")
    print(f"Total balls: {total_balls}")
    print(f"Columns: {len(fieldnames)}")
else:
    print("No data to export!")

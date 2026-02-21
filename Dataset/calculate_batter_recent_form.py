"""
Calculate each batter's strike rate over their last 5 T20I innings
(prior to the current match) and add it as 'Batter_Last5_SR' column
to T20_ball_by_ball.csv.

Strike Rate = (Total Runs / Total Balls Faced) * 100

Balls faced: all deliveries where the batter is on strike EXCEPT Wides
  (wides are not counted as balls faced by the batter).
Runs: Batter_Runs only (not extras).

If a batter has fewer than 5 prior innings, the SR is computed over
however many are available. If no prior innings exist, 0.0 is used.
"""

import csv
import os
from collections import defaultdict
from datetime import datetime

INPUT_FILE = "Data/T20_ball_by_ball.csv"
TEMP_FILE = "Data/T20_ball_by_ball_temp.csv"


def main():
    # ── Pass 1: Read all rows and extract per-innings stats ─────────────────
    # Key: (File, Batter) → { 'runs': int, 'balls': int, 'date': str }
    innings_stats = defaultdict(lambda: {'runs': 0, 'balls': 0, 'date': ''})
    match_dates = {}  # File → date string

    all_rows = []
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        for row in reader:
            all_rows.append(row)

            file_id = row['File']
            batter = row['Batter']
            match_date = row['Match_Date']
            match_dates[file_id] = match_date

            key = (file_id, batter)
            innings_stats[key]['date'] = match_date

            # Batter runs (only runs off the bat, not extras)
            batter_runs = int(row['Batter_Runs'])
            innings_stats[key]['runs'] += batter_runs

            # Ball faced? Wides are NOT balls faced by the batter
            extras_type = row.get('Extras_Type', 'N/A')
            is_wide = extras_type == 'Wide'
            if not is_wide:
                innings_stats[key]['balls'] += 1

    print(f"Pass 1: read {len(all_rows)} rows, "
          f"{len(innings_stats)} batter-innings across {len(match_dates)} matches.")

    # ── Build chronological innings history per batter ──────────────────────
    # batter_history[batter] = sorted list of (date, file_id, runs, balls)
    batter_history = defaultdict(list)
    for (file_id, batter), stats in innings_stats.items():
        batter_history[batter].append((
            stats['date'],
            file_id,
            stats['runs'],
            stats['balls']
        ))

    # Sort each batter's history chronologically (date, then file_id as tiebreak)
    for batter in batter_history:
        batter_history[batter].sort(key=lambda x: (x[0], x[1]))

    # ── Build lookup: (file_id, batter) → last-5 SR ────────────────────────
    # For each batter's match at index i, look back at indices [max(0,i-5) : i]
    last5_sr = {}  # (file_id, batter) → float

    for batter, history in batter_history.items():
        for i, (date, file_id, runs, balls) in enumerate(history):
            # Previous innings (up to 5)
            prev = history[max(0, i - 5): i]
            if prev:
                total_runs = sum(p[2] for p in prev)
                total_balls = sum(p[3] for p in prev)
                sr = (total_runs / total_balls * 100) if total_balls > 0 else 0.0
            else:
                sr = 0.0
            last5_sr[(file_id, batter)] = round(sr, 2)

    print(f"Computed last-5 SR for {len(last5_sr)} batter-match combinations.")

    # ── Pass 2: Write CSV with new column ───────────────────────────────────
    new_field = 'Batter_Last5_SR'
    if new_field in fieldnames:
        new_fieldnames = fieldnames
    else:
        new_fieldnames = fieldnames + [new_field]

    with open(TEMP_FILE, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=new_fieldnames)
        writer.writeheader()
        for row in all_rows:
            key = (row['File'], row['Batter'])
            row[new_field] = last5_sr.get(key, 0.0)
            writer.writerow(row)

    os.replace(TEMP_FILE, INPUT_FILE)
    print(f"Pass 2: wrote {len(all_rows)} rows with '{new_field}' column to {INPUT_FILE}.")

    # ── Sample output ───────────────────────────────────────────────────────
    print("\nSample batter histories (first 3 batters with 5+ innings):")
    count = 0
    for batter, history in sorted(batter_history.items()):
        if len(history) >= 5 and count < 3:
            count += 1
            print(f"\n  {batter} ({len(history)} innings):")
            for i, (date, fid, runs, balls) in enumerate(history):
                sr_at_match = last5_sr.get((fid, batter), 0.0)
                own_sr = (runs / balls * 100) if balls > 0 else 0.0
                print(f"    {date} | Runs: {runs:3d} | Balls: {balls:3d} | "
                      f"Innings SR: {own_sr:6.1f} | Last5 SR: {sr_at_match:6.1f}")


if __name__ == "__main__":
    main()

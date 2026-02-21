"""
Classify ALL venues in T20_ball_by_ball.csv as Spin Friendly, Pace Friendly, or Neutral.

Steps:
1. First pass: read every row, accumulate pace/spin bowling stats per venue.
2. Classify each venue using bowling average comparison.
3. Second pass: re-read the CSV and write it back with a new 'Venue_Type' column.

For venues with >= 3 matches: use the 15% threshold on bowling-average ratio.
For venues with < 3 matches:  classify as Neutral (insufficient sample size).
"""

import csv
import os
from collections import defaultdict

INPUT_FILE = "T20_ball_by_ball.csv"
TEMP_FILE = "T20_ball_by_ball_temp.csv"

# ── Bowler type classification ──────────────────────────────────────────────
SPIN_KEYWORDS = {
    'spin', 'orthodox', 'legbreak', 'offbreak', 'googly', 'slow',
    'wrist spin', 'chinaman'
}
PACE_KEYWORDS = {
    'fast', 'medium', 'seam', 'swing'
}

# Explicit overrides for ambiguous combo types
SPIN_OVERRIDES = {
    'Right arm Medium, Legbreak',
    'Right arm Medium, Right arm Offbreak',
    'Left arm Medium, Slow Left arm Orthodox',
    'Left arm Fast medium, Slow Left arm Orthodox',
}
PACE_OVERRIDES = set()

def get_bowling_category(bowler_type: str) -> str:
    """Return 'Spin', 'Pace', or 'Unknown'."""
    if not bowler_type or bowler_type in ('N/A', '', '| Umpire = True'):
        return 'Unknown'

    # Explicit overrides first
    if bowler_type in SPIN_OVERRIDES:
        return 'Spin'
    if bowler_type in PACE_OVERRIDES:
        return 'Pace'

    bt_lower = bowler_type.lower()

    # keyword matching
    is_spin = any(kw in bt_lower for kw in SPIN_KEYWORDS)
    is_pace = any(kw in bt_lower for kw in PACE_KEYWORDS)

    if is_spin and not is_pace:
        return 'Spin'
    if is_pace and not is_spin:
        return 'Pace'
    if is_pace and is_spin:
        # If both keywords match (e.g. "Left arm Fast medium, Slow Left arm Orthodox")
        # default to Spin since spin component is usually secondary skill being highlighted
        return 'Spin'
    return 'Unknown'

# ── Main logic ──────────────────────────────────────────────────────────────

def classify_venue(pace_balls, pace_runs, pace_wickets,
                   spin_balls, spin_runs, spin_wickets,
                   match_count):
    """Return classification string for a venue."""
    # Insufficient data → Neutral
    if match_count < 3:
        return "Neutral"
    if pace_wickets == 0 and spin_wickets == 0:
        return "Neutral"

    # Bowling average = runs / wickets  (lower = more effective)
    pace_avg = pace_runs / pace_wickets if pace_wickets > 0 else float('inf')
    spin_avg = spin_runs / spin_wickets if spin_wickets > 0 else float('inf')

    # Handle edge cases where one type has no wickets at all
    if pace_wickets == 0:
        return "Spin Friendly"     # Only spin takes wickets here
    if spin_wickets == 0:
        return "Pace Friendly"     # Only pace takes wickets here

    ratio = spin_avg / pace_avg    # < 1 → spin more effective → spin friendly
    if ratio < 0.85:
        return "Spin Friendly"
    elif ratio > 1.15:
        return "Pace Friendly"
    return "Neutral"


def main():
    # ── Pass 1: gather stats per venue ──────────────────────────────────────
    # stats[venue] = {'Pace': [balls, runs, wickets], 'Spin': [balls, runs, wickets]}
    venue_stats = defaultdict(lambda: {'Pace': [0, 0, 0], 'Spin': [0, 0, 0]})
    matches_per_venue = defaultdict(set)

    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames  # Save for rewriting
        total_rows = 0

        for row in reader:
            total_rows += 1
            venue = row['Venue']
            bowler_type = row['Bowler_Type']
            category = get_bowling_category(bowler_type)
            matches_per_venue[venue].add(row['File'])

            if category == 'Unknown':
                continue

            runs = int(row['Total_Runs_This_Ball'])
            extra_type = str(row.get('Extras_Type', '')).lower()
            is_wide = 'wides' in extra_type
            is_no_ball = 'no ball' in extra_type or 'noballs' in extra_type
            is_legal = not (is_wide or is_no_ball)

            is_wicket = row['Wicket'] not in ('No', '0', '', 'N/A')
            if is_wicket:
                wicket_mode = row.get('Wicket_Mode', '').lower()
                if any(x in wicket_mode for x in ('run out', 'retired', 'obstructing')):
                    is_wicket = False

            if is_legal:
                venue_stats[venue][category][0] += 1
            venue_stats[venue][category][1] += runs
            if is_wicket:
                venue_stats[venue][category][2] += 1

    print(f"Pass 1 complete: {total_rows} rows, {len(venue_stats)} unique venues.")

    # ── Build venue → classification map ────────────────────────────────────
    venue_class = {}
    for venue, stats in venue_stats.items():
        p_b, p_r, p_w = stats['Pace']
        s_b, s_r, s_w = stats['Spin']
        mc = len(matches_per_venue[venue])
        venue_class[venue] = classify_venue(p_b, p_r, p_w, s_b, s_r, s_w, mc)

    # Summary
    from collections import Counter
    class_counts = Counter(venue_class.values())
    print(f"\nClassification breakdown:")
    for cls, cnt in class_counts.most_common():
        print(f"  {cls}: {cnt} venues")

    print(f"\n{'Venue':<55} | {'Matches':<7} | {'Classification':<15}")
    print("-" * 85)
    for venue in sorted(venue_class, key=lambda v: len(matches_per_venue[v]), reverse=True):
        mc = len(matches_per_venue[venue])
        print(f"{venue[:53]:<55} | {mc:<7} | {venue_class[venue]:<15}")

    # ── Pass 2: rewrite CSV with new 'Venue_Type' column ───────────────────
    # Add 'Venue_Type' to the fieldnames (replace if already present)
    new_field = 'Venue_Type'
    if new_field in fieldnames:
        new_fieldnames = fieldnames  # Already present, just overwrite values
    else:
        new_fieldnames = fieldnames + [new_field]

    rows_written = 0
    with open(INPUT_FILE, 'r', encoding='utf-8') as fin, \
         open(TEMP_FILE, 'w', newline='', encoding='utf-8') as fout:
        reader = csv.DictReader(fin)
        writer = csv.DictWriter(fout, fieldnames=new_fieldnames)
        writer.writeheader()

        for row in reader:
            row[new_field] = venue_class.get(row['Venue'], 'Neutral')
            writer.writerow(row)
            rows_written += 1

    # Replace original file with updated file
    os.replace(TEMP_FILE, INPUT_FILE)
    print(f"\nPass 2 complete: wrote {rows_written} rows with '{new_field}' column to {INPUT_FILE}.")


if __name__ == "__main__":
    main()

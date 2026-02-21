"""
Calculate and add Current Run Rate (CRR) at each ball to the T20_ball_by_ball CSV.

CRR = Cumulative_Runs / Overs_Bowled
where Overs_Bowled = completed_overs + (balls_in_current_over / 6)

Over is 0-indexed in the CSV, Ball is 1-indexed.
Extras like wides/no-balls don't count as legal deliveries, but the CSV
already only has rows for legal deliveries (Ball column counts legal balls).
"""

import csv

INPUT_FILE = "T20_ball_by_ball.csv"
OUTPUT_FILE = "T20_ball_by_ball.csv"  # overwrite in place


def calculate_crr(over, ball, cumulative_runs):
    """
    Calculate Current Run Rate.
    over: 0-indexed over number (0 = first over)
    ball: 1-indexed ball within the over (1-6)
    cumulative_runs: total runs scored so far including this ball
    """
    # Total legal balls bowled = over * 6 + ball
    total_balls = int(over) * 6 + int(ball)
    if total_balls == 0:
        return 0.0
    # CRR = runs / overs, where overs = total_balls / 6
    overs_bowled = total_balls / 6.0
    return round(float(cumulative_runs) / overs_bowled, 2)


def main():
    # Read all rows
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = list(reader.fieldnames)
        rows = list(reader)

    print(f"Read {len(rows)} rows from {INPUT_FILE}")

    # Add CRR column if not present
    if "Current_Run_Rate" not in fieldnames:
        fieldnames.append("Current_Run_Rate")

    # Calculate CRR for each ball
    for row in rows:
        row["Current_Run_Rate"] = calculate_crr(
            row["Over"], row["Ball"], row["Cumulative_Runs"]
        )

    # Write back
    with open(OUTPUT_FILE, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Added Current_Run_Rate column to {OUTPUT_FILE}")
    print("Sample values (first 10 rows):")
    for r in rows[:10]:
        print(
            f"  Over {r['Over']}.{r['Ball']} | "
            f"Runs: {r['Batter_Runs']} | "
            f"Cumulative: {r['Cumulative_Runs']} | "
            f"CRR: {r['Current_Run_Rate']}"
        )


if __name__ == "__main__":
    main()

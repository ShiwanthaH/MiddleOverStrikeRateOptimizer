"""
Fetch batting and bowling styles from Wikipedia for cricket players.
Uses Wikipedia API to search for players, get their infobox data,
and map the styles to the CSV format used in player_styles.csv.
"""

import csv
import requests
import re
import time
import os

WIKI_API = "https://en.wikipedia.org/w/api.php"
CSV_FILE = "player_styles.csv"
PROGRESS_FILE = "wiki_progress.json"
SESSION = requests.Session()
SESSION.headers.update({"User-Agent": "CricketStyleFetcher/1.0 (educational project)"})

# ── Mapping functions ──────────────────────────────────────────────

def clean_wiki_markup(text):
    """Remove wiki markup from a string."""
    if not text:
        return ""
    # Remove {{nowrap|...}}
    text = re.sub(r'\{\{nowrap\|(.+?)\}\}', r'\1', text, flags=re.IGNORECASE)
    # Remove other templates like {{cricket style|...}}
    text = re.sub(r'\{\{[^}]*\|([^}]*)\}\}', r'\1', text)
    text = re.sub(r'\{\{([^}|]*)\}\}', r'\1', text)
    # Remove [[Link|Display]] → Display
    text = re.sub(r'\[\[[^\]]*\|([^\]]*)\]\]', r'\1', text)
    # Remove [[Link]] → Link
    text = re.sub(r'\[\[([^\]]*)\]\]', r'\1', text)
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    # Remove ref tags and their content
    text = re.sub(r'<ref[^>]*>.*?</ref>', '', text, flags=re.DOTALL)
    text = re.sub(r'<ref[^/]*/>', '', text)
    return text.strip()


def map_batting_style(wiki_style):
    """Map Wikipedia batting style to CSV format."""
    if not wiki_style:
        return ""
    style = clean_wiki_markup(wiki_style).lower().strip()
    if not style:
        return ""
    if "right" in style and ("hand" in style or "bat" in style or style == "right-handed" or style == "right handed"):
        return "Right hand Bat"
    if "left" in style and ("hand" in style or "bat" in style or style == "left-handed" or style == "left handed"):
        return "Left hand Bat"
    if "right" in style:
        return "Right hand Bat"
    if "left" in style:
        return "Left hand Bat"
    return ""


BOWLING_MAP = {
    # Right arm pace
    "right-arm fast": "Right arm Fast",
    "right arm fast": "Right arm Fast",
    "right-arm fast-medium": "Right arm Fast medium",
    "right arm fast-medium": "Right arm Fast medium",
    "right-arm fast medium": "Right arm Fast medium",
    "right arm fast medium": "Right arm Fast medium",
    "right-arm medium-fast": "Right arm Medium fast",
    "right arm medium-fast": "Right arm Medium fast",
    "right-arm medium fast": "Right arm Medium fast",
    "right arm medium fast": "Right arm Medium fast",
    "right-arm medium": "Right arm Medium",
    "right arm medium": "Right arm Medium",
    "right-arm medium-slow": "Right arm Medium",
    # Right arm spin
    "right-arm off-break": "Right arm Offbreak",
    "right arm off-break": "Right arm Offbreak",
    "right-arm offbreak": "Right arm Offbreak",
    "right arm offbreak": "Right arm Offbreak",
    "right-arm off break": "Right arm Offbreak",
    "right arm off break": "Right arm Offbreak",
    "right-arm off spin": "Right arm Offbreak",
    "right arm off spin": "Right arm Offbreak",
    "off break": "Right arm Offbreak",
    "off-break": "Right arm Offbreak",
    "offbreak": "Right arm Offbreak",
    # Leg spin
    "leg-break": "Legbreak",
    "leg break": "Legbreak",
    "legbreak": "Legbreak",
    "leg-spin": "Legbreak",
    "leg spin": "Legbreak",
    "right-arm leg break": "Legbreak",
    "right arm leg break": "Legbreak",
    "right-arm leg-break": "Legbreak",
    "right-arm leg spin": "Legbreak",
    "right arm leg spin": "Legbreak",
    "right-arm leg-spin": "Legbreak",
    "leg-break googly": "Legbreak Googly",
    "leg break googly": "Legbreak Googly",
    "legbreak googly": "Legbreak Googly",
    "right-arm leg-break googly": "Legbreak Googly",
    "right-arm leg break googly": "Legbreak Googly",
    "right arm leg break googly": "Legbreak Googly",
    # Left arm pace
    "left-arm fast": "Left arm Fast",
    "left arm fast": "Left arm Fast",
    "left-arm fast-medium": "Left arm Fast medium",
    "left arm fast-medium": "Left arm Fast medium",
    "left-arm fast medium": "Left arm Fast medium",
    "left arm fast medium": "Left arm Fast medium",
    "left-arm medium-fast": "Left arm Medium fast",
    "left arm medium-fast": "Left arm Medium fast",
    "left-arm medium fast": "Left arm Medium fast",
    "left arm medium fast": "Left arm Medium fast",
    "left-arm medium": "Left arm Medium",
    "left arm medium": "Left arm Medium",
    # Left arm spin
    "slow left-arm orthodox": "Slow Left arm Orthodox",
    "slow left arm orthodox": "Slow Left arm Orthodox",
    "left-arm orthodox": "Slow Left arm Orthodox",
    "left arm orthodox": "Slow Left arm Orthodox",
    "slow left-arm": "Slow Left arm Orthodox",
    "slow left arm": "Slow Left arm Orthodox",
    "left-arm slow orthodox": "Slow Left arm Orthodox",
    "left-arm wrist spin": "Left arm Wrist spin",
    "left arm wrist spin": "Left arm Wrist spin",
    "left-arm unorthodox": "Left arm Wrist spin",
    "left arm unorthodox": "Left arm Wrist spin",
    "left-arm chinaman": "Left arm Wrist spin",
    "left arm chinaman": "Left arm Wrist spin",
    # Right arm slow
    "right-arm slow": "Right arm Slow",
    "right arm slow": "Right arm Slow",
    "right-arm slow-medium": "Right arm Slow",
    # N/A
    "n/a": "N/A",
    "none": "N/A",
    "": "N/A",
    "wicket-keeper": "N/A",
    "wicketkeeper": "N/A",
}


def map_bowling_style(wiki_style):
    """Map Wikipedia bowling style to CSV format."""
    if not wiki_style:
        return ""
    style = clean_wiki_markup(wiki_style).lower().strip()
    if not style:
        return ""

    # Direct lookup
    if style in BOWLING_MAP:
        return BOWLING_MAP[style]

    # Try removing trailing punctuation / whitespace variations
    style_clean = re.sub(r'[,;.\s]+$', '', style)
    if style_clean in BOWLING_MAP:
        return BOWLING_MAP[style_clean]

    # Fuzzy matching: check if any key is contained in the style
    for key, value in sorted(BOWLING_MAP.items(), key=lambda x: -len(x[0])):
        if key and key in style:
            return value

    # If nothing matched, return cleaned version with title case
    return style.title().replace("-", " ").replace("  ", " ")


# ── Wikipedia API helpers ──────────────────────────────────────────

def search_player(player_name):
    """Search Wikipedia for a cricketer, return best page title or None."""
    surname = player_name.split()[-1]
    initials = " ".join(player_name.split()[:-1])

    # Try multiple search queries
    queries = [
        f"{player_name} cricketer",
        f"{player_name} cricket",
        f"{surname} cricketer {initials}",
    ]

    for query in queries:
        try:
            params = {
                "action": "query",
                "list": "search",
                "srsearch": query,
                "srlimit": 5,
                "format": "json",
            }
            resp = SESSION.get(WIKI_API, params=params, timeout=15)
            data = resp.json()
            results = data.get("query", {}).get("search", [])

            for result in results:
                title = result["title"]
                snippet = result.get("snippet", "").lower()
                # Check surname matches and it's a cricket page
                if surname.lower() in title.lower():
                    # Check if it's about cricket
                    if any(w in snippet for w in ["cricket", "batsman", "batswoman",
                           "bowler", "all-rounder", "allrounder", "wicket",
                           "bat", "bowl", "t20", "odi", "test", "ipl"]):
                        return title
                    # If first result has surname, likely correct
                    if result == results[0]:
                        return title
        except Exception as e:
            print(f"  Search error for '{query}': {e}")
            continue

    return None


def get_infobox_wikitext(title):
    """Get the wikitext of the lead section (section 0) which contains the infobox."""
    try:
        params = {
            "action": "query",
            "prop": "revisions",
            "rvprop": "content",
            "rvsection": 0,
            "titles": title,
            "format": "json",
            "rvslots": "main",
        }
        resp = SESSION.get(WIKI_API, params=params, timeout=15)
        data = resp.json()
        pages = data.get("query", {}).get("pages", {})
        for page_id, page_data in pages.items():
            if page_id == "-1":
                return None
            revisions = page_data.get("revisions", [])
            if revisions:
                # Handle both old and new API format
                rev = revisions[0]
                if "slots" in rev:
                    return rev["slots"]["main"].get("*", "")
                return rev.get("*", "")
        return None
    except Exception as e:
        print(f"  Error fetching wikitext for '{title}': {e}")
        return None


def parse_infobox_field(wikitext, field_name):
    """Extract a field value from infobox wikitext."""
    if not wikitext:
        return None
    # Match | field_name = value (until next | or }})
    pattern = rf'\|\s*{field_name}\s*=\s*(.+?)(?:\n\s*\||\n\s*\}})'
    match = re.search(pattern, wikitext, re.IGNORECASE | re.DOTALL)
    if match:
        value = match.group(1).strip()
        # Handle multi-line values by taking first line
        value = value.split('\n')[0].strip()
        if value:
            return value
    return None


def get_player_styles(player_name):
    """
    Search Wikipedia for a player and extract batting/bowling styles.
    Returns (batting_style, bowling_style, wiki_title, status)
    """
    title = search_player(player_name)
    if not title:
        return ("", "", "", "Not found on Wikipedia")

    time.sleep(0.3)  # Rate limit

    wikitext = get_infobox_wikitext(title)
    if not wikitext:
        return ("", "", title, "No wikitext found")

    # Parse batting and bowling from infobox
    raw_batting = parse_infobox_field(wikitext, "batting")
    raw_bowling = parse_infobox_field(wikitext, "bowling")

    # Also try batting_style / bowling_style field names
    if not raw_batting:
        raw_batting = parse_infobox_field(wikitext, "batting_style")
    if not raw_bowling:
        raw_bowling = parse_infobox_field(wikitext, "bowling_style")

    batting = map_batting_style(raw_batting)
    bowling = map_bowling_style(raw_bowling)

    status = "Success" if batting else "No style info"
    return (batting, bowling, title, status)


# ── Main ────────────────────────────────────────────────────────────

def main():
    # Read existing CSV
    rows = []
    with open(CSV_FILE, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        for row in reader:
            rows.append(row)

    # Identify players needing styles
    missing = [(i, row) for i, row in enumerate(rows)
               if not row.get("Batting_Style", "").strip()]

    print(f"Total players: {len(rows)}")
    print(f"Players needing styles: {len(missing)}")
    print()

    # Load progress
    completed = set()
    if os.path.exists(PROGRESS_FILE):
        import json
        with open(PROGRESS_FILE, "r") as f:
            completed = set(json.load(f))
        print(f"Resuming: {len(completed)} already processed")

    found = 0
    not_found = 0
    errors = 0

    for count, (idx, row) in enumerate(missing):
        name = row["Player_Name"]
        if name in completed:
            continue

        print(f"[{count+1}/{len(missing)}] {name}...", end=" ", flush=True)

        try:
            batting, bowling, wiki_title, status = get_player_styles(name)
            time.sleep(0.3)  # Rate limit between players

            if batting:
                rows[idx]["Batting_Style"] = batting
                rows[idx]["Bowling_Style"] = bowling if bowling else "N/A"
                rows[idx]["Status"] = status
                found += 1
                print(f"✓ {batting}, {bowling} ({wiki_title})")
            else:
                not_found += 1
                print(f"✗ {status}" + (f" ({wiki_title})" if wiki_title else ""))

            completed.add(name)

            # Save progress every 20 players
            if len(completed) % 20 == 0:
                _save_csv(rows, fieldnames)
                import json
                with open(PROGRESS_FILE, "w") as f:
                    json.dump(list(completed), f)
                print(f"  [Saved progress: {found} found, {not_found} not found]")

        except Exception as e:
            errors += 1
            print(f"ERROR: {e}")
            time.sleep(1)

    # Final save
    _save_csv(rows, fieldnames)
    if os.path.exists(PROGRESS_FILE):
        os.remove(PROGRESS_FILE)

    print()
    print(f"Done! Found: {found}, Not found: {not_found}, Errors: {errors}")


def _save_csv(rows, fieldnames):
    """Save rows back to CSV."""
    with open(CSV_FILE, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    main()

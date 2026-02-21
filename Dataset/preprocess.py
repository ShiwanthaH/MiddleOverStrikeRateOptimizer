import json
import os
import shutil
from pathlib import Path

# Get all JSON files from Data folder
data_folder = Path(__file__).parent / "Data"
json_files = list(data_folder.glob("*.json"))

print(f"Total files found: {len(json_files)}")

# Filter files where match_type is T20
t20_files = []
non_t20_files = []

for json_file in json_files:
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            match_type = data.get("info", {}).get("match_type", "")
            
            # Case-insensitive comparison for T20
            if match_type.upper() == "T20":
                t20_files.append({
                    "filename": json_file.name,
                    "path": str(json_file),
                    "match_type": match_type
                })
            else:
                non_t20_files.append({
                    "filename": json_file.name,
                    "path": str(json_file),
                    "match_type": match_type
                })
    except Exception as e:
        print(f"Error reading {json_file.name}: {e}")

# Display results
print(f"\nFiles with T20 match type: {len(t20_files)}")
print(f"Files with other match types: {len(non_t20_files)}")

# Create T20 folder
t20_folder = Path(__file__).parent / "T20"
t20_folder.mkdir(exist_ok=True)
print(f"\nCreated T20 folder: {t20_folder}")

# Copy T20 files to T20 folder
print("\nCopying T20 files...")
for file_info in t20_files:
    src = Path(file_info['path'])
    dst = t20_folder / file_info['filename']
    shutil.copy2(src, dst)
    print(f"  Copied: {file_info['filename']}")

# Delete non-T20 files from Data folder
print(f"\nDeleting {len(non_t20_files)} non-T20 files from Data folder...")
for file_info in non_t20_files:
    file_path = Path(file_info['path'])
    file_path.unlink()
    print(f"  Deleted: {file_info['filename']}")

# Write T20 paths to a text file
output_file = Path(__file__).parent / "t20_files.txt"
with open(output_file, 'w', encoding='utf-8') as f:
    for file_info in t20_files:
        f.write(file_info['path'] + '\n')

print(f"\nPaths written to: {output_file}")
print(f"\n✓ Process complete!")
print(f"  - T20 files in T20 folder: {len(t20_files)}")
print(f"  - Non-T20 files deleted: {len(non_t20_files)}")

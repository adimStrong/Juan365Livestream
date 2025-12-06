"""
Auto-merge all CSV exports into a single file
Run this after adding new CSV exports to the exports/ folder
"""

import pandas as pd
from pathlib import Path
from datetime import datetime

def merge_exports():
    exports_dir = Path(__file__).parent / 'exports'

    # Find all CSV files except the merged file
    csv_files = [f for f in exports_dir.glob('*.csv') if 'MERGED' not in f.name.upper()]

    if not csv_files:
        print("No CSV files found in exports/ folder")
        return

    print(f"Found {len(csv_files)} CSV file(s) to merge:")
    for f in csv_files:
        print(f"  - {f.name}")

    # Read and combine all CSVs
    all_dfs = []
    for csv_file in csv_files:
        try:
            df = pd.read_csv(csv_file)
            print(f"  Loaded {len(df)} rows from {csv_file.name}")
            all_dfs.append(df)
        except Exception as e:
            print(f"  Error reading {csv_file.name}: {e}")

    if not all_dfs:
        print("No data loaded")
        return

    # Combine all dataframes
    merged_df = pd.concat(all_dfs, ignore_index=True)

    # Remove duplicates based on Post ID
    if 'Post ID' in merged_df.columns:
        before_dedup = len(merged_df)
        merged_df = merged_df.drop_duplicates(subset=['Post ID'], keep='last')
        after_dedup = len(merged_df)
        if before_dedup != after_dedup:
            print(f"  Removed {before_dedup - after_dedup} duplicate posts")

    # Sort by publish time (newest first)
    if 'Publish time' in merged_df.columns:
        merged_df['_sort_date'] = pd.to_datetime(merged_df['Publish time'], format='%m/%d/%Y %H:%M', errors='coerce')
        merged_df = merged_df.sort_values('_sort_date', ascending=False)
        merged_df = merged_df.drop(columns=['_sort_date'])

    # Save merged file
    output_file = exports_dir / 'Juan365_MERGED_ALL.csv'
    merged_df.to_csv(output_file, index=False)

    print(f"\n{'='*50}")
    print(f"SUCCESS! Merged {len(merged_df)} total posts")
    print(f"Saved to: {output_file.name}")
    print(f"{'='*50}")

    # Show date range
    if 'Publish time' in merged_df.columns:
        dates = pd.to_datetime(merged_df['Publish time'], format='%m/%d/%Y %H:%M', errors='coerce')
        print(f"\nDate range: {dates.min().strftime('%Y-%m-%d')} to {dates.max().strftime('%Y-%m-%d')}")

    return merged_df

if __name__ == '__main__':
    merge_exports()
    try:
        input("\nPress Enter to close...")
    except EOFError:
        pass  # Running non-interactively

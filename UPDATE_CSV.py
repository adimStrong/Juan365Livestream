"""
Juan365 Live Stream CSV Data Updater
Quick script to update dashboard data from Meta Business Suite export
"""

import tkinter as tk
from tkinter import filedialog, messagebox
import pandas as pd
import shutil
from pathlib import Path
from datetime import datetime

# Paths
SCRIPT_DIR = Path(__file__).parent
EXPORTS_DIR = SCRIPT_DIR / 'exports'
TARGET_FILE = EXPORTS_DIR / 'Juan365_LiveStream_MERGED_ALL.csv'
BACKUP_DIR = EXPORTS_DIR / 'backups'

# Required columns from Meta Business Suite export
REQUIRED_COLUMNS = ['Post ID', 'Publish time', 'Reactions', 'Comments', 'Shares']
OPTIONAL_COLUMNS = ['Title', 'Post type', 'Permalink', 'Views', 'Reach', 'Total clicks']


def validate_csv(file_path):
    """Validate the CSV has required columns"""
    try:
        df = pd.read_csv(file_path)
        missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
        if missing:
            return False, f"Missing required columns: {', '.join(missing)}"

        # Check for optional columns
        present_optional = [col for col in OPTIONAL_COLUMNS if col in df.columns]
        missing_optional = [col for col in OPTIONAL_COLUMNS if col not in df.columns]

        info = f"Found {len(df)} posts\n"
        info += f"Required columns: OK\n"
        info += f"Optional columns present: {', '.join(present_optional) if present_optional else 'None'}\n"
        if missing_optional:
            info += f"Optional columns missing: {', '.join(missing_optional)}"

        return True, info
    except Exception as e:
        return False, f"Error reading file: {str(e)}"


def backup_existing():
    """Backup existing CSV file"""
    if TARGET_FILE.exists():
        BACKUP_DIR.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = BACKUP_DIR / f'Juan365_LiveStream_MERGED_ALL_backup_{timestamp}.csv'
        shutil.copy(TARGET_FILE, backup_path)
        return backup_path
    return None


def update_csv(new_file_path, mode='replace'):
    """Update the CSV file"""
    try:
        new_df = pd.read_csv(new_file_path)

        if mode == 'replace':
            # Simply replace the file
            backup_path = backup_existing()
            shutil.copy(new_file_path, TARGET_FILE)
            return True, f"Replaced with {len(new_df)} posts.\nBackup saved to: {backup_path}"

        elif mode == 'merge':
            # Merge with existing data (new data takes priority for duplicates)
            if TARGET_FILE.exists():
                existing_df = pd.read_csv(TARGET_FILE)
                backup_path = backup_existing()

                # Combine and remove duplicates (keep new data)
                combined = pd.concat([existing_df, new_df])
                combined = combined.drop_duplicates(subset=['Post ID'], keep='last')
                combined = combined.sort_values('Publish time', ascending=False)

                combined.to_csv(TARGET_FILE, index=False)

                new_count = len(combined) - len(existing_df)
                return True, f"Merged! Added {new_count} new posts.\nTotal: {len(combined)} posts\nBackup: {backup_path}"
            else:
                shutil.copy(new_file_path, TARGET_FILE)
                return True, f"Created with {len(new_df)} posts (no existing file to merge)"

    except Exception as e:
        return False, f"Error updating: {str(e)}"


def main():
    """Main GUI"""
    root = tk.Tk()
    root.title("Juan365 Live Stream CSV Updater")
    root.geometry("500x400")
    root.configure(bg='#1a1a2e')

    # Title
    title = tk.Label(root, text="Juan365 Live Stream CSV Data Updater",
                     font=('Segoe UI', 16, 'bold'), fg='#4361EE', bg='#1a1a2e')
    title.pack(pady=20)

    # Status label
    status_var = tk.StringVar(value="Select a CSV file exported from Meta Business Suite")
    status_label = tk.Label(root, textvariable=status_var,
                           font=('Segoe UI', 10), fg='white', bg='#1a1a2e',
                           wraplength=450, justify='left')
    status_label.pack(pady=10, padx=20)

    # Selected file label
    file_var = tk.StringVar(value="No file selected")
    file_label = tk.Label(root, textvariable=file_var,
                         font=('Segoe UI', 9), fg='#888', bg='#1a1a2e',
                         wraplength=450)
    file_label.pack(pady=5, padx=20)

    selected_file = [None]

    def select_file():
        file_path = filedialog.askopenfilename(
            title="Select Meta Business Suite CSV Export",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            initialdir=Path.home() / 'Downloads'
        )
        if file_path:
            selected_file[0] = file_path
            file_var.set(f"Selected: {Path(file_path).name}")

            # Validate
            valid, info = validate_csv(file_path)
            if valid:
                status_var.set(f"Valid CSV file!\n\n{info}")
                replace_btn.config(state='normal')
                merge_btn.config(state='normal')
            else:
                status_var.set(f"Invalid CSV file!\n\n{info}")
                replace_btn.config(state='disabled')
                merge_btn.config(state='disabled')

    def do_replace():
        if selected_file[0]:
            success, msg = update_csv(selected_file[0], mode='replace')
            if success:
                messagebox.showinfo("Success", msg + "\n\nRefresh your browser at http://localhost:8501")
                status_var.set("Update complete! Refresh your browser.")
            else:
                messagebox.showerror("Error", msg)

    def do_merge():
        if selected_file[0]:
            success, msg = update_csv(selected_file[0], mode='merge')
            if success:
                messagebox.showinfo("Success", msg + "\n\nRefresh your browser at http://localhost:8501")
                status_var.set("Merge complete! Refresh your browser.")
            else:
                messagebox.showerror("Error", msg)

    # Buttons frame
    btn_frame = tk.Frame(root, bg='#1a1a2e')
    btn_frame.pack(pady=20)

    # Select file button
    select_btn = tk.Button(btn_frame, text="1. Select CSV File",
                          command=select_file,
                          font=('Segoe UI', 11, 'bold'),
                          bg='#4361EE', fg='white',
                          padx=20, pady=10,
                          cursor='hand2')
    select_btn.pack(pady=10)

    # Action buttons frame
    action_frame = tk.Frame(root, bg='#1a1a2e')
    action_frame.pack(pady=10)

    # Replace button
    replace_btn = tk.Button(action_frame, text="2a. Replace All Data",
                           command=do_replace,
                           font=('Segoe UI', 10),
                           bg='#E94560', fg='white',
                           padx=15, pady=8,
                           state='disabled',
                           cursor='hand2')
    replace_btn.pack(side='left', padx=10)

    # Merge button
    merge_btn = tk.Button(action_frame, text="2b. Merge (Add New)",
                         command=do_merge,
                         font=('Segoe UI', 10),
                         bg='#06D6A0', fg='white',
                         padx=15, pady=8,
                         state='disabled',
                         cursor='hand2')
    merge_btn.pack(side='left', padx=10)

    # Info label
    info_text = """
Replace: Completely replaces existing data with new file
Merge: Adds new posts, updates existing ones (keeps all history)

After updating, refresh your browser at http://localhost:8501
    """
    info_label = tk.Label(root, text=info_text,
                         font=('Segoe UI', 9), fg='#888', bg='#1a1a2e',
                         justify='left')
    info_label.pack(pady=20, padx=20)

    root.mainloop()


if __name__ == '__main__':
    main()

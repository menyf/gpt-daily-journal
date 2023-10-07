"""
# README

This Daily Markdown Generator processes backup files containing summaries and notes and generates individual daily markdown files with structured content.

## Description

Given a set of markdown files starting with "Summaries" and CSV files starting with "Notes" in a "Backup" directory, the script:

1. Identifies the latest files based on their timestamp in the filename.
2. Extracts sections from the latest summary markdown file based on date headings.
3. Extracts notes from the latest CSV file and adjusts dates for entries with times before 3:00 AM to be considered as the previous day's note.
4. Writes individual daily markdown files for each extracted section into a "Daily" directory, appending relevant notes to each file.

## Prerequisites

1. Ensure Python is installed on your machine.
2. The script depends on the `os`, `re`, `csv`, `datetime`, and `glob` modules, which are part of Python's standard library, so no additional installation is required.
3. Place your backup files in a directory named "Backup".
    - Markdown files should start with "Summaries" and have a ".md" extension.
    - CSV files should start with "Notes" and have a ".csv" extension.
4. Ensure that your CSV notes are structured with "time" and "content" fields.

## Configuration

- `BACKUP_DIR`: The directory where backup files (summaries and notes) are located. Default is "Backup".
- `OUTPUT_DIR`: The directory where the script will output the generated daily markdown files. Default is "Daily".
- `SUMMARY_PATTERN`: File pattern to detect the summary markdown files. Default is "Summaries*.md".
- `NOTE_PATTERN`: File pattern to detect the notes CSV files. Default is "Notes*.csv".

These fields can be adjusted at the top of the script if you wish to customize the directory names or file patterns.

## Usage

1. Place the script in the directory containing the "Backup" folder.
2. Run the script using Python: `python script_name.py` (replace `script_name.py` with the actual script's filename).
3. Check the "Daily" directory for the generated markdown files.
"""


import os
import re
import csv
from datetime import datetime, timedelta
import glob

# Directory and file pattern configurations
BACKUP_DIR = "Backup"
OUTPUT_DIR = "Daily"
NOTE_PATTERN = "Notes*.csv"
SUMMARY_PATTERN = "Summaries*.md"

def get_latest_file(pattern):
    """Retrieve the latest file based on the provided pattern."""
    files = glob.glob(os.path.join(BACKUP_DIR, pattern))
    if not files:
        return None
    files.sort(reverse=True)
    return files[0]

def extract_sections_from_md(file_path):
    """Extract date sections from the markdown file."""
    with open(file_path, 'r') as f:
        content = f.read()
    pattern = r'## (\d{4}-\d{2}-\d{2})\n(.*?)(?=## \d{4}-\d{2}-\d{2}|\Z)'
    return re.findall(pattern, content, re.DOTALL)

def extract_notes_from_csv(file_path):
    """Extract notes from the CSV and adjust date based on time."""
    notes = {}
    with open(file_path, 'r') as csv_f:
        reader = csv.reader(csv_f)
        next(reader)  # skip header
        for row in reader:
            date_obj = datetime.strptime(row[0], '%Y/%m/%d %H:%M')
            if date_obj.time().hour < 3:
                date_obj = date_obj - timedelta(days=1)
            date_str = date_obj.strftime('%Y-%m-%d')
            time = row[0].split()[1]
            notes.setdefault(date_str, []).append((time, row[1]))
    return notes

def write_daily_files(sections, notes):
    """Generate daily files based on sections and notes."""
    for date_str, section_content in sections:
        output_filename = os.path.join(OUTPUT_DIR, f"{date_str}.md")
        if os.path.exists(output_filename):
            continue
        with open(output_filename, 'w') as f:
            f.write(section_content.strip() + '\n')
            if date_str in notes:
                f.write("\n## Time-based Note\n")
                for time, note_content in notes[date_str]:
                    f.write(f"[{time}] {note_content.strip()}\n\n")

if __name__ == '__main__':
    # Ensure output directory exists
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    # Extract latest summary and note files
    summary_file = get_latest_file(SUMMARY_PATTERN)
    note_file = get_latest_file(NOTE_PATTERN)

    if not summary_file or not note_file:
        print("Ensure both latest summary and note files are present in the Backup directory!")
        exit()

    # Process files to generate daily outputs
    sections = extract_sections_from_md(summary_file)
    notes = extract_notes_from_csv(note_file)
    write_daily_files(sections, notes)

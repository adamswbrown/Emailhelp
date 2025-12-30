#!/usr/bin/env python3
"""Quick diagnostic script to inspect the Envelope Index database schema."""

import sqlite3
from pathlib import Path

db_path = Path.home() / "Library" / "Mail" / "V10" / "MailData" / "Envelope Index"

if not db_path.exists():
    print(f"Database not found at: {db_path}")
    exit(1)

print(f"Connecting to: {db_path}")
conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
conn.row_factory = sqlite3.Row

cursor = conn.cursor()

# Get table names
print("\n=== Tables ===")
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
for table in tables:
    print(f"  - {table[0]}")

# Check messages table schema
print("\n=== Messages Table Schema ===")
try:
    cursor.execute("PRAGMA table_info(messages)")
    columns = cursor.fetchall()
    for col in columns:
        print(f"  {col[1]:20s} {col[2]:15s} (nullable: {not col[3]})")
except Exception as e:
    print(f"  Error: {e}")

# Check a few sample rows
print("\n=== Sample Rows (first 3) ===")
try:
    cursor.execute("SELECT * FROM messages LIMIT 3")
    rows = cursor.fetchall()
    for i, row in enumerate(rows, 1):
        print(f"\nRow {i}:")
        for key in row.keys():
            value = row[key]
            if isinstance(value, str) and len(value) > 50:
                value = value[:50] + "..."
            print(f"  {key:20s} = {value}")
except Exception as e:
    print(f"  Error: {e}")

# Check distinct mailbox values
print("\n=== Distinct Mailbox Values (first 10) ===")
try:
    cursor.execute("SELECT DISTINCT mailbox FROM messages WHERE mailbox IS NOT NULL LIMIT 10")
    mailboxes = cursor.fetchall()
    for mb in mailboxes:
        value = mb[0]
        print(f"  Type: {type(value).__name__}, Value: {repr(value)}")
except Exception as e:
    print(f"  Error: {e}")

# Check if account column exists and has values
print("\n=== Account Column Check ===")
try:
    cursor.execute("PRAGMA table_info(messages)")
    columns = [col[1] for col in cursor.fetchall()]
    if 'account' in columns:
        cursor.execute("SELECT DISTINCT account FROM messages WHERE account IS NOT NULL LIMIT 10")
        accounts = cursor.fetchall()
        print(f"  Found {len(accounts)} distinct accounts:")
        for acc in accounts:
            print(f"    - {acc[0]}")
    else:
        print("  'account' column not found in messages table")
except Exception as e:
    print(f"  Error: {e}")

# Check for other potential account-related columns
print("\n=== Looking for Account-Related Columns ===")
try:
    cursor.execute("PRAGMA table_info(messages)")
    columns = [col[1] for col in cursor.fetchall()]
    account_cols = [col for col in columns if 'account' in col.lower() or 'mailbox' in col.lower()]
    print(f"  Found columns: {account_cols}")
except Exception as e:
    print(f"  Error: {e}")

conn.close()


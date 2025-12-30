#!/usr/bin/env python3
"""
inspect_outlook_db.py - Inspect Outlook SQLite database structure

This script explores the Outlook database schema to understand:
- Table structure
- Column names
- Sample data
"""

import sqlite3
from pathlib import Path
import sys

def find_outlook_db():
    """Find Outlook database location."""
    # Try Outlook 2016/2019/365 location
    db_path = Path.home() / "Library" / "Group Containers" / "UBF8T346G9.Office" / "Outlook" / "Outlook 15 Profiles" / "Main Profile" / "Data" / "Outlook.sqlite"
    
    if db_path.exists():
        return str(db_path)
    
    # Try alternative location
    db_path = Path.home() / "Library" / "Group Containers" / "UBF8T346G9.Office" / "Outlook" / "Outlook 15 Profiles" / "Main Profile" / "Outlook.sqlite"
    
    if db_path.exists():
        return str(db_path)
    
    return None

def inspect_database(db_path: str):
    """Inspect Outlook database structure."""
    print(f"Connecting to: {db_path}\n")
    
    try:
        conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get all tables
        print("=" * 80)
        print("TABLES")
        print("=" * 80)
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = cursor.fetchall()
        
        for table in tables:
            table_name = table[0]
            print(f"\n{table_name}")
            print("-" * 80)
            
            # Get table schema
            try:
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns = cursor.fetchall()
                
                if columns:
                    print("Columns:")
                    for col in columns[:20]:  # Limit to first 20 columns
                        col_name = col[1]
                        col_type = col[2]
                        nullable = "NULL" if not col[3] else "NOT NULL"
                        print(f"  {col_name:30s} {col_type:15s} {nullable}")
                    
                    if len(columns) > 20:
                        print(f"  ... and {len(columns) - 20} more columns")
                    
                    # Try to get row count
                    try:
                        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                        count = cursor.fetchone()[0]
                        print(f"\nRow count: {count}")
                    except:
                        pass
                    
                    # Try to get sample data (if it looks like a messages table)
                    if 'message' in table_name.lower() or 'mail' in table_name.lower() or 'item' in table_name.lower():
                        try:
                            cursor.execute(f"SELECT * FROM {table_name} LIMIT 1")
                            sample = cursor.fetchone()
                            if sample:
                                print("\nSample row:")
                                for key in sample.keys()[:10]:  # First 10 columns
                                    value = sample[key]
                                    if isinstance(value, str) and len(value) > 50:
                                        value = value[:50] + "..."
                                    print(f"  {key:30s} = {value}")
                        except Exception as e:
                            print(f"  Could not read sample: {e}")
                
            except Exception as e:
                print(f"  Error reading table: {e}")
        
        conn.close()
        
    except sqlite3.Error as e:
        print(f"ERROR: {e}")
        return False
    
    return True

def main():
    """Main entry point."""
    db_path = find_outlook_db()
    
    if not db_path:
        print("ERROR: Could not find Outlook database.")
        print("\nTried locations:")
        print("  ~/Library/Group Containers/UBF8T346G9.Office/Outlook/Outlook 15 Profiles/Main Profile/Data/Outlook.sqlite")
        print("  ~/Library/Group Containers/UBF8T346G9.Office/Outlook/Outlook 15 Profiles/Main Profile/Outlook.sqlite")
        sys.exit(1)
    
    print("Outlook Database Inspector")
    print("=" * 80)
    print()
    
    if inspect_database(db_path):
        print("\n" + "=" * 80)
        print("Inspection complete!")
        print("=" * 80)
    else:
        print("\nInspection failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()


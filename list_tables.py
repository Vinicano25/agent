#!/usr/bin/env python3
"""
Script to list all tables from the estrutura.json.txt file.

This script reads the database structure from the JSON file and displays
all table names in a formatted list.
"""

import json
import sys
from pathlib import Path


def list_tables(json_file_path):
    """
    Read the JSON file and list all tables.
    
    Args:
        json_file_path: Path to the estrutura.json.txt file
        
    Returns:
        tuple: (database_name, list of table names)
    """
    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        database_name = data.get('database_name', 'Unknown')
        tables = [table['table_name'] for table in data.get('tables', [])]
        
        return database_name, tables
    except FileNotFoundError:
        print(f"Error: File not found: {json_file_path}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON format: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyError as e:
        print(f"Error: Missing expected key in JSON: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    """Main function to execute the script."""
    # Default path to the estrutura.json.txt file
    script_dir = Path(__file__).parent
    default_file = script_dir / 'knowledge' / 'estrutura.json.txt'
    
    # Allow custom file path as command line argument
    if len(sys.argv) > 1:
        json_file = Path(sys.argv[1])
    else:
        json_file = default_file
    
    if not json_file.exists():
        print(f"Error: File does not exist: {json_file}", file=sys.stderr)
        sys.exit(1)
    
    # Read and list tables
    database_name, tables = list_tables(json_file)
    
    # Display results
    print(f"Database: {database_name}")
    print(f"Total number of tables: {len(tables)}")
    print("\nTables:")
    print("-" * 50)
    
    for i, table_name in enumerate(tables, 1):
        print(f"{i:3}. {table_name}")
    
    print("-" * 50)
    print(f"\nTotal: {len(tables)} tables")


if __name__ == "__main__":
    main()

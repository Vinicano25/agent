# Database Structure Analyzer

This repository contains tools to analyze and list database table structures from the `estrutura.json.txt` file.

## Files

- `list_tables.py` - Python script to list all tables from the database structure file
- `knowledge/estrutura.json.txt` - JSON file containing the database structure (355 tables from the 'dsm' database)

## Usage

### List all tables

To list all tables from the database structure file:

```bash
python3 list_tables.py
```

### Use with a custom file

You can also specify a custom JSON file path:

```bash
python3 list_tables.py path/to/your/file.json
```

## Output

The script displays:
- Database name
- Total number of tables
- Numbered list of all table names
- Final count summary

Example output:
```
Database: dsm
Total number of tables: 355

Tables:
--------------------------------------------------
  1. Integracao_Status
  2. Centro_Custo_Dieta
  3. Peso
  ...
--------------------------------------------------

Total: 355 tables
```

## Requirements

- Python 3.6 or higher
- No external dependencies (uses only Python standard library)

## Database Structure

The database analyzed (`dsm`) contains 355 tables covering various aspects of agricultural/livestock management, including:
- Animal tracking and management
- Financial/cost control
- Feed/nutrition management  
- Veterinary records
- GTA (animal transport) documentation
- Reports and analytics

## File Format

The `estrutura.json.txt` file follows this structure:

```json
{
  "database_name": "dsm",
  "tables": [
    {
      "table_name": "TableName",
      "columns": [
        {
          "column_name": "column_name",
          "data_type": "data_type",
          "max_length": 123,
          "is_nullable": true/false,
          "primary_key": 0/1
        }
      ]
    }
  ]
}
```

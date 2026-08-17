import re
import sys
import os

def clean_mysql_line(line):
    if not line or line.startswith(('--', '/*', 'LOCK TABLES', 'UNLOCK TABLES', 'DROP TABLE', 'SET ', '/*!')):
        return None
    
    # Replace backticks with double quotes for SQLite
    line = line.replace('`', '"')
    
    if line.startswith('INSERT INTO'):
        # Convert MySQL escapes to SQLite double-single quotes
        # This is a simple heuristic; smart_import.py is more robust for complex data
        line = line.replace("\\'", "''")
        return line
    
    return None

def convert(input_file, output_file):
    print(f"Converting {input_file} to {output_file}...")
    
    tables = set()
    # First pass to find all tables mentioned in INSERTs
    with open(input_file, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            if line.startswith('INSERT INTO'):
                match = re.search(r'INSERT INTO [`"]([^`"]+)[`"]', line)
                if match:
                    tables.add(match.group(1))
    
    with open(input_file, 'r', encoding='utf-8', errors='ignore') as f:
        with open(output_file, 'w', encoding='utf-8') as out:
            out.write("PRAGMA foreign_keys=OFF;\n")
            out.write("BEGIN TRANSACTION;\n")
            
            # Clear all tables first to avoid duplicates
            for table in sorted(list(tables)):
                out.write(f'DELETE FROM "{table}";\n')
            
            for line in f:
                converted = clean_mysql_line(line)
                if converted:
                    out.write(converted)
            
            out.write("COMMIT;\n")
            out.write("PRAGMA foreign_keys=ON;\n")
    
    print(f"Done! Created {output_file}")
    print(f"You can now run: sqlite3 db.sqlite3 < {output_file}")

if __name__ == '__main__':
    input_f = 'dump.sql'
    output_f = 'data_only.sql'
    if not os.path.exists(input_f):
        print(f"Error: {input_f} not found.")
        sys.exit(1)
    convert(input_f, output_f)

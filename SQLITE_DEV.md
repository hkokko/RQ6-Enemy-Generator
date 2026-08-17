# SQLite Development Quick Start

This guide explains how to run the Mythras Encounter Generator locally using SQLite while maintaining compatibility with the default MySQL production database.

---

### 1. Environment Setup
The project requires a `temp/` directory and installed dependencies.

```bash
# Automated setup (creates temp/ and installs requirements)
chmod +x setup_sqlite.sh
./setup_sqlite.sh
```

---

### 2. Database Configuration
You can switch between MySQL and SQLite using the `USE_SQLITE` environment variable.

#### Option A: Use MySQL (Default)
Run the app normally. Ensure your `mythras_eg/settings.py` (copied from `settings_example.py`) has your MySQL credentials.

#### Option B: Use SQLite
Set `USE_SQLITE=1` in your environment:
```bash
export USE_SQLITE=1
python3 manage.py runserver
```

---

### 3. Importing Production Data (MySQL to SQLite)

If you have a MySQL dump (`dump.sql`), follow these steps to import it into SQLite.

#### Step 1: Initialize SQLite Schema
```bash
export USE_SQLITE=1
python3 manage.py migrate
```

#### Step 2: Convert and Import Data
You have two methods to import the data:

**Method A: Direct Import (Recommended)**
Use the `smart_import.py` script. it handles complex data, multi-line strings, and column mapping automatically.
```bash
python3 smart_import.py
```

**Method B: SQL Export/Import**
Use `mysql_to_sqlite_data.py` to create a compatible SQL file that can be uploaded via the `sqlite3` CLI.
```bash
# 1. Create the SQLite-compatible data file
python3 mysql_to_sqlite_data.py
# (Creates data_only.sql)

# 2. Upload the data to SQLite
sqlite3 db.sqlite3 < data_only.sql
```

#### Step 3: Synchronize Migration History
After importing data, you must tell Django that the schema is already up to date:
```bash
export USE_SQLITE=1
python3 manage.py migrate --fake-initial
python3 manage.py migrate --fake
```

---

### 4. Verification
Run the tests to ensure everything is working correctly:
```bash
export USE_SQLITE=1
python3 manage.py test
```

---

### Summary of Scripts
- `setup_sqlite.sh`: Automates initial environment setup.
- `smart_import.py`: Robustly imports data from `dump.sql` directly into `db.sqlite3`.
- `mysql_to_sqlite_data.py`: Converts `dump.sql` into a `data_only.sql` file for manual SQLite import.
- `verify_migration.py`: Compares record counts between MySQL dump and SQLite database.

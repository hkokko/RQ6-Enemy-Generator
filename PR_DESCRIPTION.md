### **Pull Request Description: Add SQLite support for local development**

#### **Summary**
This Pull Request introduces SQLite support for the Mythras Encounter Generator to simplify local development and onboarding. It allows developers to run the application and execute tests without requiring a full MySQL installation.

#### **Motivation**
Setting up a local MySQL instance can be a barrier for new contributors. By providing an automated SQLite setup, we lower the entry barrier while maintaining full compatibility with the production MySQL environment.

#### **Changes**
- **Database Engine Switching**: Modified `mythras_eg/settings_example.py` to support a `USE_SQLITE` environment variable.
- **Automated Setup**: Added `setup_sqlite.sh` to initialize the environment, install dependencies, and seed the database.
- **Data Migration Tools**: 
    - `smart_import.py`: A robust script to import production data from a MySQL dump into SQLite, handling schema mapping and multi-line strings.
    - `mysql_to_sqlite_data.py`: A utility to convert MySQL data into SQLite-compatible SQL.
    - `verify_migration.py`: A script to compare record counts and ensure data integrity between MySQL and SQLite.
- **Documentation**: Created `SQLITE_DEV.md` with detailed instructions on how to use the new SQLite-based workflow.

#### **Verification**
- Verified that `python manage.py runserver` works with `USE_SQLITE=1`.
- Confirmed that `python manage.py test` passes using the SQLite backend.
- Successfully imported a production dump using `smart_import.py`.

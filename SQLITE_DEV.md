# SQLite Development Quick Start

Follow these steps to run the Mythras Encounter Generator locally using SQLite.

### Automated Setup
The easiest way to set up the environment is to use the provided setup script.

```bash
# Make the script executable
chmod +x setup_sqlite.sh

# Run the setup
./setup_sqlite.sh
```

---

### Manual Setup
If you prefer to perform the steps manually, follow these instructions:

### 1. Preparation
Ensure you have Python 3.11+ and a virtual environment active.

```bash
# Create the temporary directory for generated files
mkdir temp

# Install dependencies
pip install -r requirements.txt
```

**Example Output:**
```text
$ mkdir temp
$ pip install -r requirements.txt
Collecting ...
...
Successfully installed Django-3.2.25 ...
```

### 2. Configure Settings
Update `mythras_eg/settings.py` to use SQLite. You can replace the `DATABASES` block with:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(PROJECT_ROOT, 'db.sqlite3'),
    }
}
```

Ensure `STATICFILES_DIRS` and `TEMP` are also correctly set (they are by default in `settings_example.py`).

### 3. Initialize Database
```bash
# Apply migrations to create the database schema
python3 manage.py migrate

# Load initial test data (races, spells, templates, etc.)
python3 manage.py loaddata enemygen_testdata.json
```

**Example Output:**
```text
$ python3 manage.py migrate
Operations to perform:
  Apply all migrations: admin, auth, contenttypes, django_registration, enemygen, sessions, taggit
Running migrations:
  Applying contenttypes.0001_initial... OK
  Applying auth.0001_initial... OK
  ...

$ python3 manage.py loaddata enemygen_testdata.json
Installed 1998 object(s) from 1 fixture(s)
```

### 4. Run Server
```bash
python3 manage.py runserver
```

**Example Output:**
```text
$ python3 manage.py runserver
Watching for file changes with StatReloader
Performing system checks...

System check identified no issues (0 silenced).
August 15, 2026 - 19:15:23
Django version 3.2.25, using settings 'mythras_eg.settings'
Starting development server at http://127.0.0.1:8000/
Quit the server with CONTROL-C.
```
Access the app at http://127.0.0.1:8000/

### 5. Run Tests
```bash
python3 manage.py test
```

**Example Output:**
```text
$ python3 manage.py test
Found 23 test(s).
Creating test database for alias 'default'...
System check identified no issues (0 silenced).
.......................
----------------------------------------------------------------------
Ran 23 tests in 1.226s

OK
Destroying test database for alias 'default'...
```

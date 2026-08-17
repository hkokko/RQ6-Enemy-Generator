# Mythras Encounter Generator

A tool for Mythras GM's for generating enemy stats.

Hosted at https://mythras.skoll.xyz/

## Dev env installation

Mythras Encounter Generator has been tested with Python 3.11. Other versions might or might not work.

### Using MySQL (Default)
1. Copy `mythras_eg/settings_example.py` to `mythras_eg/settings.py`
2. Fill in your MySQL database configuration.
3. Install requirements: `pip install -r requirements.txt`
4. Create a folder named `temp` in the project directory.

### Using SQLite (Development Alternative)
For a faster setup without MySQL, you can use SQLite. See **[SQLITE_DEV.md](SQLITE_DEV.md)** for detailed instructions on automated setup and importing production data.

### WeasyPrint

If you want to use PDF/PNG export features, follow OS-specific installation instructions for WeasyPrint at
https://doc.courtbouillon.org/weasyprint/stable/

## Start Dev env

`python manage.py runserver`

## Unit tests

`python manage.py test`

## AWS Setup reminder list

* Add IPv6 to the VPC
* Create a subnet with IPv6 and Private IPv4
* Add IPv6 to Routing table - Internet Gateway (not Egress Only)
* Create EC2 instance
  * Disable public IPv4 address
* Connect using EC2 Connect Endpoint
* Run script `setup.sh`

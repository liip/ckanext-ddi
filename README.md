ckanext-ddi
===========

**IMPORTANT: This extension is work in progress (WIP)**

DDI extension for CKAN for the Worldbank.

Planned Features:

* Harvest DDI data
* Manage DDI data manually via the CKAN frontend
* Upload DDI files (XML) to a CKAN instance
* Provide data from CKAN as DDI

## Usage

This plugin provides the possibility to import DDI XML files using a paster command.
The file can either be loaded from a local path or a publicly available URL.

```bash
paster --plugin=ckanext-ddi ddi import <path_or_url> -c <path to config file>
```

## Installation

Use `pip` to install this plugin. This example installs it in `/home/www-data`

```bash
source /home/www-data/pyenv/bin/activate
pip install -e git+https://github.com/liip/ckanext-ddi.git#egg=ckanext-ddi --src /home/www-data
cd /home/www-data/ckanext-ddi
pip install -r requirements.txt
python setup.py develop
```

Make sure to add `ddi` and `ddi_harvester` to `ckan.plugins` in your config file.

## Run harvester

```bash
source /home/www-data/pyenv/bin/activate
paster --plugin=ckanext-ddi harvester gather_consumer -c development.ini &
paster --plugin=ckanext-ddi harvester fetch_consumer -c development.ini &
paster --plugin=ckanext-ddi harvester run -c development.ini
```

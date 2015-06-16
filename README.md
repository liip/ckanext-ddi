[![Build Status](https://travis-ci.org/liip/ckanext-ddi.svg?branch=master)](https://travis-ci.org/liip/ckanext-ddi)

ckanext-ddi
===========

DDI extension for CKAN for the Worldbank.

Features:

* Import DDI data
* Manage DDI data manually via the CKAN frontend
* Upload DDI files (XML) to a CKAN instance
* Harvest data from a [NADA](http://www.ihsn.org/home/projects/NADA-development) instance


## Installation

Use `pip` to install this plugin. This example installs it in `/home/www-data`

```bash
source /home/www-data/pyenv/bin/activate
pip install -e git+https://github.com/liip/ckanext-ddi.git#egg=ckanext-ddi --src /home/www-data
cd /home/www-data/ckanext-ddi
pip install -r requirements.txt
python setup.py develop
```

Make sure to add `ddi_schema`, `ddi_theme` and `nada_harvester` to `ckan.plugins` in your config file.
If you don't want to use the frontend-part of this extension, you can omit the `ddi_theme`.

To use the `nada_harvester`, make sure the [ckanext-harvest extension](https://github.com/ckan/ckanext-harvest) is installed as well.

## Configuration

### CKAN configuration (production.ini)
Two options are available:

```bash
ckanext.ddi.config_file = /path/to/my/config.yml
ckanext.ddi.default_license = CC0-1.0
```

The `config_file` is simply the path to the DDI-specific configuration of this extension (see below).
The `default_license` allows a user to configure a license that is used for all DDI imports, if the license is not specified explicitly.

### DDI fields configuration
The display and structure of the DDI fields can be configured individually. A separate YAML config file is used for that.

There are 3 sections:

1. `sections`: describes different section, used to group together `fields`
2. `vocabularies`: describes availables controlled vocabularies, that can be referenced
3. `fields`: describes all fields, their type and how they are displayed. Only the predefined fields can be used:
    * `id`
    * `name`
    * `title`
    * `url`
    * `author`
    * `author_email`
    * `maintainer`
    * `maintainer_email`
    * `license_id`
    * `copyright`
    * `version`
    * `version_notes`
    * `notes`
    * `tags`
    * `abbreviation`
    * `study_type`
    * `series_info`
    * `id_number`
    * `description`
    * `production_type`
    * `production_date`
    * `abstract`
    * `kind_of_data`
    * `unit_of_analysis`
    * `description_of_scope`
    * `country`
    * `geographic_coverage`
    * `time_period_covered`
    * `universe`
    * `primary_investigator`
    * `other_producers`
    * `funding`
    * `sampling_procedure`
    * `data_collection_dates`
    * `access_authority`
    * `conditions`
    * `citation_requirement`
    * `contact_persons`

Example:

```bash
fields:
    identification:
        title:
            type: text
            visible: False
            display: Title
        url:
            type: url
            display_field: title
            visible: True
            display: Source
    overview:
        abstract:
            type: markdown
            visible: True
            display: Abstract
        kind_of_data:
            type: vocabulary
            visible: True
            display: Kind of Data

vocabularies:
    kind_of_data:
        - Sample survey data [ssd]
        - Census/enumeration data [cen]
        - Administrative records data [adm]
        - Aggregate data [agg]
        - Clinical data [cli]
        - Event/transaction data [evn]
        - Observation data/ratings [obs]
        - Process-produced data [pro]

sections:
    identification: Identification
    overview: Overview
```

Based on this configuration the web UI is generated:

![Dataset page](https://raw.github.com/liip/ckanext-ddi/master/screenshots/dataset_view.png)

## Usage
Data can be imported either via command line or using the web interface.

### Web interface
If you are logged in and you have the appropriate permissions, you find a new button "Import Dataset from DDI/XML" on the dataset page.

![Import Dataset from DDI/XML button](https://raw.github.com/liip/ckanext-ddi/master/screenshots/add_dataset_button.png)

This buttons leads you to an import page, where a DDI XML can either be uploaded or specified as URL.

![Import Dataset page](https://raw.github.com/liip/ckanext-ddi/master/screenshots/import_dataset.png)

Instead of importing the DDI data, you can manually add datasets just like you would on any CKAN instance.
The "Add Dataset" form is modified, so you can find all the fields from your DDI configuration (see above).

![Dataset form](https://raw.github.com/liip/ckanext-ddi/master/screenshots/manual_dataset.png)


### Run import from command line
This plugin provides the possibility to import DDI XML files using a paster command.

```bash
source /home/www-data/pyenv/bin/activate
paster --plugin=ckanext-ddi ddi import <path_or_url> [<license>] -c <path to config file>
```

* `<path_or_url>` is a required parameter and - as the name implies - it can can either be a local file or a publicly accessible URL.
* `<license>` is an optional parameter to specify the license of the dataset. Ideally this is a value from the [configured license group file](http://docs.ckan.org/en/943-writing-extensions-tutorial/configuration.html#licenses-group-url).

### NADA harvester
To add a NADA harvester, you should be logged in and visit `/harvest` on your CKAN installation (e.g. http://my.ckaninstance.org/harvest).
There you can add a new harvest source with the type "NADA harvester for DDI".

In the URL field, specify the base URL of your NADA instance. If the start page of your NADA instance is my.nada-instance.org/index.php/home, then please specify http://my.nada-instance.org as the URL for the harvester.

![Example configuration for NADA harvester](https://raw.github.com/liip/ckanext-ddi/master/screenshots/nada_harvester_config.png)

You can specify the configuration as JSON:

* `user`: the CKAN user to perform the harvesting (default: `harvest`)
* `license`: A default license to apply to all harvested datasets (default: empty). If this is not specified the config value `ckanext.ddi.default_license` is used (see above).
* `access_type`: Parameter for NADA to specify the the data access type of the datasets, that should be harvester (default: `public_use`)

Possible values for `access_type`:
* `direct_access`
* `public_use`
* `licensed`
* `data_enclave`
* `data_external`
* `no_data_available`
* `open_data`

JSON example:
```bash
{"user": "harvest", "access_type": "public_use", "license": "CC-BY-SA-4.0"}
```


## Development

This CKAN extensions uses flake8 to ensure basic code quality.

You can add a pre-commit hook when you have installed flake8:

```bash
flake8 --install-hook
```

Travis CI is used to check the code for all PRs.

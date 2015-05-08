from setuptools import setup, find_packages
import sys, os

version = '0.1'

setup(
    name='ckanext-ddi',
    version=version,
    description="CKAN extension for the DDI standard format for the Worldbank",
    long_description="""\
    """,
    classifiers=[], # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
    keywords='',
    author='Liip AG',
    author_email='ogd@liip.ch',
    url='http://www.liip.ch',
    license='GPL',
    packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
    namespace_packages=['ckanext', 'ckanext.ddi'],
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        # -*- Extra requirements: -*-
    ],
    entry_points=\
    """
    [ckan.plugins]
    ddi=ckanext.ddi.plugins:DdiHarvest
    ddi_harvester=ckanext.ddi.harvesters:DdiHarvester
    ddi_theme=ckanext.ddi.plugins:DdiTheme
    ddi_schema=ckanext.ddi.plugins:DdiSchema
    ddi_import=ckanext.ddi.plugins:DdiImport
    [paste.paster_command]
    harvester=ckanext.ddi.commands.harvester:Harvester
    ddi=ckanext.ddi.commands.ddi:DdiCommand
    """,
)

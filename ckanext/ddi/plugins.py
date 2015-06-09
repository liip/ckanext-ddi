# -*- coding: utf-8 -*-

import ckan.plugins as plugins
import ckan.plugins.toolkit as tk
import yaml
from collections import OrderedDict
from importer import ddiimporter

import logging
from pylons import config
log = logging.getLogger(__name__)


def ordered_load(stream, Loader=yaml.Loader, object_pairs_hook=OrderedDict):
    class OrderedLoader(Loader):
        pass

    def construct_mapping(loader, node):
        loader.flatten_mapping(node)
        return object_pairs_hook(loader.construct_pairs(node))
    OrderedLoader.add_constructor(
        yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
        construct_mapping)
    return yaml.load(stream, OrderedLoader)


def get_ddi_config():
    with open(config.get('ckanext.ddi.config_file')) as config_file:
        ddi_config = ordered_load(config_file)
    return ddi_config


def get_vocabulary_values(vocabulary):
    """
    Given the name of a vocabulary, get the accepted values for it
    """
    log.debug(vocabulary)
    log.debug(get_ddi_config()['vocabularies'])
    values = get_ddi_config()['vocabularies'][vocabulary]
    log.debug(values)
    return values


def get_package_dict(dataset_id):
    if dataset_id:
        user = tk.get_action('get_site_user')({}, {})
        context = {'user': user['name']}
        return tk.get_action('package_show')(context, {'id': dataset_id})
    return None


def import_from_xml():
    importer = ddiimporter.DdiImporter
    importer.run(
        url='http://microdata.statistics.gov.rw/index.php/catalog/ddi/26'
    )


class DdiImport(plugins.SingletonPlugin):
    plugins.implements(plugins.IRoutes)
    plugins.implements(plugins.IConfigurer)

    def before_map(self, map):
        map.connect(
            '/dataset/import',
            controller='ckanext.ddi.controllers:ImportFromXml',
            action='import_form'
        )
        map.connect(
            '/dataset/importfile',
            controller='ckanext.ddi.controllers:ImportFromXml',
            action='run_import'
        )
        return map

    def after_map(self, map):
        return map

    def update_config(self, config):
        tk.add_template_directory(config, 'templates')


class DdiSchema(plugins.SingletonPlugin, tk.DefaultDatasetForm):
    """
    Plugin containing the extended schema for ddi for the World Bank
    """

    plugins.implements(plugins.IConfigurer, inherit=False)
    plugins.implements(plugins.IDatasetForm, inherit=False)

    def update_config(self, config):
        pass

    def get_helpers(self):
        return {}

    def is_fallback(self):
        # Return True to register this plugin as the default handler for
        # package types not handled by any other IDatasetForm plugin.
        return True

    def package_types(self):
        # This plugin doesn't handle any special package types, it just
        # registers itself as the default (above).
        return []

    def _modify_package_schema(self, schema):
        # Add new fields from the config as extras
        fields = get_ddi_config()['fields']

        for section in fields:
            for field in fields[section]:
                    schema.update({
                        field: [tk.get_validator('ignore_missing'),
                                tk.get_converter('convert_to_extras')]
                    })

        return schema

    def create_package_schema(self):
        schema = super(DdiSchema, self).create_package_schema()
        schema = self._modify_package_schema(schema)
        return schema

    def update_package_schema(self):
        schema = super(DdiSchema, self).update_package_schema()
        schema = self._modify_package_schema(schema)
        return schema

    def show_package_schema(self):
        schema = super(DdiSchema, self).show_package_schema()

        # Don't show vocab tags mixed in with normal 'free' tags
        # (e.g. on dataset pages, or on the search page)
        schema['tags']['__extras'].append(tk.get_converter('free_tags_only'))

        # Add new fields from the config to the dataset schema.
        fields = get_ddi_config()['fields']

        for section in fields:
            for field in fields[section]:
                schema.update({
                    field: [tk.get_converter('convert_from_extras'),
                            tk.get_validator('ignore_missing')]
                })

        return schema


class DdiTheme(plugins.SingletonPlugin, tk.DefaultDatasetForm):
    """
    Plugin containing the theme for ddi for the World Bank
    """

    plugins.implements(plugins.IConfigurer, inherit=False)
    plugins.implements(plugins.ITemplateHelpers, inherit=False)

    ddi_config = None

    def update_config(self, config):
        self.ddi_config = yaml.load(config.get('ckanext.ddi.config_file'))
        tk.add_template_directory(config, 'templates')
        tk.add_public_directory(config, 'public')
        log.debug("update config")

    def get_helpers(self):
        log.debug("get_helpers")
        return {
            'ddi_theme_get_ddi_config': get_ddi_config,
            'ddi_theme_get_vocabulary_values': get_vocabulary_values,
            'ddi_theme_get_package_dict': get_package_dict,
            'ddi_theme_import_from_xml': import_from_xml
        }

    def is_fallback(self):
        # Return True to register this plugin as the default handler for
        # package types not handled by any other IDatasetForm plugin.
        return False

    def package_types(self):
        # This plugin doesn't handle any special package types, it just
        # registers itself as the default (above).
        return []

    def setup_template_variables(self, context, data_dict):
        context['ddi_config'] = self.ddi_config
        return super(DdiTheme, self).setup_template_variables(
            context, data_dict
        )

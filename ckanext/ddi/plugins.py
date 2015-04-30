# -*- coding: utf-8 -*-

import ckan.plugins as plugins
import ckan.plugins.toolkit as tk
import yaml
from collections import OrderedDict

import logging
from pylons import config
log = logging.getLogger(__name__)


class DdiHarvest(plugins.SingletonPlugin):
    """
    Plugin containing the harvester for ddi for
    the World Bank
    """


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


def create_vocabularies():
    """
    Create vocabularies from config, if they don't exist already
    """
    user = tk.get_action('get_site_user')({'ignore_auth': True}, {})
    context = {'user': user['name']}
    vocabularies = get_ddi_config()['vocabularies']

    for vocab in vocabularies:
        try:
            data = {'id': vocab}
            tk.get_action('vocabulary_show')(context, data)
            logging.info('Vocabulary ' + vocab + ' already exists')
        except tk.ObjectNotFound:
            logging.info('Creating vocabulary ' + vocab)
            data = {'name': vocab}
            new_vocab = tk.get_action('vocabulary_create')(context, data)
            # Add a blank value to the list of values in the vocabulary
            vocabularies[vocab].append('    ')

            for tag in vocabularies[vocab]:
                logging.info(
                    "Adding tag {0} to vocab 'updateInterval'".format(tag))
                data = {'name': tag, 'vocabulary_id': new_vocab['id']}
                tk.get_action('tag_create')(context, data)


def get_vocabulary(vocabulary):
    try:
        return tk.get_action('tag_list')(data_dict={'vocabulary_id': vocabulary})
    except tk.ObjectNotFound:
        logging.info('Could not get tags for vocabulary ' + vocabulary)

        return None


def get_vocabulary_values(package_dict):
    results = {}
    vocabularies = get_ddi_config()['vocabularies']

    for vocab in vocabularies:
        results[vocab] = ['    ']

    try:
        extras = package_dict['extras']
        for extra in extras:
            for vocab in vocabularies:
                if extra['key'] == vocab:
                    results[vocab].append(extra['value'])

        return results

    except KeyError as e:
        logging.info(e)
        return results


def get_package_dict(dataset_id):
    user = tk.get_action('get_site_user')({}, {})
    context = {'user': user['name']}
    return tk.get_action('package_show')(context, {'id': dataset_id})


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
                if fields[section][field]['type'] == 'vocabulary':
                    schema.update({
                        field: [tk.get_validator('ignore_missing'),
                                tk.get_converter('convert_to_tags')(field)]
                    })
                else:
                    schema.update({
                        field: [tk.get_validator('ignore_missing'),
                                tk.get_converter('convert_to_extras')]
                    })

        return schema

    def create_package_schema(self):
        create_vocabularies()
        schema = super(DdiSchema, self).create_package_schema()
        schema = self._modify_package_schema(schema)
        return schema

    def update_package_schema(self):
        create_vocabularies()
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
                if fields[section][field]['type'] == 'vocabulary':
                    schema.update({
                        field: [tk.get_converter('convert_from_tags')(field),
                                tk.get_validator('ignore_missing')]
                    })
                else:
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
            'ddi_theme_get_vocabulary': get_vocabulary,
            'ddi_theme_get_vocabulary_values': get_vocabulary_values,
            'ddi_theme_get_package_dict': get_package_dict
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

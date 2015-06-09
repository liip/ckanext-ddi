import requests
import codecs
from pprint import pprint

from ckan.lib.munge import munge_title_to_name
from ckanext.harvest.harvesters import HarvesterBase
from ckanext.ddi.importer import metadata

import ckanapi

import logging
from pylons import config
log = logging.getLogger(__name__)


class DdiImporter(HarvesterBase):
    def __init__(self, username=None):
        self.username = username

    def run(self, file_path=None, url=None, params=None):
        pkg_dict = None
        ckan_metadata = metadata.DdiCkanMetadata()
        if file_path is not None:
            with codecs.open(file_path, 'r', encoding='utf-8') as xml_file:
                pkg_dict = ckan_metadata.load(xml_file.read())
        elif url is not None:
            log.debug('Fetch file from %s' % url)
            try:
                r = requests.get(url)
            except requests.exceptions.RequestException, e:
                raise ContentFetchError(
                    'Error while getting URL %s: %r'
                    % (url, e)
                )
            r.encoding = 'utf-8'
            xml_file = r.text

            pkg_dict = ckan_metadata.load(xml_file)
            if pkg_dict['url'] == '':
                pkg_dict['url'] = url

            resources = []
            resources.append({
                'url': url,
                'name': pkg_dict['title'],
                'format': 'xml'
            })
            pkg_dict['resources'] = resources

        pkg_dict = self.improve_pkg_dict(pkg_dict, params)
        try:
            return self.insert_or_update_pkg(pkg_dict)
        except Exception, e:
            raise ContentImportError(
                'Could not import package %s: %s'
                % (pkg_dict['name'], e)
            )

    def insert_or_update_pkg(self, pkg_dict):
        registry = ckanapi.LocalCKAN(username=self.username)
        if pkg_dict['id'] and pkg_dict['id'] != '':
            try:
                existing_pkg = registry.call_action('package_show', pkg_dict)
                del pkg_dict['name']
                existing_pkg.update(pkg_dict)
                pkg_dict = existing_pkg
                registry.call_action('package_update', pkg_dict)
            except ckanapi.NotFound:
                del pkg_dict['id']
                pkg_dict['name'] = self._gen_new_name(pkg_dict['name'])
                registry.call_action('package_create', pkg_dict)
        else:
            del pkg_dict['id']
            registry.call_action('package_create', pkg_dict)

        pprint(pkg_dict)
        return pkg_dict['name']

    def improve_pkg_dict(self, pkg_dict, params):
        if pkg_dict['name'] != '':
            pkg_dict['name'] = munge_title_to_name(pkg_dict['name'])
        else:
            pkg_dict['name'] = munge_title_to_name(pkg_dict['title'])
        if pkg_dict['url'] == '':
            del pkg_dict['url']

        if params is not None and params.get(license, None) is not None:
            pkg_dict['license_id'] = params['license']
        else:
            pkg_dict['license_id'] = config.get('ckanext.ddi.default_license')

        return pkg_dict


class ContentFetchError(Exception):
    pass


class ContentImportError(Exception):
    pass

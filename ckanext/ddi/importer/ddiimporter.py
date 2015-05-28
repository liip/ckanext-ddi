import requests
import traceback
from pprint import pprint

from ckan.lib.munge import munge_title_to_name
from ckanext.harvest.harvesters import HarvesterBase
from ckanext.ddi.importer import metadata

import ckanapi

import logging
from pylons import config
log = logging.getLogger(__name__)


class DdiImporter(HarvesterBase):
    def run(self, file_path=None, url=None, params=None):
        pkg_dict = None
        ckan_metadata = metadata.DdiCkanMetadata()
        if file_path is not None:
            with open(file_path) as xml_file:
                pkg_dict = ckan_metadata.load(xml_file.read())
        elif url is not None:
            log.debug('Fetch file from %s' % url)
            r = requests.get(url)
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
        return self.insert_or_update_pkg(pkg_dict)

    def insert_or_update_pkg(self, pkg_dict):
        try:
            registry = ckanapi.LocalCKAN()
            pprint(pkg_dict)
            if pkg_dict['id'] and pkg_dict['id'] != '':
                try:
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
        except:
            traceback.print_exc()

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

from pprint import pprint

import requests

from ckan.lib.munge import munge_title_to_name

from ckanext.harvest.harvesters import HarvesterBase

from ckanext.ddi.importer import metadata

import ckanapi

import logging
log = logging.getLogger(__name__)


class DdiImporter(HarvesterBase):
    def run(self, file_path=None, url=None):
        pkg_dict = None
        ckan_metadata = metadata.DdiCkanMetadata()
        if file_path is not None:
            with open(file_path) as xml_file:
                pkg_dict = ckan_metadata.load(xml_file.read())
        elif url is not None:
            log.debug('Fetch file from %s' % url)
            r = requests.get(url)
            xml_file = r.text

            # fd, temp_path = tempfile.mkstemp()
            # fd.write(xml_file.data)
            pkg_dict = ckan_metadata.load(xml_file)
            # os.close(fd)
            # os.remove(temp_path)

        try:
            registry = ckanapi.LocalCKAN()
            pprint(pkg_dict)
            if pkg_dict['name'] != '':
                pkg_dict['name'] = munge_title_to_name(pkg_dict['name'])
            else:
                pkg_dict['name'] = munge_title_to_name(pkg_dict['title'])
            if pkg_dict['url'] == '':
                del pkg_dict['url']
            if pkg_dict['id'] and pkg_dict['id'] != '':
                try:
                    registry.call_action('package_update', pkg_dict)
                except ckanapi.NotFound:
                    del pkg_dict['id']
                    registry.call_action('package_create', pkg_dict)
            else:
                del pkg_dict['id']
                registry.call_action('package_create', pkg_dict)
        except:
            import traceback
            traceback.print_exc()

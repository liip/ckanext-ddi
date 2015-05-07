import os
from lxml import etree
from uuid import uuid4
from pprint import pprint

import urllib3
import tempfile
import shutil

from ckan import model
from ckan.model import Session, Package
from ckan.logic import get_action, action
from ckan.lib.helpers import json
from ckanext.harvest.harvesters.base import munge_tag
from ckan.lib.munge import munge_title_to_name

from ckanext.harvest.model import HarvestObject
from ckanext.harvest.harvesters import HarvesterBase

from ckanext.ddi.importer import metadata

import ckanapi

from pylons import config

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
            http = urllib3.PoolManager()
            xml_file = http.request('GET', url)

            # fd, temp_path = tempfile.mkstemp()
            # fd.write(xml_file.data)
            pkg_dict = ckan_metadata.load(xml_file.data)
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

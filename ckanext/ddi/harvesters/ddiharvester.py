# -*- coding: utf-8 -*-

# from lxml import etree
# from uuid import uuid4

from ckan import model
from ckan.model import Session
from ckan.lib.helpers import json

from ckanext.harvest.model import HarvestObject
from ckanext.harvest.harvesters import HarvesterBase

# from pylons import config

import logging
log = logging.getLogger(__name__)


class NadaHarvester(HarvesterBase):
    '''
    The harvester for DDI data
    '''

    HARVEST_USER = 'harvest'

    config = {
        'user': u'harvest'
    }

    def info(self):
        return {
            'name': 'nada',
            'title': 'NADA harvester for DDI (Worldbank)',
            'description': 'Harvests DDI data from NADA',
            'form_config_interface': 'Text'
        }

    def _set_config(self, config_str):
        if config_str:
            self.config = json.loads(harvest_job.source.config)
        else:
            self.config = {}
        log.debug('Using config: %r' % self.config)

    def gather_stage(self, harvest_job):
        log.debug('In NadaHarvester gather_stage')
        try:
            self._set_config(harvest_job.source.config)
            base_url = harvest_job.source.url.rstrip('/')


            ids = []
            return ids
        except Exception, e:
            self._save_gather_error('Unable to get content for URL: %s: %s' % (url, str(e)), harvest_job)

    def fetch_stage(self, harvest_object):
        log.debug('In NadaHarvester fetch_stage')

        dataset_id = json.loads(harvest_object.content)['datasetID']
        log.debug(harvest_object.content)

        try:
            harvest_object.save()
            log.debug('successfully processed ' + dataset_id)
            return True
        except Exception, e:
            self._save_object_error(
                'Unable to get content for package: %s: %r' % (url, e), harvest_object)
            )
            return False

    def import_stage(self, harvest_object):
        log.debug('In NadaHarvester import_stage')

        if not harvest_object:
            log.error('No harvest object received')
            self._save_object_error(
                'Unable to get content for package: %s: %r' % (url, e), harvest_object)
            )
            return False

        try:
            package_dict = json.loads(harvest_object.content)

            package_dict['id'] = harvest_object.guid

            user = model.User.get(self.HARVEST_USER)
            # context = {
            #     'model': model,
            #     'session': Session,
            #     'user': self.HARVEST_USER
            #     }

            package = model.Package.get(package_dict['id'])
            model.PackageRole(
                package=package,
                user=user,
                role=model.Role.ADMIN
            )

            self._create_or_update_package(package_dict, harvest_object)
            Session.commit()
            return True

        except Exception, detail:
            self._save_object_error(
                'Unable to get content for package: %s: %r' % (url, e), harvest_object)
            )
            return False


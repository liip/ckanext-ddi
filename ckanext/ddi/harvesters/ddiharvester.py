#coding: utf-8

import os
from lxml import etree
from uuid import uuid4

from ckan import model
from ckan.model import Session, Package
from ckan.logic import get_action, action
from ckan.lib.helpers import json
from ckanext.harvest.harvesters.base import munge_tag
from ckan.lib.munge import munge_title_to_name

from ckanext.harvest.model import HarvestObject
from ckanext.harvest.harvesters import HarvesterBase

from pylons import config

import logging
log = logging.getLogger(__name__)


class DdiHarvester(HarvesterBase):
    '''
    The harvester for DDI data
    '''

    HARVEST_USER = 'harvest'

    config = {
        'user': u'harvest'
    }

    def info(self):
        return {
            'name': 'ddi',
            'title': 'DDI harvester (Worldbank)',
            'description': 'Harvests DDI data',
            'form_config_interface': 'Text'
        }

    def gather_stage(self, harvest_job):
        log.debug('In DdiHarvester gather_stage')

        ids = []

        return ids

    def fetch_stage(self, harvest_object):
        log.debug('In DdiHarvester fetch_stage')

        dataset_id = json.loads(harvest_object.content)['datasetID']
        log.debug(harvest_object.content)

        try:
            harvest_object.save()
            log.debug('successfully processed ' + dataset_id)
            return True
        except Exception, detail:
            log.exception(detail)
            raise

    def import_stage(self, harvest_object):
        log.debug('In DdiHarvester import_stage')

        if not harvest_object:
            log.error('No harvest object received')
            return False

        try:
            package_dict = json.loads(harvest_object.content)

            package_dict['id'] = harvest_object.guid

            user = model.User.get(self.HARVEST_USER)
            context = {
                'model': model,
                'session': Session,
                'user': self.HARVEST_USER
                }

            package = model.Package.get(package_dict['id'])
            model.PackageRole(
                package=package,
                user=user,
                role=model.Role.ADMIN
            )

            self._create_or_update_package(package_dict, harvest_object)
            Session.commit()

        except Exception, detail:
            log.exception(detail)
            raise

        return True

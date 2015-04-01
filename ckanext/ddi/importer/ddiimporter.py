from pylons import config
import yaml

class DdiImporter(object):

    def import():
        config_file = config.get('ckanext.ddi.config_file')
        ddi_config = yaml.load(config_file)

import ckan.lib.cli
import sys
from pprint import pprint

from ckanext.ddi.importer import ddiimporter

import logging
log = logging.getLogger(__name__)


class DdiCommand(ckan.lib.cli.CkanCommand):
    '''Command to handle DDI data

    Usage:

        # General usage
        paster --plugin=ckanext-ddi <command> -c <path to config file>

        # Show this help
        paster ddi help

        # Import datasets
        paster ddi import <path_or_url>

    '''
    summary = __doc__.split('\n')[0]
    usage = __doc__

    def command(self):
        # load pylons config
        self._load_config()
        options = {
            'import': self.importCmd,
            'help': self.helpCmd,
        }

        try:
            cmd = self.args[0]
            options[cmd](*self.args[1:])
        except KeyError:
            self.helpCmd()
            sys.exit(1)

    def helpCmd(self):
        print self.__doc__

    def importCmd(self, path_or_url=None):
        if path_or_url is None:
            print "Argument 'path_or_url' must be set"
            self.helpCmd()
            sys.exit(1)
        try:
            pprint(path_or_url)
            importer = ddiimporter.DdiImporter()
            if path_or_url.startswith('http:'):
                importer.run(url=path_or_url)
            else:
                importer.run(file_path=path_or_url)
        except Exception, e:
            import traceback
            traceback.print_exc()

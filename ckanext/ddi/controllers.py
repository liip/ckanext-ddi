from ckan.controllers.package import PackageController

import logging

import ckan.logic as logic
import ckan.lib.base as base
import ckan.lib.navl.dictization_functions as dict_fns
import ckan.lib.helpers as h
import ckan.model as model
import ckan.lib.plugins
import ckan.lib.render

from ckan.common import OrderedDict, _, json, request, c, g, response
from ckan.controllers.home import CACHE_PARAMETERS

from ckanext.ddi.importer import ddiimporter

log = logging.getLogger(__name__)

render = base.render
abort = base.abort
redirect = base.redirect

NotFound = logic.NotFound
NotAuthorized = logic.NotAuthorized
ValidationError = logic.ValidationError
check_access = logic.check_access
get_action = logic.get_action
tuplize_dict = logic.tuplize_dict
clean_dict = logic.clean_dict
parse_params = logic.parse_params
flatten_to_string_key = logic.flatten_to_string_key

lookup_package_plugin = ckan.lib.plugins.lookup_package_plugin


class ImportFromXml(PackageController):
    package_form = 'package/import_package_form.html'

    def import_form(self, data=None, errors=None, error_summary=None):
        package_type = self._guess_package_type(True)

        context = {'model': model, 'session': model.Session,
                   'user': c.user or c.author, 'auth_user_obj': c.userobj,
                   'save': 'save' in request.params}

        # Package needs to have a organization group in the call to
        # check_access and also to save it
        try:
            check_access('package_create', context)
        except NotAuthorized:
            abort(401, _('Unauthorized to create a package'))

        if context['save'] and not data:
            return self._save_new(context, package_type=package_type)

        data = data or clean_dict(dict_fns.unflatten(tuplize_dict(parse_params(
            request.params, ignore_keys=CACHE_PARAMETERS))))
        c.resources_json = h.json.dumps(data.get('resources', []))
        # convert tags if not supplied in data
        if data and not data.get('tag_string'):
            data['tag_string'] = ', '.join(
                h.dict_list_reduce(data.get('tags', {}), 'name'))

        errors = errors or {}
        error_summary = error_summary or {}

        # if we are creating from a group then this allows the group to be
        # set automatically
        data['group_id'] = request.params.get('group') or \
            request.params.get('groups__0__id')

        form_snippet = self.package_form
        form_vars = {'data': data, 'errors': errors,
                     'error_summary': error_summary,
                     'action': 'new',
                     'dataset_type': package_type,
                    }
        c.errors_json = h.json.dumps(errors)

        self._setup_template_variables(context, {},
                                       package_type=package_type)

        new_template = self._new_template(package_type)
        c.form = ckan.lib.render.deprecated_lazy_render(
            new_template,
            form_snippet,
            lambda: render(form_snippet, extra_vars=form_vars),
            'use of c.form is deprecated. please see '
            'ckan/templates/package/base_form_page.html for an example '
            'of the new way to include the form snippet'
            )
        return render(new_template,
                      extra_vars={'form_vars': form_vars,
                                  'form_snippet': form_snippet,
                                  'dataset_type': package_type})

    def run_import(self, data=None, errors=None, error_summary=None):
        importer = ddiimporter.DdiImporter()

        # Check whether upload is a file or a url
        # If it's a url, we pass in the url to the importer.run and call it
        # If it's a file, check whether it's a valid XML and if not, return a message
        # If it is a proper XML, pass it into the importer.run and call it

        if 'upload' in request.params and request.params['upload']:
            log.debug('upload = ' + request.params['upload'])
            id = importer.run(file_path=request.params['upload'])
        elif 'url' in request.params and request.params['url']:
            log.debug('url = ' + request.params['url'])
            id = importer.run(url=request.params['url'])

        redirect(h.url_for(controller='package', action='read', id=id))

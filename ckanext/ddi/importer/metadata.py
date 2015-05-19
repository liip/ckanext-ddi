from lxml import etree
import logging
from ckan.lib.munge import munge_title_to_name
log = logging.getLogger(__name__)

namespaces = {
    'atom': 'http://www.w3.org/2005/Atom',
    'che': 'http://www.geocat.ch/2008/che',
    'csw': 'http://www.opengis.net/cat/csw/2.0.2',
    'dc': 'http://purl.org/dc/elements/1.1/',
    'dct': 'http://purl.org/dc/terms/',
    'ddi': 'http://www.icpsr.umich.edu/DDI',
    'dif': 'http://gcmd.gsfc.nasa.gov/Aboutus/xml/dif/',
    'fgdc': 'http://www.opengis.net/cat/csw/csdgm',
    'gco': 'http://www.isotc211.org/2005/gco',
    'gmd': 'http://www.isotc211.org/2005/gmd',
    'gml': 'http://www.opengis.net/gml',
    'ogc': 'http://www.opengis.net/ogc',
    'ows': 'http://www.opengis.net/ows',
    'rim': 'urn:oasis:names:tc:ebxml-regrep:xsd:rim:3.0',
    'rdf': 'http://www.w3.org/1999/02/22-rdf-syntax-ns#',
    'srv': 'http://www.isotc211.org/2005/srv',
    'xs': 'http://www.w3.org/2001/XMLSchema',
    'xs2': 'http://www.w3.org/XML/Schema',
    'xsi': 'http://www.w3.org/2001/XMLSchema-instance',
}


class Attribute(object):
    def __init__(self, config, **kwargs):
        self._config = config
        self.env = kwargs

    def get_value(self, **kwargs):
        """ Abstract method to return the value of the attribute """
        raise NotImplementedError


class StringAttribute(Attribute):
    def get_value(self, **kwargs):
        return self._config


class XmlAttribute(Attribute):
    def get_value(self, **kwargs):
        self.env.update(kwargs)
        xml = self.env['xml']
        return etree.tostring(xml)


class XPathAttribute(Attribute):
    def get_element(self, xml, xpath):
        return xml.xpath(xpath, namespaces=namespaces)[0]

    def get_value(self, **kwargs):
        self.env.update(kwargs)
        xml = self.env['xml']

        xpath = self._config
        log.debug("XPath: %s" % (xpath))

        try:
            # this should probably return a XPathTextAttribute
            value = self.get_element(xml, xpath)
        except Exception:
            log.debug('XPath not found: %s' % xpath)
            value = ''
        return value


class XPathMultiAttribute(XPathAttribute):
    def get_element(self, xml, xpath):
        return xml.xpath(xpath, namespaces=namespaces)


class XPathTextAttribute(XPathAttribute):
    def get_value(self, **kwargs):
        value = super(XPathTextAttribute, self).get_value(**kwargs)
        return value.text.strip() if hasattr(value, 'text') else value


class XPathMultiTextAttribute(XPathMultiAttribute):
    def get_value(self, **kwargs):
        self.env.update(kwargs)
        values = super(XPathMultiTextAttribute, self).get_value(**kwargs)
        return_values = []
        for value in values:
            if hasattr(value, 'text') and value.text is not None and value.text.strip() != '':
                return_values.append(value.text.strip())
        return return_values


class CombinedAttribute(Attribute):
    def get_value(self, **kwargs):
        self.env.update(kwargs)
        value = ''
        separator = self.env['separator'] if 'separator' in self.env else ' '
        for attribute in self._config:
            new_value = attribute.get_value(**kwargs)
            if new_value is not None:
                value = value + attribute.get_value(**kwargs) + separator
        return value.strip(separator)


class MultiAttribute(Attribute):
    def get_value(self, **kwargs):
        self.env.update(kwargs)
        value = ''
        separator = self.env['separator'] if 'separator' in self.env else ' '
        for attribute in self._config:
            new_value = attribute.get_value(**kwargs)
            try:
                iterator = iter(new_value)
                for inner_attribute in iterator:
                    # it should be possible to call inner_attribute.get_value
                    # and the right thing(tm) happens'
                    if hasattr(inner_attribute, 'text'):
                        value = value + inner_attribute.text
                    else:
                        value = value + inner_attribute
                    value = value + separator
            except TypeError:
                value = value + new_value + separator
        return value.strip(separator)


class ArrayAttribute(Attribute):
    def get_value(self, **kwargs):
        self.env.update(kwargs)
        value = []
        for attribute in self._config:
            new_value = attribute.get_value(**kwargs)
            try:
                iterator = iter(new_value)
                for inner_attribute in iterator:
                    # it should be possible to call inner_attribute.get_value
                    # and the right thing(tm) happens'
                    if hasattr(inner_attribute, 'text'):
                        value.append(inner_attribute.text)
                    else:
                        value.append(inner_attribute)
            except TypeError:
                value.append(new_value)
        return value


class ArrayTextAttribute(Attribute):
    def get_value(self, **kwargs):
        self.env.update(kwargs)
        values = self._config.get_value(**kwargs)
        separator = self.env['separator'] if 'separator' in self.env else ' '
        return separator.join(values)


class ArrayDictNameAttribute(ArrayAttribute):
    def get_value(self, **kwargs):
        value = super(ArrayDictNameAttribute, self).get_value(**kwargs)
        return self.wrap_in_name_dict(value)

    def wrap_in_name_dict(self, values):
        return [{'name': munge_title_to_name(value)} for value in values]


class FirstInOrderAttribute(CombinedAttribute):
    def get_value(self, **kwargs):
        for attribute in self._config:
            value = attribute.get_value(**kwargs)
            if value != '':
                return value
        return ''


class CkanMetadata(object):
    """ Provides general access to metadata for CKAN """
    def __init__(self):
        self.metadata = dict.fromkeys([
            'id',
            'name',
            'title',
            'url',
            'author',
            'author_email',
            'maintainer',
            'maintainer_email',
            'license_url',
            'version',
            'notes',
            'tags',
            'abbreviation',
            'study_type',
            'series_info',
            'id_number',
            'description',
            'production_type',
            'abstract',
            'kind_of_data',
            'unit_of_analysis',
            'description_of_scope',
            'country',
            'geographic_coverage',
            'time_period_covered',
            'universe',
            'primary_investigator',
            'other_producers',
            'funding',
            'sampling_procedure',
            'data_collection_dates',
            'access_authority',
            'citation_requirement',
            'contact_persons'
        ])

    def get_attribute(self, ckan_attribute):
        """
            Abstract method to define the mapping of
            a ckan attribute to an XML attribute
        """
        raise NotImplementedError

    def load(self, xml_string):
        dataset_xml = etree.fromstring(xml_string)
        ckan_metadata = {}
        log.debug("heeere")
        for key in self.metadata:
            log.debug("Metadata key: %s" % key)
            attribute = self.get_attribute(key)
            ckan_metadata[key] = attribute.get_value(
                xml=dataset_xml
            )
        return ckan_metadata


class DdiCkanMetadata(CkanMetadata):
    """ Provides access to the DDI metadata """
    mapping = {
        'id': XPathTextAttribute('//ddi:codeBook/ddi:stdyDscr/ddi:citation/ddi:titlStmt/ddi:IDNo'),  # noqa
        'name': FirstInOrderAttribute([
            XPathTextAttribute(
                "//ddi:codeBook/ddi:stdyDscr/ddi:citation/ddi:titlStmt/ddi:altTitl"  # noqa
            ),
            XPathTextAttribute(
                "//ddi:codeBook/ddi:stdyDscr/ddi:citation/ddi:titlStmt/ddi:titl"  # noqa
            ),
        ]),
        'title': XPathTextAttribute(
            "//ddi:codeBook/ddi:stdyDscr/ddi:citation/ddi:titlStmt/ddi:titl"  # noqa
        ),
        'abbreviation': XPathTextAttribute(
            "//ddi:codeBook/ddi:stdyDscr/ddi:citation/ddi:titlStmt/ddi:altTitl"  # noqa
        ),
        'study_type': XPathTextAttribute(
            "//ddi:codeBook/ddi:stdyDscr/ddi:citation/ddi:serStmt/ddi:serName"  # noqa
        ),
        'series_info': XPathTextAttribute(
            "//ddi:codeBook/ddi:stdyDscr/ddi:citation/ddi:serStmt/ddi:serInfo"  # noqa
        ),
        'id_number': XPathTextAttribute(
            "//ddi:codeBook/ddi:stdyDscr/ddi:citation/ddi:titlStmt/ddi:IDNo"  # noqa
        ),
        'description': XPathTextAttribute(
            "//ddi:codeBook/ddi:stdyDscr/ddi:stdyInfo/ddi:abstract"  # noqa
        ),
        'production_type': XPathTextAttribute(
            "//ddi:codeBook/ddi:stdyDscr/ddi:method/ddi:collMode"  # noqa
        ),
        'abstract': XPathTextAttribute(
            "//ddi:codeBook/ddi:stdyDscr/ddi:stdyInfo/ddi:abstract"  # noqa
        ),
        'kind_of_data': XPathTextAttribute(
            "//ddi:codeBook/ddi:stdyDscr/ddi:stdyInfo/ddi:sumDescr/ddi:dataKind"  # noqa
        ),
        'unit_of_analysis': XPathTextAttribute(
            "//ddi:codeBook/ddi:stdyDscr/ddi:stdyInfo/ddi:sumDescr/ddi:anlyUnit"  # noqa
        ),
        'description_of_scope': XPathTextAttribute(
            "//ddi:codeBook/ddi:stdyDscr/ddi:stdyInfo/ddi:abstract"  # noqa
        ),
        'country': XPathTextAttribute(
            "//ddi:codeBook/ddi:stdyDscr/ddi:stdyInfo/ddi:sumDescr/ddi:nation"  # noqa
        ),
        'geographic_coverage': XPathTextAttribute(
            "//ddi:codeBook/ddi:stdyDscr/ddi:stdyInfo/ddi:sumDescr/ddi:geogCover"  # noqa
        ),
        'time_period_covered': ArrayTextAttribute(
            XPathMultiTextAttribute(
                "//ddi:codeBook/ddi:stdyDscr/ddi:stdyInfo/ddi:sumDescr/ddi:timePrd"  # noqa
            ),
            separator=', '
        ),
        'universe': XPathTextAttribute(
            "//ddi:codeBook/ddi:stdyDscr/ddi:stdyInfo/ddi:sumDescr/ddi:universe"  # noqa
        ),
        'primary_investigator': XPathTextAttribute(
            "//ddi:codeBook/ddi:stdyDscr/ddi:citation/ddi:rspStmt/ddi:AuthEnty"  # noqa
        ),
        'other_producers': FirstInOrderAttribute([
            ArrayTextAttribute(
                XPathMultiTextAttribute(
                    "//ddi:codeBook/ddi:stdyDscr/ddi:citation/ddi:rspStmt/ddi:othId"  # noqa
                ),
                separator=', '
            ),
            ArrayTextAttribute(
                XPathMultiTextAttribute(
                    "//ddi:codeBook/ddi:stdyDscr/ddi:citation/ddi:rspStmt/ddi:othId/ddi:p"  # noqa
                ),
                separator=', '
            ),
        ]),
        'funding': ArrayTextAttribute(
            XPathMultiTextAttribute(
                "//ddi:codeBook/ddi:stdyDscr/ddi:citation/ddi:prodStmt/ddi:fundAg"
            ),
            separator=', '
        ),
        'sampling_procedure': XPathTextAttribute(
            "//ddi:codeBook/ddi:stdyDscr/ddi:method/ddi:sampProc"  # noqa
        ),
        'data_collection_dates': ArrayTextAttribute(
            XPathMultiTextAttribute(
                "//ddi:codeBook/ddi:stdyDscr/ddi:stdyInfo/ddi:sumDescr/ddi:collDate",  # noqa
            ),
            separator=', '
        ),
        'access_authority': XPathTextAttribute(
            "//ddi:codeBook/ddi:stdyDscr/ddi:dataAccs/ddi:useStmt/ddi:contact"  # noqa
        ),
        'citation_requirement': XPathTextAttribute(
            "//ddi:codeBook/ddi:stdyDscr/ddi:dataAccs/ddi:useStmt/ddi:conditions"  # noqa
        ),
        'contact_persons': XPathTextAttribute(
            "//ddi:codeBook/ddi:stdyDscr/ddi:citation/ddi:distStmt/ddi:contact"  # noqa
        ),
        'url': XPathTextAttribute(
            "//ddi:codeBook/ddi:stdyDscr/ddi:dataAccs/ddi:setAvail/ddi:accsPlac/@URI"  # noqa
        ),
        'author': CombinedAttribute(
            [
                XPathTextAttribute('//ddi:codeBook/ddi:stdyDscr/ddi:citation/ddi:rspStmt/ddi:AuthEnty'),  # noqa
                XPathTextAttribute('//ddi:codeBook/ddi:stdyDscr/ddi:citation/ddi:contributor'),  # noqa
            ],
            separator=', '
        ),
        'author_email': StringAttribute(''),
        'maintainer': XPathTextAttribute(
            "//ddi:codeBook/ddi:stdyDscr/ddi:citation/ddi:distStmt/ddi:contact"  # noqa
        ),
        'maintainer_email': XPathTextAttribute(
            "//ddi:codeBook/ddi:stdyDscr/ddi:citation/ddi:distStmt/ddi:contact/@email"  # noqa
        ),
        'license_url': XPathTextAttribute(
            '//ddi:codeBook/ddi:stdyInfo/ddi:citation/ddi:prodStmt/ddi:copyright'  # noqa
        ),
        'version': XPathTextAttribute('//ddi:codeBook/ddi:stdyDscr/ddi:citation/ddi:verStmt/ddi:version'),  # noqa
        'notes': XPathTextAttribute(
            "//ddi:codeBook/ddi:stdyDscr/ddi:stdyInfo/ddi:notes"  # noqa
        ),
        'tags': ArrayDictNameAttribute([
            XPathMultiAttribute(
                "//ddi:codeBook/ddi:stdyDscr/ddi:stdyInfo/ddi:subject/ddi:keyword"  # noqa
            )
        ]),
    }

    def get_mapping(self):
        return self.mapping

    def get_attribute(self, ckan_attribute):
        mapping = self.get_mapping()
        if ckan_attribute in mapping:
            return mapping[ckan_attribute]
        raise AttributeMappingNotFoundError(
            "No mapping found for attribute '%s'" % ckan_attribute
        )


class AttributeMappingNotFoundError(Exception):
    pass

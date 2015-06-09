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


class Value(object):
    def __init__(self, config, **kwargs):
        self._config = config
        self.env = kwargs

    def get_value(self, **kwargs):
        """ Abstract method to return the value of the attribute """
        raise NotImplementedError


class StringValue(Value):
    def get_value(self, **kwargs):
        return self._config


class XmlValue(Value):
    def get_value(self, **kwargs):
        self.env.update(kwargs)
        xml = self.env['xml']
        return etree.tostring(xml)


class XPathValue(Value):
    def get_element(self, xml, xpath):
        return xml.xpath(xpath, namespaces=namespaces)[0]

    def get_value(self, **kwargs):
        self.env.update(kwargs)
        xml = self.env['xml']

        xpath = self._config
        log.debug("XPath: %s" % (xpath))

        try:
            # this should probably return a XPathTextValue
            value = self.get_element(xml, xpath)
        except Exception:
            log.debug('XPath not found: %s' % xpath)
            value = ''
        return value


class XPathMultiValue(XPathValue):
    def get_element(self, xml, xpath):
        return xml.xpath(xpath, namespaces=namespaces)


class XPathTextValue(XPathValue):
    def get_value(self, **kwargs):
        value = super(XPathTextValue, self).get_value(**kwargs)
        if hasattr(value, 'text') and value.text is not None:
            return value.text.strip()
        else:
            return ''


class XPathMultiTextValue(XPathMultiValue):
    def get_value(self, **kwargs):
        self.env.update(kwargs)
        values = super(XPathMultiTextValue, self).get_value(**kwargs)
        return_values = []
        for value in values:
            if (hasattr(value, 'text') and
                    value.text is not None and
                    value.text.strip() != ''):
                return_values.append(value.text.strip())
            elif isinstance(value, basestring):
                return_values.append(value)
        return return_values


class CombinedValue(Value):
    def get_value(self, **kwargs):
        self.env.update(kwargs)
        value = ''
        separator = self.env['separator'] if 'separator' in self.env else ' '
        for attribute in self._config:
            new_value = attribute.get_value(**kwargs)
            if new_value is not None:
                value = value + attribute.get_value(**kwargs) + separator
        return value.strip(separator)


class DateCollectionValue(Value):
    def get_value(self, **kwargs):
        self.env.update(kwargs)
        separator = self.env['separator'] if 'separator' in self.env else ' '

        start_dates = self._config[0].get_value(**kwargs)
        end_dates = self._config[1].get_value(**kwargs)
        cycles = self._config[2].get_value(**kwargs)

        value = ''
        for i, date in enumerate(start_dates):
            value += date + ' - '
            if i <= len(end_dates) - 1:
                value += end_dates[i]
            if i <= len(cycles) - 1:
                value += ': ' + cycles[i]
            value += separator

        return value.strip(separator)


class MultiValue(Value):
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


class ArrayValue(Value):
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


class ArrayTextValue(Value):
    def get_value(self, **kwargs):
        self.env.update(kwargs)
        values = self._config.get_value(**kwargs)
        separator = self.env['separator'] if 'separator' in self.env else ' '
        return separator.join(values)


class ArrayDictNameValue(ArrayValue):
    def get_value(self, **kwargs):
        value = super(ArrayDictNameValue, self).get_value(**kwargs)
        return self.wrap_in_name_dict(value)

    def wrap_in_name_dict(self, values):
        return [{'name': munge_title_to_name(value)} for value in values]


class FirstInOrderValue(CombinedValue):
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
            'license_id',
            'copyright',
            'version',
            'version_notes',
            'notes',
            'tags',
            'abbreviation',
            'study_type',
            'series_info',
            'id_number',
            'description',
            'production_type',
            'production_date',
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
            'conditions',
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
        try:
            dataset_xml = etree.fromstring(xml_string)
        except etree.XMLSyntaxError, e:
            raise MetadataFormatError('Could not parse XML: %r' % e)

        ckan_metadata = {}
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
        'id': XPathTextValue('//ddi:codeBook/ddi:stdyDscr/ddi:citation/ddi:titlStmt/ddi:IDNo'),  # noqa
        'name': XPathTextValue(
            "//ddi:codeBook/ddi:stdyDscr/ddi:citation/ddi:titlStmt/ddi:IDNo"  # noqa
        ),
        'title': XPathTextValue(
            "//ddi:codeBook/ddi:stdyDscr/ddi:citation/ddi:titlStmt/ddi:titl"  # noqa
        ),
        'abbreviation': XPathTextValue(
            "//ddi:codeBook/ddi:stdyDscr/ddi:citation/ddi:titlStmt/ddi:altTitl"  # noqa
        ),
        'study_type': XPathTextValue(
            "//ddi:codeBook/ddi:stdyDscr/ddi:citation/ddi:serStmt/ddi:serName"  # noqa
        ),
        'series_info': XPathTextValue(
            "//ddi:codeBook/ddi:stdyDscr/ddi:citation/ddi:serStmt/ddi:serInfo"  # noqa
        ),
        'id_number': XPathTextValue(
            "//ddi:codeBook/ddi:stdyDscr/ddi:citation/ddi:titlStmt/ddi:IDNo"  # noqa
        ),
        'description': XPathTextValue(
            "//ddi:codeBook/ddi:stdyDscr/ddi:stdyInfo/ddi:abstract"  # noqa
        ),
        'production_date': XPathTextValue(
            "//ddi:codeBook/ddi:stdyDscr//ddi:citation/ddi:verStmt/ddi:version/@date"  # noqa
        ),
        'production_type': XPathTextValue(
            "//ddi:codeBook/ddi:stdyDscr/ddi:method/ddi:collMode"  # noqa
        ),
        'abstract': XPathTextValue(
            "//ddi:codeBook/ddi:stdyDscr/ddi:stdyInfo/ddi:abstract"  # noqa
        ),
        'kind_of_data': XPathTextValue(
            "//ddi:codeBook/ddi:stdyDscr/ddi:stdyInfo/ddi:sumDscr/ddi:dataKind"  # noqa
        ),
        'unit_of_analysis': XPathTextValue(
            "//ddi:codeBook/ddi:stdyDscr/ddi:stdyInfo/ddi:sumDscr/ddi:anlyUnit"  # noqa
        ),
        'description_of_scope': XPathTextValue(
            "//ddi:codeBook/ddi:stdyDscr/ddi:stdyInfo/ddi:abstract"  # noqa
        ),
        'country': ArrayTextValue(
            XPathMultiTextValue(
                "//ddi:codeBook/ddi:stdyDscr/ddi:stdyInfo/ddi:sumDscr/ddi:nation"  # noqa
            ),
            separator=', '
        ),
        'geographic_coverage': XPathTextValue(
            "//ddi:codeBook/ddi:stdyDscr/ddi:stdyInfo/ddi:sumDscr/ddi:geogCover"  # noqa
        ),
        'time_period_covered': ArrayTextValue(
            XPathMultiTextValue(
                "//ddi:codeBook/ddi:stdyDscr/ddi:stdyInfo/ddi:sumDscr/ddi:timePrd"  # noqa
            ),
            separator=', '
        ),
        'universe': XPathTextValue(
            "//ddi:codeBook/ddi:stdyDscr/ddi:stdyInfo/ddi:sumDscr/ddi:universe"  # noqa
        ),
        'primary_investigator': XPathTextValue(
            "//ddi:codeBook/ddi:stdyDscr/ddi:citation/ddi:rspStmt/ddi:AuthEnty"  # noqa
        ),
        'other_producers': FirstInOrderValue([
            ArrayTextValue(
                XPathMultiTextValue(
                    "//ddi:codeBook/ddi:stdyDscr/ddi:citation/ddi:rspStmt/ddi:othId"  # noqa
                ),
                separator="<br />\r\n"
            ),
            ArrayTextValue(
                XPathMultiTextValue(
                    "//ddi:codeBook/ddi:stdyDscr/ddi:citation/ddi:rspStmt/ddi:othId/ddi:p"  # noqa
                ),
                separator="<br />\r\n"
            ),
        ]),
        'funding': ArrayTextValue(
            XPathMultiTextValue(
                "//ddi:codeBook/ddi:stdyDscr/ddi:citation/ddi:prodStmt/ddi:fundAg"  # noqa
            ),
            separator="<br />\r\n"
        ),
        'sampling_procedure': XPathTextValue(
            "//ddi:codeBook/ddi:stdyDscr/ddi:method/ddi:dataColl/ddi:sampProc"  # noqa
        ),
        'data_collection_dates': CombinedValue(
            [
                DateCollectionValue(
                    [
                        XPathMultiTextValue(
                            "//ddi:codeBook/ddi:stdyDscr/ddi:stdyInfo/ddi:sumDscr/ddi:collDate[@event='start']/@date",  # noqa
                        ),
                        XPathMultiTextValue(
                            "//ddi:codeBook/ddi:stdyDscr/ddi:stdyInfo/ddi:sumDscr/ddi:collDate[@event='end']/@date",  # noqa
                        ),
                        XPathMultiTextValue(
                            "//ddi:codeBook/ddi:stdyDscr/ddi:stdyInfo/ddi:sumDscr/ddi:collDate[@event='end']/@cycle",  # noqa
                        ),
                    ],
                    separator="<br />\r\n"
                ),
                ArrayTextValue(
                    XPathMultiTextValue(
                            "//ddi:codeBook/ddi:stdyDscr/ddi:stdyInfo/ddi:sumDscr/ddi:collDate[@event='single' or not(@event)]/@date",  # noqa
                    ),
                    separator="<br />\r\n"
                ),
            ],
            separator="<br />\r\n"
        ),
        'access_authority': XPathTextValue(
            "//ddi:codeBook/ddi:stdyDscr/ddi:dataAccs/ddi:useStmt/ddi:contact"  # noqa
        ),
        'conditions': XPathTextValue(
            "//ddi:codeBook/ddi:stdyDscr/ddi:dataAccs/ddi:useStmt/ddi:conditions"  # noqa
        ),
        'citation_requirement': XPathTextValue(
            "//ddi:codeBook/ddi:stdyDscr/ddi:dataAccs/ddi:useStmt/ddi:citReq"  # noqa
        ),
        'contact_persons': XPathTextValue(
            "//ddi:codeBook/ddi:stdyDscr/ddi:citation/ddi:distStmt/ddi:contact"  # noqa
        ),
        'url': XPathTextValue(
            "//ddi:codeBook/ddi:stdyDscr/ddi:dataAccs/ddi:setAvail/ddi:accsPlac/@URI"  # noqa
        ),
        'author': CombinedValue(
            [
                XPathTextValue('//ddi:codeBook/ddi:stdyDscr/ddi:citation/ddi:rspStmt/ddi:AuthEnty'),  # noqa
                XPathTextValue('//ddi:codeBook/ddi:stdyDscr/ddi:citation/ddi:contributor'),  # noqa
            ],
            separator="<br />\r\n"
        ),
        # TODO: Do we need that? What DDI field should be used?
        'author_email': StringValue(''),
        'maintainer': XPathTextValue(
            "//ddi:codeBook/ddi:stdyDscr/ddi:citation/ddi:distStmt/ddi:contact"  # noqa
        ),
        'maintainer_email': XPathTextValue(
            "//ddi:codeBook/ddi:stdyDscr/ddi:citation/ddi:distStmt/ddi:contact/@email"  # noqa
        ),
        'copyright': XPathTextValue(
            '//ddi:codeBook/ddi:stdyInfo/ddi:citation/ddi:prodStmt/ddi:copyright'  # noqa
        ),
        'license_id': XPathTextValue(
            '//ddi:codeBook/ddi:stdyInfo/ddi:citation/ddi:prodStmt/ddi:copyright'  # noqa
        ),
        'version': XPathTextValue('//ddi:codeBook/ddi:stdyDscr/ddi:citation/ddi:verStmt/ddi:version'),  # noqa
        'version_notes': XPathTextValue('//ddi:codeBook/ddi:stdyDscr/ddi:citation/ddi:verStmt/ddi:notes'),  # noqa
        'notes': XPathTextValue(
            "//ddi:codeBook/ddi:stdyDscr/ddi:stdyInfo/ddi:notes"  # noqa
        ),
        'tags': ArrayDictNameValue([
            XPathMultiValue(
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
        raise MappingNotFoundError(
            "No mapping found for attribute '%s'" % ckan_attribute
        )


class MappingNotFoundError(Exception):
    pass


class MetadataFormatError(Exception):
    pass

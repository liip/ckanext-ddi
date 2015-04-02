from lxml import etree
import logging
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

# oai_ddi_reader = MetadataReader(
#     fields={
#         'title':        ('textList', 'oai_ddi:codeBook/stdyDscr/citation/titlStmt/titl/text()'),  # noqa
#         'creator':      ('textList', 'oai_ddi:codeBook/stdyDscr/citation/rspStmt/AuthEnty/text()'),  # noqa
#         'subject':      ('textList', 'oai_ddi:codeBook/stdyDscr/stdyInfo/subject/keyword/text()'),  # noqa
#         'description':  ('textList', 'oai_ddi:codeBook/stdyDscr/stdyInfo/abstract/text()'),  # noqa
#         'publisher':    ('textList', 'oai_ddi:codeBook/stdyDscr/citation/distStmt/contact/text()'),  # noqa
#         'contributor':  ('textList', 'oai_ddi:codeBook/stdyDscr/citation/contributor/text()'),  # noqa
#         'date':         ('textList', 'oai_ddi:codeBook/stdyDscr/citation/prodStmt/prodDate/text()'),  # noqa
#         'type':         ('textList', 'oai_ddi:codeBook/stdyDscr/stdyInfo/sumDscr/dataKind/text()'),  # noqa
#         'format':       ('textList', 'oai_ddi:codeBook/fileDscr/fileType/text()'),  # noqa
#         'identifier':   ('textList', "oai_ddi:codeBook/stdyDscr/citation/titlStmt/IDNo/text()"),  # noqa
#         'source':       ('textList', 'oai_ddi:codeBook/stdyDscr/dataAccs/setAvail/accsPlac/@URI'),  # noqa
#         'language':     ('textList', 'oai_ddi:codeBook/@xml:lang'),  # noqa
#         'tempCoverage': ('textList', 'oai_ddi:codeBook/stdyDscr/stdyInfo/sumDscr/timePrd/text()'),  # noqa
#         'geoCoverage':  ('textList', 'oai_ddi:codeBook/stdyDscr/stdyInfo/sumDscr/geogCover/text()'),  # noqa
#         'rights':       ('textList', 'oai_ddi:codeBook/stdyInfo/citation/prodStmt/copyright/text()')   # noqa
#     },
# )


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
        value = super(XPathMultiTextAttribute, self).get_value(**kwargs)
        return value.text if hasattr(value, 'text') else value


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

#         'title':        ('textList', 'oai_ddi:codeBook/stdyDscr/citation/titlStmt/titl/text()'),  # noqa
#         'creator':      ('textList', 'oai_ddi:codeBook/stdyDscr/citation/rspStmt/AuthEnty/text()'),  # noqa
#         'subject':      ('textList', 'oai_ddi:codeBook/stdyDscr/stdyInfo/subject/keyword/text()'),  # noqa
#         'description':  ('textList', 'oai_ddi:codeBook/stdyDscr/stdyInfo/abstract/text()'),  # noqa
#         'publisher':    ('textList', 'oai_ddi:codeBook/stdyDscr/citation/distStmt/contact/text()'),  # noqa
#         'contributor':  ('textList', 'oai_ddi:codeBook/stdyDscr/citation/contributor/text()'),  # noqa
#         'date':         ('textList', 'oai_ddi:codeBook/stdyDscr/citation/prodStmt/prodDate/text()'),  # noqa
#         'type':         ('textList', 'oai_ddi:codeBook/stdyDscr/stdyInfo/sumDscr/dataKind/text()'),  # noqa
#         'format':       ('textList', 'oai_ddi:codeBook/fileDscr/fileType/text()'),  # noqa
#         'identifier':   ('textList', "oai_ddi:codeBook/stdyDscr/citation/titlStmt/IDNo/text()"),  # noqa
#         'source':       ('textList', 'oai_ddi:codeBook/stdyDscr/dataAccs/setAvail/accsPlac/@URI'),  # noqa
#         'language':     ('textList', 'oai_ddi:codeBook/@xml:lang'),  # noqa
#         'tempCoverage': ('textList', 'oai_ddi:codeBook/stdyDscr/stdyInfo/sumDscr/timePrd/text()'),  # noqa
#         'geoCoverage':  ('textList', 'oai_ddi:codeBook/stdyDscr/stdyInfo/sumDscr/geogCover/text()'),  # noqa
#         'rights':       ('textList', 'oai_ddi:codeBook/stdyInfo/citation/prodStmt/copyright/text()')   # noqa
    mapping = {
        'id': XPathTextAttribute('//ddi:codeBook/ddi:stdyDscr/ddi:citation/ddi:titlStmt/ddi:IDNo'),
        'name': FirstInOrderAttribute([
            XPathTextAttribute(
                "//ddi:codeBook/ddi:stdyDscr/ddi:citation/ddi:titlStmt/ddi:altTitl"
            ),
            XPathTextAttribute(
                "//ddi:codeBook/ddi:stdyDscr/ddi:citation/ddi:titlStmt/ddi:titl"
            ),
        ]),
        'title': XPathTextAttribute(
            "//ddi:codeBook/ddi:stdyDscr/ddi:citation/ddi:titlStmt/ddi:titl"
        ),
        'url': XPathTextAttribute(
            "//ddi:codeBook/ddi:stdyDscr/ddi:dataAccs/ddi:setAvail/ddi:accsPlac/ddi:@URI"
        ),
        'author': CombinedAttribute(
            [
                XPathTextAttribute('//ddi:codeBook/ddi:stdyDscr/ddi:citation/ddi:rspStmt/ddi:AuthEnty'),
                XPathTextAttribute('//ddi:codeBook/ddi:stdyDscr/ddi:citation/ddi:contributor'),
            ],
            separator=', '
        ),
        'author_email': StringAttribute(''),
        'maintainer': StringAttribute(''),
        'maintainer_email': StringAttribute(''),
        'license_url': XPathTextAttribute(
            '//ddi:codeBook/ddi:stdyInfo/ddi:citation/ddi:prodStmt/ddi:copyright'
        ),
        'version': XPathTextAttribute('//ddi:codeBook/ddi:stdyDscr/ddi:citation/ddi:prodStmt/ddi:prodDate'),
        'notes': XPathTextAttribute(
            "//ddi:codeBook/ddi:stdyDscr/ddi:stdyInfo/ddi:abstract"
        ),
        'tags': ArrayAttribute([
            XPathMultiTextAttribute(
                "//ddi:codeBook/ddi:stdyDscr/ddi:stdyInfo/ddi:subject/ddi:keyword"
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

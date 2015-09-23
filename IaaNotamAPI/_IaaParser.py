import re
from xml.etree import ElementTree


class Parser(object):
    _html_id_regex = \
        re.compile(r'divMainInfo_(\d+).+?<\s*td\s+class="NotamID"\s*>\s*(.+?)</\s*td\s*>', re.IGNORECASE | re.DOTALL)

    @staticmethod
    def list_notams(iaa_html_page):
        """Parses the contents of the IAA NOTAMs page into a list of NOTAMs.

        :param iaa_html_page: The HTML page, as returned by a call to Feed.notams_short_html().
        :return: A tuple of tuples. The first element of this is a list of the IAA internal NOTAM identifiers
                 (e.g.: 532372). The second is a corresponding list of ICAO NOTAM identifiers (e.g.: C2000/15).
                 The list indexes match; i.e.: r[1][i] is the ICAO identifier of the NOTAM whose internal-
                 IAA identifier is r[0][i].
        """
        r = Parser._html_id_regex.findall(iaa_html_page)
        return tuple( zip(*r) )

    @staticmethod
    def parse_notam_xml(xml_str):
        """Parses out the information from the NOTAM details XML.

        :param xml_str: NOTAM details XML, as returned by a call to Feed.detailed_notam_xml().
        :return: A Python dictionary repesenting the NOTAM. This shall have, at least, the following keys:
                 'IAA_id', for the internal IAA NOTAM identifier (e.g.: 532372); 'contents', for the
                 contents of the NOTAM (as a multi-line string).
        """
        msg_root = ElementTree.fromstring(xml_str).find('.//Msg')
        if msg_root is None:
            raise ParserXMLError('Msg element missing', xml_str)
        notam = {}
        notam['IAA_id'] = msg_root.get('MsgNumber')
        msg_text_nodes = msg_root.findall('MsgText')
        if not msg_text_nodes:
            raise ParserXMLError('NOTAM contents seem to be missing', xml_str)
        notam['contents'] = '\n'.join( map(lambda e: e.text, msg_text_nodes) )
        return notam


class ParserXMLError(Exception):
    def __init__(self, msg, xml_str):
        super(ParserXMLError, self).__init__('Badly-structured XML: {}\nIn: {}'.format(msg, xml_str))
import requests_cache


class Feed(object):
    def __init__(self):
        # We reload content every 30 seconds. This should be plenty fresh enough for NOTAMs,
        # while not bombarding the IAA server.
        self._sess = requests_cache.CachedSession(backend='memory', expire_after=30)

    def notams_short_html(self):
        """Gets the HTML body of the IAA site's NOTAMs list.

        :return: A string containing the HTML page's body.
        """
        resp = self._sess.get(Feed._ShortNotam.url, params=Feed._ShortNotam.params, stream=True)
        resp.raise_for_status()
        return resp.text

    class _ShortNotam(object):
        url = 'http://ext.iaa.gov.il/aeroinfo/AeroInfo.aspx'
        params = {'msgType': 'Notam'}

    def detailed_notam_xml(self, notam_id):
        """Gets the detailed NOTAM XML provided by the IAA SOAP interface.

        :param notam_id: Numerical NOTAM id, as specified within the IAA NOTAMs listing HTML source. e.g.:
                         the number 522159 in ` <div id="divMainInfo_522159" '. Note this is NOT the ICAO
                         NOTAM identifier.
        :return: XML providing full details of the NOTAM, exactly as it is provided by the IAA
                 SOAP interface.
        """
        req_body = Feed._NotamDetails.body.format(notam_id=notam_id)
        resp = self._sess.post(Feed._NotamDetails.url,
                               params=Feed._NotamDetails.params,
                               headers=Feed._NotamDetails.headers,
                               data=req_body,
                               stream=True)
        resp.raise_for_status()
        return resp.text

    class _NotamDetails(object):
        url = 'http://ext.iaa.gov.il/aeroinfo/AeroInfo.asmx'
        params = {'op': 'getMoreMsgInfo'}
        headers = {
            'SOAPAction': 'http://tempuri.org/getMoreMsgInfo',
            'Content-Type': 'text/xml'
        }
        body = """<?xml version='1.0' encoding='utf-8'?>
                  <soap:Envelope xmlns:xsi='http://www.w3.org/2001/XMLSchema-instance' xmlns:xsd='http://www.w3.org/2001/XMLSchema' xmlns:soap='http://schemas.xmlsoap.org/soap/envelope/'>
                      <soap:Body>
                          <getMoreMsgInfo xmlns='http://tempuri.org/'>
                              <msgNum>{notam_id}</msgNum>
                              <mode>more</mode>
                              <CurrOrHist>Current</CurrOrHist>
                          </getMoreMsgInfo>
                      </soap:Body>
                  </soap:Envelope>"""

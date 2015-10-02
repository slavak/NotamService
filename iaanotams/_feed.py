import cachetools
import aiohttp


def _raise_for_status(client_response):
    if client_response.status != 200:
        raise aiohttp.errors.HttpProcessingError(code=client_response.status,
                                                 message='HTTP request failed with status: {} {}'.
                                                    format(client_response.status, client_response.reason))


class Feed(object):
    def __init__(self):
        # We reload content every 30 seconds. This should be plenty fresh enough for NOTAMs,
        # while not bombarding the IAA server.
        self._cache = cachetools.TTLCache(maxsize = 1000, ttl = 30)
        self._session = aiohttp.ClientSession(connector=aiohttp.TCPConnector(conn_timeout=30))

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._session is not None:
            self._session.close()
            self._session = None
        return False

    def __del__(self):
        self.__exit__(None,None,None)

    async def notams_short_html(self):
        """Gets the HTML body of the IAA site's NOTAMs list.

        :return: A string containing the HTML page's body.
        """
        cached = self._cache.get("list_html")
        if cached is not None:
            return cached
        resp = await self._session.get(Feed._ShortNotam.url, params=Feed._ShortNotam.params)
        _raise_for_status(resp)
        content = await resp.text()
        self._cache["list_html"] = content
        return content

    class _ShortNotam(object):
        url = 'http://ext.iaa.gov.il/aeroinfo/AeroInfo.aspx'
        params = {'msgType': 'Notam'}

    async def detailed_notam_xml(self, notam_id):
        """Gets the detailed NOTAM XML provided by the IAA SOAP interface.

        :param notam_id: Numerical NOTAM id, as specified within the IAA NOTAMs listing HTML source. e.g.:
                         the number 522159 in ` <div id="divMainInfo_522159" '. Note this is NOT the ICAO
                         NOTAM identifier.
        :return: XML providing full details of the NOTAM, exactly as it is provided by the IAA
                 SOAP interface.
        """
        cached = self._cache.get(notam_id)
        if cached is not None:
            return cached
        req_body = Feed._NotamDetails.body.format(notam_id=notam_id)
        resp = await self._session.post(Feed._NotamDetails.url,
                                        params=Feed._NotamDetails.params,
                                        headers=Feed._NotamDetails.headers,
                                        data=req_body)
        _raise_for_status(resp)
        content = await resp.text()
        self._cache[notam_id] = content
        return content

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

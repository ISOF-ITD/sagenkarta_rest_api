from . import secrets

host = secrets.host
index_name = 'isof-publik'
protocol = 'http://'
cert_file = False
restApiRecordUrl = 'https://frigg.isof.se/sagendatabas/api/records/'
feedbackEmail = 'fredrik.skott@isof.se'
LantmaterietProxy = 'http://maps.lantmateriet.se/topowebb/v1/wmts/1.0.0/topowebb/default/3006/'
LantmaterietEpsg3857Proxy = 'http://maps.lantmateriet.se/topowebb/v1/wmts/1.0.0/topowebb/default/3857/'
LantmaterietNedtonadEpsg3857Proxy = 'http://maps.lantmateriet.se/topowebb/v1/wmts/1.0.0/topowebb_nedtonad/default/3857/'
LantmaterietOrtoProxy = 'http://maps.lantmateriet.se/ortofoto/wms/v1.3/'
LantmaterietProxy_access = secrets.LantmaterietProxy_access
IsofGeoProxy = 'https://oden-test.isof.se/geoserver/'
IsofHomepage = 'https://www.isof.se/'
FriggStatic = 'https://frigg.isof.se/static/'
FilemakerProxy = 'https://filemaker.isof.se/'
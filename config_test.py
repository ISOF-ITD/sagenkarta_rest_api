from . import secrets

host = secrets.host
index_name = 'isof-publik'
protocol = 'http://'
cert_file = False
restApiRecordUrl = 'https://frigg-test.isof.se/sagendatabas/api/records/'
feedbackEmail = 'fredrik.skott@isof.se'
LantmaterietProxy = 'http://maps.lantmateriet.se/topowebb/v1/wmts/1.0.0/topowebb/default/3006/'
LantmaterietEpsg3857Proxy = 'http://maps.lantmateriet.se/topowebb/v1/wmts/1.0.0/topowebb/default/3857/'
LantmaterietNedtonadEpsg3857Proxy = 'http://maps.lantmateriet.se/topowebb/v1/wmts/1.0.0/topowebb_nedtonad/default/3857/'
LantmaterietOrtoProxy = 'http://maps.lantmateriet.se/ortofoto/wms/v1.3/'
LantmaterietHistOrtoProxy = 'https://api.lantmateriet.se/historiska-ortofoton/wms/v1/'
#LantmaterietHistOrtoProxy = 'https://api.lantmateriet.se/historiska-ortofoton/wms/v1/token/'
LantmaterietProxy_access = secrets.LantmaterietProxy_access
LantmaterietProxy_access_opendata = secrets.LantmaterietProxy_access_opendata
IsofGeoProxy = 'https://oden-test.isof.se/geoserver/'
IsofHomepage = 'https://www.isof.se/'
FriggStatic = 'https://frigg-test.isof.se/static/'
FilemakerProxy = 'https://filemaker.isof.se/'


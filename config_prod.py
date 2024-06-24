from . import secrets_env

host = secrets_env.host
user = secrets_env.user
password = secrets_env.password
es_version = '8'
index_name = 'isof-publik'
protocol = 'http://'
cert_file = False
restApiRecordUrl = 'https://garm.isof.se/folkeservice/api/records/'
feedbackEmail = 'fredrik.skott@isof.se'
LantmaterietProxy = 'http://maps.lantmateriet.se/topowebb/v1/wmts/1.0.0/topowebb/default/3006/'
LantmaterietEpsg3857Proxy = 'http://maps.lantmateriet.se/topowebb/v1/wmts/1.0.0/topowebb/default/3857/'
LantmaterietNedtonadEpsg3857Proxy = 'http://maps.lantmateriet.se/topowebb/v1/wmts/1.0.0/topowebb_nedtonad/default/3857/'
LantmaterietOrtoProxy = 'http://maps.lantmateriet.se/ortofoto/wms/v1.3/'
LantmaterietHistOrtoProxy = 'https://api.lantmateriet.se/historiska-ortofoton/wms/v1/'
#LantmaterietHistOrtoProxy = 'https://api.lantmateriet.se/historiska-ortofoton/wms/v1/token/'
LantmaterietProxy_access = secrets_env.LantmaterietProxy_access
LantmaterietProxy_access_opendata = secrets_env.LantmaterietProxy_access_opendata
IsofGeoProxy = 'https://oden-test.isof.se/geoserver/'
IsofHomepage = 'https://www.isof.se/'
FriggStatic = 'https://garm.isof.se/static/'
FilemakerProxy = 'https://filemaker.isof.se/'
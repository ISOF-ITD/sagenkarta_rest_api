from django.conf.urls import url, include
from rest_framework import routers
from . import views

router = routers.DefaultRouter()
router.register(r'records', views.RecordsViewSet, basename='record')
router.register(r'persons', views.PersonsViewSet, basename='person')
router.register(r'locations', views.LocationsViewSet, basename='locations')
router.register(r'categories', views.CategoriesViewSet, basename='categories')
router.register(r'feedback', views.FeedbackViewSet, basename='feedback')
router.register(r'transcribe', views.TranscribeViewSet, basename='transcribe')
router.register(r'transcribesave', views.TranscribeSaveViewSet, basename='transcribesave')
router.register(r'transcribestart', views.TranscribeStartViewSet, basename='transcribestart')
router.register(r'transcribecancel', views.TranscribeCancelViewSet, basename='transcribecancel')

# App name must be specified,
# otherwise Django will complain about the URL's.
app_name = 'api'

urlpatterns = [
	url(r'^isofGeoProxy/', views.isofGeoProxy, name='IsofGeoProxy'),

	url(r'^simple_lm_proxy/', views.SimpleLantmaterietProxy,  name='SimpleLantmaterietProxy'),
	url(r'^lm_proxy/(?P<path>.*)$', views.LantmaterietProxyView.as_view()),
	url(r'^lm_epsg3857_proxy/(?P<path>.*)$', views.LantmaterietEpsg3857ProxyView.as_view()),
	url(r'^lm_nedtonad_epsg3857_proxy/(?P<path>.*)$', views.LantmaterietNedtonadEpsg3857ProxyView.as_view()),
	url(r'^lm_orto_proxy/(?P<path>.*)$', views.LantmaterietOrtoProxyView.as_view()),
	url(r'^lm_historto_proxy/(?P<path>.*)$', views.LantmaterietHistOrtoProxyView.as_view()),
	url(r'^isofgeo_proxy/(?P<path>.*)$', views.IsofGeoProxyView.as_view()),
	url(r'^isofhomepage/(?P<path>.*)$', views.IsofHomepageView.as_view()),
	url(r'^frigg_static/(?P<path>.*)$', views.FriggStaticView.as_view()),
	url(r'^filemaker_proxy/(?P<path>.*)$', views.FilemakerProxyView.as_view()),
	url(r'^', include(router.urls)),
]
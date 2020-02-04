from django.conf.urls import url, include
from rest_framework import routers
from . import views
from revproxy.views import ProxyView

router = routers.DefaultRouter()
router.register(r'records', views.RecordsViewSet, base_name='record')
router.register(r'persons', views.PersonsViewSet, base_name='person')
router.register(r'locations', views.LocationsViewSet, base_name='locations')
router.register(r'categories', views.CategoriesViewSet, base_name='categories')
router.register(r'feedback', views.FeedbackViewSet, base_name='feedback')
router.register(r'transcribe', views.TranscribeViewSet, base_name='transcribe')
router.register(r'transcribestart', views.TranscribeStartViewSet, base_name='transcribestart')

urlpatterns = [
	url(r'^lm_proxy/(?P<path>.*)$', views.LantmaterietProxyView.as_view()),
	url(r'^lm_topo_proxy/(?P<path>.*)$', views.LantmaterietTopoProxyView.as_view()),
	url(r'^isofgeo_proxy/(?P<path>.*)$', views.IsofGeoProxyView.as_view()),
	url(r'^isofhomepage/(?P<path>.*)$', views.IsofHomepageView.as_view()),
	url(r'^', include(router.urls)),
]
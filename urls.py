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

urlpatterns = [
	url(r'^lm_proxy/(?P<path>.*)$', views.LantmaterietProxyView.as_view()),
	url(r'^isofgeo_proxy/(?P<path>.*)$', views.IsofGeoProxyView.as_view()),
	url(r'^', include(router.urls)),
]
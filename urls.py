from django.urls import path, re_path, include
from rest_framework import routers
from . import views
from .views.describe_views import DescribeViewSet

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
router.register(r'describe', DescribeViewSet, basename='describe')
router.register(r'utterances', views.UtterancesViewSet, basename='utterances')

# App name must be specified,
# otherwise Django will complain about the URL's.
app_name = 'api'

urlpatterns = [
    path('isofGeoProxy/', views.isofGeoProxy, name='IsofGeoProxy'),
    path('simple_lm_proxy/', views.SimpleLantmaterietProxy, name='SimpleLantmaterietProxy'),
    re_path(r'^lm_proxy/(?P<path>.*)$', views.LantmaterietProxyView.as_view()),
    re_path(r'^lm_epsg3857_proxy/(?P<path>.*)$', views.LantmaterietEpsg3857ProxyView.as_view()),
    re_path(r'^lm_nedtonad_epsg3857_proxy/(?P<path>.*)$', views.LantmaterietNedtonadEpsg3857ProxyView.as_view()),
    re_path(r'^lm_orto_proxy/(?P<path>.*)$', views.LantmaterietOrtoProxyView.as_view()),
    re_path(r'^lm_historto_proxy/(?P<path>.*)$', views.LantmaterietHistOrtoProxyView.as_view()),
    re_path(r'^isofgeo_proxy/(?P<path>.*)$', views.IsofGeoProxyView.as_view()),
    re_path(r'^isofhomepage/(?P<path>.*)$', views.IsofHomepageView.as_view()),
    re_path(r'^frigg_static/(?P<path>.*)$', views.FriggStaticView.as_view()),
    re_path(r'^filemaker_proxy/(?P<path>.*)$', views.FilemakerProxyView.as_view()),
    path('', include(router.urls)),
]
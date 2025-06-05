from django.urls import path, re_path, include
from django.http import HttpResponseNotFound
from rest_framework import routers
from sagenkarta_rest_api.views import (
    RecordsViewSet, PersonsViewSet, LocationsViewSet, CategoriesViewSet,
    FeedbackViewSet, TranscribeViewSet, TranscribeSaveViewSet,
    TranscribeStartViewSet, TranscribeCancelViewSet,
    DescribeViewSet, UtterancesViewSet,
    # proxies
    isofGeoProxy, SimpleLantmaterietProxy,
    LantmaterietProxyView, LantmaterietEpsg3857ProxyView,
    LantmaterietNedtonadEpsg3857ProxyView, LantmaterietOrtoProxyView,
    LantmaterietHistOrtoProxyView, IsofGeoProxyView, IsofHomepageView,
    FriggStaticView, FilemakerProxyView,
)

router = routers.DefaultRouter()
router.register(r'records', RecordsViewSet, basename='record')
router.register(r'persons', PersonsViewSet, basename='person')
router.register(r'locations', LocationsViewSet, basename='locations')
router.register(r'categories', CategoriesViewSet, basename='categories')
router.register(r'feedback', FeedbackViewSet, basename='feedback')
router.register(r'transcribe', TranscribeViewSet, basename='transcribe')
router.register(r'transcribesave', TranscribeSaveViewSet, basename='transcribesave')
router.register(r'transcribestart', TranscribeStartViewSet, basename='transcribestart')
router.register(r'transcribecancel', TranscribeCancelViewSet, basename='transcribecancel')
router.register(r'describe', DescribeViewSet, basename='describe')
router.register(r'utterances', UtterancesViewSet, basename='utterances')

app_name = 'api'

urlpatterns = [
    path('isofGeoProxy/', isofGeoProxy),
    path('simple_lm_proxy/', SimpleLantmaterietProxy),
    re_path(r'^lm_proxy/(?P<path>.*)$', LantmaterietProxyView.as_view()),
    re_path(r'^lm_epsg3857_proxy/(?P<path>.*)$', LantmaterietEpsg3857ProxyView.as_view()),
    re_path(r'^lm_nedtonad_epsg3857_proxy/(?P<path>.*)$', LantmaterietNedtonadEpsg3857ProxyView.as_view()),
    re_path(r'^lm_orto_proxy/(?P<path>.*)$', LantmaterietOrtoProxyView.as_view()),
    re_path(r'^lm_historto_proxy/(?P<path>.*)$', LantmaterietHistOrtoProxyView.as_view()),
    re_path(r'^isofgeo_proxy/(?P<path>.*)$', IsofGeoProxyView.as_view()),
    re_path(r'^isofhomepage/(?P<path>.*)$', IsofHomepageView.as_view()),
    re_path(r'^frigg_static/(?P<path>.*)$', FriggStaticView.as_view()),
    re_path(r'^filemaker_proxy/(?P<path>.*)$', FilemakerProxyView.as_view()),
    path('', include(router.urls)),
]

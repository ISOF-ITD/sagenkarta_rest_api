from django.conf.urls import url, include
from rest_framework import routers
from . import views

router = routers.DefaultRouter()
router.register(r'records', views.RecordsViewSet, base_name='record')
router.register(r'persons', views.PersonsViewSet, base_name='person')
router.register(r'locations', views.LocationsViewSet, base_name='locations')

urlpatterns = [
	url(r'^', include(router.urls)),
]
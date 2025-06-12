from rest_framework import viewsets
from sagenkarta_rest_api.models import Persons
from sagenkarta_rest_api.serializers import PersonsSerializer

class PersonsViewSet(viewsets.ReadOnlyModelViewSet):
    # Read-only list/detail of `Persons`
    queryset = Persons.objects.all()
    serializer_class = PersonsSerializer
    pagination_class = None
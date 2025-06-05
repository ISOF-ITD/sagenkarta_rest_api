from django.db.models import Q
from rest_framework import viewsets
from sagenkarta_rest_api.models import Persons, Socken
from sagenkarta_rest_api.serializers import PersonsSerializer, SockenSerializer


class PersonsViewSet(viewsets.ReadOnlyModelViewSet):
    # Read-only list/detail of `Persons`
    queryset = Persons.objects.all()
    serializer_class = PersonsSerializer
    pagination_class = None


class LocationsViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Filters `Socken` (places) by query-params:

    • ?socken_name= str – fuzzy-match on `Socken.name`
    • ?landskap_name= str – fuzzy-match on `harad.name` or `harad.landskap`

    Combines multiple params with AND logic and returns a DISTINCT set.
    """
    serializer_class = SockenSerializer
    pagination_class = None

    def get_queryset(self):
        qs = Socken.objects.all()
        p = self.request.query_params

        socken_name = p.get("socken_name")
        if socken_name:
            qs = qs.filter(name__icontains=socken_name.strip().lower())

        landskap_name = p.get("landskap_name")
        if landskap_name:
            val = landskap_name.strip().lower()
            qs = qs.filter(
                Q(harad__name__icontains=val) |
                Q(harad__landskap__icontains=val)
            )

        return qs.distinct()

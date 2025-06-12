from rest_framework import viewsets
from sagenkarta_rest_api.models import Categories
from sagenkarta_rest_api.serializers import CategorySerializer


class CategoriesViewSet(viewsets.ReadOnlyModelViewSet):
    #/api/categories/ – read-only list of category codes.
    queryset = Categories.objects.all()
    serializer_class = CategorySerializer
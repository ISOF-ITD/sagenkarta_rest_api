from .models import Records, Persons, Socken
from rest_framework import viewsets
from .serializers import RecordsSerializer, SingleRecordSerializer, PersonsSerializer, SockenSerializer
from rest_framework.response import Response
from django.db.models import Q
from django.shortcuts import get_object_or_404

class RecordsViewSet(viewsets.ReadOnlyModelViewSet):
	serializer_class = RecordsSerializer

	def get_queryset(self):
		queryset = Records.objects.all()

		filters = {}
		
		country = self.request.query_params.get('country', None)
		if country is not None:
			filters['country__iexact'] = country

		only_categories = self.request.query_params.get('only_categories', None)
		if only_categories is not None:
			queryset = queryset.exclude(category='')

		category = self.request.query_params.get('category', None)
		if category is not None:
			category_values = category.upper().split(',')
			filters['category__in'] = category_values

		type = self.request.query_params.get('type', None)
		if type is not None:
			type_values = type.split(',')
			filters['type__in'] = type_values

		person = self.request.query_params.get('person', None)
		if person is not None:
			filters['persons__id'] = person

		search_string = self.request.query_params.get('search', None)
		if search_string is not None:
			search_field = self.request.query_params.get('search_field', 'record')

			if search_field.lower() == 'record':
				queryset = queryset.filter(Q(title__icontains=search_string) | Q(text__icontains=search_string))
			if search_field.lower() == 'person':
				filters['persons__name__icontains'] = search_string

		queryset = queryset.filter(**filters).distinct()

		print(queryset.query)

		return queryset

	def retrieve(self, request, pk=None):
		queryset = Records.objects.all()
		user = get_object_or_404(queryset, pk=pk)
		serializer = SingleRecordSerializer(user)
		return Response(serializer.data)

class PersonsViewSet(viewsets.ReadOnlyModelViewSet):
	queryset = Persons.objects.all()
	serializer_class = PersonsSerializer


class LocationsViewSet(viewsets.ReadOnlyModelViewSet):
	def get_queryset(self):
		queryset = Socken.objects.all()

		filters = {}

		only_categories = self.request.query_params.get('only_categories', None)
		if only_categories is not None:
			queryset = queryset.exclude(socken_records__category=None)

		country = self.request.query_params.get('country', None)
		if country is not None:
			#queryset = queryset.filter(socken_records__country=country)
			filters['socken_records__country'] = country

		category = self.request.query_params.get('category', None)
		if category is not None:
			#queryset = queryset.filter(socken_records__category=category)
			filters['socken_records__category'] = category.upper()

		type = self.request.query_params.get('type', None)
		if type is not None:
			type_values = type.split(',')
			#queryset = queryset.filter(socken_records__type__in=type_values).distinct()
			filters['socken_records__type__in'] = type_values

		search_string = self.request.query_params.get('search', None)
		if search_string is not None:
			search_field = self.request.query_params.get('search_field', 'record')

			if search_field.lower() == 'record':
				queryset = queryset.filter(Q(socken_records__title__icontains=search_string) | Q(socken_records__text__icontains=search_string))
			if search_field.lower() == 'person':
				filters['socken_records__persons__name__icontains'] = search_string

		queryset = queryset.filter(**filters).distinct()

		print(queryset.query)

		return queryset

	def paginate_queryset(self, queryset, view=None):
		return None

	serializer_class = SockenSerializer
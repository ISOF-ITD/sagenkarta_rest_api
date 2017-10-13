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
		country = self.request.query_params.get('country', None)
		category = self.request.query_params.get('category', None)
		type = self.request.query_params.get('type', None)
		only_categories = self.request.query_params.get('only_categories', None)
		search_string = self.request.query_params.get('search', None)
		search_field = self.request.query_params.get('search_field', 'record')
		
		joins = []
		where = []
		
		if country is not None or category is not None or type is not None or only_categories is not None or search_string is not None:
			joins.append('LEFT JOIN records_places ON records_places.place = socken.id')
			joins.append('LEFT JOIN records ON records.id = records_places.record')

		if search_string is not None:
			if search_field.lower() == 'record':
				if search_string.find(';') > -1:
					where.append('MATCH(records.text) AGAINST("'+search.replace(';', '+')+'")')
				else:
					where.append('(LOWER(records.title) LIKE "%'+search_string.lower()+'%" OR LOWER(records.text) LIKE "%'+search_string.lower()+'%" OR LOWER(records.archive_id) LIKE "%'+search_string.lower()+'%")')
			elif search_field.lower() == 'person':
				where.append('(LOWER(persons.name) LIKE "%'+search_string.lower()+'%")')

		if type is not None:
			if type.find(',') > -1:
				types = type.split(',')
				type_criteria = '(LOWER(records.type) = "'+'" OR LOWER(records.type) = "'.join(types)+'")'
				where.append(type_criteria)
			else:
				where.append('LOWER(records.type) = "'+type.lower()+'"')

		if category is not None:
			if category.find(',') > -1:
				categories = category.split(',')
				category_criteria = '(LOWER(records.category) = "'+'" OR LOWER(records.category) = "'.join(categories)+'")';
				where.append(category_criteria)
			else:
				where.append('LOWER(records.category) = "'+category.lower()+'"')

		if only_categories is not None and only_categories == True:
			where.join('records.category != ""')

		if country is not None:
			if country.find(',') > -1:
				countries = country.split(',')
				country_criterias = '(LOWER(records.country) = "'+'" OR LOWER(records.country) = "'.join(countries)+'")';
				where.append(country_criterias)
			else:
				where.append('LOWER(records.country) = "'+country.lower()+'"')

		where.append('socken.lat IS NOT NULL')
		where.append('socken.lng IS NOT NULL')

		joins.append('LEFT JOIN harad ON harad.id = socken.harad')

		sql = 'SELECT DISTINCT socken.id, socken.name, socken.lat, socken.lng, socken.lmId lm_id, harad.name harad, harad.landskap, harad.lan county, socken.fylke FROM socken '+(' '.join(joins)+' WHERE '+' AND '.join(where) if len(where) > 0 else '')+' GROUP BY socken.id'

		print(sql)
		queryset = Socken.objects.raw(sql)

		return queryset

	def paginate_queryset(self, queryset, view=None):
		return None

	serializer_class = SockenSerializer

class _LocationsViewSet(viewsets.ReadOnlyModelViewSet):
	def get_queryset(self):
		queryset = Socken.objects.all()

		filters = {}

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

		only_categories = self.request.query_params.get('only_categories', None)
		if only_categories is not None:
			#queryset = queryset.filter(~Q(socken_records__category=None))
			queryset = queryset.exclude(socken_records__category='')

		queryset = queryset.filter(**filters).distinct()

		print(queryset.query)

		return queryset

	def paginate_queryset(self, queryset, view=None):
		return None

	serializer_class = SockenSerializer
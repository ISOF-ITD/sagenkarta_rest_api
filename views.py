from .models import Records, Persons, Socken, Category
from rest_framework import viewsets, permissions
from .serializers import RecordsSerializer, PersonsSerializer, SockenSerializer, CategorySerializer
from rest_framework.response import Response
from django.db.models import Q
from django.shortcuts import get_object_or_404
from revproxy.views import ProxyView
from base64 import b64encode
from django.core.mail import send_mail
from django.http import JsonResponse
import json

import es_config

class CategoriesViewSet(viewsets.ReadOnlyModelViewSet):
	queryset = Category.objects.all()
	serializer_class = CategorySerializer

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
			filters['categories__id__exact'] = category_values

		record_ids = self.request.query_params.get('record_ids', None)
		if record_ids is not None:
			record_id_list = record_ids.upper().split(',')
			filters['id__in'] = record_id_list

		type = self.request.query_params.get('type', None)
		if type is not None:
			type_values = type.split(',')
			filters['type__in'] = type_values

		person = self.request.query_params.get('person', None)
		if person is not None:
			filters['records_persons__id'] = person

		place = self.request.query_params.get('place', None)
		if place is not None:
			filters['places__id'] = place

		gender = self.request.query_params.get('gender', None)
		if gender is not None:
			person_relation = self.request.query_params.get('person_relation', None)

			if person_relation is not None:
				queryset = queryset.filter(Q(records_persons__gender=gender.lower()) and Q(records_persons__recordspersons__relation=person_relation.lower()))
			else:
				filters['records_persons__gender'] = gender.lower()
				#filters['records_persons__recordspersons__relation'] = person_relation.lower()

		search_string = self.request.query_params.get('search', None)
		if search_string is not None:
			search_field = self.request.query_params.get('search_field', 'record')
			search_string = search_string.lower();

			if search_field.lower() == 'record':
				queryset = queryset.filter(Q(title__icontains=search_string) | Q(text__icontains=search_string))
			elif search_field.lower() == 'person':
				filters['records_persons__name__icontains'] = search_string
			elif search_field.lower() == 'place':
				queryset = queryset.filter(Q(places__name__icontains=search_string) | Q(places__harad__name__icontains=search_string) | Q(places__harad__lan__icontains=search_string) | Q(places__harad__landskap__icontains=search_string))

		record_ids = self.request.query_params.get('record_ids', None)
		if record_ids is not None:
			record_id_list = record_ids.split(',')
			filters['id__in'] = record_id_list

		queryset = queryset.filter(**filters).distinct()

		#processed_query = str(queryset.query)
		#processed_query = processed_query.replace('INNER JOIN', 'LEFT JOIN')
		#queryset.raw(processed_query)

		print(queryset.query)

		return queryset

	#def retrieve(self, request, pk=None):
	#	queryset = Records.objects.all()
	#	record = get_object_or_404(queryset, pk=pk)
	#	serializer = SingleRecordSerializer(record)
	#	return Response(serializer.data)

class PersonsViewSet(viewsets.ReadOnlyModelViewSet):
	queryset = Persons.objects.all()
	serializer_class = PersonsSerializer


class LocationsViewSet(viewsets.ReadOnlyModelViewSet):
	def get_queryset(self):
		queryset = Socken.objects.all()

		filters = {}

		socken_name = self.request.query_params.get('socken_name', None)
		if socken_name is not None:
			socken_name = socken_name.lower();

			filters['name__icontains'] = socken_name

		landskap_name = self.request.query_params.get('landskap_name', None)
		if landskap_name is not None:
			landskap_name = landskap_name.lower();

			queryset = queryset.filter(Q(harad__name__icontains=landskap_name) | Q(harad__landskap__icontains=landskap_name))

		queryset = queryset.filter(**filters).distinct()

		return queryset

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

class LantmaterietProxyView(ProxyView):
	upstream = 'http://maps.lantmateriet.se/topowebb/v1/wmts/1.0.0/topowebb/default/3006/'

	def get_request_headers(self):
		headers = super(LantmaterietProxyView, self).get_request_headers()

		authHeaderHash = b64encode(b'ifsf0001:XgDmt3SC60l').decode("ascii")

		headers['Authorization'] = 'Basic %s' %  authHeaderHash
		return headers

class FeedbackViewSet(viewsets.ViewSet):
	def list(self, request):
		return Response()

	def post(self, request, format=None):
		if 'json' in request.data:
			jsonData = json.loads(request.data['json'])
			print(jsonData['from_email'])

			send_mail(jsonData['subject'], jsonData['message'], jsonData['from_email'], [jsonData['email']+'@sprakochfolkminnen.se' if hasattr(jsonData, 'email') else es_config.feedbackEmail], fail_silently=False)
		return JsonResponse({'success':'true', 'data': jsonData})

	def get_permissions(self):
		permission_classes = [permissions.AllowAny]

		return [permission() for permission in permission_classes]

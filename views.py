from django.db.models.functions import Now

from .models import Records, Persons, Socken, Categories, RecordsPersons, CrowdSourceUsers
from django.contrib.auth.models import User
import requests
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
from django.views.decorators.clickjacking import xframe_options_exempt

from . import config

import logging
logger = logging.getLogger(__name__)

from rest_framework.authentication import SessionAuthentication, BasicAuthentication

class CsrfExemptSessionAuthentication(SessionAuthentication):

    def enforce_csrf(self, request):
        return  # To not perform the csrf check previously happening

@xframe_options_exempt
def isofGeoProxy(request):
    # Example:
    # https://oden-test.isof.se/geoserver/gwc/service/wmts?REQUEST=GetTile&SERVICE=WMTS&VERSION=1.0.0&LAYER=SockenStad_ExtGranskning-clipped:SockenStad_ExtGranskn_v1.0_clipped&STYLE=&TILEMATRIX=EPSG:900913:4&TILEMATRIXSET=EPSG:900913&FORMAT=application/x-protobuf;type=mapbox-vector&TILECOL=9&TILEROW=4
    # http://localhost:8000/api/isofGeoProxy?REQUEST=GetTile&SERVICE=WMTS&VERSION=1.0.0&LAYER=SockenStad_ExtGranskning-clipped:SockenStad_ExtGranskn_v1.0_clipped&STYLE=&TILEMATRIX=EPSG:900913:4&TILEMATRIXSET=EPSG:900913&FORMAT=application/x-protobuf;type=mapbox-vector&TILECOL=9&TILEROW=4
    url = 'https://oden-test.isof.se/geoserver/gwc/service/wmts'
    #response = requests.get(url, params=request.GET)
    headers = None
    if headers in request:
        headers=request.headers

    response = requests.get(url, headers=headers, params=request.GET)
    print(request)
    print(response)
    print(request.GET)
    print(response.headers)
    print(response.content)
    print(response.GET)
    return response

class CategoriesViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Categories.objects.all()
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

        recordtype = self.request.query_params.get('recordtype', None)
        if recordtype is not None:
            recordtype_values = recordtype.split(',')
            filters['record_type__in'] = recordtype_values

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
                queryset = queryset.filter(Q(records_persons__gender=gender.lower()) and Q(
                    records_persons__recordspersons__relation=person_relation.lower()))
            else:
                filters['records_persons__gender'] = gender.lower()
            # filters['records_persons__recordspersons__relation'] = person_relation.lower()

        search_string = self.request.query_params.get('search', None)
        if search_string is not None:
            search_field = self.request.query_params.get('search_field', 'record')
            search_string = search_string.lower();

            if search_field.lower() == 'record':
                queryset = queryset.filter(Q(title__icontains=search_string) | Q(text__icontains=search_string))
            elif search_field.lower() == 'person':
                filters['records_persons__name__icontains'] = search_string
            elif search_field.lower() == 'place':
                queryset = queryset.filter(
                    Q(places__name__icontains=search_string) | Q(places__harad__name__icontains=search_string) | Q(
                        places__harad__lan__icontains=search_string) | Q(
                        places__harad__landskap__icontains=search_string))

        record_ids = self.request.query_params.get('record_ids', None)
        if record_ids is not None:
            record_id_list = record_ids.split(',')
            filters['id__in'] = record_id_list

        queryset = queryset.filter(**filters).distinct()

        # processed_query = str(queryset.query)
        # processed_query = processed_query.replace('INNER JOIN', 'LEFT JOIN')
        # queryset.raw(processed_query)

        print(queryset.query)

        return queryset

# def retrieve(self, request, pk=None):
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

            queryset = queryset.filter(
                Q(harad__name__icontains=landskap_name) | Q(harad__landskap__icontains=landskap_name))

        queryset = queryset.filter(**filters).distinct()

        return queryset

    serializer_class = SockenSerializer


class _LocationsViewSet(viewsets.ReadOnlyModelViewSet):
    def get_queryset(self):
        queryset = Socken.objects.all()

        filters = {}

        country = self.request.query_params.get('country', None)
        if country is not None:
            # queryset = queryset.filter(socken_records__country=country)
            filters['socken_records__country'] = country

        category = self.request.query_params.get('category', None)
        if category is not None:
            # queryset = queryset.filter(socken_records__category=category)
            filters['socken_records__category'] = category.upper()

        type = self.request.query_params.get('type', None)
        if type is not None:
            type_values = type.split(',')
            # queryset = queryset.filter(socken_records__type__in=type_values).distinct()
            filters['socken_records__type__in'] = type_values

        search_string = self.request.query_params.get('search', None)
        if search_string is not None:
            search_field = self.request.query_params.get('search_field', 'record')

            if search_field.lower() == 'record':
                queryset = queryset.filter(Q(socken_records__title__icontains=search_string) | Q(
                    socken_records__text__icontains=search_string))
            if search_field.lower() == 'person':
                filters['socken_records__persons__name__icontains'] = search_string

        only_categories = self.request.query_params.get('only_categories', None)
        if only_categories is not None:
            # queryset = queryset.filter(~Q(socken_records__category=None))
            queryset = queryset.exclude(socken_records__category='')

        queryset = queryset.filter(**filters).distinct()

        print(queryset.query)

        return queryset

    def paginate_queryset(self, queryset, view=None):
        return None

    serializer_class = SockenSerializer


class LantmaterietProxyView(ProxyView):
    upstream = config.LantmaterietProxy

    def get_request_headers(self):
        headers = super(LantmaterietProxyView, self).get_request_headers()

        authHeaderHash = b64encode(config.LantmaterietProxy_access.encode()).decode("ascii")

        headers['Authorization'] = 'Basic %s' % authHeaderHash
        return headers

class LantmaterietEpsg3857ProxyView(ProxyView):
    upstream = config.LantmaterietEpsg3857Proxy

    def get_request_headers(self):
        headers = super(LantmaterietEpsg3857ProxyView, self).get_request_headers()

        authHeaderHash = b64encode(config.LantmaterietProxy_access.encode()).decode("ascii")

        headers['Authorization'] = 'Basic %s' % authHeaderHash
        return headers

class LantmaterietNedtonadEpsg3857ProxyView(ProxyView):
    upstream = config.LantmaterietNedtonadEpsg3857Proxy

    def get_request_headers(self):
        headers = super(LantmaterietNedtonadEpsg3857ProxyView, self).get_request_headers()

        authHeaderHash = b64encode(config.LantmaterietProxy_access.encode()).decode("ascii")

        headers['Authorization'] = 'Basic %s' % authHeaderHash
        return headers

class LantmaterietOrtoProxyView(ProxyView):
    upstream = config.LantmaterietOrtoProxy

    def get_request_headers(self):
        headers = super(LantmaterietOrtoProxyView, self).get_request_headers()

        authHeaderHash = b64encode(config.LantmaterietProxy_access.encode()).decode("ascii")

        headers['Authorization'] = 'Basic %s' % authHeaderHash
        return headers

class LantmaterietHistOrtoProxyView(ProxyView):
    upstream = config.LantmaterietHistOrtoProxy

    def get_request_headers(self):
        headers = super(LantmaterietHistOrtoProxyView, self).get_request_headers()

        authHeaderHash = config.LantmaterietProxy_access_opendata.encode().decode("ascii")
        print(authHeaderHash)

        headers['Authorization'] = authHeaderHash
        return headers

class IsofGeoProxyView(ProxyView):
    upstream = config.IsofGeoProxy

    def get_request_headers(self):
        headers = super(IsofGeoProxyView, self).get_request_headers()
        return headers

# Probably not needed anymore, removed references in client code. Keep for a while, just in case. (20210610)
class IsofHomepageView(ProxyView):
    upstream = config.IsofHomepage

    def get_request_headers(self):
        headers = super(IsofHomepageView, self).get_request_headers()
        return headers

class FilemakerProxyView(ProxyView):
    upstream = config.FilemakerProxy

    def get_request_headers(self):
        headers = super(FilemakerProxyView, self).get_request_headers()
        return headers

class FriggStaticView(ProxyView):
    upstream = config.FriggStatic

    def get_request_headers(self):
        headers = super(FriggStaticView, self).get_request_headers()
        return headers


class FeedbackViewSet(viewsets.ViewSet):
    def list(self, request):
        return Response()

    def post(self, request, format=None):
        if 'json' in request.data:
            jsonData = json.loads(request.data['json'])
            print(jsonData['from_email'])

            recordid = None
            send_to_user = User.objects.filter(username='supportisof').first()
            if send_to_user is not None:
                send_to = send_to_user.email
            if 'recordid' in jsonData:
                recordid = jsonData['recordid']
                record = Records.objects.filter(id=recordid).first()
                if record is not None:
                    orgcode = record.id[0 : 3]
                    if not orgcode.isnumeric():
                        send_to_user = User.objects.filter(username='support' + orgcode).first()
                        if send_to_user is not None:
                            send_to = send_to_user.email

#            if 'send_to' in jsonData:
#                logger.debug(jsonData['send_to'])
#                user = User.objects.get(name=jsonData['send_to']).first()
#                if user is not None:
#                    if user.email is not None:
#                        if '@' in user.email:
#                            send_to = user.email
#            logger.debug(send_to)

            send_mail(jsonData['subject'], jsonData['message'], jsonData['from_email'], [
                send_to if send_to is not None else config.feedbackEmail],
                      fail_silently=False)
            # send_mail(jsonData['subject'], jsonData['message'], jsonData['from_email'], [
            #    jsonData['send_to'] + '@sprakochfolkminnen.se' if 'send_to' in jsonData else config.feedbackEmail],
            #          fail_silently=False)
        return JsonResponse({'success': 'true', 'data': jsonData})

    def get_permissions(self):
        permission_classes = [permissions.AllowAny]

        return [permission() for permission in permission_classes]


class TranscribeViewSet(viewsets.ViewSet):
    authentication_classes = (CsrfExemptSessionAuthentication, BasicAuthentication)

    def list(self, request):
        return Response()

    # I'm almost certain the DRF authentication middleware entirely ignores any such decorator. https://stackoverflow.com/questions/19897973/how-to-unset-csrf-in-modelviewset-of-django-rest-framework
    #@method_decorator(csrf_exempt)
    def post(self, request, format=None):
        # if request.data is not None:
        response_status = 'false'
        response_message = None
        if 'json' in request.data:
            jsonData = json.loads(request.data['json'])
            print(jsonData)
            recordid = jsonData['recordid']

            # find record
            # transcribed_record_arr = []
            transcribedrecord = Records.objects.get(pk=recordid)
            # transcribed_record_arr += transcribedrecord
            # if len(transcribed_record_arr) == 1:
            # Check if transcribed (message)
            if transcribedrecord is not None and 'message' in jsonData:
                # Naive logic: First transcriber of a record saving WINS!
                # TODO: Make transcription of same record less likely
                statuses_for_already_transcribed = ['transcribed', 'reviewing', 'approved', 'published']
                if transcribedrecord.transcriptionstatus == 'readytotranscribe':
                    response_message = 'OBS: BETAVERSION med begränsat stöd för avskriftstatus: Status avskrift av uppteckningen har inte aktiverats. Om detta händer och du vill meddela isof: Tryck "Frågor och svar" och förklara i meddelandetexten.'
                if transcribedrecord.transcriptionstatus in statuses_for_already_transcribed:
                    response_message = 'OBS: BETAVERSION med begränsat stöd för avskriftstatus: Uppteckningen avskriven av någon annan. Om detta händer och du vill meddela isof: Tryck "Frågor och svar" och förklara i meddelandetexten.'
                if transcribedrecord.transcriptionstatus == 'untranscribed':
                    response_message = 'Ett oväntat fel: Uppteckningen är inte utvald för transkribering.'
                # Only possible to register transcription when status (not already transcribed):
                # ('readytotranscribe'?),'undertranscription':
                if transcribedrecord.transcriptionstatus == 'undertranscription':
                        user = User.objects.filter(username='restapi').first()

                    transcribedrecord.text = jsonData['message']
                    if 'recordtitle' in jsonData:
                        # Validate the string
                        recordtitle = jsonData['recordtitle']
                        if self.validateString(recordtitle):
                            transcribedrecord.title = recordtitle

                    if 'messageComment' in jsonData:
                        # transcribedrecord.transcriptioncomment = jsonData['messageComment']
                        if transcribedrecord.comment is None:
                            transcribedrecord.comment = 'Transcriptioncomment:' + jsonData['messageComment']
                        else:
                            transcribedrecord.comment = transcribedrecord.comment + ' Transcriptioncomment:' + jsonData[
                                'messageComment']
                    transcribedrecord.transcriptionstatus = 'transcribed'
                    transcribedrecord.transcriptiondate = Now()

                    # Save informant when there is an informant name
                    if 'informantName' in jsonData:
                        informant = Persons()
                        informant.id = 'crwd' + recordid
                        informant.name = jsonData['informantName']
                        if 'informantBirthPlace' in jsonData:
                            informant.birthplace = jsonData['informantBirthPlace']
                            # informant.biography = 'BirthPlace: ' + jsonData['informantBirthPlace'] + 'Extra: ' + jsonData['informantInformation']
                        if 'informantBirthDate' in jsonData:
                            if jsonData['informantBirthDate'].isdigit():
                                informant.birth_year = jsonData['informantBirthDate']
                        if 'informantInformation' in jsonData:
                            # biography = biography + 'Extra: ' + jsonData['informantInformation']
                            informant.transcriptioncomment = jsonData['informantInformation']

                        # if 'informantBirthPlace' in jsonData and 'informantBirthDate' in jsonData:
                        # Check if a informant that is crowdsourced already exists
                        # to avoid lots of rows with the same informant data:
                        existing_person = Persons.objects.filter(name=informant.name, birth_year=informant.birth_year,
                                                                 biography=informant.biography,transcriptioncomment=informant.transcriptioncomment).first()
                        if existing_person is None:
                            print(informant)
                            informant.createdby = user
                            informant.editedby = user
                            # Save new informant
                            try:
                                # informant.createdate = Now()
                                informant.save()
                            except Exception as e:
                                print(e)
                        else:
                            # Use existing informant
                            informant = existing_person

                    if informant is not None:
                        # Check if records_person relation already exists:
                        existing_records_person = RecordsPersons.objects.filter(person=informant,
                                                                                record=transcribedrecord,
                                                                                relation='i').first()
                        if existing_records_person is None:
                            # records_person = RecordsPersons()
                            records_person = RecordsPersons(person=informant, record=transcribedrecord, relation='i')
                            # records_person.person = informant.id
                            # records_person.record = transcribedrecord.id
                            # records_person.relation = 'i'
                            try:
                                records_person.save()
                            except Exception as e:
                                print(e)

                        # transcribedrecord.records_persons = records_person
                    crowdsource_user = None
                    if 'from_name' in jsonData:
                        crowdsource_user = CrowdSourceUsers()
                        # TODO: Find unique id if transcription rejected and new user starts with same recordid
                        crowdsource_user.userid = 'rid' + recordid
                        crowdsource_user.name = jsonData['from_name']
                        if 'from_email' in jsonData:
                            crowdsource_user.email = jsonData['from_email']
                            transcribedrecord.comment = 'Transkriberat av: ' + jsonData['from_name'] + ', ' + jsonData['from_email']

                        if crowdsource_user.email is not None or crowdsource_user.name is not None:

                            # Check if crowdsource user already exists:
                            existing_crowdsource_user = CrowdSourceUsers.objects.filter(name=crowdsource_user.name,
                                email=crowdsource_user.email).first()
                            if existing_crowdsource_user is None:
                                # print(crowdsource_user)
                                # Save new
                                crowdsource_user.save()
                            else:
                                # Use existing
                                crowdsource_user = existing_crowdsource_user

                        # print(transcribedrecord)
                    else:
                        crowdsource_user = CrowdSourceUsers.objects.filter(userid='isof-unspecified').first()
                    if crowdsource_user is not None:
                        transcribedrecord.transcribedby = crowdsource_user
                    try:
                        transcribedrecord.save()
                        response_status = 'true'
                        logger.debug("TranscribeViewSet data %s", jsonData)
                    except Exception as e:
                        print(e)
                else:
                    if response_message is None:
                        response_message = 'Ett oväntat fel: Inte redo för transkribering.'
            else:
                response_message = 'Ett oväntat fel: Posten finns inte.'
        else:
            response_message = 'Ett oväntat fel: Error in request'
        json_response = {'success': response_status, 'data': jsonData}
        if response_message is not None:
            json_response = {'success': response_status, 'data': jsonData, 'message': response_message}
        return JsonResponse(json_response)

    def validateString(self, title):
        if title is not None:
            return isinstance(title, str) and len(title) > 0  # It is a string that is longer than 0.
        return False

    def get_permissions(self):
        permission_classes = [permissions.AllowAny]

        return [permission() for permission in permission_classes]


class TranscribeStartViewSet(viewsets.ViewSet):
    authentication_classes = (CsrfExemptSessionAuthentication, BasicAuthentication)

    def list(self, request):
        return Response()

    # I'm almost certain the DRF authentication middleware entirely ignores any such decorator. https://stackoverflow.com/questions/19897973/how-to-unset-csrf-in-modelviewset-of-django-rest-framework
    #@method_decorator(csrf_exempt)
    def post(self, request, format=None):
        response_status = 'false'
        response_message = None
        #if request.data is not None:
        if 'json' in request.data:
            jsonData = json.loads(request.data['json'])
            print(jsonData)
            recordid = jsonData['recordid']

            # find record
            transcribedrecord = Records.objects.get(pk=recordid)
            if transcribedrecord is not None:
                if transcribedrecord.transcriptionstatus == 'readytotranscribe':
                    transcribedrecord.transcriptionstatus = 'undertranscription'
                    transcribedrecord.transcriptiondate = Now()

                    try:
                        transcribedrecord.save()
                        response_status = 'true'
                        logger.debug("TranscribeStartViewSet data %s", jsonData)
                    except Exception as e:
                        logger.debug("TranscribeStartViewSet Exception: %s", jsonData)
                        print(e)
                else:
                    response_message = 'OBS BETAVERSION! Åtgärdsförslag finns för att undvika detta: Posten är redan avskriven och under behandling.'
                    statuses_for_already_transcribed = ['transcribed', 'reviewing', 'approved', 'published']
                    if transcribedrecord.transcriptionstatus == 'undertranscription':
                        response_message = 'OBS: BETAVERSION med begränsat stöd för avskriftstatus: Uppteckningen under avskrift av någon annan. Om detta händer och du vill meddela isof: Tryck "Frågor och svar" och förklara i meddelandetexten.'
                    if transcribedrecord.transcriptionstatus in statuses_for_already_transcribed:
                        response_message = 'OBS: BETAVERSION med begränsat stöd för avskriftstatus: Uppteckningen avskriven av någon annan. Om detta händer och du vill meddela isof: Tryck "Frågor och svar" och förklara i meddelandetexten.'
                    if transcribedrecord.transcriptionstatus == 'untranscribed':
                        response_message = 'Ett oväntat fel: Uppteckningen är inte utvald för transkribering.'
            else:
                response_message = 'Ett oväntat fel: Posten finns inte!'
        else:
            response_message = 'Ett oväntat fel: Error in request'
        json_response = {'success': response_status, 'data': jsonData}
        if response_message is not None:
            json_response = {'success': response_status, 'data': jsonData, 'message': response_message}
        return JsonResponse(json_response)

    def get_permissions(self):
        permission_classes = [permissions.AllowAny]

        return [permission() for permission in permission_classes]


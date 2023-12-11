from django.db.models.functions import Now
from datetime import datetime
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
from django.http import JsonResponse, HttpResponse
import json
from django.views.decorators.clickjacking import xframe_options_exempt
# from csp.decorators import csp

from . import config
from . import secrets_env

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

        publishstatus = self.request.query_params.get('publishstatus', None)
        if publishstatus is not None:
            publishstatus_values = publishstatus.split(',')
            filters['publishstatus__in'] = publishstatus_values

        update_status = self.request.query_params.get('update_status', None)
        if update_status is not None:
            update_status_values = update_status.split(',')
            filters['update_status__in'] = update_status_values

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

"""
Simple Lantmäteriet service proxy using basic request module

NOTE: NOT YET WORKING:
b'<!DOCTYPE HTML PUBLIC "-//IETF//DTD HTML 2.0//EN">\n<html><head>\n<title>401 Unauthorized</title>\n</head><body>\n<h1>Unauthorized</h1>\n<p>This server could not verify that you\nare authorized to access the document\nrequested.  Either you supplied the wrong\ncredentials (e.g., bad password), or your\nbrowser doesn\'t understand how to supply\nthe credentials required.</p>\n</body></html>\n'

https://frigg.isof.se/sagendatabas/api/lm_epsg3857_proxy/9/151/277.png
https://frigg.isof.se/sagendatabas/api/simple_lm_proxy/9/151/277.png
http://localhost:8000/api/simple_lm_proxy/9/151/277.png
"""
def SimpleLantmaterietProxy(request):
    import requests

    print(request)
    print(request.path)
    print(request.GET)

    access = config.LantmaterietProxy_access. split(":")
    username = access[0]
    password = access[1]

    # username = b64encode(username.encode()).decode("ascii")
    # password = b64encode(password.encode()).decode("ascii")

    path = request.path.split("simple_lm_proxy")[1]
    url = config.LantmaterietProxy + path[1:]

    from requests.auth import HTTPBasicAuth
    #res = requests.get(url, auth=HTTPBasicAuth('user', 'password'))
    #res = requests.get(url, auth=(username, password))
    #print(res)

    #response = requests.get(url, params=request.GET)
    headers = None
    if headers in request:
        headers=request.headers

        authHeaderHash = b64encode(config.LantmaterietProxy_access.encode()).decode("ascii")
        headers['Authorization'] = 'Basic %s' % authHeaderHash
    else:
        authHeaderHash = b64encode(config.LantmaterietProxy_access.encode()).decode("ascii")
        authHeaderHash = config.LantmaterietProxy_access
        headers = {
            'Authorization': 'Basic %s' % authHeaderHash,
        }

    # response = requests.get(url, auth=(username, password))
    # response = requests.get(url, headers=headers, auth=(username, password))
    response = requests.get(url, headers=headers)
    # , params=request.GET)

    print(url)
    print(response)
    print(response.headers)
    print(response.content)
    # print(response.GET)

    return response


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

# Does not work: url(r'^filemaker_proxy/(?P<path>.*)$', views.FilemakerProxyView.as_view()),
# AttributeError: 'function' object has no attribute 'as_view'
# @csp(DEFAULT_SRC=["'self'"], IMG_SRC=['imgsrv.com'], MEDIA_SRC=['imgsrv.com'], FRAME_SRC=['imgsrv.com'],OBJECT_SRC=['scriptsrv.com', 'googleanalytics.com'])
class FilemakerProxyView(ProxyView):
    upstream = config.FilemakerProxy

    def get_request_headers(self):
        headers = super(FilemakerProxyView, self).get_request_headers()
        # Does not work: Should be added to response-headers instead:
        # https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/X-Frame-Options:
        # The Content-Security-Policy HTTP header has a frame-ancestors directive which you can use instead.
        # headers['Content-Security-Policy'] = "frame-ancestors 'self' https://sok.folke.isof.se"
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

"""
Common method for save transcription

Parameters
response_status
set_status_to_transcribed Boolean: True if transcription is finished, i.e. "sent", otherwise only saved temporarily
"""
def save_transcription(request, response_message, response_status, set_status_to_transcribed):
    if 'json' in request.data:
        jsonData = json.loads(request.data['json'])
        print(jsonData)
        recordid = jsonData['recordid']

        # find record
        # transcribed_record_arr = []
        transcribedrecord = None
        if Records.objects.filter(pk=recordid).exists():
            transcribedrecord = Records.objects.get(pk=recordid)
        # transcribed_record_arr += transcribedrecord
        # if len(transcribed_record_arr) == 1:

        # Check transcribe session id:
        transcribesession_status = False
        if 'transcribesession' in jsonData:
            transcribesession = None
            if 'transcribesession' in jsonData:
                transcribesession = jsonData['transcribesession']
            # if str(transcribedrecord.transcriptiondate.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]) in transcribesession:
            if str(transcribedrecord.transcriptiondate.strftime('%Y-%m-%d %H:%M:%S')) in transcribesession:
                transcribesession_status = True
        # Temporarily avoid transcribesession_status:
        # transcribesession_status = True
        # Check transcribesession_status:
        if transcribesession_status != True:
            transcribedrecord = None

        # Check if transcribed (message)
        if transcribedrecord is not None and 'message' in jsonData:
            # Naive logic: First transcriber of a record saving WINS!
            # Idea for improvement: Somehow make transcription of same record less likely
            statuses_for_already_transcribed = ['transcribed', 'reviewing', 'needsimprovement', 'approved',
                                                'published', 'autopublished']
            if transcribedrecord.transcriptionstatus == 'readytotranscribe':
                response_message = 'OBS: BETAVERSION med begränsat stöd för avskriftstatus: Status avskrift av uppteckningen har inte aktiverats. Om detta händer och du vill meddela isof: Tryck "Frågor och synpunkter" och förklara i meddelandetexten.'
                if transcribedrecord.transcriptionstatus in statuses_for_already_transcribed:
                    response_message = 'Uppteckningen skrivs av av en annan användare. Gå gärna tillbaka och välj en annan uppteckning.'
                if transcribedrecord.transcriptionstatus == 'untranscribed':
                    response_message = 'Ett oväntat fel: Uppteckningen är inte utvald för transkribering.'
            # Only possible to register transcription when status (not already transcribed):
            # ('readytotranscribe'?),'undertranscription':
            if transcribedrecord.transcriptionstatus == 'undertranscription':
                informant = None
                user = User.objects.filter(username='restapi').first()
                transcribe_time = 0
                if transcribedrecord.transcriptiondate is not None:
                    transcribe_time = datetime.now() - transcribedrecord.transcriptiondate
                if transcribe_time.total_seconds() > 0:
                    if transcribedrecord.transcribe_time is None:
                        transcribedrecord.transcribe_time = int(transcribe_time.total_seconds() / 60)
                    else:
                        # Not using "saves before last transcribed":
                        transcribedrecord.transcribe_time = int(transcribe_time.total_seconds() / 60)
                        # Note: To handle "saves before last transcribed":
                        # 1. When first save for this session: make sure transcribe_time starts from zero
                        # HOW TO: Identify first save for this session?
                        # 2. Add transcribe times:
                        # transcribedrecord.transcribe_time = transcribedrecord.transcribe_time + int(transcribe_time.total_seconds() / 60)
                transcribedrecord.text = jsonData['message']
                if 'recordtitle' in jsonData:
                    # Validate the string
                    recordtitle = jsonData['recordtitle']
                    if validateString(recordtitle):
                        transcribedrecord.title = recordtitle

                if 'messageComment' in jsonData:
                    # transcribedrecord.transcriptioncomment = jsonData['messageComment']
                    if transcribedrecord.transcription_comment is None:
                        transcribedrecord.transcription_comment = jsonData['messageComment']
                    else:
                        separator = ''
                        if len(transcribedrecord.transcription_comment) > 0:
                            separator = ';'
                        transcribedrecord.transcription_comment = transcribedrecord.transcription_comment + separator + \
                                                                  jsonData['messageComment']
                if set_status_to_transcribed == True:
                    transcribedrecord.transcriptionstatus = 'transcribed'
                    transcribedrecord.transcriptiondate = Now()

                    # Save informant when there is an informant name (more than 1 letter)
                    if 'informantName' in jsonData:
                        if len(jsonData['informantName']) > 1:
                            informant = Persons()
                            informant.id = 'crwd' + recordid
                            informant.name = jsonData['informantName']
                            if 'informantBirthPlace' in jsonData:
                                informant.birthplace = jsonData['informantBirthPlace']
                                # informant.biography = 'BirthPlace: ' + jsonData['informantBirthPlace'] + 'Extra: ' + jsonData['informantInformation']
                            if 'informantBirthDate' in jsonData:
                                if jsonData['informantBirthDate'].isdigit():
                                    informant.birth_year = jsonData['informantBirthDate']

                            # if 'informantBirthPlace' in jsonData and 'informantBirthDate' in jsonData:
                            # Check if a informant that is crowdsourced already exists
                            # to avoid lots of rows with the same informant data.
                            # Very likely same informant if:
                            # Name, birth year and birthplace exactly the same.
                            # 'Field under "informant"' is saved in person.transcriptioncomment
                            existing_person = Persons.objects.filter(name=informant.name,
                                                                     birth_year=informant.birth_year,
                                                                     birthplace=informant.birthplace).first()
                            if existing_person is None:
                                logger.debug(informant)
                                informant.transcriptionstatus = 'transcribed'
                                informant.createdby = user
                                informant.editedby = user
                                informant.createdate = Now()
                            else:
                                # Use existing informant
                                informant = existing_person

                            if informant is not None:
                                if 'informantInformation' in jsonData:
                                    informantInformation = jsonData['informantInformation']
                                    # Check if informant.transcriptioncomment is empty
                                    if informant.transcriptioncomment is None:
                                        # Set informant.transcriptioncomment to informantInformation
                                        informant.transcriptioncomment = informantInformation
                                    # Else: informant.transcriptioncomment is not empty
                                    else:
                                        # check if informantInformation already exists as substring in informant.transcriptioncomment
                                        if informantInformation not in informant.transcriptioncomment:
                                            # Append informantInformation to informant.transcriptioncomment, separated by ';'
                                            informant.transcriptioncomment = informant.transcriptioncomment + ';' + informantInformation
                                            # cut off any leading or trailing spaces or ';'
                                            informant.transcriptioncomment = informant.transcriptioncomment.strip()
                                            informant.transcriptioncomment = informant.transcriptioncomment.strip(';')
                                    
                                    # cut off informant.transcriptioncomment if longer than 255 characters and add '...'
                                    if len(informant.transcriptioncomment) > 250:
                                        informant.transcriptioncomment = informant.transcriptioncomment[:250] + '...'


                                # Save new or updated informant
                                try:
                                    # informant.createdate = Now()
                                    informant.save()
                                except Exception as e:
                                    print(e)

                                # Check if records_person relation already exists:
                                existing_records_person = RecordsPersons.objects.filter(person=informant,
                                                                                        record=transcribedrecord,
                                                                                        relation__in=['i', 'informant']).first()
                                if existing_records_person is None:
                                    # records_person = RecordsPersons()
                                    records_person = RecordsPersons(person=informant, record=transcribedrecord,
                                                                    relation='informant')
                                    # records_person.person = informant.id
                                    # records_person.record = transcribedrecord.id
                                    # records_person.relation = 'informant'
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
                        # crowdsource_user gets default values for: role
                        crowdsource_user.name = jsonData['from_name']
                        if 'from_email' in jsonData:
                            crowdsource_user.email = jsonData['from_email']
                            # Set "transcribed by" when published in admin interface:
                            # transcribedrecord.comment = 'Transkriberat av: ' + jsonData['from_name'] + ', ' + jsonData['from_email']

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
                        # Add anonymous user:
                        crowdsource_user = CrowdSourceUsers.objects.filter(userid='crowdsource-anonymous').first()
                    if crowdsource_user is not None:
                        # TODO: if user undefined add anonymous user 'crowdsource-anonymous':
                        # if len(crowdsource_user.name) == 0 and len(crowdsource_user.email):
                        transcribedrecord.transcribedby = crowdsource_user

                # Check if transcribed record should be automatically published
                # If crowdsource user has role supertranscriber:
                if crowdsource_user is not None:
                    if "supertranscriber" in crowdsource_user.role:
                        transcribedrecord.transcriptionstatus = "autopublished"
                        transcribedrecord.publishstatus = "published"
                        if informant is not None:
                            # Set autopublish for informants not published
                            if informant.transcriptionstatus != 'published':
                                informant.transcriptionstatus = 'autopublished'
                                informant.save()

                # Save record
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
            response_message = 'Ett oväntat fel: Posten finns inte, felaktigt sessions-id eller inget json-data.'
    else:
        response_message = 'Ett oväntat fel: Error in request'
    return jsonData, response_message, response_status

def validateString(string):
    if string is not None:
        return isinstance(string, str) and len(string) > 0  # It is a string that is longer than 0.
    return False

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
        set_status_to_transcribed = True
        jsonData, response_message, response_status = save_transcription(request, response_message,
                                                                              response_status,
                                                                              set_status_to_transcribed)
        json_response = {'success': response_status, 'data': jsonData}
        if response_message is not None:
            json_response = {'success': response_status, 'data': jsonData, 'message': response_message}
        return JsonResponse(json_response)

    def get_permissions(self):
        permission_classes = [permissions.AllowAny]

        return [permission() for permission in permission_classes]

class TranscribeSaveViewSet(viewsets.ViewSet):
    authentication_classes = (CsrfExemptSessionAuthentication, BasicAuthentication)

    def list(self, request):
        return Response()

    # I'm almost certain the DRF authentication middleware entirely ignores any such decorator. https://stackoverflow.com/questions/19897973/how-to-unset-csrf-in-modelviewset-of-django-rest-framework
    #@method_decorator(csrf_exempt)
    def post(self, request, format=None):
        # if request.data is not None:
        response_status = 'false'
        response_message = None
        set_status_to_transcribed = False
        jsonData, response_message, response_status = save_transcription(request, response_message,
                                                                              response_status,
                                                                              set_status_to_transcribed)
        json_response = {'success': response_status, 'data': jsonData}
        if response_message is not None:
            json_response = {'success': response_status, 'data': jsonData, 'message': response_message}
        return JsonResponse(json_response)

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
            transcribedrecord = None
            if Records.objects.filter(pk=recordid).exists():
                transcribedrecord = Records.objects.get(pk=recordid)
            if transcribedrecord is not None:
                if transcribedrecord.transcriptionstatus == 'readytotranscribe':
                    transcribedrecord.transcriptionstatus = 'undertranscription'
                    transcribedrecord.transcriptiondate = Now()

                    try:
                        transcribedrecord.save()
                        response_status = 'true'
                        # Temporary transcribe session id:
                        # jsonData['transcribesession'] = str(transcribedrecord.changedate)
                        # Temporary transcribe session id: transcriptiondate
                        # Get saved transcriptiondate from database:
                        transcribedrecord2 = Records.objects.get(pk=recordid)
                        if transcribedrecord2 is not None:
                            jsonData['transcribesession'] = str(transcribedrecord2.transcriptiondate.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3])
                        logger.debug("TranscribeStartViewSet data %s", jsonData)
                    except Exception as e:
                        logger.debug("TranscribeStartViewSet Exception: %s", jsonData)
                        print(e)
                else:
                    response_message = 'OBS BETAVERSION! Åtgärdsförslag finns för att undvika detta: Posten är redan avskriven och under behandling.'
                    statuses_for_already_transcribed = ['transcribed', 'reviewing', 'needsimprovement', 'approved', 'published', 'autopublished']
                    if transcribedrecord.transcriptionstatus == 'undertranscription':
                        response_message = 'Enkel konfliktlösning vid förhoppning om ett minimum av konflikter: Den som börjar först vinner. Om detta händer och du vill meddela isof: Tryck "Frågor och synpunkter" och förklara i meddelandetexten.'
                    if transcribedrecord.transcriptionstatus in statuses_for_already_transcribed:
                        response_message = 'Uppteckningen skrivs av av en annan användare. Gå gärna tillbaka och välj en annan uppteckning.'
                    if transcribedrecord.transcriptionstatus == 'untranscribed':
                        response_message = 'Ett oväntat fel: Uppteckningen är inte utvald för transkribering.'
            else:
                response_message = 'Ett oväntat fel: Posten finns inte eller hör inte till avskriftsessionen!'
        else:
            response_message = 'Ett oväntat fel: Error in request'
        json_response = {'success': response_status, 'data': jsonData}
        if response_message is not None:
            json_response = {'success': response_status, 'data': jsonData, 'message': response_message}
        return JsonResponse(json_response)

    def get_permissions(self):
        permission_classes = [permissions.AllowAny]

        return [permission() for permission in permission_classes]

class TranscribeCancelViewSet(viewsets.ViewSet):
    authentication_classes = (CsrfExemptSessionAuthentication, BasicAuthentication)

    def list(self, request):
        return Response()

    # I'm almost certain the DRF authentication middleware entirely ignores any such decorator. https://stackoverflow.com/questions/19897973/how-to-unset-csrf-in-modelviewset-of-django-rest-framework
    # @method_decorator(csrf_exempt)
    def post(self, request, format=None):
        response_status = 'false'
        response_message = None
        # if request.data is not None:
        if 'json' in request.data:
            jsonData = json.loads(request.data['json'])
            print(jsonData)
            recordid = jsonData['recordid']

            # find record
            transcribedrecord = None
            if Records.objects.filter(pk=recordid).exists():
                transcribedrecord = Records.objects.get(pk=recordid)
            if transcribedrecord is not None:
                transcribesession = None
                changedate = 'None'
                if 'transcribesession' in jsonData:
                    transcribesession = jsonData['transcribesession']
                # Check transcription session:
                if transcribesession is not None:
                    # if str(transcribedrecord.transcriptiondate.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]) in transcribesession:
                    if str(transcribedrecord.transcriptiondate.strftime('%Y-%m-%d %H:%M:%S')) in transcribesession:
                        if transcribedrecord.transcriptionstatus == 'undertranscription':
                            transcribedrecord.transcriptionstatus = 'readytotranscribe'

                            try:
                                transcribedrecord.save()
                                response_status = 'true'
                                logger.debug("TranscribeStartViewSet data %s", jsonData)
                            except Exception as e:
                                logger.debug("TranscribeStartViewSet Exception: %s", jsonData)
                                print(e)
                        else:
                            response_message = 'OBS BETAVERSION! Åtgärdsförslag finns för att undvika detta: Posten är redan avskriven och under behandling.'
                            statuses_for_already_transcribed = ['transcribed', 'reviewing', 'needsimprovement', 'approved',
                                                                'published', 'autopublished']
                            if transcribedrecord.transcriptionstatus == 'undertranscription':
                                response_message = 'Enkel konfliktlösning vid förhoppning om ett minimum av konflikter: Den som börjar först vinner. Om detta händer och du vill meddela isof: Tryck "Frågor och synpunkter" och förklara i meddelandetexten.'
                            if transcribedrecord.transcriptionstatus in statuses_for_already_transcribed:
                                response_message = 'Uppteckningen skrivs av av en annan användare. Gå gärna tillbaka och välj en annan uppteckning.'
                            if transcribedrecord.transcriptionstatus == 'untranscribed':
                                response_message = 'Ett oväntat fel: Uppteckningen är inte utvald för transkribering.'
                    else:
                        response_message = 'Ett oväntat fel: Posten finns men i annan användarsession!'
                else:
                    response_message = 'Ett oväntat fel: Posten finns men fel status!'
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

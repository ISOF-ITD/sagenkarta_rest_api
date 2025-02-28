# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey has `on_delete` set to the desired behavior.
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from __future__ import unicode_literals
from django.contrib.auth.models import User

from django.db.models.signals import post_save
import requests, json
from threading import Timer

from django.utils.safestring import mark_safe
from string import Template

from django.db import models
from django.db.models.deletion import *
from requests.auth import HTTPBasicAuth

from . import config

import logging

from .models_accessionsregister import Accessionsregister_FormLista

import threading

logger = logging.getLogger(__name__)

# Create a thread-local data object
_thread_locals = threading.local()

def set_avoid_timer_before_update_of_search_database(avoid_timer_before_update_of_search_database):
    _thread_locals.avoid_timer_before_update_of_search_database = avoid_timer_before_update_of_search_database

def get_avoid_timer_before_update_of_search_database():
    return getattr(_thread_locals, 'avoid_timer_before_update_of_search_database', None)

class Categories(models.Model):
    id = models.CharField(primary_key=True,max_length=255)
    name = models.CharField(max_length=100, blank=False, null=False)
    type = models.CharField(max_length=100, blank=False, null=False)

    class Meta:
        managed = False
        db_table = 'categories_v2'
        ordering = ['-type', 'id']


class Harad(models.Model):
    name = models.CharField(max_length=50, blank=True, null=True)
    lan = models.CharField(max_length=30, blank=True, null=True)
    landskap = models.CharField(max_length=14, blank=True, null=True)
    country = models.CharField(unique=True, max_length=100, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'harad'


class Socken(models.Model):
    archive_row = models.IntegerField(default=None, blank=True, null=True)
    name = models.CharField(max_length=200)
    harad = models.ForeignKey(Harad, db_column='harad', on_delete=DO_NOTHING)
    lat = models.FloatField()
    lng = models.FloatField()
    name = models.CharField(max_length=200)
    fylke = models.CharField(max_length=200)
    lmId = models.IntegerField()

    socken_records = models.ManyToManyField(
        'Records',
        through = 'RecordsPlaces'
    )

    class Meta:
        managed = False
        db_table = 'socken'

class Places(models.Model):
    source_choices = [
        ('none', 'Ingen'),
        ('LM-SockenStad', 'LM-SockenStad'),
        ('NFS', 'NFS'),
        ('SLS', 'SLS'),
    ]
    polygon_type_choices = [
        ('none', 'Ingen'),
        ('LM-SockenStad', 'LM-SockenStad'),
        ('other', 'Annan'),
    ]
    mapping_status_choices = [
        ('not_reviewed', 'Ej granskad'),
        ('to_be_reviewed', 'Bör kontrolleras'),
        ('reviewed', 'Granskad'),
    ]
    id = models.IntegerField(primary_key=True)
    # socken = models.ForeignKey(Socken, null=True, blank=True, unique=True, db_column='socken', on_delete=DO_NOTHING, help_text='Folke unikt sockenid')
    socken = models.ForeignKey(Socken, null=True, blank=True, db_column='socken', on_delete=DO_NOTHING, help_text='Folke unikt sockenid')
    source = models.CharField(max_length=255, choices=source_choices, verbose_name="Datakälla", help_text='Ursprunglig databas')
    comment = models.TextField(blank=True, null=True, verbose_name="Datakällskommentar")
    polygon_type = models.CharField(max_length=255, choices=polygon_type_choices, verbose_name="Polygontyp")
    geography_comment = models.TextField(blank=True, null=True, verbose_name="Geografikommentar", help_text='Geografikommentar fritext')
    evidence = models.TextField(blank=True, null=True, verbose_name="Belägg", help_text='Källor/belägg för val av "plats med yta".')
    # Mapping check example:
    # Check LM SockenStad -> folke.place. Fields socken.lmid, socken.lmname; folke socken.name, harad.name (through places)
    mapping_check = models.CharField(max_length=255, null=True, blank=True, verbose_name="Check", help_text='Matchningscheck LM socken -> folke.socken')
    mapping_check_previous = models.CharField(max_length=255, null=True, blank=True, verbose_name="Check föregående", help_text='Matchningscheck LM socken -> folke.socken föregående')
    mapping_check_change_date = models.DateTimeField(blank=True, null=True, verbose_name="Check datum", help_text='Matchningscheck datum')
    mapping_check_previous_change_date = models.DateTimeField(blank=True, null=True, verbose_name="Check föregående datum", help_text='Matchningscheck föregående datum')
    # Geography check example: Contains point in polygon
    geography_check = models.CharField(max_length=255, null=True, blank=True, verbose_name="Geocheck", help_text='Geo matchningscheck accessionsregister socken -> folke.places')
    geography_check_previous = models.CharField(max_length=255, null=True, blank=True, verbose_name="Geocheck föregående", help_text=' Geo matchningscheck accessionsregister socken -> folke.places föregående')
    geography_check_change_date = models.DateTimeField(blank=True, null=True, verbose_name="Geocheck datum", help_text='Geo matchningscheck datum')
    geography_check_previous_change_date = models.DateTimeField(blank=True, null=True, verbose_name="Geocheck föregående datum", help_text='Geo matchningscheck föregående datum')
    mapping_status = models.CharField(max_length=255, null=True, blank=True, default='not_reviewed', choices=mapping_status_choices, verbose_name="Matchningsstatus")
    records_row_count = models.IntegerField(default=None, blank=True, null=True, verbose_name="#poster", help_text='Antal records')

    def __str__(self):
        return str(self.socken)+' ('+str(self.id)+') '
    class Meta:
        managed = True
        db_table = 'places'
        verbose_name = 'Plats med yta'
        verbose_name_plural = 'Plats med yta'

"""
Possible statuses for transcription
"""
class Transcription_statuses(models.TextChoices):
    accession = 'accession', 'Accession'  # Makes it clear that "accessions" will not be transcribed
    nottranscribable = 'nottranscribable', 'Icke transkriberbar'
    untranscribed = 'untranscribed', 'Ej transkriberad'
    readytotranscribe = 'readytotranscribe', 'Publicerad för transkribering'
    undertranscription = 'undertranscription', 'Under transkription'
    transcribed = 'transcribed', 'Transkriberad'
    reviewing = 'reviewing', 'Under granskning'
    needsimprovement = 'needsimprovement', 'Sparas för förbättring'
    approved = 'approved', 'Godkänd'
    published = 'published', 'Publicerad'
    autopublished = 'autopublished', 'Autopublicerad'

class Persons(models.Model):
    archive_row = models.IntegerField(default=None, blank=True, null=True)
    id = models.CharField(primary_key=True, max_length=50)
    name = models.CharField(max_length=255)
    gender = models.CharField(max_length=8, choices=[('female', 'Kvinna'), ('male', 'Man'), ('unknown', 'Okänd')])
    birth_year = models.IntegerField(blank=True, null=True)
    address = models.CharField(blank=True, null=True, max_length=255)
    birthplace = models.CharField(blank=True, null=True, max_length=255, verbose_name='Födelseort')
    biography = models.TextField(blank=True, null=True)
    # Pillow is used by models.ImageField: used in Sagenkarta_Rest_API and TradarkAdmin!:
    image = models.ImageField(blank=True, null=True, verbose_name='Bildfil', upload_to='personer')
    import_row_id = models.IntegerField(default=0, blank=False, null=False)
    transcriptioncomment = models.CharField(max_length=255, verbose_name='Kommentarer', default='')
    transcriptionstatus = models.CharField(max_length=20, blank=False, null=False,
                                           default=Transcription_statuses.accession,
                                           choices=Transcription_statuses.choices, verbose_name='Transkriptionstatus',
                                           help_text='OBS: one_accession_row ska ha "accession"')
    # changedate = models.DateTimeField()
    createdate = models.DateTimeField(auto_now_add=True, verbose_name="Skapad datum")
    changedate = models.DateTimeField(auto_now=True, blank=True, verbose_name="Ändrad datum")
    createdby = models.ForeignKey(User, db_column='createdby', null=True, blank=True, editable=False,
                                 on_delete=DO_NOTHING,verbose_name="Excerperad av")
    editedby = models.ForeignKey(User, db_column='editedby', null=True, blank=True, editable=False,
                                 on_delete=DO_NOTHING,related_name='Uppdaterad av+', verbose_name="Uppdaterad av")
    places = models.ManyToManyField(
        Socken,
        through='PersonsPlaces',
        through_fields = ('person', 'place')
    )

    class Meta:
        managed = False
        db_table = 'persons'


class PersonsPlaces(models.Model):
    person = models.ForeignKey(Persons, db_column='person', on_delete=DO_NOTHING, related_name='person_object')
    place = models.ForeignKey(Socken, db_column='place', on_delete=DO_NOTHING)
    relation = models.CharField(max_length=5, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'persons_places'


class Languages(models.Model):
    """
    Språk som används i materialet

    Kod/Språkkod: I första hand enligt ISO 639-1, vid behov ISO 639-3 för t.ex. Romani
    Typ: Kan användas för t.ex. att skilja på språk och dialekt
    """
    type_choices = [
        ('sprak', 'Språk'),
        ('dialekt', 'Dialekt'),
    ]


    name = models.CharField(max_length=255, blank=False, null=False, verbose_name="Namn")
    # name_en = models.CharField(max_length=255, null=True, blank=True, verbose_name="Namn på engelska")
    type = models.CharField(max_length=255, blank=True, null=True, choices=type_choices, verbose_name="Typ")
    code = models.CharField(max_length=20, blank=True, null=True, verbose_name="Språkkod")


    def __str__(self):
        # return str(self.name)+' ('+self.id+') ['+self.type+']'
        return f'{str(self.name)} ({self.id})'


    class Meta:
        managed = False
        db_table = 'languages'
        verbose_name = 'Språk'
        verbose_name_plural = 'Språk'


class CrowdSourceUsers(models.Model):
    roles = [
        ('unknown', 'Okänd'),
        ('supertranscriber', 'Supertranskriberare')
    ]

    userid = models.CharField(primary_key=True, max_length=150)
    name = models.CharField(max_length=255)
    email = models.EmailField()
    role = models.CharField(max_length=20, blank=False, null=False, default='unknown', choices=roles)
    # Track changes:
    createdate = models.DateTimeField(auto_now_add=True, verbose_name="Skapad datum")
    changedate = models.DateTimeField(auto_now=True, blank=True, verbose_name="Ändrad datum")
    createdby = models.ForeignKey(User, db_column='createdby', related_name='records_created+', null=True, blank=True,
                                  editable=False, on_delete=DO_NOTHING,
                                  verbose_name="Excerperad av")
    editedby = models.ForeignKey(User, db_column='editedby', null=True, blank=True, editable=False,
                                 on_delete=DO_NOTHING,
                                 related_name='Uppdaterad av+', verbose_name="Uppdaterad av")

    class Meta:
        managed = False
        db_table = 'crowdsource_users'


class Records(models.Model):
    transcription_statuses = [
        ('nottranscribable', 'Icke transkriberbar'),
        ('untranscribed', 'Ej transkriberad'),
        ('readytotranscribe', 'Publicerad för transkribering'),
        ('undertranscription', 'Under transkription'),
        ('transcribed', 'Transkriberad'),
        ('reviewing', 'Under granskning'),
        ('needsimprovement', 'Sparas för förbättring'),
        ('approved', 'Godkänd'),
        ('published', 'Publicerad'),
        ('autopublished', 'Autopublicerad')
    ]

    transcriptiontype_choices = [
        ('fritext', 'Fritext'),
        ('uppteckningsblankett', 'Uppteckningsblankett'),
    ]

    id = models.CharField(max_length=50, primary_key=True)
    title = models.CharField(max_length=300, verbose_name='Titel', blank=True, null=True)
    text = models.TextField(blank=True, null=True)
    contents = models.TextField(blank=True, null=True)
    headwords = models.TextField(blank=True, null=True)
    year = models.DateField(blank=True, null=True)
    # Archives not yet needed in API:
    #archive_org = models.ForeignKey(Archives, db_column="archive_org", blank=True, null=True, editable=False,
    #								on_delete=DO_NOTHING, verbose_name='Arkiv-org')
    archive_org = models.IntegerField(blank=False, null=True)
    archive = models.CharField(max_length=255, blank=True)
    archive_id = models.CharField(max_length=255, blank=True)
    archive_row = models.IntegerField(blank=False, null=True)
    type = models.CharField(max_length=20)
    record_type = models.CharField(max_length=255, blank=True, null=True)
    archive_page = models.CharField(max_length=20, blank=True, null=True)
    total_pages = models.IntegerField(blank=True, null=True)
    source = models.TextField(blank=True)
    comment = models.TextField(blank=True)
    transcription_comment = models.TextField(blank=True)
    country = models.CharField(max_length=50)
    transcriptiondate = models.DateTimeField(blank=True, verbose_name="Transkriptionsdatum")
    transcriptiontype = models.CharField(max_length=20, blank=True, null=True, default=None, choices=transcriptiontype_choices)
    transcribedby = models.ForeignKey(CrowdSourceUsers, db_column='transcribedby', null=True, blank=True, on_delete=DO_NOTHING)
    transcriptionstatus = models.CharField(max_length=20, blank=False, null=False, default=Transcription_statuses.accession, choices=Transcription_statuses.choices, verbose_name='Transkriptionstatus',
                                           help_text='OBS: one_accession_row ska ha "accession"')
    publishstatus = models.CharField(max_length=20, blank=False, null=False, default='unpublished')
    update_status = models.CharField(max_length=20, blank=True, null=True, verbose_name='Uppdateringsstatus', help_text='Utvalda för uppdatering')
    language = models.CharField(max_length=50)
    copyright_license = models.TextField(blank=True, verbose_name='Datalicens')
    pages_transcribed = models.IntegerField(blank=True, null=True, default=0)
    transcribe_time = models.IntegerField(blank=True, null=True, verbose_name='Tid att transkribera',
                                          help_text='Tid att transkribera i minuter')
    #archive_metadata_publish_level = models.CharField(max_length=20, blank=False, null=False, default='none',
    #												  choices=archive_metadata_publish_levels)
    #archive_material_publish_level = models.CharField(max_length=20, blank=False, null=False, default='none',
    #												  choices=archive_material_publish_levels)

    import_batch = models.IntegerField(blank=True, null=True, verbose_name='Importbatch')

    # Track changes:
    approvedby = models.ForeignKey(User, db_column='approvedby', null=True, blank=True, editable=False, on_delete=DO_NOTHING, verbose_name='Godkänd av')
    approvedate = models.DateTimeField(null=True, blank=True, verbose_name="Godkänd datum")
    createdate = models.DateTimeField(auto_now_add=True, verbose_name="Skapad datum")
    changedate = models.DateTimeField(auto_now=True, blank=True, verbose_name="Ändrad datum")
    createdby = models.ForeignKey(User, db_column='createdby', related_name='records_created', null=True, blank=True,
                                  editable=False, on_delete=DO_NOTHING,
                                  verbose_name="Excerperad av")
    editedby = models.ForeignKey(User, db_column='editedby', null=True, blank=True, editable=False,
                                 on_delete=DO_NOTHING,
                                 related_name='Uppdaterad av+', verbose_name="Uppdaterad av")

    records_persons = models.ManyToManyField(
        Persons,
        through='RecordsPersons', symmetrical=False
    )
    records_places = models.ManyToManyField(
        Socken,
        through = 'RecordsPlaces', symmetrical=False
    )
    taxonomy = models.ManyToManyField(
        Categories,
        through = 'RecordsCategory', symmetrical=False
    )
    languages = models.ManyToManyField(
        Languages,
        through = 'RecordsLanguage', symmetrical=False
    )

    #Only publish text when transcriptionstatus published
    def text_to_publish(self):
        text_to = None
        if self.text is not None and self.text != '':
            text_to = 'Denna text håller på att skrivas av, av en användare eller är under behandling.'
            if self.transcriptionstatus == 'nottranscribable':
                text_to = 'Denna text går inte att skriva av i nuläget.'
            # Maybe later show current status of transcription, maybe point to current status in a status list:
            # text_to = dict(self.transcription_statuses)[str(self.transcriptionstatus)]
            if self.transcriptionstatus in ['published', 'autopublished'] or self.record_type == 'one_accession_row':
                text_to = str(self.text)
        return text_to

    class Meta:
        managed = False
        db_table = 'records'


class RecordsPersons(models.Model): #ingredient
    archive_row = models.IntegerField(default=None, blank=True, null=True)
    record = models.ForeignKey(Records, db_column='record', related_name='persons', on_delete=DO_NOTHING)
    person = models.ForeignKey(Persons, db_column='person', on_delete=DO_NOTHING)
    relation = models.CharField(max_length=5, blank=True, null=True)

    createdate = models.DateTimeField(auto_now_add=True, verbose_name="Skapad datum")
    changedate = models.DateTimeField(auto_now=True, blank=True, verbose_name="Ändrad datum")

    class Meta:
        db_table = 'records_persons'


class RecordsMedia(models.Model):
    archive_row = models.IntegerField(default=None, blank=True, null=True)
    record = models.ForeignKey(Records, db_column='record', related_name='media', on_delete=DO_NOTHING)
    type = models.CharField(max_length=50, blank=True, null=True)
    store = models.CharField(max_length=20, blank=False, null=False, default='unknown', verbose_name='Lagringsyta', help_text='Pekar ut url')
    source = models.CharField(max_length=255, blank=True, null=True, verbose_name='Filidentifierare', help_text='Unik filidentifierare i lagringsytan')
    title = models.CharField(max_length=255, blank=True, null=True)
    text = models.TextField(blank=True, null=True)
    description = models.TextField(blank=True, null=True, verbose_name='Beskrivningar', help_text='Tidsatta beskrivningar')
    utterances = models.TextField(blank=True, null=True, verbose_name='Yttranden', help_text='Yttranden med ord')
    comment = models.TextField(blank=True, null=True, verbose_name='Kommentar', help_text='Publik')

    # Transcription task
    transcriptiontype = models.CharField(max_length=20, blank=True, null=True, default=None, verbose_name='Transkriptionstyp', help_text='Typ av formulär för transkribering')
    transcriptionstatus = models.CharField(max_length=20, blank=False, null=False,
                                           default=Transcription_statuses.accession,
                                           choices=Transcription_statuses.choices, verbose_name='Transkriptionstatus',
                                           help_text='OBS: one_accession_row ska ha "accession"')
    transcriptiondate = models.DateTimeField(blank=True, null=True, verbose_name="Transkriptionsdatum")
    transcription_comment = models.TextField(blank=True, null=True)
    transcribedby = models.ForeignKey(CrowdSourceUsers, db_column='transcribedby', null=True, blank=True, on_delete=DO_NOTHING, )
    approvedate = models.DateTimeField(null=True, blank=True, verbose_name="Godkänd datum")

    #Only publish text when transcriptionstatus published
    def text_to_publish(self):
        text_to = None
        if self.text is not None and self.text != '':
            text_to = 'Denna text håller på att skrivas av, av en användare eller är under behandling.'
            if self.transcriptionstatus == 'nottranscribable':
                text_to = 'Denna text går inte att skriva av i nuläget.'
            # Maybe later show current status of transcription, maybe point to current status in a status list:
            # text_to = dict(self.transcription_statuses)[str(self.transcriptionstatus)]
            if self.transcriptionstatus in ['published', 'autopublished']:
                text_to = str(self.text)
        return text_to

    #Only publish comment when transcriptionstatus published
    def comment_to_publish(self):
        text_to = None
        if self.text is not None and self.text != '':
            text_to = None # = 'Denna text håller på att skrivas av, av en användare eller är under behandling.'
            if self.transcriptionstatus in ['published', 'autopublished']:
                text_to = str(self.comment)
        return text_to

    class Meta:
        managed = False
        db_table = 'records_media'

class TextChanges(models.Model):
    """
    Track text changes in json within a text field to easier show and find them,
    than using a track history table on the whole field
    """
    recordsmedia = models.ForeignKey(RecordsMedia, db_column='recordsmedia', related_name='textchanges', on_delete=DO_NOTHING, db_index=True, related_query_name='textchanges' )
    action = models.CharField(max_length=8, choices=[('insert', 'insert'), ('update', 'update'), ('delete', 'delete')])
    type = models.CharField(max_length=10, blank=True, null=True, choices=[('desc', 'beskrivning'), ('utter', 'utterance')])
    start = models.DecimalField(max_digits=6, decimal_places=2)
    end = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True)
    change_from = models.TextField(blank=True, null=True)
    change_to = models.TextField(blank=True, null=True)
    changedby = models.ForeignKey(CrowdSourceUsers, db_column='changedby', null=True, blank=True, on_delete=DO_NOTHING,)

    # Track data changes
    createdate = models.DateTimeField(auto_now_add=True, verbose_name="Skapad datum")
    changedate = models.DateTimeField(auto_now=True, blank=True, verbose_name="Ändrad datum")
    createdby = models.ForeignKey(User, db_column='createdby', related_name='records_created+',null=True, blank=True, editable=False, on_delete=DO_NOTHING,
                             verbose_name="Skapad av")
    editedby = models.ForeignKey(User, db_column='editedby', null=True, blank=True, editable=False, on_delete=DO_NOTHING,
                                 related_name='Uppdaterad av+', verbose_name="Uppdaterad av")

    def __str__(self):
        return self.start+': '+self.change_to if self.start and self.change_to else ''

    class Meta:
        managed = False
        db_table = 'text_changes'
        #indexes = [
            #models.Index(fields=['record']),
        #]
        #verbose_name = 'Text changes'
        #verbose_name_plural = LEVEL2 + 'Text changes'


class RecordsMetadata(models.Model):
    record = models.ForeignKey(Records, db_column='record', related_name='metadata', on_delete=DO_NOTHING)
    type = models.CharField(max_length=30, blank=True, null=True, choices=[('sitevision_url', 'Sitevision url'), ('custom', 'Example')])
    value = models.CharField(max_length=30, blank=True, null=True)

    def __str__(self):
        return self.type+': '+self.value if self.type else ''

    class Meta:
        db_table = 'records_metadata'


class RecordsPlaces(models.Model):
    archive_row = models.IntegerField(default=None, blank=True, null=True)
    record = models.ForeignKey(Records, db_column='record', on_delete=DO_NOTHING, related_name='places')
    place = models.ForeignKey(Socken, db_column='place', on_delete=DO_NOTHING)
    type = models.CharField(max_length=20, blank=True, null=True)
    specification = models.CharField(max_length=100, blank=True, null=True, verbose_name="Platsspecificering",help_text="by_anteckn")

    class Meta:
        db_table = 'records_places'

class RecordsCategory(models.Model):
    record = models.ForeignKey(Records, db_column='record', related_name='categories', on_delete=DO_NOTHING)
    category = models.ForeignKey(Categories, db_column='category', on_delete=DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'records_category'


class RecordsLanguage(models.Model):
    """
    Relationstabell mellan records och språk (languages)
    """
    record = models.ForeignKey(Records, db_column='record', on_delete=DO_NOTHING, db_index=True, )
    language = models.ForeignKey(Languages, db_column='language', on_delete=DO_NOTHING, db_index=True)

    class Meta:
        managed = False
        db_table = 'records_language'


# Spara/uppdatera modell JSON i Elasticsearch
def records_post_saved(sender, **kwargs):
    def save_es_model():
        logger.debug('records_post_saved start')
        modelId = kwargs['instance'].id
        # print('print records_post_saved start')

        restUrl = config.restApiRecordUrl+str(modelId)
        logger.info('records_post_saved get json: ' + restUrl)
        document = {}
        modelJson = None
        try:
            modelResponseData = requests.get(restUrl, verify=False)
            modelResponseData.encoding = 'utf-8'
            modelJson = modelResponseData.json()

            document = {
                #'doc': modelJson
            }
            #ES7 Do not add top element to json:
            document = modelJson
        except Exception as e:
            logger.debug("records_post_saved get Exception: %s", modelResponseData)
            logger.debug("records_post_saved get Exception: %s",e)
        logger.info("records_post_saved get: url, data %s %s", restUrl, json.dumps(document).encode('utf-8'))

        # Check if not empty
        if len(document) > 0:
            # Do not use ES-mapping-type for ES >6
            es_mapping_type = ''
            # Old ES-mapping-type:
            #es_mapping_type = 'legend/'
            host = config.host
            protocol = config.protocol
            index_name = config.index_name
            user = None
            password = None
            if hasattr(config, 'user'):
                user = config.user
                password = config.password
            authentication_type_ES8 = False
            if hasattr(config, 'es_version'):
                if (config.es_version == '8'):
                    authentication_type_ES8 = True

            #Use Index API  _doc (Update API _update seems not to work here in ES7):
            #esUrl = config.protocol+(config.user+':'+config.password+'@' if hasattr(config, 'user') else '')+config.host+'/'+config.index_name+'/_doc/'+str(modelId)
            #Authentication not in url from ES8:
            esUrl = protocol + host + '/' + index_name + '/_doc/' + str(modelId)
            # Elasticsearch 6 seems to need headers:
            headers = {'Accept': 'application/json', 'content-type': 'application/json'}
            esResponse = None
            try:
                if authentication_type_ES8 == True and user is not None:
                    esResponse = requests.post(esUrl, data=json.dumps(document).encode('utf-8'), verify=False, headers=headers, auth=HTTPBasicAuth(user, password))
                else:
                    esResponse = requests.post(esUrl, data=json.dumps(document).encode('utf-8'), verify=False,
                                               headers=headers)
            except Exception as e:
                logger.error("records_post_saved post: Exception: %s %s", e, str(document))
                logger.error("records_post_saved post: Exception: %s",e)
            logger.info("records_post_saved post: url, user, authentication_type_ES8, esResponse %s %s %s %s ", esUrl, user, authentication_type_ES8, esResponse)

            if esResponse is not None:
                # Log errors
                if esResponse.status_code != 200:
                    logger.debug("records_post_saved post: Exception %s ", esResponse.text)
                    if esResponse.json() is not None:
                        logger.debug("records_post_saved post: Exception json %s ", esResponse.json())
                # TODO Is put really needed? (Guess it was to do update if insert failed)
                # if 'status' in esResponse.json() and esResponse.json()['status'] == 404:
                if 'status' in esResponse.json() and esResponse.status_code == 404:
                    logger.debug("records_post_saved put url %s ", esUrl)
                    try:
                        esResponse = requests.put(config.protocol + (
                            config.user + ':' + config.password + '@' if hasattr(config,
                                                                                       'user') else '') + config.host + '/' + config.index_name + '/_doc/' + str(
                            modelId), data=json.dumps(modelJson).encode('utf-8'), verify=False, headers=headers)
                    except Exception as e:
                        logger.error("records_post_saved put: Exception: %s", str(document))
                        logger.error("records_post_saved put: Exception: %s", e)
                else:
                    # Normally not an error!?:
                    logger.debug("records_post_saved put: \"'status' in esResponse.json() and esResponse.status_code == 404\" == False." + str(json))
            else:
                logger.error("records_post_saved put: esResponse is None = 'No response from ES'." + str(document))

    # If request variable avoid_timer_before_update_of_search_database set timer to zero
    timer_interval = 5
    if get_avoid_timer_before_update_of_search_database():
        timer_interval = 0

    t = Timer(timer_interval, save_es_model)
    t.start()

post_save.connect(records_post_saved, sender=Records)


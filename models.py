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

from . import config

import logging
logger = logging.getLogger(__name__)

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


class Persons(models.Model):
	id = models.CharField(primary_key=True, max_length=50)
	name = models.CharField(max_length=255)
	gender = models.CharField(max_length=8, choices=[('female', 'Kvinna'), ('male', 'Man'), ('unknown', 'Okänd')])
	birth_year = models.IntegerField(blank=True, null=True)
	address = models.CharField(blank=True, null=True, max_length=255)
	birthplace = models.CharField(blank=True, null=True, max_length=255, verbose_name='Födelseort')
	biography = models.TextField(blank=True, null=True)
	# Pillow is used by models.ImageField: used in Sagenkarta-Rest-API and TradarkAdmin!:
	image = models.ImageField(blank=True, null=True, verbose_name='Bildfil', upload_to='personer')
	import_row_id = models.IntegerField(default=0, blank=False, null=False)
	transcriptioncomment = models.CharField(max_length=255, verbose_name='Kommentarer', default='')
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

class CrowdSourceUsers(models.Model):
	userid = models.CharField(primary_key=True, max_length=150)
	name = models.CharField(max_length=255)
	email = models.EmailField()
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
		('untranscribed', 'Ej transkriberad'),
		('readytotranscribe', 'Publicerad för transkribering'),
		('undertranscription', 'Under transkription'),
		('transcribed', 'Transkriberad'),
		('reviewing', 'Under granskning'),
		('approved', 'Godkänd'),
		('published', 'Publicerad')
	]

	id = models.CharField(max_length=50, primary_key=True)
	title = models.CharField(max_length=300, verbose_name='Titel', blank=True, null=True)
	text = models.TextField(blank=True, null=True)
	year = models.DateField(blank=True, null=True)
	archive = models.CharField(max_length=255, blank=True)
	archive_id = models.CharField(max_length=255, blank=True)
	type = models.CharField(max_length=20)
	record_type = models.CharField(max_length=255, blank=True, null=True)
	archive_page = models.CharField(max_length=20, blank=True, null=True)
	total_pages = models.IntegerField(blank=True, null=True)
	source = models.TextField(blank=True)
	comment = models.TextField(blank=True)
	country = models.CharField(max_length=50)
	transcriptiondate = models.DateTimeField(blank=True, verbose_name="Transkriptionsdatum")
	transcribedby = models.ForeignKey(CrowdSourceUsers, db_column='transcribedby', null=True, blank=True, on_delete=DO_NOTHING)
	transcriptionstatus = models.CharField(max_length=20, blank=False, null=False, default='new', choices=transcription_statuses)
	language = models.CharField(max_length=50)
	copyright_license = models.TextField(blank=True, verbose_name='Datalicens')
	# Track changes:
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

	#Only publish text when transcriptionstatus published
	def text_to_publish(self):
		text_to = None
		if self.text is not None:
			text_to = dict(self.transcription_statuses)[str(self.transcriptionstatus)]
			if self.transcriptionstatus == 'published' or self.record_type == 'one_accession_row':
				text_to = str(self.text)
		return text_to

	class Meta:
		managed = False
		db_table = 'records'


class RecordsPersons(models.Model): #ingredient
	record = models.ForeignKey(Records, db_column='record', related_name='persons', on_delete=DO_NOTHING)
	person = models.ForeignKey(Persons, db_column='person', on_delete=DO_NOTHING)
	relation = models.CharField(max_length=5, blank=True, null=True)

	createdate = models.DateTimeField(auto_now_add=True, verbose_name="Skapad datum")
	changedate = models.DateTimeField(auto_now=True, blank=True, verbose_name="Ändrad datum")

	class Meta:
		db_table = 'records_persons'


class RecordsMedia(models.Model):
	record = models.ForeignKey(Records, db_column='record', related_name='media', on_delete=DO_NOTHING)
	type = models.CharField(max_length=50, blank=True, null=True)
	source = models.CharField(max_length=255, blank=True, null=True)
	title = models.CharField(max_length=255, blank=True, null=True)

	class Meta:
		managed = False
		db_table = 'records_media'


class RecordsMetadata(models.Model):
	record = models.ForeignKey(Records, db_column='record', related_name='metadata', on_delete=DO_NOTHING)
	type = models.CharField(max_length=30, blank=True, null=True, choices=[('sitevision_url', 'Sitevision url'), ('custom', 'Example')])
	value = models.CharField(max_length=30, blank=True, null=True)

	def __str__(self):
		return self.type+': '+self.value if self.type else ''

	class Meta:
		db_table = 'records_metadata'


class RecordsPlaces(models.Model):
	record = models.ForeignKey(Records, db_column='record', on_delete=DO_NOTHING, related_name='places')
	place = models.ForeignKey(Socken, db_column='place', on_delete=DO_NOTHING)
	type = models.CharField(max_length=20, blank=True, null=True)

	class Meta:
		db_table = 'records_places'


class RecordsCategory(models.Model):
	record = models.ForeignKey(Records, db_column='record', related_name='categories', on_delete=DO_NOTHING)
	category = models.ForeignKey(Categories, db_column='category', on_delete=DO_NOTHING)

	class Meta:
		managed = False
		db_table = 'records_category'

# Spara/uppdatera modell JSON i Elasticsearch
def records_post_saved(sender, **kwargs):
	def save_es_model():
		logger.debug('records_post_saved start')
		modelId = kwargs['instance'].id
		print('print records_post_saved start')

		restUrl = config.restApiRecordUrl+str(modelId)
		modelResponseData = requests.get(restUrl, verify=False)
		modelResponseData.encoding = 'utf-8'
		modelJson = modelResponseData.json()

		document = {
			#'doc': modelJson
		}
		#ES7 Do not add top element to json:
		document = modelJson
		logger.debug("records_post_saved url, data %s %s", restUrl, json.dumps(document).encode('utf-8'))

		# Do not use ES-mapping-type for ES >6
		es_mapping_type = ''
		# Old ES-mapping-type:
		#es_mapping_type = 'legend/'
		#Use Index API  _doc (Update API _update seems not to work here in ES7):
		esUrl = config.protocol+(config.user+':'+config.password+'@' if hasattr(config, 'user') else '')+config.host+'/'+config.index_name+'/_doc/'+str(modelId)
		# Elasticsearch 6 seems to need headers:
		headers = {'Accept': 'application/json', 'content-type': 'application/json'}

		try:
			esResponse = requests.post(esUrl, data=json.dumps(document).encode('utf-8'), verify=False, headers=headers)
		except Exception as e:
			logger.debug("records_post_saved post Exception: %s", jsonData)
			print(e)
		logger.debug("records_post_saved post: url, esResponse %s %s", esUrl, esResponse.text)

		if 'status' in esResponse.json() and esResponse.json()['status'] == 404:
			esResponse = requests.put(esUrl, data=json.dumps(modelJson).encode('utf-8'), verify=False)
			logger.debug("records_post_saved put: url, esResponse %s %s", esUrl, esResponse.text)

	t = Timer(5, save_es_model)
	t.start()

post_save.connect(records_post_saved, sender=Records)


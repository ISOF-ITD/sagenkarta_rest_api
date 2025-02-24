from rest_framework import serializers
import json
from .models import Records, Persons, Socken, Harad, RecordsMetadata, Categories, RecordsMedia, RecordsPersons, \
	RecordsPersons, RecordsCategory, RecordsPlaces, Places, RecordsLanguage
from .models_accessionsregister import Accessionsregister_FormLista, Accessionsregister_pers

import logging
logger = logging.getLogger(__name__)

class HaradSerializer(serializers.ModelSerializer):
	class Meta:
		model = Harad

		fields = (
			'name',
			'lan',
			'landskap'
		)

class RecordsPlacesSerializer(serializers.ModelSerializer):
	#  här betyder place egentligen socken (modell socken)
	id = serializers.CharField(source='place.id')
	name = serializers.CharField(source='place.name')
	harad = serializers.CharField(source='place.harad.name')
	harad_id = serializers.IntegerField(source='place.harad.id')
	landskap = serializers.CharField(source='place.harad.landskap')
	county = serializers.CharField(source='place.harad.lan')
	lm_id = serializers.CharField(source='place.lmId')
	fylke = serializers.CharField(source='place.fylke')
	comment = serializers.SerializerMethodField('get_comment')

	location = serializers.SerializerMethodField('get_location_object')

	def get_location_object(self, obj):
		try:
			location = {
				'lat': obj.place.lat,
				'lon': obj.place.lng
			}
		except :
			location = {}

		return location
	
	def get_comment(self, obj):
		place = None
		try:
			if obj is not None:
				if obj.place is not None:
					if obj.place.id is not None:
						if Places.objects.filter(socken = obj.place.id).exists():
							place = Places.objects.filter(
								socken = obj.place.id,
							).first()
		except Exception as e:
			# logger.info as this error can happen if records_places row exists with a socken that does not exist
			logger.info("RecordsPlacesSerializer get_comment %s Exception: %s", str(obj), e)

		if place is not None:
			return place.comment
		else:
			return None

	class Meta:
		model = RecordsPlaces

		fields = (
			'id',
			'name',
			'location',
			'harad',
			'harad_id',
			'landskap',
			'county',
			'lm_id',
			'fylke',
			'type',
			'specification',
			'comment',
		)

class SockenSerializer(serializers.ModelSerializer):
	harad = serializers.CharField(source='harad.name')
	harad_id = serializers.IntegerField(source='harad.id')
	landskap = serializers.CharField(source='harad.landskap')
	county = serializers.CharField(source='harad.lan')
	lm_id = serializers.CharField(source='lmId')
	fylke = serializers.CharField()

	location = serializers.SerializerMethodField('get_location_object')
	comment = serializers.SerializerMethodField('get_comment')

	def get_location_object(self, obj):
		return {
			'lat': obj.lat,
			'lon': obj.lng
		}
	
	def get_comment(self, obj):
		place = Places.objects.filter(
			socken = obj.id,
		).first()
		if place is not None:
			return place.comment
		else:
			return None

	class Meta:
		model = Socken

		fields = (
			'id',
			'name',
			'location',
			'harad',
			'harad_id',
			'landskap',
			'county',
			'lm_id',
			'fylke',
			'comment',
		)

class CategorySerializer(serializers.ModelSerializer):
	category = serializers.CharField(source='id')
	class Meta:
		model = Categories

		fields = (
			'category',
			'name',
			'type'
		)

class PersonsSerializer(serializers.ModelSerializer):
	places = SockenSerializer(many=True, read_only=True);
	# Field image gets full path for some reason: amybe from imagefield or pillow
	# imagepath as is from database:
	imagepath = serializers.SerializerMethodField('image_url')
	source_data = serializers.SerializerMethodField('get_source_data')

	# Field image gets full path for some reason: maybe from imagefield or pillow
	# image path as is from database
	def image_url(self, obj):
		url = None
		if obj.image is not None:
			url = str(obj.image)
		# if obj.image == 'one_accession_row':
		return url

	# Get physical media data from source database (Accessionsregister form table)
	def get_source_data(self, person):
		data = None
		# Only get physical media if archive_row > 0 (0 can be "no value")
		if person.archive_row is not None:
			if person.archive_row > 0:
				qs = Accessionsregister_pers.objects.filter(persid=person.archive_row)
				if len(qs) > 0:
					serializer = AccessionsPersSerializer(instance=qs, many=True)
					data = serializer.data
		return data

	class Meta:
		model = Persons

		fields = (
			'id',
			'name',
			'gender',
			'birth_year',
			'birthplace',
			'address',
			'biography',
			# Default model field named image adds incorrect full path:
			# 'image',
			# Returns relative path as it is in the database:
			'imagepath',
			'places',
			'source_data'
		)

class PersonsMinimalSerializer(serializers.ModelSerializer):
	places = SockenSerializer(many=True, read_only=True);

	class Meta:
		model = Persons

		fields = (
			'id',
			'name',
			'gender',
			'birth_year',
			'places'
		)

class RecordsPersonsSerializer(serializers.ModelSerializer):
	#person = PersonsMinimalSerializer(read_only=True)
	id = serializers.CharField(source='person.id')
	name = serializers.CharField(source='person.name')
	gender = serializers.CharField(source='person.gender')
	birth_year = serializers.CharField(source='person.birth_year')
	birthplace = serializers.CharField(source='person.birthplace')
	home = SockenSerializer(source='person.places', many=True)
	
	class Meta:
		model = RecordsPersons

		fields = (
			'id',
			'name',
			'gender',
			'birth_year',
			'birthplace',
			'home',
			'relation'
		)

class RecordsMetadataSerializer(serializers.ModelSerializer):
	"""
	Serialize RecordsMetadata
	"""

	class Meta:
		model = RecordsMetadata

		fields = (
			'type',
			'value'
		)


class RecordsMediaSerializer(serializers.ModelSerializer):
	"""
	Serialize RecordsMedia

	Title for file type:
	pdf, audio: not transcribed (at all?)
	image: may be transcribed?

	Transcription data follow same state logic as serializer for records
	"""
	text = serializers.CharField(source='text_to_publish')
	comment = serializers.CharField(source='comment_to_publish')
	transcriptionstatus = serializers.SerializerMethodField('public_transcriptionstatus')
	transcribedby = serializers.SerializerMethodField('transcribed_by')
	description = serializers.SerializerMethodField()

	"""
	Only show public transcriptionstatuses
	"""
	def public_transcriptionstatus(self, obj):
		text = obj.transcriptionstatus
		if obj.transcriptionstatus == 'autopublished':
			text = 'published'
		return text

	# transcribed_by is shown if transcriptionstatus is published
	def transcribed_by(self, obj):
		text = None
		# Type image might be transcribed
		if obj.type == 'image' and obj.transcriptionstatus in ['published', 'autopublished']:
			if obj.transcribedby is not None:
				if obj.transcribedby.name is not None:
					text = str(obj.transcribedby.name)
		return text

	class Meta:
		model = RecordsMedia

		fields = (
			'type',
			'source',
			'store',
			'title',
			# Transcription:
			'text',
			'description',
			'comment',
			'transcriptionstatus',
			'transcriptiontype',
			'transcribedby',
			'transcriptiondate',
			'approvedate'
		)

	def get_description(self, obj):
		""" Ensure description is returned as a list of dictionaries instead of a JSON string. """
		try:
			return json.loads(obj.description) if obj.description else []
		except json.JSONDecodeError:
			return []

class RecordsCategorySerializer(serializers.ModelSerializer):
	category = serializers.CharField(source='category.id')
	name = serializers.CharField(source='category.name')
	type = serializers.CharField(source='category.type')
	
	class Meta:
		model = RecordsCategory

		fields = (
			'category',
			'name',
			'type'
		)


class AccessionsFormListaSerializer(serializers.ModelSerializer):
	specified_type = serializers.CharField(source='typtext')
	type = serializers.CharField(source='formgrundtext')
	media = serializers.CharField(source='formdetaljtext')
	count = serializers.CharField(source='omfang_antal')
	count_description = serializers.CharField(source='omfang')
	language = serializers.CharField(source='spr')
	questionnaire = serializers.CharField(source='frgl')

	class Meta:
		model = Accessionsregister_FormLista

		fields = (
			'specified_type',
			'type',
			'media',
			'count',
			'count_description',
			'language',
			'questionnaire',
		)

class AccessionsPersSerializer(serializers.ModelSerializer):
	namn = serializers.CharField()
	fodd = serializers.CharField()
	fodd_ar = serializers.IntegerField()
	kon = serializers.CharField()
	titel = serializers.CharField()
	osaker = serializers.CharField()
	personalia = serializers.CharField()
	roll = serializers.IntegerField()

	class Meta:
		model = Accessionsregister_FormLista

		fields = (
			'namn',
			'fodd',
			'fodd_ar',
			'kon',
			'titel',
			'osaker',
			'personalia',
			'roll',
		)


class RecordsLanguageSerializer(serializers.ModelSerializer):
	"""
	Serialize RecordsLanguages and return suitable Languages fields
	"""
	name = serializers.CharField()
	code = serializers.CharField()

	class Meta:
		model = RecordsLanguage
		fields = ['name', 'code']

class RecordsSerializer(serializers.ModelSerializer):
	#places = SockenSerializer(many=True, read_only=True);
	places = RecordsPlacesSerializer(many=True, read_only=True);
	languages = RecordsLanguageSerializer(many=True, read_only=True);
	metadata = RecordsMetadataSerializer(many=True, read_only=True);
	#taxonomy = CategorySerializer(source='category', read_only=True);
	taxonomy = RecordsCategorySerializer(many=True, read_only=True, source='categories');
	media = RecordsMediaSerializer(many=True, read_only=True);
	materialtype = serializers.CharField(source='type')
	recordtype = serializers.CharField(source='record_type')
	archive = serializers.SerializerMethodField('get_archive_object')
	text = serializers.CharField(source='text_to_publish')
	copyrightlicense = serializers.CharField(source='copyright_license')
	numberofonerecord = serializers.SerializerMethodField('number_of_one_record')
	numberoftranscribedonerecord = serializers.SerializerMethodField('number_of_transcribed_one_record')
	numberoftranscribedpages = serializers.SerializerMethodField('number_of_transcribed_pages')
	numberofpages = serializers.SerializerMethodField('number_of_pages')
	transcribedby = serializers.SerializerMethodField('transcribed_by')
	# Return only public transcription statuses:
	transcriptionstatus = serializers.SerializerMethodField('public_transcriptionstatus')
	# Return persons according to filter:
	persons = serializers.SerializerMethodField('get_persons')
	headwords = serializers.SerializerMethodField('get_headwords')
	contents = serializers.SerializerMethodField('get_contents')
	# OLD: Return all persons:
	#persons = RecordsPersonsSerializer(many=True, read_only=True);

	# physical_media direct from source form table in accessionsregister:
	# Activate WHEN mapping added to index:
	physical_media = serializers.SerializerMethodField('get_physical_media')

	# return headwords only if record_type is one_accession_row, otherwise return None
	def get_headwords(self, obj):
		if obj.record_type == 'one_accession_row':
			return obj.headwords
		else:
			return None
		
	# return contents only if record_type is one_accession_row, otherwise return None
	def get_contents(self, obj):
		if obj.record_type == 'one_accession_row':
			return obj.contents
		else:
			return None

	# Filter to return only published persons
	def get_persons(self, record):
		qs = RecordsPersons.objects.filter(person__transcriptionstatus__in=['published', 'autopublished'], record=record)
		# testing:
		# qs = RecordsPersons.objects.filter(person__gender='female', person__transcriptionstatus='published', record=record)
		serializer = RecordsPersonsSerializer(instance=qs, many=True)
		return serializer.data

	# Get physical media data from source database (Accessionsregister form table)
	def get_physical_media(self, record):
		data = None
		# Only get physical media if archive_row > 0 (0 can be "no value")
		if record.archive_row is not None:
			if record.archive_row > 0:
				qs = Accessionsregister_FormLista.objects.filter(accid=record.archive_row)
				serializer = AccessionsFormListaSerializer(instance=qs, many=True)
				data = serializer.data
		return data

	# number_of_one_record (number of records with type one_record)
	# for records of type one_accession_row with same record.archive_id
	def number_of_one_record(self, obj):
		count = 0
		if obj.record_type == 'one_accession_row':
			# Get only published "tradark" one_record instances for this archive_id
			# that also is imported "directly" from accessionsregistret (record_type='one_record', taxonomy__type='tradark')
			count = Records.objects.filter(
				publishstatus='published',
				record_type='one_record',
				taxonomy__type='tradark',
				id__startswith=obj.id
				).distinct().count()
			# OLD: that also is imported directly from accessionsregistret (id starts with acc)
			# count = Records.objects.filter(record_type='one_record', id__istartswith='acc',archive_id=obj.archive_id).count()
		return count

	# number_of_transcribed_one_record (number of records with type one_record and transcriptionstatus=published)
	# for records of type one_accession_row with same record.archive_id
	def number_of_transcribed_one_record(self, obj):
		# return False
		count = 0
		if obj.record_type == 'one_accession_row':
			# Get only published "tradark" one_record instances for this archive_id
			# that also is imported "directly" from accessionsregistret (record_type='one_record', taxonomy__type='tradark')
			count = Records.objects.filter(
				publishstatus='published',
				transcriptionstatus__in=['published', 'autopublished'] ,
				record_type='one_record',
				taxonomy__type='tradark',id__startswith=obj.id
				).distinct().count()
		return count

	# number_of_transcribed_pages (number transcribed pages in records with type one_record and transcriptionstatus=published)
	# for records of type one_accession_row with same record.archive_id
	def number_of_transcribed_pages(self, obj):
		# return False
		count = 0
		if obj.record_type == 'one_accession_row':
			# Get only published "tradark" one_record instances for this archive_id?
			# that also is imported "directly" from accessionsregistret (record_type='one_record', taxonomy__type='tradark')?
			count = RecordsMedia.objects.filter(
				# Do not exist on RecordsMedia. Needed?
				# publishstatus='published',
				record__record_type = 'one_record',
				# 'transcribed' pages counted as transcribed even not yet approved to show work in progress
				transcriptionstatus__in=['transcribed', 'published', 'autopublished'],
				record__id__startswith=obj.id
				).count()
		return count

	def number_of_pages(self, obj):
		"""
		number_of_pages (number pages in records with type one_record)
		for records of type one_accession_row with same record.archive_id
		return count
		"""
		count = 0
		if obj.record_type == 'one_accession_row':
			# Get only published "tradark" one_record instances for this archive_id
			# that also is imported "directly" from accessionsregistret (record_type='one_record', taxonomy__type='tradark')
			count = RecordsMedia.objects.filter(
				# Do not exist on RecordsMedia. Needed?
				# publishstatus='published',
				# transcriptionstatus__in=['published', 'autopublished'] ,
				record__record_type = 'one_record',
				record__id__startswith=obj.id
				).count()

		return count

	# transcribed_by is shown if transcriptionstatus is published
	def transcribed_by(self, obj):
		text = None
		if obj.record_type == 'one_record' and obj.transcriptionstatus in ['published', 'autopublished']:
			if obj.transcribedby is not None:
				if obj.transcribedby.name is not None:
					text = str(obj.transcribedby.name)
		return text

	def get_archive_object(self, obj):
		source_organisation = {
			0: 'Okänt',
			1: 'Lund',
			2: 'Göteborg',
			3: 'Uppsala',
			4: 'Umeå',
			5: 'Språkrådet',
			100: 'NFS',
			200: 'SLS',
			#100: 'Norsk folkeminnesamling (NFS)',
			#200: 'Svenska litteratursällskapet i Finland (SLS)',
		}

		return {
			'archive_id': obj.archive_id,
			'archive_row': obj.archive_row,
			'archive_id_row': str(obj.archive_id) + '_' + str(obj.archive_row),
			'page': obj.archive_page,
			'total_pages': obj.total_pages,
			'country': obj.country,
			'archive': obj.archive,
			'archive_org': source_organisation[obj.archive_org] if obj.archive_org is not None else None
		}

	"""
	Only show public transcriptionstatuses
	"""
	def public_transcriptionstatus(self, obj):
		text = obj.transcriptionstatus
		if obj.transcriptionstatus == 'autopublished':
			text = 'published'
		return text

	class Meta:
		model = Records

		fields = (
			'id', 
			'title', 
			'text',
			'year',
			'contents',
			'headwords',
			'taxonomy', 
			'archive', 
			'language', # Replaced with language model (languages): To be removed
			'languages',
			'materialtype',
			'numberofonerecord',
			'numberoftranscribedonerecord',
			'numberofpages',
			'numberoftranscribedpages',
			'recordtype',
			'copyrightlicense',
			'source', 
			'comment',
			'places',
			'persons',
			'metadata',
			'media',
			'physical_media',
			'publishstatus',
			'update_status',
			'transcriptionstatus',
			'transcriptiontype',
			# Show only transcriptiondate when publishstatus = published:
			# 'transcriptiondate',
			'transcribedby',
			'transcriptiondate',
			'changedate',
			'approvedate'
		)

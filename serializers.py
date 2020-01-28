from rest_framework import serializers
from .models import Records, Persons, Socken, Harad, RecordsMetadata, Categories, RecordsMedia, RecordsPersons, RecordsPersons, RecordsCategory, RecordsPlaces


class HaradSerializer(serializers.ModelSerializer):
	class Meta:
		model = Harad

		fields = (
			'name',
			'lan',
			'landskap'
		)

class RecordsPlacesSerializer(serializers.ModelSerializer):
	id = serializers.CharField(source='place.id')
	name = serializers.CharField(source='place.name')
	harad = serializers.CharField(source='place.harad.name')
	harad_id = serializers.IntegerField(source='place.harad.id')
	landskap = serializers.CharField(source='place.harad.landskap')
	county = serializers.CharField(source='place.harad.lan')
	lm_id = serializers.CharField(source='place.lmId')
	fylke = serializers.CharField(source='place.fylke')

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
			'type'
		)

class SockenSerializer(serializers.ModelSerializer):
	harad = serializers.CharField(source='harad.name')
	harad_id = serializers.IntegerField(source='harad.id')
	landskap = serializers.CharField(source='harad.landskap')
	county = serializers.CharField(source='harad.lan')
	lm_id = serializers.CharField(source='lmId')
	fylke = serializers.CharField()

	location = serializers.SerializerMethodField('get_location_object')

	def get_location_object(self, obj):
		return {
			'lat': obj.lat,
			'lon': obj.lng
		}

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
			'fylke'
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

	class Meta:
		model = Persons

		fields = (
			'id',
			'name',
			'gender',
			'birth_year',
			'address',
			'biography',
			'image',
			'places'
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
	home = SockenSerializer(source='person.places', many=True)
	
	class Meta:
		model = RecordsPersons

		fields = (
			'id',
			'name',
			'gender',
			'birth_year',
			'home',
			'relation'
		)

class RecordsMetadataSerializer(serializers.ModelSerializer):
	class Meta:
		model = RecordsMetadata

		fields = (
			'type',
			'value'
		)

class RecordsMediaSerializer(serializers.ModelSerializer):
	class Meta:
		model = RecordsMedia

		fields = (
			'type',
			'source',
			'title'
		)

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

class RecordsSerializer(serializers.ModelSerializer):
	persons = RecordsPersonsSerializer(many=True, read_only=True);
	#places = SockenSerializer(many=True, read_only=True);
	places = RecordsPlacesSerializer(many=True, read_only=True);
	metadata = RecordsMetadataSerializer(many=True, read_only=True);
	#taxonomy = CategorySerializer(source='category', read_only=True);
	taxonomy = RecordsCategorySerializer(many=True, read_only=True, source='categories');
	media = RecordsMediaSerializer(many=True, read_only=True);
	materialtype = serializers.CharField(source='type')
	archive = serializers.SerializerMethodField('get_archive_object')

	def get_archive_object(self, obj):
		return {
			'archive_id': obj.archive_id,
			'total_pages': obj.total_pages,
			'country': obj.country,
			'archive': obj.archive
		}

	class Meta:
		model = Records

		fields = (
			'id', 
			'title', 
			'text', 
			'year', 
			'taxonomy', 
			'archive', 
			'language',
			'materialtype', 
			'source', 
			'comment',
			'places',
			'persons',
			'metadata',
			'media',
			'transcriptionstatus',
			'transcriptiondate'
		)

from rest_framework import serializers
from .models import Records, Persons, Socken, Harad, RecordsMetadata, Category, RecordsMedia, RecordsPersons, RecordsPersons


class HaradSerializer(serializers.ModelSerializer):
	class Meta:
		model = Harad

		fields = (
			'name',
			'lan',
			'landskap'
		)

class SockenSerializer(serializers.ModelSerializer):
	harad = serializers.CharField(source='harad.name')
	harad_id = serializers.IntegerField(source='harad.id')
	landskap = serializers.CharField(source='harad.landskap')
	county = serializers.CharField(source='harad.lan')
	lm_id = serializers.CharField(source='lmId')

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
			'lm_id'
		)

class CategorySerializer(serializers.ModelSerializer):
	category = serializers.CharField(source='id')
	class Meta:
		model = Category

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

class InformantsSerializer(PersonsSerializer):
	places = SockenSerializer(many=True, read_only=True);

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
			'source'
		)

class RecordsSerializer(serializers.ModelSerializer):
	persons = RecordsPersonsSerializer(many=True, read_only=True);
	places = SockenSerializer(many=True, read_only=True);
	metadata = RecordsMetadataSerializer(many=True, read_only=True);
	taxonomy = CategorySerializer(source='category', read_only=True);
	media = RecordsMediaSerializer(many=True, read_only=True);
	materialtype = serializers.CharField(source='type')
	archive = serializers.SerializerMethodField('get_archive_object')

	def get_archive_object(self, obj):
		return {
			'archive_id': obj.archive_id,
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
			'materialtype', 
			'source', 
			'comment',
			'places',
			'persons',
			'metadata',
			'media'
		)

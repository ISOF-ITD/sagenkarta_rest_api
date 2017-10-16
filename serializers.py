from rest_framework import serializers
from .models import Records, Persons, Socken, Harad, RecordsMetadata, Category, Media, RecordsPersons, RecordsPersons


class HaradSerializer(serializers.ModelSerializer):
	class Meta:
		model = Harad

		fields = (
			'name',
			'lan',
			'landskap'
		)

class SockenSerializer(serializers.ModelSerializer):
	harad = HaradSerializer(read_only=True)

	class Meta:
		model = Socken

		fields = (
			'id',
			'name',
			'lat',
			'lng',
			'harad'
		)

class MediaSerializer(serializers.ModelSerializer):
	class Meta:
		model = Media

		fields = (
			'source',
			'type'
		)

class CategorySerializer(serializers.ModelSerializer):
	class Meta:
		model = Category

		fields = (
			'id',
			'name'
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

class InformantsSerializer(PersonsSerializer):
	places = SockenSerializer(many=True, read_only=True);

class RecordsPersonsSerializer(serializers.ModelSerializer):
	person = PersonsSerializer(read_only=True)
	
	class Meta:
		model = RecordsPersons

		fields = (
			'relation',
			'person'
		)

class RecordsMetadataSerializer(serializers.ModelSerializer):
	class Meta:
		model = RecordsMetadata

		fields = (
			'type',
			'value'
		)

class SingleRecordSerializer(serializers.ModelSerializer):
	#records_persons = PersonsSerializer(many=True, read_only=True);
	persons = RecordsPersonsSerializer(many=True, read_only=True);
	places = SockenSerializer(many=True, read_only=True);
	metadata = RecordsMetadataSerializer(many=True, read_only=True);
	category = CategorySerializer(read_only=True);
	media = MediaSerializer(many=True, read_only=True);

	class Meta:
		model = Records

		fields = (
			'id', 
			'title', 
			'text', 
			'year', 
			'category', 
			'archive', 
			'archive_id', 
			'type', 
			'archive_page', 
			'source', 
			'comment',
			'places',
			'persons',
			'metadata',
			'media'
		)

class RecordsSerializer(serializers.ModelSerializer):
	places = SockenSerializer(many=True, read_only=True);
	category = CategorySerializer(read_only=True);

	class Meta:
		model = Records

		fields = (
			'id', 
			'title', 
			'year', 
			'category', 
			'archive', 
			'archive_id', 
			'type', 
			'archive_page', 
			'source', 
			'places',
			'metadata'
		)


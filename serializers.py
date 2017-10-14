from rest_framework import serializers
from .models import Records, Persons, Socken, Harad, RecordsMetadata, Category


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

class RecordsMetadataSerializer(serializers.ModelSerializer):
	class Meta:
		model = RecordsMetadata

		fields = (
			'type',
			'value'
		)

class SingleRecordSerializer(serializers.ModelSerializer):
	persons = PersonsSerializer(many=True, read_only=True);
	places = SockenSerializer(many=True, read_only=True);
	metadata = RecordsMetadataSerializer(many=True, read_only=True);
	category = CategorySerializer(read_only=True);

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
			'metadata'
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


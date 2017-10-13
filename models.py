# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey has `on_delete` set to the desired behavior.
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from __future__ import unicode_literals
from django.utils.safestring import mark_safe
from string import Template

from django.db import models


class Category(models.Model):
	id = models.CharField(primary_key=True,max_length=255)
	name = models.CharField(max_length=100, blank=False, null=False)

	class Meta:
		db_table = 'categories_v2'


class Harad(models.Model):
	name = models.CharField(max_length=50, blank=True, null=True)
	lan = models.CharField(max_length=30, blank=True, null=True)
	landskap = models.CharField(max_length=14, blank=True, null=True)
	country = models.CharField(unique=True, max_length=100, blank=True, null=True)

	class Meta:
		db_table = 'harad'


class Socken(models.Model):
	name = models.CharField(max_length=200)
	harad = models.ForeignKey(Harad, models.DO_NOTHING, db_column='harad')
	lat = models.FloatField()
	lng = models.FloatField()

	socken_records = models.ManyToManyField(
		'Records', 
		through = 'RecordsPlaces'
	)

	class Meta:
		db_table = 'socken'


class Persons(models.Model):
	id = models.CharField(primary_key=True,max_length=255)
	name = models.CharField(max_length=255)
	gender = models.CharField(max_length=2, choices=[('k', 'Kvinna'), ('m', 'Man')])
	birth_year = models.IntegerField(blank=True, null=True)
	address = models.CharField(max_length=255)
	biography = models.TextField()
	image = models.ImageField(verbose_name='Bildfil')
	changedate = models.DateTimeField()
	places = models.ManyToManyField(
		Socken, 
		through='PersonsPlaces', 
		through_fields = ('person', 'place')
	)

	class Meta:
		db_table = 'persons'


class PersonsPlaces(models.Model):
	person = models.ForeignKey(Persons, db_column='person')
	place = models.ForeignKey(Socken, db_column='place')
	relation = models.CharField(max_length=5, blank=True, null=True)

	class Meta:
		db_table = 'persons_places'


class Records(models.Model):
	id = models.IntegerField(primary_key=True)
	title = models.CharField(max_length=255)
	text = models.TextField()
	year = models.IntegerField(blank=True, null=True)
	#category = models.CharField(max_length=20, blank=True)
	category = models.ForeignKey(Category, db_column='category')
	archive = models.CharField(max_length=255, blank=True)
	archive_id = models.CharField(max_length=255, blank=True)
	type = models.CharField(max_length=20)
	archive_page = models.CharField(max_length=20, blank=True, null=True)
	source = models.TextField(blank=True)
	comment = models.TextField(blank=True)
	country = models.TextField()
	changedate = models.DateTimeField()
	persons = models.ManyToManyField(
		Persons, 
		through='RecordsPersons',
		related_name='persons'
	)
	places = models.ManyToManyField(
		Socken, 
		through = 'RecordsPlaces'
	)

	class Meta:
		db_table = 'records'


class RecordsMetadata(models.Model):
    record = models.ForeignKey(Records, db_column='record', related_name='metadata')
    type = models.CharField(max_length=30, blank=True, null=True, choices=[('sitevision_url', 'Sitevision url'), ('custom', 'Example')])
    value = models.CharField(max_length=30, blank=True, null=True)

    def __str__(self):
        return self.type+': '+self.value if self.type else ''

    class Meta:
        managed = False
        db_table = 'records_metadata'


class RecordsPlaces(models.Model):
	record = models.ForeignKey(Records, db_column='record')
	place = models.ForeignKey(Socken, db_column='place')

	class Meta:
		db_table = 'records_places'


class RecordsPersons(models.Model):
	record = models.ForeignKey(Records, db_column='record')
	person = models.ForeignKey(Persons, db_column='person')
	relation = models.CharField(max_length=5, blank=True, null=True, choices=[('i', 'Informant'), ('c', 'Uppteckare')])

	class Meta:
		db_table = 'records_persons'
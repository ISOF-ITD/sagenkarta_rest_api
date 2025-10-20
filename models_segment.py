from django.contrib.auth.models import User
from django.db.models.deletion import *
from .models import Records, Categories, Persons, RecordsMedia

import logging
logger = logging.getLogger(__name__)

# Invisible space used to change default django admin alphabetic order of models
LEVEL1 = u"\u200B"
LEVEL2 = u"\u200B" + u"\u200B"
LEVEL3 = u"\u200B" + u"\u200B" + u"\u200B"
LEVEL4 = u"\u200B" + u"\u200B" + u"\u200B" + u"\u200B"

"""
Module for:
Models for handling segments of records
"""
class Segments(models.Model):
    """
    Segments within a record

    Data definition language is managed
    """
    record = models.ForeignKey(Records, db_column='record', related_name='segment', on_delete=DO_NOTHING, db_index=True,)
    start = models.ForeignKey(RecordsMedia, db_column='start', on_delete=DO_NOTHING, db_index=True,)

    # Track data changes
    createdate = models.DateTimeField(auto_now_add=True, verbose_name="Skapad datum")
    changedate = models.DateTimeField(auto_now=True, blank=True, verbose_name="Ändrad datum")
    createdby = models.ForeignKey(User, db_column='createdby', null=True, blank=True, editable=False, on_delete=DO_NOTHING,
                             verbose_name="Skapad av")
    editedby = models.ForeignKey(User, db_column='editedby', null=True, blank=True, editable=False, on_delete=DO_NOTHING,
                                 related_name='Uppdaterad av+', verbose_name="Uppdaterad av")

    class Meta:
        managed = True
        db_table = 'segments'
        verbose_name = 'Segment'
        verbose_name_plural = LEVEL2 + 'Segment'
        indexes = [
            models.Index(fields=['record']),
            models.Index(fields=['start']),
        ]

class SegmentsCategory(models.Model):
    """
    Categories related to segments within a record

    Data definition language is managed
    """
    segment = models.ForeignKey(Segments, db_column='segment', on_delete=DO_NOTHING, db_index=True,)
    category = models.ForeignKey(Categories, db_column='category', on_delete=DO_NOTHING, db_index=True,)

    # Track data changes
    createdate = models.DateTimeField(auto_now_add=True, verbose_name="Skapad datum")
    changedate = models.DateTimeField(auto_now=True, blank=True, verbose_name="Ändrad datum")
    createdby = models.ForeignKey(User, db_column='createdby', null=True, blank=True, editable=False, on_delete=DO_NOTHING,
                             verbose_name="Skapad av")
    editedby = models.ForeignKey(User, db_column='editedby', null=True, blank=True, editable=False, on_delete=DO_NOTHING,
                                 related_name='Uppdaterad av+', verbose_name="Uppdaterad av")

    class Meta:
        managed = True
        db_table = 'segments_category'
        verbose_name = 'Segment kategori'
        verbose_name_plural = LEVEL2 + 'Segment katergorier'
        indexes = [
            models.Index(fields=['segment']),
            models.Index(fields=['category']),
        ]

class SegmentsPersons(models.Model):
    """
    Categories related to segments within a record

    Data definition language is managed
    """
    segment = models.ForeignKey(Segments, db_column='segment', on_delete=CASCADE, db_index=True,)
    person = models.ForeignKey(Persons, db_column='person', on_delete=CASCADE, db_index=True,)

    # Track data changes
    createdate = models.DateTimeField(auto_now_add=True, verbose_name="Skapad datum")
    changedate = models.DateTimeField(auto_now=True, blank=True, verbose_name="Ändrad datum")
    createdby = models.ForeignKey(User, db_column='createdby', null=True, blank=True, editable=False, on_delete=DO_NOTHING,
                             verbose_name="Skapad av")
    editedby = models.ForeignKey(User, db_column='editedby', null=True, blank=True, editable=False, on_delete=DO_NOTHING,
                                 related_name='Uppdaterad av+', verbose_name="Uppdaterad av")

    class Meta:
        managed = True
        db_table = 'segments_persons'
        verbose_name = 'Segment person'
        verbose_name_plural = LEVEL2 + 'Segment personer'
        indexes = [
            models.Index(fields=['segment']),
            models.Index(fields=['person']),
        ]


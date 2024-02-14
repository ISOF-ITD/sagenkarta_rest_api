# File copied from:
# TradarkAdmin/TradarkAdmin/models_accessionsregister.py
# cp dev/server/TradarkAdmin/TradarkAdmin/TradarkAdmin/models_accessionsregister.py dev/server/folkeservice/sagenkarta_rest_api/
# All models not needed are removed
#
from __future__ import unicode_literals
from django.db import models
# Not used at the moment, but needed for django migrations to work on older migrations:
#from tinymce.models import HTMLField

import logging
logger = logging.getLogger(__name__)

import urllib3
urllib3.disable_warnings()

# Invisible space used to change default django admin alphabetic order of models
LEVEL1 = u"\u200B"
LEVEL2 = u"\u200B" + u"\u200B"
LEVEL3 = u"\u200B" + u"\u200B" + u"\u200B"
LEVEL4 = u"\u200B" + u"\u200B" + u"\u200B" + u"\u200B"

# Not used at the moment, but needed for django migrations to work on older migrations:
# you need to import HTMLField: from tinymce.models import HTMLField
#class MediumHtmlField(HTMLField):
#     def db_type(self, connection):
#         return 'MEDIUMTEXT'

class Accessionsregister_FormLista(models.Model):
    formid = models.IntegerField(default=None,verbose_name="FormId")
    accid = models.IntegerField(verbose_name="AccId")

    form = models.TextField(blank=True, null=True, verbose_name="Form")

    omfang = models.TextField(blank=True, null=True, verbose_name="Omfång")
    omfang_antal = models.IntegerField(blank=True, null=True, verbose_name="Omfång antal")
    typ = models.TextField(blank=True, null=True, verbose_name="Typ")
    frgl = models.TextField(blank=True, null=True, verbose_name="Frgl")
    spr = models.TextField(blank=True, null=True, verbose_name="Spr")
    org = models.IntegerField(verbose_name="!Org")
    cd_nr = models.TextField(blank=True, null=True, verbose_name="CD_nr")
    fonoanvandarcd = models.TextField(blank=True, null=True, verbose_name="FonoAnvändarCD")
    fonoarkivcd = models.TextField(blank=True, null=True, verbose_name="FonoArkivCD")
    fonoavlyssnad = models.TextField(blank=True, null=True, verbose_name="FonoAvlyssnad")
    fonobandsort = models.TextField(blank=True, null=True, verbose_name="FonoBandsort")
    fonobearbkopia = models.TextField(blank=True, null=True, verbose_name="FonoBearbKopia")
    fonoexabyteband = models.TextField(blank=True, null=True, verbose_name="FonoExabyteband")
    fonohastighet = models.TextField(blank=True, null=True, verbose_name="FonoHastighet")
    fonoinspelningstid = models.IntegerField(blank=True, null=True, verbose_name="FonoInspelningstid")
    fonokanal = models.TextField(blank=True, null=True, verbose_name="FonoKanal")
    fonosida = models.TextField(blank=True, null=True, verbose_name="FonoSida")
    fonostorlek = models.TextField(blank=True, null=True, verbose_name="FonoStorlek")
    fonoutskrift = models.TextField(blank=True, null=True, verbose_name="FonoUtskrift")
    digdat = models.TextField(blank=True, null=True, verbose_name="digdat")
    typ2 =  models.TextField(blank=True, null=True, verbose_name="!Typ")
    typtext =  models.TextField(blank=True, null=True, verbose_name="typtext")
    formgrund = models.TextField(blank=True, null=True, verbose_name="!FormGrund")
    formgrundtext = models.TextField(blank=True, null=True, verbose_name="FormGrundText")
    formdetalj = models.TextField(blank=True, null=True, verbose_name="!FormDetalj")
    formdetaljtext = models.TextField(blank=True, null=True, verbose_name="FormDetaljText")
    disc = models.TextField(blank=True, null=True, verbose_name="Disc")
    klipptidning = models.TextField(blank=True, null=True, verbose_name="KlippTidning")

    import_batch = models.IntegerField( blank=True, null=True, verbose_name="Importbatch")

    # Track changes in source database
    postskapadtid = models.DateTimeField(blank=True, null=True, verbose_name="PostSkapadTid")
    postandradtid = models.DateTimeField(blank=True, null=True, verbose_name="PostÄndradTid")
    postandradav = models.IntegerField(blank=True, null=True, verbose_name="!PostÄndradAv")
    postkapadav = models.IntegerField(blank=True, null=True, verbose_name="!PostSkapadAv")

    class Meta:
        managed = False
        db_table = 'accessionsregister_formlista_vy'
        verbose_name_plural = LEVEL1 + 'accessionsregister_formlista_vy'

class Accessionsregister_pers(models.Model):
    id = models.IntegerField(primary_key=True)
    # Might be primary key i origin:
    # persid = models.IntegerField(primary_key=True, verbose_name="PersID")
    persid = models.IntegerField(verbose_name="PersID")

    # batch_id = models.AutoField(primary_key=True, null=False, editable=False)
    namn = models.TextField(blank=True, null=True,verbose_name="Namn")
    fodd = models.TextField(blank=True, null=True,verbose_name="Född")
    # fodd_ar: extra column in view returning only a year. NOT a column in main table!
    fodd_ar = models.TextField(blank=True, null=True,verbose_name="Född år")
    osaker = models.TextField(blank=True, null=True, verbose_name="Osäker uppgift med ev. förklaring")
    titel = models.TextField(blank=True, null=True, verbose_name="Titel")
    kon = models.TextField(blank=True, null=True, verbose_name="Kön")
    personalia = models.TextField(blank=True, null=True, verbose_name="Personalia")

    # Might be foreign keys:
    org = models.IntegerField(verbose_name="!Org")
    acc = models.IntegerField(verbose_name="!Acc")
    roll = models.IntegerField(verbose_name="!Roll")

    # Should be link (and text?) but column type Binär. Might be empty?
    personalia_dokument = models.TextField(blank=True, null=True,verbose_name="Personalia dokument")
    fotografi = models.TextField(blank=True, null=True,verbose_name="Fotografi")

    import_batch = models.IntegerField( blank=True, null=True, verbose_name="Importbatch")

    # Track data changes
    postskapad = models.DateTimeField(auto_now_add=True, verbose_name="PostSkapad")
    postandrad = models.DateTimeField(auto_now=True, blank=True, verbose_name="PostÄndrad")
    anvandradav = models.IntegerField(blank=True, null=True, verbose_name="!AnvÄndradAv")
    anvskapadav = models.IntegerField(blank=True, null=True, verbose_name="!AnvSkapadAv")

    class Meta:
        managed = False
        db_table = 'accessionsregister_pers_vy'
        verbose_name_plural = LEVEL1 + 'accessionsregister_pers_vy'

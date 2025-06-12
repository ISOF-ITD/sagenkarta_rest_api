import logging
from django.db.models import Q
from rest_framework import viewsets, permissions
from sagenkarta_rest_api.models import Records, Categories
from sagenkarta_rest_api.serializers import RecordsSerializer, CategorySerializer

logger = logging.getLogger(__name__)


class RecordsViewSet(viewsets.ReadOnlyModelViewSet):
    """
    /api/records/ – heavy-duty filter endpoint.

    Examples:
    - /api/records/?transcriptiondate_after=2024-01-01
    - /api/records/?transcriptionstatus=published,autopublished&transcriptiondate_after=2024-01-01

    Accepted query parameters for `/api/records/`
    ---------------------------------------------
    * `country` (str, case-insensitive)
    * `archive_org` (str, case-insensitive)
    * `only_categories` (bool flag)
    * `category` (comma-separated list, case-insensitive)
    * `record_ids` (comma-separated list)
    * `type`, `recordtype`, `transcriptionstatus`, `import_batch`,
      `publishstatus`, `update_status` (each: comma-separated list)
    * `transcriptiondate_after` (YYYY-MM-DD)
    * `person`, `place`, `gender`, `person_relation`
    * `search` + `search_field` (`record` | `person` | `place`)

    If you add / rename parameters, also update the docs above
    """
    serializer_class = RecordsSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        qs = Records.objects.all()
        p  = self.request.query_params

        # simple scalar & list params
        mapping = {
            'country':            ('country__iexact', lambda v: v),
            'archive_org':        ('archive_org__iexact', lambda v: v),
            'record_ids':         ('id__in', lambda v: [x.strip().upper() for x in v.split(',')]),
            'type':               ('type__in', lambda v: v.split(',')),
            'recordtype':         ('record_type__in', lambda v: v.split(',')),
            'transcriptionstatus':('transcriptionstatus__in', lambda v: v.split(',')),
            'import_batch':       ('import_batch__in', lambda v: v.split(',')),
            'publishstatus':      ('publishstatus__in', lambda v: v.split(',')),
            'update_status':      ('update_status__in', lambda v: v.split(',')),
            'transcriptiondate_after': ('transcriptiondate__gte', str),
            'category':           ('categories__id__in', lambda v: [c.strip().upper() for c in v.split(',')]),
        }

        filters = {dj_key: transform(pv)
                   for pv_key, (dj_key, transform) in mapping.items()
                   if (pv := p.get(pv_key)) is not None}

        # special-case filters
        if p.get('only_categories'):
            qs = qs.exclude(category='')

        if person := p.get('person'):
            filters['records_persons__id'] = person

        if place := p.get('place'):
            filters['places__id'] = place

        if gender := p.get('gender'):
            if rel := p.get('person_relation'):
                qs = qs.filter(
                    Q(records_persons__gender=gender.lower()) &
                    Q(records_persons__recordspersons__relation=rel.lower())
                )
            else:
                filters['records_persons__gender'] = gender.lower()

        # free-text search
        if search := p.get('search'):
            field = p.get('search_field', 'record').lower()
            s = search.lower()
            if field == 'record':
                qs = qs.filter(Q(title__icontains=s) | Q(text__icontains=s))
            elif field == 'person':
                filters['records_persons__name__icontains'] = s
            elif field == 'place':
                qs = qs.filter(
                    Q(places__name__icontains=s) |
                    Q(places__harad__name__icontains=s) |
                    Q(places__socken__name__icontains=s) |
                    Q(places__harad__lan__icontains=s) |
                    Q(places__harad__landskap__icontains=s)
                )

        qs = qs.filter(**filters).distinct()
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug("RecordsViewSet raw SQL:\n%s", qs.query)
        return qs

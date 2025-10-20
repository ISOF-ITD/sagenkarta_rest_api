# serializers.py
from rest_framework import serializers
from django.contrib.auth.models import User
from .models_segment import (
    Records, Categories, Persons, RecordsMedia,
    Segments, SegmentsCategory, SegmentsPersons
)

# --- Segment-related serializers (FKs -> IDs only, no audit fields) ---

class SegmentsSerializer(serializers.ModelSerializer):
    # record = serializers.PrimaryKeyRelatedField(read_only=True)
    start  = serializers.PrimaryKeyRelatedField(read_only=True)

    # Lists of pure FK ids for the relations below:
    category_ids = serializers.SerializerMethodField()
    person_ids   = serializers.SerializerMethodField()

    class Meta:
        model = Segments
        fields = ("id", "record", "start", "category_ids", "person_ids")

    def get_category_ids(self, obj):
        # Default reverse name since no related_name=... on the FK:
        # SegmentsCategory -> segmentscategory_set
        return list(
            obj.segmentscategory_set.values_list("category_id", flat=True)
        )

    def get_person_ids(self, obj):
        # Default reverse name: SegmentsPersons -> segmentspersons_set
        return list(
            obj.segmentspersons_set.values_list("person_id", flat=True)
        )


class SegmentsCategorySerializer(serializers.ModelSerializer):
    segment = serializers.PrimaryKeyRelatedField(read_only=True)
    category = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = SegmentsCategory
        fields = ("id", "segment", "category")  # no audit fields


class SegmentsPersonsSerializer(serializers.ModelSerializer):
    segment = serializers.PrimaryKeyRelatedField(read_only=True)
    person = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = SegmentsPersons
        fields = ("id", "segment", "person")  # no audit fields

# --- End of segment-related serializers ---

from django.db import transaction
from django.utils.timezone import now as Now
from django.utils.html import strip_tags
from rest_framework import serializers, viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from sagenkarta_rest_api.models import Records, RecordsMedia, CrowdSourceUsers, TextChanges
import json
import logging
from rest_framework.authentication import SessionAuthentication, BasicAuthentication

class CsrfExemptSessionAuthentication(SessionAuthentication):

    def enforce_csrf(self, request):
        return  # To not perform the csrf check previously happening

logger = logging.getLogger(__name__)

def time_to_seconds(time_str):
    """Convert a string time mm:ss to float seconds with two decimal places."""
    if isinstance(time_str, str) and '.' in time_str:
        # If already float-like (e.g. "10.3"), just parse it
        return float(time_str)
    else:
        minutes, seconds = map(float, time_str.split(':'))
        return round(minutes * 60 + seconds, 2)

def seconds_to_time(seconds):
    """Convert seconds (float) back to mm:ss format with 2 decimals."""
    minutes = int(seconds // 60)
    seconds = seconds % 60
    return f"{minutes}:{seconds:05.2f}"

class TermSerializer(serializers.Serializer):
    term = serializers.CharField()
    termid = serializers.CharField()

class DescribeUpdateSerializer(serializers.Serializer):
    """
    Serialize describe request parameters (json)
    """
    recordid = serializers.CharField()
    file = serializers.CharField()
    transcribesession = serializers.CharField()
    from_email = serializers.EmailField(required=False, allow_blank=True)
    from_name = serializers.CharField(required=False)
    speaker = serializers.CharField(required=False)
    start = serializers.CharField(required=False)
    start_from = serializers.CharField(required=False, allow_null=True)
    # Start id is order number within array items with the same start/start_from:
    start_id = serializers.IntegerField(required=False, allow_null=True)
    start_to = serializers.CharField(required=False, allow_null=True)
    change_from = serializers.CharField(required=False, allow_blank=True)
    change_to = serializers.CharField(required=False, allow_blank=True)
    terms = TermSerializer(required=False, many=True)

    def validate_terms(self, value):
        """Ensure that all 'term' values are unique."""
        term_values = [term["term"].lower() for term in value]
        if len(term_values) != len(set(term_values)):
            raise serializers.ValidationError("Terms must be case-insensitively unique.")
        return value

class DescribeStartSerializer(serializers.Serializer):
    """
    Serialize describe start request parameters (json)
    """
    recordid = serializers.CharField()

class DescribeViewSet(viewsets.ViewSet):
    """
    Handle descriptions for files in RecordsMedia.
    Provides endpoints to 'start' (lock) a transcription session,
    'change' (update/insert) description, and 'delete' single description.
    """

    authentication_classes = (
        CsrfExemptSessionAuthentication, BasicAuthentication
    )

    def get_permissions(self):
        permission_classes = [permissions.AllowAny]
        return [permission() for permission in permission_classes]

    @action(detail=False, methods=['post'], url_path='start')
    def describestart(self, request):
        """
        API endpoint for starting a transcription session (mark record as 'undertranscription').
        """
        response_status = 'false'
        serializer = DescribeStartSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        record_id = data.get("recordid")

        try:
            record = Records.objects.get(id=record_id)
            if record is not None:
                with transaction.atomic():
                    if record.transcriptionstatus == 'readytotranscribe':
                        record.transcriptionstatus = 'undertranscription'
                        record.transcriptiondate = Now()
                        record.save()

                        # read again
                        record.refresh_from_db()
                        response_status = 'true'

                        # Provide transcribesession info in the response
                        data['transcribesession'] = str(
                            record.transcriptiondate.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
                        )
                        logger.debug("TranscribeStartViewSet data %s", data)
                    else:
                        json_response = {'success': response_status, 'data': data}
                        return Response(json_response, status=status.HTTP_400_BAD_REQUEST)

            json_response = {'success': response_status, 'data': data}
            return Response(json_response, status=status.HTTP_200_OK)

        except Records.DoesNotExist:
            return Response({"error": "Record not found."}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=['post'], url_path='change')
    def change(self, request):
        """
        API endpoint for creating/updating text descriptions for the selected media.
        """
        serializer = DescribeUpdateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        record_id = data.get("recordid")
        file = data.get("file")
        transcribesession = data.get("transcribesession")
        start_time = data.get("start")
        start_from = data.get("start_from")
        start_to = data.get("start_to")
        change_from = data.get("change_from", "")
        change_to = data.get("change_to", "")
        terms = data.get("terms", None)
        username = data.get("from_name", "Anonymous")
        email = data.get("from_email", "")

        # Convert to float seconds if present
        start_time_sec = time_to_seconds(start_time) if start_time else None
        start_from_sec = time_to_seconds(start_from) if start_from else None
        start_to_sec = time_to_seconds(start_to) if start_to else None

        try:
            record = Records.objects.get(id=record_id)
            if record.transcriptionstatus == 'undertranscription':
                # Example: filter the record's media that is 'readytotranscribe'
                records_media = RecordsMedia.objects.filter(
                    record=record_id,
                    source=file,
                    transcriptionstatus='readytotranscribe'
                ).first()
                if records_media is not None:
                    existing_text = json.loads(records_media.description or "[]")

                    # Check if transcribesession matches the locked record
                    if str(record.transcriptiondate.strftime('%Y-%m-%d %H:%M:%S')) in transcribesession:
                        action = None
                        message = ''

                        # ----- INSERT / ADD -----
                        if start_time is not None:
                            # Ensure unique start time
                            if any(entry['start'] == start_time for entry in existing_text):
                                return Response({"error": "Start time must be unique."}, status=status.HTTP_400_BAD_REQUEST)

                            time_exists = False
                            for entry in existing_text:
                                if entry["start"] == start_from:
                                    time_exists = True
                                    message = 'start_from exists'
                            if not time_exists:
                                # Build new entry
                                new_entry = {}
                                if change_to:
                                    new_entry["text"] = change_to
                                if terms is not None:
                                    new_entry["terms"] = terms
                                new_entry["start"] = start_time

                                action = 'insert'
                                start_time_to_log = start_time_sec
                                existing_text.append(new_entry)

                        # ----- UPDATE TEXT -----
                        else:
                            if start_from and change_from is not None and change_to is not None:
                                for entry in existing_text:
                                    if entry["start"] == start_from:
                                        action = 'update'
                                        entry["text"] = change_to
                                        start_time_to_log = start_from_sec
                                if action is None:
                                    message = 'start_to does not exist'

                            # ----- UPDATE TIME -----
                            if start_from and start_to:
                                # Check if the new start_to is already used by other entries
                                if any(entry['start'] == start_to for entry in existing_text if
                                       entry['start'] != start_from):
                                    return Response({"error": "Start time must be unique."},
                                                    status=status.HTTP_400_BAD_REQUEST)
                                for entry in existing_text:
                                    if entry["start"] == start_from:
                                        entry["start"] = start_to
                                        action = 'update'
                                        start_time_to_log = start_to_sec
                                if action is None:
                                    message = 'start_from does not exist'

                        # Save updated data
                        if action is not None:
                            existing_text = sorted(
                                existing_text,
                                key=lambda x: time_to_seconds(x['start'])
                            )

                            with transaction.atomic():
                                records_media.description = json.dumps(existing_text, ensure_ascii=False)
                                records_media.save()

                                # Log the change
                                clean_name = strip_tags(username).replace(';', '')
                                user, _ = CrowdSourceUsers.objects.get_or_create(
                                    userid=clean_name,
                                    defaults={"name": clean_name, "email": email}
                                )
                                TextChanges.objects.create(
                                    recordsmedia=records_media,
                                    type='desc',
                                    action=action,
                                    start=start_time_to_log,
                                    end=start_to_sec,
                                    change_from=change_from,
                                    change_to=change_to,
                                    changedby=user
                                )

                                # Update contributor field:
                                unique_users = TextChanges.objects.filter(
                                    recordsmedia=records_media
                                ).values_list("changedby__name", flat=True).distinct()
                                records_media.contributors = "; ".join(unique_users)
                                records_media.save()

                        else:
                            return Response({"error": message}, status=status.HTTP_400_BAD_REQUEST)
                    else:
                        return Response({"error": "Uppdateras av annan användare."}, status=status.HTTP_400_BAD_REQUEST)
                else:
                    return Response({"error": "Uppdateras av annan användare."}, status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response(
                    {"error": f"Record media with source {file} does not exist or is locked."},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Return updated text
            return Response(
                {"message": "Text updated successfully.", "updated_text": existing_text},
                status=status.HTTP_200_OK
            )

        except RecordsMedia.DoesNotExist:
            return Response({"error": "RecordMedia not found."}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=['post'], url_path='delete')
    def delete_description(self, request):
        """
        API endpoint to DELETE a single description entry by its start time.
        The incoming JSON must provide:
         - recordid
         - file (the audio or relevant media)
         - transcribesession (the lock session)
         - from_email, from_name (optional)
         - start (the time to identify which item to remove)
        """
        serializer = DescribeUpdateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        record_id = data.get("recordid")
        file = data.get("file")
        transcribesession = data.get("transcribesession")
        start_time = data.get("start")
        username = data.get("from_name", "Anonymous")
        email = data.get("from_email", "")

        if not start_time:
            return Response(
                {"error": "You must provide 'start' in the request data to delete an item."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            record = Records.objects.get(id=record_id)
            if record.transcriptionstatus == 'undertranscription':
                records_media = RecordsMedia.objects.filter(
                    record=record_id,
                    source=file,
                    transcriptionstatus='readytotranscribe'
                ).first()

                if records_media is None:
                    return Response(
                        {"error": "No matching media found or is not ready to transcribe."},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                existing_text = json.loads(records_media.description or "[]")

                # Check if transcribesession matches the locked record
                if str(record.transcriptiondate.strftime('%Y-%m-%d %H:%M:%S')) not in transcribesession:
                    return Response({"error": "Uppdateras av annan användare."}, status=status.HTTP_400_BAD_REQUEST)

                # Find the entry with this start time
                entry_to_remove = None
                for entry in existing_text:
                    if entry.get("start") == start_time:
                        entry_to_remove = entry
                        break

                if not entry_to_remove:
                    return Response(
                        {"error": f"No description entry found with start='{start_time}'."},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                # Remove entry from the list
                existing_text.remove(entry_to_remove)

                # Sort again just to keep ordering
                existing_text = sorted(existing_text, key=lambda x: time_to_seconds(x['start']))

                with transaction.atomic():
                    records_media.description = json.dumps(existing_text, ensure_ascii=False)
                    records_media.save()

                    # Log the deletion
                    clean_name = strip_tags(username).replace(';', '')
                    user, _ = CrowdSourceUsers.objects.get_or_create(
                        userid=clean_name,
                        defaults={"name": clean_name, "email": email}
                    )
                    # We can store the old text in 'change_from' if we like:
                    old_text = entry_to_remove.get('text', '')
                    TextChanges.objects.create(
                        recordsmedia=records_media,
                        type='desc',
                        action='delete',
                        start=time_to_seconds(start_time),
                        change_from=old_text,
                        change_to='',
                        changedby=user
                    )

                    # Update contributor field
                    unique_users = TextChanges.objects.filter(recordsmedia=records_media)\
                        .values_list("changedby__name", flat=True).distinct()
                    records_media.contributors = "; ".join(unique_users)
                    records_media.save()

                return Response(
                    {"message": f"Entry with start='{start_time}' deleted.", "updated_text": existing_text},
                    status=status.HTTP_200_OK
                )

            else:
                return Response(
                    {"error": "Record is not under transcription (cannot delete)."},
                    status=status.HTTP_400_BAD_REQUEST
                )

        except Records.DoesNotExist:
            return Response({"error": "Record not found."}, status=status.HTTP_404_NOT_FOUND)

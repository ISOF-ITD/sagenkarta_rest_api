from django.db import transaction
from django.utils.dateparse import parse_datetime
from rest_framework import viewsets, permissions, status
from rest_framework.authentication import BasicAuthentication
from rest_framework.response import Response

from sagenkarta_rest_api.models import Records, RecordsMedia, CrowdSourceUsers, TextChanges
from sagenkarta_rest_api.views import DescribeUpdateSerializer, CsrfExemptSessionAuthentication
from sagenkarta_rest_api.views import time_to_seconds
from rest_framework.decorators import action

import json

import logging
logger = logging.getLogger(__name__)

class UtterancesViewSet(viewsets.ViewSet):
    """
    Handle utterances for files in records_media stored in field utterances
    Currently only descriptions for files of type audio
    """
    authentication_classes = (CsrfExemptSessionAuthentication, BasicAuthentication)
    # permission_classes = [AllowAny]  # This allows any user to access the endpoint

    transcriptionstatuses_allowed_to_update = {'readytocontribute', 'readytotranscribe'}

    def get_permissions(self):
        permission_classes = [permissions.AllowAny]
        return [permission() for permission in permission_classes]

    """
    @action(detail=False, methods=['post'], url_path='start')
    def utterancesstart(self, request):
        USE describestart instead as it is same logic
        API endpoint for starting a session for updating and creating text descriptions for RecordsMedia.
    """

    @action(detail=False, methods=['post'], url_path='change')
    def change(self, request):
        """
        API endpoint for updating text utterances for RecordsMedia.

        UNDER UTVECKLING
        """
        serializer = DescribeUpdateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        record_id = data.get("recordid")
        file = data.get("file")
        transcribesession = data.get("transcribesession")
        speaker = data.get("speaker")
        start_time = data.get("start")
        start_from = data.get("start_from")
        # Start id is order number within array items with the same start_time/start_from:
        # Used if start_from time is not unique
        start_id = data.get("start_id")
        start_to = data.get("start_to")
        # Log time standardized in seconds
        start_time_sec = time_to_seconds(data.get("start")) if data.get("start") else None
        start_from_sec = time_to_seconds(data.get("start_from")) if data.get("start_from") else None
        start_to_sec = time_to_seconds(data.get("start_to")) if data.get("start_to") else None
        change_from = data.get("change_from", "")
        change_to = data.get("change_to", "")
        username = data.get("from_name", "Anonymous")
        email = data.get("from_email", "")

        try:
            record = Records.objects.get(id=record_id)
            #record = RecordsMedia.objects.get(id=record_id)
            if record.transcriptionstatus == 'undertranscription':
                # Maybe: Also check that the record of RecordsMedia has transcriptiontype audio? record__transcriptiontype='audio'
                records_media = RecordsMedia.objects.filter(record=record_id, source=file, transcriptionstatus_in=self.transcriptionstatuses_allowed_to_update).first()
                if records_media is not None:
                    existing_text = json.loads(records_media.utterances or "[]")
                    logger.debug(transcribesession)
                    logger.debug(str(record.transcriptiondate.strftime('%Y-%m-%d %H:%M:%S')))
                    session_time = parse_datetime(transcribesession)
                    if record.transcriptiondate.replace(microsecond=0) == session_time.replace(microsecond=0):
                        action = None
                        message = ''
                        # INSERT: If start_time: new entry
                        # Currently: Deactivated with "or False"
                        if start_time is not None or False:
                            # Ensure start time is unique
                            if any(entry['start'] == start_time for entry in existing_text):
                                return Response({"error": "Start time must be unique."}, status=status.HTTP_400_BAD_REQUEST)
                            time_exists = False
                            for entry in existing_text:
                                # If start_from in elements
                                if entry["start"] == start_from:
                                    time_exists = True
                                    message = 'start_from exists'
                            if not time_exists:
                                # Keep time format from client
                                # OR standardize time format here?
                                if change_to is not None:
                                    new_entry = {"text": change_to, "start": start_time}
                                action = 'insert'
                                start_time_to_log = start_time_sec
                                existing_text.append(new_entry)

                        else:
                            # UPDATE TEXT: Check if text change: update
                            if start_from_sec is not None and change_from is not None and change_to is not None:
                                counter = 0
                                for entry in existing_text:
                                    # If start_to in elements
                                    if entry["start"] == start_from_sec:
                                        speaker_correct = True
                                        if speaker is not None:
                                            speaker_correct = False
                                            if entry["speaker"] == speaker:
                                                speaker_correct = True
                                        if start_id is not None and speaker_correct:
                                            counter = counter + 1
                                            if not (start_id == counter):
                                                continue
                                        action = 'update'
                                        entry["text"] = change_to
                                        start_time_to_log = start_from_sec
                                        # Found the object to change so exit:
                                        break
                                if action is None:
                                    message = 'start_to does not exist'
                            # UPDATE TIME: Check if time change: update
                            # NOT YET TESTED
                            if start_from_sec is not None and start_to is not None:
                                for entry in existing_text:
                                    # If start_from in elements
                                    if entry["start"] == start_from_sec:
                                        entry["start"] = start_to
                                        # Log start_time
                                        start_time_to_log = start_to_sec
                                        action = 'update'
                                if action is None:
                                    message = 'start_from does not exist'

                        # Check if action valid
                        if action is not None:
                            # Ensure JSON elements are ordered by start time
                            # For string minutes:seconds with leading zeros
                            # existing_text = sorted(existing_text, key=lambda x: time_to_seconds(x['start']))
                            # For numerical values:
                            existing_text = sorted(existing_text, key=lambda x: x['start'])

                            with transaction.atomic():
                                records_media.utterances = json.dumps(existing_text, ensure_ascii=False)
                                # DO NOT change transcriptiondate as it is the sessionid:
                                # records_media.transcriptiondate = Now()
                                # Save contributor: Where? See example records_media.contributeby below
                                records_media.save()

                                # Log the change
                                user, _ = CrowdSourceUsers.objects.get_or_create(userid=username,
                                                                                 defaults={"name": username, "email": email})
                                TextChanges.objects.create(
                                    recordsmedia=records_media,
                                    type='utter',
                                    action=action,
                                    start=start_time_to_log,
                                    end=start_to_sec,
                                    # value=json.dumps(existing_text),
                                    change_from=change_from,
                                    change_to=change_to,
                                    changedby=user
                                )

                                # Update contributor field
                                # IF need: Add check user status/role if user should be registered and shown?
                                unique_users = TextChanges.objects.filter(recordsmedia=records_media).values_list("changedby__name",
                                                                                                                  flat=True).distinct()
                                unique_users_text = "; ".join(unique_users)
                                records_media.contributors = unique_users_text
                                records_media.save()
                        else:
                            return Response({"error": message}, status=status.HTTP_400_BAD_REQUEST)
                    else:
                        return Response({"error": "Uppdateras av annan användare."}, status=status.HTTP_400_BAD_REQUEST)
                else:
                    return Response({"error": "Uppdateras av annan användare."}, status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response(
                    {"error": f"Record media med source {file} finns inte"},
                    status=status.HTTP_404_NOT_FOUND
                )

            if existing_text is None:
                response_data = []
            else:
                # Not needed when we store time format in request:
                # Convert start times back to mm:ss format for response
                # response_data = [{"text": entry["text"], "start": seconds_to_time(entry["start"])} for entry in
                #                 existing_text]
                response_data = existing_text

            return Response({"message": "Text updated successfully.", "updated_text": response_data},
                            status=status.HTTP_200_OK)

        except RecordsMedia.DoesNotExist:
            return Response({"error": "Record not found."}, status=status.HTTP_404_NOT_FOUND)

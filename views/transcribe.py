"""
Endpoints under **/api/transcribe***.

│  ViewSet                    │ Verb │ Purpose
├─────────────────────────────┼──────┼─────────────────────────────────────────
│ TranscribeStartViewSet      │ POST │ lock a record → *undertranscription*
│ TranscribeViewSet           │ POST │ save ➜ finish session                 │
│ TranscribeSaveViewSet       │ POST │ save intermediate draft               │
│ TranscribeCancelViewSet     │ POST │ unlock / abort session                │

The helpers below encapsulate the rather gnarly business rules around:

* page-by-page vs whole-document transcription
* super-transcriber auto-publish flow
* informant + contributor de-duplication

Whenever you touch this file, please update these rules here – it is the
single point of truth for future developers.
"""
import json
import logging
from datetime import datetime

from django.db import transaction
from django.db.models.functions import Now
from django.contrib.auth.models import User
from django.http import JsonResponse
from rest_framework import viewsets, permissions
from rest_framework.authentication import BasicAuthentication
from rest_framework.response import Response

from sagenkarta_rest_api.models import (
    Records, RecordsMedia, Persons, RecordsPersons, CrowdSourceUsers,
    set_avoid_timer_before_update_of_search_database,
)

from .utils import (
    CsrfExemptSessionAuthentication,
    validate_string as validateString,
)

logger = logging.getLogger(__name__)

# Transcription status values
# Used to determine if a record has already been handled and shouldn't be modified again.
STATUSES_COMPLETED = {
    'transcribed', 'reviewing', 'needsimprovement',
    'approved', 'published', 'autopublished'
}

# Helper functions

def save_message_comment(comment: str, supertranscriber: bool, obj):
    """
    Append *comment* to the correct field (comment / transcription_comment)
    unless it is already present.  Hard-limit to 255 chars.
    """
    if not comment:
        return

    # Supertranscribers store comments in 'comment', others in 'transcription_comment'
    field = "comment" if supertranscriber else "transcription_comment"
    current = getattr(obj, field) or ""

    if comment in current:
        return                       # already there – nothing to do

    combined = f"{current};{comment}" if current else comment
    if len(combined) > 255:
        combined = combined[:252] + "..."

    setattr(obj, field, combined)


def calculate_transcribe_time(page_id, obj):
    if page_id is not None or obj.transcriptiondate is None:
        return
    delta = datetime.now() - obj.transcriptiondate
    obj.transcribe_time = int(delta.total_seconds() / 60)



def create_or_update_crowdsource_user(crowdsource_user):
    """
    Insert or return existing CrowdSourceUsers row that matches name+email.
    """
    if not (crowdsource_user.email or crowdsource_user.name):
        # fall back to anonymous user
        return CrowdSourceUsers.objects.filter(userid='crowdsource-anonymous').first()

    existing = CrowdSourceUsers.objects.filter(
        name=crowdsource_user.name, email=crowdsource_user.email
    ).first()
    if existing:
        return existing

    crowdsource_user.createdate = Now()
    crowdsource_user.save()
    return crowdsource_user


def save_crowdsource_user(_, jsonData, recordid):
    """
    Wrapper that builds CrowdSourceUsers instance from the incoming JSON
    then lets create_or_update_crowdsource_user() persist / reuse it.
    """
    u = CrowdSourceUsers(
        userid=f"rid{recordid}",
        name=jsonData.get("from_name", ""),
        email=jsonData.get("from_email", ""),
    )
    return create_or_update_crowdsource_user(u)


def save_informant_to_record(informant, jsonData, recordid, transcribed_object, user):
    """
    Persist Persons row (informant) + RecordsPersons relation if ‘informantName’ present.
    """
    if isinstance(transcribed_object, RecordsMedia):
        transcribed_object = transcribed_object.record
    if len(jsonData.get("informantName", "")) <= 1:
        return informant  # nothing to do

    informant = Persons(
        id=f"crwd{recordid}",
        name=jsonData["informantName"],
        birthplace=jsonData.get("informantBirthPlace", ""),
        birth_year=jsonData.get("informantBirthDate", "") if jsonData.get("informantBirthDate", "").isdigit() else None,
    )

    existing = Persons.objects.filter(
        name=informant.name,
        birth_year=informant.birth_year,
        birthplace=informant.birthplace,
    ).first()
    if existing:
        informant = existing
    else:
        informant.transcriptionstatus = "transcribed"
        informant.createdby = user
        informant.editedby = user
        informant.createdate = Now()
        informant.save()

    # Update transcriptioncomment (avoid duplicates; trim 255)
    info_extra = jsonData.get("informantInformation", "")
    if info_extra:
        current = informant.transcriptioncomment or ""
        if info_extra not in current:
            current = (current + ";" if current else "") + info_extra
            informant.transcriptioncomment = current[:252] + "..." if len(current) > 255 else current
            informant.save()

    # Link record ↔ person
    if not RecordsPersons.objects.filter(
        person=informant, record=transcribed_object, relation__in=["i", "informant"]
    ).exists():
        RecordsPersons.objects.create(person=informant, record=transcribed_object, relation="informant")

    return informant


# --------------- the big “do-everything” helper ----------------------------#


def save_transcription(request, response_message, response_status, set_status_to_transcribed):
    """
    Heavy-lifting helper shared by /transcribe/ (finish) and /transcribesave/ (intermediate save)
    """
    jsonData = None
    if 'json' not in request.data:
        return jsonData, 'Ett oväntat fel: Error in request', response_status

    jsonData = json.loads(request.data['json'])
    logger.debug("save_transcription post %s", jsonData)

    recordid = jsonData['recordid']
    page_id = jsonData.get('page')  # None if not present

    # Locate the object to be transcribed
    transcribed_object = None
    transcribed_object_parent = None
    if page_id is None:
        transcribed_object = Records.objects.filter(pk=recordid).first()
        transcribed_object_parent = transcribed_object
    else:
        transcribed_object = RecordsMedia.objects.filter(record=recordid, source=page_id).first()
        transcribed_object_parent = Records.objects.filter(pk=recordid).first()

    if not transcribed_object:
        response_message = 'Ett oväntat fel: posten finns inte.'
        return jsonData, response_message, response_status

    # Session validation
    transcribesession_status = False
    if 'transcribesession' in jsonData:
        ts = jsonData['transcribesession']
        cmp_obj = transcribed_object_parent if page_id else transcribed_object
        if str(cmp_obj.transcriptiondate.strftime('%Y-%m-%d %H:%M:%S')) in ts:
            transcribesession_status = True

    if not transcribesession_status:
        response_message = 'Felaktigt sessions-id.'
        return jsonData, response_message, response_status

    #   Main save logic
    if 'message' not in jsonData:
        response_message = 'Ett oväntat fel: inget meddelande.'
        return jsonData, response_message, response_status

    # Naive conflict handling
    if transcribed_object.transcriptionstatus not in ['undertranscription', 'readytotranscribe']:
        response_message = 'Posten är inte redo att transkriberas.'
        return jsonData, response_message, response_status

    # Whole-record vs page-by-page status rules
    if page_id is None and transcribed_object.transcriptionstatus != 'undertranscription':
        response_message = 'Posten är inte låst för avskrift.'
        return jsonData, response_message, response_status
    if page_id and not (
        transcribed_object.transcriptionstatus == 'readytotranscribe'
        and transcribed_object_parent.transcriptionstatus == 'undertranscription'
    ):
        response_message = 'Sidan är inte redo för avskrift.'
        return jsonData, response_message, response_status

    # ------------------ perform update ---------------------------------- #
    user = User.objects.filter(username='restapi').first()
    calculate_transcribe_time(page_id, transcribed_object)

    transcribed_object.text = jsonData['message']
    if validateString(jsonData.get('recordtitle')):
        transcribed_object.title = jsonData['recordtitle']

    # Finalise status?
    if set_status_to_transcribed and transcribed_object.transcriptionstatus == 'undertranscription':
        transcribed_object.transcriptionstatus = 'transcribed'
        transcribed_object.transcriptiondate = Now()

    # Save informant / contributor
    informant = None
    if 'informantName' in jsonData:
        informant = save_informant_to_record(informant, jsonData, recordid, transcribed_object, user)

    crowdsource_user = save_crowdsource_user(None, jsonData, recordid)
    if crowdsource_user:
        transcribed_object.transcribedby = crowdsource_user

    # Super-transcriber auto-publish
    supertranscriber = crowdsource_user and "supertranscriber" in crowdsource_user.role
    if supertranscriber:
        transcribed_object.transcriptionstatus = "autopublished"
        transcribed_object.publishstatus = "published"
        if informant and informant.transcriptionstatus != 'published':
            informant.transcriptionstatus = 'autopublished'
            informant.save()

    save_message_comment(jsonData.get('messageComment', ''), supertranscriber, transcribed_object)

    # ------------------ persist to DB ----------------------------------- #
    try:
        set_avoid_timer_before_update_of_search_database(True)
        transcribed_object.save()
        # Page-by-page: update parent record when all pages done
        if page_id:
            pages_left = RecordsMedia.objects.filter(
                record__record_type='one_record',
                transcriptionstatus='readytotranscribe',
                record__id__startswith=transcribed_object_parent.id
            ).count()
            if pages_left == 0:
                transcribed_object_parent.transcriptionstatus = 'published'
            transcribed_object_parent.save()

        response_status = 'true'
        logger.info("Transcription saved for %s", recordid)


    except Exception as e:
        logger.exception("Could not save transcription for %s", recordid)
        response_message = 'Kunde inte spara posten.'
    finally:
        set_avoid_timer_before_update_of_search_database(False)

    if transcribed_object_parent.id.count('_') == 2:
        parent_id = transcribed_object_parent.id.rsplit('_', 1)[0]
        one_row = Records.objects.filter(
            type='arkiv', record_type='one_accession_row', id=parent_id
        ).first()
        if one_row:
            one_row.save()

    return jsonData, response_message, response_status


# ---------------------------------------------------------------------------#
#                                ViewSets                                    #
# ---------------------------------------------------------------------------#


class _BaseTranscribeViewSet(viewsets.ViewSet):
    """
    Common base for all transcribe-related endpoints.
    Disables CSRF and allows public (unauthenticated) access.
    """
    authentication_classes = (CsrfExemptSessionAuthentication, BasicAuthentication)

    def list(self, request):
        return Response()

    def get_permissions(self):
        return [permissions.AllowAny()]


class TranscribeViewSet(_BaseTranscribeViewSet):
    """
    POST /api/transcribe/  – save + mark record as ‘transcribed’ / finished
    """

    def post(self, request, *_, **__):
        response_status = 'false'
        jsonData, msg, response_status = save_transcription(
            request, None, response_status, set_status_to_transcribed=True
        )
        resp = {'success': response_status, 'data': jsonData}
        if msg:
            resp['message'] = msg
        return JsonResponse(resp)


class TranscribeSaveViewSet(_BaseTranscribeViewSet):
    """
    POST /api/transcribesave/  – save WITHOUT finishing the session
    """

    def post(self, request, *_, **__):
        response_status = 'false'
        jsonData, msg, response_status = save_transcription(
            request, None, response_status, set_status_to_transcribed=False
        )
        resp = {'success': response_status, 'data': jsonData}
        if msg:
            resp['message'] = msg
        return JsonResponse(resp)


class TranscribeStartViewSet(_BaseTranscribeViewSet):
    """
    POST /api/transcribestart/  – lock a record (status → undertranscription)
    Expects JSON with at least { "recordid": "<id>" }
    """

    def post(self, request, *_, **__):
        if 'json' not in request.data:
            return JsonResponse({'success': 'false'}, status=400)

        data = json.loads(request.data['json'])
        recordid = data.get('recordid')
        page = data.get('page')  # optional

        target = (
            Records.objects.filter(pk=recordid).first()
            if page is None
            else RecordsMedia.objects.filter(record=recordid, source=page).first()
        )

        if not target:
            return JsonResponse({'success': 'false', 'message': 'Posten finns inte!'}, status=404)

        if target.transcriptionstatus not in ['readytotranscribe', 'readytocontribute']:
            return JsonResponse({'success': 'false', 'message': 'Redan låst eller klar.'}, status=409)

        with transaction.atomic():
            if page is None:
                target = (Records.objects
                          .select_for_update()
                          .filter(pk=recordid).first())
            else:
                target = (RecordsMedia.objects
                          .select_for_update()
                          .filter(record=recordid, source=page).first())

            if not target or target.transcriptionstatus not in ['readytotranscribe',
                                                                'readytocontribute']:
                return JsonResponse({'success': 'false'}, status=409)

            target.transcriptionstatus = 'undertranscription'
            target.transcriptiondate = Now()
            target.save()
            target.refresh_from_db()

        data['transcribesession'] = target.transcriptiondate.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        return JsonResponse({'success': 'true', 'data': data})


class TranscribeCancelViewSet(_BaseTranscribeViewSet):
    """
    POST /api/transcribecancel/ – unlock the record if session id matches.
    """

    def post(self, request, *_, **__):
        if 'json' not in request.data:
            return JsonResponse({'success': 'false'}, status=400)

        data = json.loads(request.data['json'])
        recordid = data.get('recordid')
        page = data.get('page')
        session = data.get('transcribesession', '')

        target = (
            Records.objects.filter(pk=recordid).first()
            if page is None
            else RecordsMedia.objects.filter(record=recordid, source=page).first()
        )

        if not target:
            return JsonResponse({'success': 'false', 'message': 'Posten finns inte!'}, status=404)

        # Ensure session matches
        if str(target.transcriptiondate.strftime('%Y-%m-%d %H:%M:%S')) not in session:
            return JsonResponse({'success': 'false', 'message': 'Fel sessions-id.'}, status=409)

        # Only unlock if still undertranscription
        if target.transcriptionstatus != 'undertranscription':
            return JsonResponse({'success': 'false', 'message': 'Felaktig status.'}, status=409)


        # Special case for page-by-page transcriptions:
        # If no pages left, mark whole record as transcribed or autopublished.
        if target.transcriptiontype == 'sida':
            pages_left = RecordsMedia.objects.filter(
                record=recordid, transcriptionstatus='readytotranscribe'
            ).exists()
            if not pages_left:
                target.transcriptionstatus = (
                    'autopublished' if not RecordsMedia.objects.filter(
                        record=recordid
                    ).exclude(transcriptionstatus='autopublished').exists() else 'transcribed'
                )
            else:
                target.transcriptionstatus = (
                    'readytocontribute' if target.transcriptiontype == 'audio' else 'readytotranscribe'
                )
        else:
            target.transcriptionstatus = (
                'readytocontribute' if target.transcriptiontype == 'audio'
                else 'readytotranscribe'
            )

        try:
            set_avoid_timer_before_update_of_search_database(True)
            target.save()
        except Exception:  # pragma: no cover
            logger.exception("Could not unlock %s", target.id)
            return JsonResponse({'success': 'false'}, status=500)
        finally:
            set_avoid_timer_before_update_of_search_database(False)

        return JsonResponse({'success': 'true', 'data': data})

import json
import logging
from typing import Any, Dict

from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.http import JsonResponse
from rest_framework import permissions, viewsets, status
from rest_framework.response import Response
from rest_framework.authentication import BasicAuthentication
from rest_framework.exceptions import ValidationError

from .utils import CsrfExemptSessionAuthentication
from sagenkarta_rest_api import config
from rest_framework import serializers
logger = logging.getLogger(__name__)

class FeedbackSerializer(serializers.Serializer):
    subject = serializers.CharField()
    message = serializers.CharField()
    from_email = serializers.EmailField(required=False, allow_blank=True)
    recordid = serializers.CharField(required=False, allow_blank=True)
    send_to = serializers.CharField(required=False, allow_blank=True)

class FeedbackViewSet(viewsets.ViewSet):
    """
    Accepts JSON POST with a json payload:

        {
            "subject": "...",
            "message": "...",
            "from_email": "...", # optional
            "recordid": "UUB123", # optional – routes to archive support account
            "send_to": "alice" # optional – explicit staff username (legacy)
        }

    Routing rules (highest to lowest priority):

    1. If `send_to` is present and resolves to a user with an e-mail, use that.
    2. Else if `recordid` begins with an alpha org-code and that support user exists, use it.
    3. Else fall back to the global `supportisof` inbox.
    4. Finally, default to `config.feedbackEmail`.
    """

    # Public endpoint, no CSRF
    authentication_classes = (CsrfExemptSessionAuthentication, BasicAuthentication)
    permission_classes = [permissions.AllowAny]

    def list(self, request):  # OPTIONS /feedback/ pre-flights need this
        return JsonResponse({})

    def create(self, request):
        try:
            raw = request.data.get("json", {})
            if isinstance(raw, str):
                try:
                    raw = json.loads(raw)
                except json.JSONDecodeError as exc:
                    logger.warning("Malformed JSON in feedback payload", exc_info=True)
                    raise ValidationError("`json` must be valid JSON.") from exc
            elif not isinstance(raw, dict):
                raise ValidationError("`json` must be an object or JSON string.")

            serializer = FeedbackSerializer(data=raw)
            serializer.is_valid(raise_exception=True)
            data = serializer.validated_data

            send_to = _resolve_recipient(data)
            send_mail(
                subject=data["subject"],
                message=data["message"],
                from_email=data.get("from_email") or "",
                recipient_list=[send_to],
                fail_silently=False,
            )
            return Response(
                {"success": "true", "data": data},
                status=status.HTTP_200_OK,
            )

        except ValidationError as exc:
            # handled by DRF default exception handler, but we still log
            logger.info("Bad feedback payload: %s", exc.detail)
            raise

        except Exception as exc:  # noqa: BLE001
            logger.exception("Unexpected failure in FeedbackViewSet.create")
            return Response(
                {"success": "false", "error": str(exc)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


# Internal helpers

def _resolve_recipient(payload: Dict[str, Any]) -> str:
    """
    Returns an *e-mail address* following the priority chain:

    1. `send_to` username → user.email
    2. alpha prefix of `recordid` (e.g. "UUB") → supportUUB user.email
    3. global "supportisof" user.email
    4. config.feedbackEmail (hard fallback)
    """
    # 1 explicit username
    explicit = payload.get("send_to")
    if explicit:
        user = User.objects.filter(username=explicit).first()
        if user and user.email:
            return user.email

    # 2 archive-specific support account by recordid
    rec_id = payload.get("recordid", "")
    if rec_id and len(rec_id) >= 3:
        org = rec_id[:3]
        if org.isalpha():  # i.e. "UUB"
            user = User.objects.filter(username=f"support{org}").first()
            if user and user.email:
                return user.email

    # 3 global supportisof
    default_user = User.objects.filter(username="supportisof").first()
    if default_user and default_user.email:
        return default_user.email

    # 4 hard-coded fallback
    return config.feedbackEmail

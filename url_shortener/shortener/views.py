from __future__ import annotations

from typing import Optional

from django.http import HttpResponseRedirect, HttpResponseGone, HttpResponseNotFound
from django.urls import reverse
from django.utils import timezone
from django.core.exceptions import ValidationError

from rest_framework.decorators import api_view, renderer_classes
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework import status

from drf_spectacular.utils import extend_schema, OpenApiResponse

from .models import Link
from .serializers import (
    ShortenRequestSerializer,
    ShortenResponseSerializer,
    ResolveResponseSerializer,
    StatsResponseSerializer,
)


def _build_short_url(request, code: str) -> str:
    # Build absolute URL to redirect endpoint
    path = reverse("redirect", kwargs={"code": code})
    scheme = "https" if request.is_secure() else "http"
    return f"{scheme}://{request.get_host()}{path}"


def _json_error(message: str, status_code: int) -> Response:
    return Response({"error": message}, status=status_code)


@extend_schema(
    request=ShortenRequestSerializer,
    responses={
        201: ShortenResponseSerializer,
        400: OpenApiResponse(description="Validation error"),
        405: OpenApiResponse(description="Method not allowed"),
    },
    summary="Create a short URL",
)
@api_view(["POST"])
@renderer_classes([JSONRenderer])
def shorten(request):
    """Create a new short URL.

    Accepts a JSON body (or form data via DRF parsers) with canonical fields:
    - target_url (required): destination URL to shorten
    - ttl (optional): expiration in seconds

    The short code is generated automatically.

    Parameters:
    - request: DRF Request containing input data.

    Returns:
    - 201 Created with a JSON body including short_id, short_url, target_url,
      created_at and expires_at on success.
    - 400 Bad Request with {"error": "..."} when validation fails.

    Notes:
    - Error response format is preserved as {"error": "..."} for compatibility.
    """
    serializer = ShortenRequestSerializer(data=request.data)
    if not serializer.is_valid():
        # Flatten serializer errors into a single message to preserve previous API shape
        errors = serializer.errors
        if isinstance(errors, dict):
            first_key = next(iter(errors.keys())) if errors else None
            msg = "; ".join(map(str, errors.get(first_key, []))) if first_key else "Invalid input"
        else:
            msg = "Invalid input"
        return _json_error(msg, status.HTTP_400_BAD_REQUEST)

    target_url = serializer.validated_data["target_url"]
    ttl_val: Optional[int] = serializer.validated_data.get("ttl_seconds")

    try:
        link = Link.create_with_ttl(url=target_url, ttl_seconds=ttl_val)
    except ValidationError as e:
        return _json_error("; ".join(e.messages), status.HTTP_400_BAD_REQUEST)

    body = {
        "short_id": link.code,
        "short_url": _build_short_url(request, link.code),
        "target_url": link.target_url,
        "created_at": link.created_at,
        "expires_at": link.expires_at,
    }
    return Response(ShortenResponseSerializer(body).data, status=status.HTTP_201_CREATED)


def _get_link_or_error(code: str) -> Optional[Link]:
    try:
        return Link.objects.get(code=code)
    except Link.DoesNotExist:
        return None


@extend_schema(
    responses={
        200: ResolveResponseSerializer,
        404: OpenApiResponse(description="Not found"),
        410: OpenApiResponse(description="Expired"),
        405: OpenApiResponse(description="Method not allowed"),
    },
    summary="Resolve short code to target URL",
)
@api_view(["GET"])
@renderer_classes([JSONRenderer])
def resolve(request, code: str):
    """Resolve a short code to its target URL without redirecting.

    Parameters:
    - request: DRF Request
    - code (str): Short identifier to resolve.

    Returns:
    - 200 OK with {"url": target_url, "short_id": code} if found and not expired.
    - 404 Not Found with {"error": "Short URL not found"} when code does not exist.
    - 410 Gone with {"error": "Short URL expired"} when the link is expired.
    """
    link = _get_link_or_error(code)
    if link is None:
        return _json_error("Short URL not found", status.HTTP_404_NOT_FOUND)
    if link.is_expired:
        return _json_error("Short URL expired", status.HTTP_410_GONE)

    return Response({"url": link.target_url, "short_id": link.code})


# Keep redirect as a plain Django view (not part of DRF schema)
def redirect_view(request, code: str):
    """HTTP redirect to the target URL for a given short code.

    This is a plain Django view (not DRF) intentionally excluded from the API
    schema. It increments the hit counter when redirecting.

    Parameters:
    - request: Django HttpRequest
    - code (str): Short identifier to redirect.

    Returns:
    - 302 Found redirecting to the target URL if found and not expired.
    - 404 Not Found plain response if the code does not exist.
    - 410 Gone plain response if the link is expired.
    """
    link = _get_link_or_error(code)
    if link is None:
        return HttpResponseNotFound("Not Found")
    if link.is_expired:
        return HttpResponseGone("Expired")

    link.register_hit()
    return HttpResponseRedirect(link.target_url)


@extend_schema(
    responses={
        200: StatsResponseSerializer,
        404: OpenApiResponse(description="Not found"),
        405: OpenApiResponse(description="Method not allowed"),
    },
    summary="Get statistics for a short URL",
)
@api_view(["GET"])
@renderer_classes([JSONRenderer])
def stats(request, code: str):
    """Return statistics for a given short code.

    Parameters:
    - request: DRF Request
    - code (str): Short identifier to inspect.

    Returns:
    - 200 OK with counts and timestamps: short_id, target_url, hit_count,
      created_at, expires_at, expired, and ttl_seconds_remaining.
    - 404 Not Found with {"error": "Short URL not found"} when code does not exist.
    """
    link = _get_link_or_error(code)
    if link is None:
        return _json_error("Short URL not found", status.HTTP_404_NOT_FOUND)

    ttl_remaining = None
    if link.expires_at is not None:
        seconds = int((link.expires_at - timezone.now()).total_seconds())
        ttl_remaining = max(0, seconds)

    body = {
        "short_id": link.code,
        "target_url": link.target_url,
        "hit_count": link.hit_count,
        "created_at": link.created_at,
        "expires_at": link.expires_at,
        "expired": link.is_expired,
        "ttl_seconds_remaining": ttl_remaining,
    }
    return Response(StatsResponseSerializer(body).data)

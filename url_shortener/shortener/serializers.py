from __future__ import annotations

from typing import Optional

from rest_framework import serializers


class ShortenRequestSerializer(serializers.Serializer):
    # Canonical fields only: require target_url, optional ttl (seconds)
    target_url = serializers.URLField(required=True, allow_blank=False)
    ttl = serializers.IntegerField(required=False, min_value=0)

    def validate(self, attrs):
        url = attrs.get("target_url")
        if not url:
            raise serializers.ValidationError({"target_url": "This field is required."})
        ttl = attrs.get("ttl")
        return {"target_url": url, "ttl_seconds": ttl}


class ShortenResponseSerializer(serializers.Serializer):
    short_id = serializers.CharField()
    short_url = serializers.CharField()
    target_url = serializers.URLField()
    created_at = serializers.DateTimeField()
    expires_at = serializers.DateTimeField(allow_null=True)


class ResolveResponseSerializer(serializers.Serializer):
    url = serializers.URLField()
    short_id = serializers.CharField()


class StatsResponseSerializer(serializers.Serializer):
    short_id = serializers.CharField()
    target_url = serializers.URLField()
    hit_count = serializers.IntegerField()
    created_at = serializers.DateTimeField()
    expires_at = serializers.DateTimeField(allow_null=True)
    expired = serializers.BooleanField()
    ttl_seconds_remaining = serializers.IntegerField(allow_null=True)

from __future__ import annotations

import string
from dataclasses import dataclass
from datetime import timedelta
from typing import Optional

from django.core.validators import URLValidator
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
import secrets


ALPHABET = string.ascii_letters + string.digits  # base62
DEFAULT_CODE_LENGTH = 7


def generate_unique_code(length: int = DEFAULT_CODE_LENGTH) -> str:
    """Generate a random unique code of given length using base62 characters.
    Uniqueness is ensured by checking against existing codes.
    """
    for _ in range(10):
        code = "".join(secrets.choice(ALPHABET) for _ in range(length))
        if not Link.objects.filter(code=code).exists():
            return code
    # As a last resort, increase length to reduce collision probability
    while True:
        code = "".join(secrets.choice(ALPHABET) for _ in range(length + 1))
        if not Link.objects.filter(code=code).exists():
            return code


@dataclass
class TTLResult:
    expired: bool
    expires_at: Optional[timezone.datetime]


class Link(models.Model):
    code = models.CharField(max_length=32, unique=True, db_index=True)
    target_url = models.URLField()
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    expires_at = models.DateTimeField(null=True, blank=True, db_index=True)
    hit_count = models.PositiveIntegerField(default=0)

    class Meta:
        indexes = [
            models.Index(fields=["code"]),
            models.Index(fields=["expires_at"]),
        ]

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.code} -> {self.target_url}"

    @property
    def is_expired(self) -> bool:
        if self.expires_at is None:
            return False
        return timezone.now() >= self.expires_at

    def ttl_info(self) -> TTLResult:
        return TTLResult(expired=self.is_expired, expires_at=self.expires_at)

    @classmethod
    def create_with_ttl(
        cls,
        url: str,
        ttl_seconds: Optional[int] = None,
        code: Optional[str] = None,
    ) -> "Link":
        # Validate URL
        validator = URLValidator(schemes=("http", "https"))
        try:
            validator(url)
        except ValidationError:
            # Attempt to add http:// if missing scheme, then validate again
            if not (url.startswith("http://") or url.startswith("https://")):
                url2 = "http://" + url
                try:
                    validator(url2)
                    url = url2
                except ValidationError as e:
                    raise e
            else:
                raise

        if code:
            if cls.objects.filter(code=code).exists():
                raise ValidationError("Code already in use")
        else:
            code = generate_unique_code()

        expires_at = None
        if ttl_seconds is not None:
            if ttl_seconds < 0:
                raise ValidationError("ttl_seconds must be >= 0")
            expires_at = timezone.now() + timedelta(seconds=ttl_seconds)

        return cls.objects.create(code=code, target_url=url, expires_at=expires_at)

    def register_hit(self) -> None:
        # Increment hit counter atomically
        Link.objects.filter(pk=self.pk).update(hit_count=models.F("hit_count") + 1)
        # Refresh the in-memory value (optional)
        self.refresh_from_db(fields=["hit_count"]) 

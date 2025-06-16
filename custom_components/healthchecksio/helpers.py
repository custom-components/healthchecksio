"""Helper methods for the HealthChecks.io integration."""

from __future__ import annotations

import re
from urllib.parse import ParseResult, urlparse, urlunparse


def clean_url(url: str) -> str:
    """Cleanup slashes from URL."""
    parsed: ParseResult = urlparse(url)

    if not parsed.scheme:
        parsed = urlparse("https://" + url)

    cleaned_path: str = re.sub(r"/+", "/", parsed.path)
    if cleaned_path != "/":
        cleaned_path = cleaned_path.rstrip("/")

    cleaned: ParseResult = parsed._replace(path=cleaned_path)
    return urlunparse(cleaned)

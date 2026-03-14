"""
services/mistral_client.py
--------------------------
Initialises the Mistral AI client singleton and exposes:
  - `mistral_client`  — shared Mistral instance
  - `call_mistral_api()` — rate-limited, retried API call helper
  - `verify_islamic_citations()` — citation integrity check on AI output
"""

import logging
import re
from typing import Dict, List

from mistralai import Mistral

from app.core.config import GENERATION_CONFIG, MISTRAL_API_KEY, MISTRAL_MODEL
from app.services.rate_limiter import rate_limiter, retry_with_backoff

logger = logging.getLogger(__name__)

# Compile regex patterns once for performance
_QURAN_MENTION_PATTERN = re.compile(r"Qur'?an|Surah|Ayah|verse", re.IGNORECASE)
_HADITH_MENTION_PATTERN = re.compile(
    r"Hadith|narrated|reported by|Bukhari|Muslim|Tirmidhi|Abu Dawud|Nasa'?i|Ibn Majah",
    re.IGNORECASE,
)
_QURAN_REF_PATTERN = re.compile(r"Surah\s+\w+\s*[:\-]\s*\d+", re.IGNORECASE)
_HADITH_REF_PATTERN = re.compile(
    r"(Bukhari|Muslim|Tirmidhi|Abu Dawud|Nasa'?i|Ibn Majah)\s+\d+",
    re.IGNORECASE,
)

# ---------------------------------------------------------------------------
# Client singleton
# ---------------------------------------------------------------------------

try:
    mistral_client = Mistral(api_key=MISTRAL_API_KEY)
    logger.info("Mistral client initialised successfully")
except Exception as exc:
    logger.error(f"Failed to initialise Mistral client: {exc}")
    raise RuntimeError(f"Failed to initialise Mistral client: {exc}")


# ---------------------------------------------------------------------------
# API call helper
# ---------------------------------------------------------------------------

@retry_with_backoff(max_retries=3, base_delay=2)
async def call_mistral_api(messages: List[Dict]) -> str:
    """Call the Mistral chat completion API with rate limiting and retry logic.

    Args:
        messages: List of role/content message dicts.

    Returns:
        The assistant's reply as a plain string.

    Raises:
        Exception: Propagated after all retries are exhausted.
    """
    import asyncio

    # Honour rate limit — wait if needed
    if not rate_limiter.is_allowed():
        wait = rate_limiter.get_wait_time()
        logger.warning(f"Rate limit reached — waiting {wait:.2f}s")
        await asyncio.sleep(wait)

    try:
        logger.info("Calling Mistral API…")
        response = await mistral_client.chat.complete_async(
            model=MISTRAL_MODEL,
            messages=messages,
            **GENERATION_CONFIG,
        )
        if response and response.choices:
            return response.choices[0].message.content
        raise Exception("Empty response from Mistral API")

    except Exception as exc:
        logger.error(f"Mistral API error: {exc}")
        err_str = str(exc).lower()
        exc_type = type(exc).__name__

        if "429" in err_str or "quota" in err_str or "rate limit" in err_str or "too many" in err_str:
            raise Exception("API quota exceeded — rate limit reached. Please try again in a moment.")
        if "401" in err_str or "unauthorized" in err_str or "invalid api key" in err_str:
            raise Exception("401 Unauthorized — the Mistral API key is invalid or expired.")
        if "403" in err_str or "forbidden" in err_str:
            raise Exception("403 Forbidden — API key lacks permission for this model.")
        if "timeout" in err_str or "timed out" in err_str:
            raise Exception("Request timed out while waiting for AI response.")
        if any(keyword in err_str for keyword in (
            "getaddrinfo", "connect", "connection refused",
            "network", "unreachable", "name resolution",
            "dns", "ssl", "certificate",
        )):
            raise Exception(
                "Unable to connect to the AI service. "
                "Please check your internet connection and try again."
            )
        if "model" in err_str and ("not found" in err_str or "does not exist" in err_str):
            raise Exception(
                f"Model not found — the configured model '{MISTRAL_MODEL}' is unavailable."
            )
        if "content" in err_str and ("filter" in err_str or "blocked" in err_str or "safety" in err_str):
            raise Exception("Content blocked by safety filters. Please rephrase your question.")
        raise Exception(f"API error ({exc_type}): {exc}")


# ---------------------------------------------------------------------------
# Citation integrity check
# ---------------------------------------------------------------------------

def verify_islamic_citations(text: str) -> str:
    """Append a notice if the AI mentions Quran/Hadith without a proper citation.

    This is a lightweight safety net — not a replacement for scholarly review.
    Uses precompiled regex patterns for better performance.
    """
    has_quran = _QURAN_MENTION_PATTERN.search(text) is not None
    has_hadith = _HADITH_MENTION_PATTERN.search(text) is not None

    # Check for actual references (e.g. "Surah Al-Baqarah 2:286")
    has_quran_ref = _QURAN_REF_PATTERN.search(text) is not None
    has_hadith_ref = _HADITH_REF_PATTERN.search(text) is not None

    warnings: List[str] = []
    if has_quran and not has_quran_ref:
        warnings.append(
            "\n\n**Citation Notice**: A Quranic verse was mentioned but no specific "
            "reference was provided. Please verify with an authentic copy of the Quran."
        )
    if has_hadith and not has_hadith_ref:
        warnings.append(
            "\n\n**Citation Notice**: A Hadith was mentioned but no specific source "
            "reference was provided. Please verify with authenticated collections."
        )

    return text + "".join(warnings) if warnings else text

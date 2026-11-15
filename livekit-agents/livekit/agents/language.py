# Copyright 2023 LiveKit, Inc.

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0


# distributed under the License is distributed on an "AS IS" BASIS,

# See the License for the specific language governing permissions and
# limitations under the License.

"""Normalized BCP-47 language identifier."""

from __future__ import annotations

from typing import Any

from pydantic import GetCoreSchemaHandler
from pydantic_core import CoreSchema, core_schema

from ._language_data import CODE_TO_LANGUAGE_NAME, ISO_639_3_TO_1, LANGUAGE_NAMES_TO_CODE


def _normalize_language(code: str) -> str:
    """Normalize a language code/name to BCP-47 format.

    Rules:
    - Language names (e.g. "english") → ISO 639-1 ("en")
    - ISO 639-3 (e.g. "eng") → ISO 639-1 ("en")
    - ISO 639-1 (e.g. "en") → pass-through
    - BCP-47 (e.g. "en-US") → normalized casing ("en-US")
    - Unknown codes → lowercase pass-through
    """
    lowered = code.strip().lower()

    if lowered in LANGUAGE_NAMES_TO_CODE:
        return LANGUAGE_NAMES_TO_CODE[lowered]

    if lowered in ISO_639_3_TO_1:
        mapped = ISO_639_3_TO_1[lowered]
        if mapped is not None:
            return mapped

        return lowered

    parts = lowered.replace("_", "-").split("-")
    if len(parts) >= 2:
        lang = parts[0]

        normalized_parts = [lang]
        for part in parts[1:]:
            if len(part) == 4:
                normalized_parts.append(part.capitalize())
            else:
                normalized_parts.append(part.upper())
        return "-".join(normalized_parts)

    return lowered


class LanguageCode(str):
    """Normalized BCP-47 language identifier. Accepts any common format.

    Examples::

        LanguageCode("english")  # → "en"
        LanguageCode("eng")      # → "en"
        LanguageCode("en")       # → "en"
        LanguageCode("en-US")    # → "en-US"
        LanguageCode("en_us")    # → "en-US"
        LanguageCode("multi")    # → "multi"
    """

    def __new__(cls, code: str) -> LanguageCode:
        normalized = _normalize_language(code)
        return super().__new__(cls, normalized)

    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: Any, handler: GetCoreSchemaHandler
    ) -> CoreSchema:
        return core_schema.no_info_plain_validator_function(
            cls,
            serialization=core_schema.to_string_ser_schema(),
        )

    @property
    def language(self) -> str:
        """Base language code (ISO 639-1 when possible).

        E.g., ``'en'`` from ``'en-US'``, ``'zh'`` from ``'cmn-Hans-CN'``.
        """
        base = self.split("-")[0]
        mapped = ISO_639_3_TO_1.get(base)
        return mapped if mapped is not None else base

    @property
    def iso(self) -> str:
        """ISO 639-1 tag with region, e.g., ``'zh-CN'`` from ``'cmn-Hans-CN'``."""
        parts = self.split("-")
        base = self.language
        region_parts = [p for p in parts[1:] if len(p) == 2]
        return f"{base}-{region_parts[0]}" if region_parts else base

    @property
    def region(self) -> str | None:
        """Region code, e.g., ``'US'`` from ``'en-US'``, or ``None``."""
        parts = self.split("-")
        for p in parts[1:]:
            if len(p) == 2:
                return p
        return None

    def to_language_name(self) -> str | None:
        """Return the English language name (e.g. ``'english'``), or ``None`` if unknown."""
        return CODE_TO_LANGUAGE_NAME.get(self.language)

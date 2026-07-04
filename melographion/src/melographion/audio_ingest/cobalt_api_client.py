from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CobaltApiConfig:
    api_url: str | None = None

    @property
    def enabled(self) -> bool:
        return bool(self.api_url)


class CobaltApiClient:
    """Placeholder for a future local/private cobalt API integration."""

    def __init__(self, config: CobaltApiConfig):
        self.config = config

    def download(self, public_url: str):
        raise NotImplementedError(
            "Local cobalt API support is reserved for Melographion v0.3. "
            "Set COBALT_API_URL later when a private local cobalt instance is available."
        )

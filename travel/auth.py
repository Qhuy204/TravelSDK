"""
Authentication manager for TravelSDK.
Handles token acquisition and automatic refresh from travel.com/getToken.
"""

from __future__ import annotations

import time
import logging
from typing import Optional

import httpx

from travel.constants import GET_TOKEN_URL, DEFAULT_HEADERS
from travel.models import TokenResponse

logger = logging.getLogger(__name__)


class TokenManager:
    """
    Manages the Travel Bearer token lifecycle.
    
    The token is acquired by sending an empty POST to /getToken with
    browser-like headers (Origin: https://travel.com is required).
    Token expires in 3600 seconds (1 hour).
    """

    def __init__(self) -> None:
        self._token: Optional[TokenResponse] = None
        self._acquired_at: float = 0.0
        # Safety margin: refresh 5 minutes before expiry
        self._refresh_margin: int = 300

    @property
    def is_expired(self) -> bool:
        if self._token is None:
            return True
        elapsed = time.time() - self._acquired_at
        return elapsed >= (self._token.expires_in - self._refresh_margin)

    @property
    def bearer_header(self) -> str:
        if self._token is None:
            raise RuntimeError("No token acquired. Call ensure_token() first.")
        return self._token.bearer

    async def ensure_token(self, client: httpx.AsyncClient) -> str:
        """Return a valid bearer token, refreshing if necessary."""
        if self.is_expired:
            await self._acquire(client)
        return self.bearer_header

    async def _acquire(self, client: httpx.AsyncClient) -> None:
        """Acquire a new token from /getToken."""
        logger.debug("Acquiring new Travel token...")
        try:
            response = await client.post(
                GET_TOKEN_URL,
                headers={
                    **DEFAULT_HEADERS,
                    # Token endpoint uses same-origin
                    "sec-fetch-site": "same-origin",
                },
            )
            response.raise_for_status()
            data = response.json()
            self._token = TokenResponse(**data)
            self._acquired_at = time.time()
            logger.debug(
                f"Token acquired. Expires in {self._token.expires_in}s. "
                f"Type: {self._token.token_type}"
            )
        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to acquire token: {e.response.status_code} {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Token acquisition error: {e}")
            raise

    def invalidate(self) -> None:
        """Force token refresh on next request."""
        self._token = None
        self._acquired_at = 0.0

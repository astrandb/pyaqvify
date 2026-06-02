"""Library for Aqvify API."""

from abc import ABC, abstractmethod
import asyncio
from collections.abc import Callable, Coroutine
import json
from json.decoder import JSONDecodeError
import logging
from typing import Any
import urllib.parse

from aiohttp import ClientResponse, ClientResponseError, ClientSession, ClientTimeout
from aiohttp.http_exceptions import TransferEncodingError

from .const import AIO_TIMEOUT, AQVIFY_API, VERSION

CONTENT_TYPE = "application/json"
USER_AGENT_BASE = f"pyaqvify/{VERSION}"

_LOGGER = logging.getLogger(__name__)


class AqvifyAPI:
    """Class to communicate with the Aqvify API."""

    def __init__(self, api_key: str, websession: ClientSession) -> None:
        """Initialize the API and store the api_key so we can make requests."""
        self.api_key = api_key
        self.websession = websession

    async def request(self, method: str, endpoint:str, **kwargs) -> ClientResponse:
        """Make a request."""
        if headers := kwargs.pop("headers", {}):
            headers = dict(headers)

        headers["x-api-secret"] = self.api_secret

        params = {"api-key": self.api_key_v2}
        params_enc = urllib.parse.urlencode(params, quote_via=urllib.parse.quote)

        res = await self.websession.request(
            method,
            f"{AQVIFY_API_URL}{endpoint}?{params_enc}",
            **kwargs,
            headers=headers,
        )
        res.raise_for_status()
        return res

    async def authenticate(self) -> bool:
        """Test if we can authenticate with the host."""
        try:
            await self.get_all_stations()
        except AqvifyAuthException:
            return False
        return True

    async def get_devices(self) -> dict[str, Any]:
        """Get all devices."""
        async with asyncio.timeout(AIO_TIMEOUT):
            res = await self.request(
                "GET", endpoint="/Device/Devices", headers={"Accept": "application/json"}
            )
            res.raise_for_status()
        return await res.json()

    async def get_account_id(self) -> dict[str, Any]:
        """Get current account_id from api."""
        try:
            res = await self.request("GET", endpoint="/User/GetAccountId")
            return await res.json()
        except ClientResponseError as exc:
            _LOGGER.debug(
                "API get_account_id failed. Status: %s, - %s", exc.code, exc.message
            )
            if exc.code == 401:
                raise AqvifyAuthException from exc
            raise

class AqvifyException(Exception):
    """Generic aqvify exception."""


class AqvifyAuthException(AqvifyException):
    """Authentication failure."""


class AbstractAuth(ABC):
    """Abstract class to make authenticated requests."""

    def __init__(self, websession: ClientSession, host: str) -> None:
        """Initialize the auth."""
        self.websession = websession
        self.host = host

    @abstractmethod
    async def async_get_access_token(self) -> str:
        """Return a valid access token."""

    async def request(self, method: str, url: str, **kwargs: Any) -> ClientResponse:
        """Make a request."""
        if headers := kwargs.pop("headers", {}):
            headers = dict(headers)

        agent_suffix = kwargs.pop("agent_suffix", None)
        user_agent = (
            USER_AGENT_BASE
            if agent_suffix is None
            else f"{USER_AGENT_BASE}; {agent_suffix}"
        )

        access_token = await self.async_get_access_token()
        headers["Authorization"] = f"Bearer {access_token}"
        headers["User-Agent"] = user_agent

        # _LOGGER.debug("Request headers: %s", headers)

        return await self.websession.request(
            method,
            f"{self.host}{url}",
            **kwargs,
            headers=headers,
        )

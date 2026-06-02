"""Library for Aqvify API."""

import asyncio
import logging
from typing import Any

from aiohttp import ClientResponse, ClientResponseError, ClientSession

from .const import AIO_TIMEOUT, AQVIFY_API as AQVIFY_API

_LOGGER = logging.getLogger(__name__)

ACCEPT_DATA = "application/json"


class AqvifyAPI:
    """Class to communicate with the Aqvify API."""

    def __init__(self, api_key: str, websession: ClientSession) -> None:
        """Initialize the API and store the api_key so we can make requests."""
        self.api_key = api_key
        self.websession = websession

    async def request(
        self, method: str, endpoint: str, **kwargs: Any
    ) -> ClientResponse:
        """Make a request."""
        if headers := kwargs.pop("headers", {}):
            headers = dict(headers)

        headers["x-api-key"] = self.api_key

        res = await self.websession.request(
            method,
            f"{AQVIFY_API}{endpoint}",
            **kwargs,
            headers=headers,
        )
        res.raise_for_status()
        return res

    async def authenticate(self) -> bool:
        """Test if we can authenticate with the host."""
        try:
            await self.get_account_id()
        except AqvifyAuthException:
            return False
        return True

    async def get_devices(self) -> dict[str, Any]:
        """Get all devices."""
        async with asyncio.timeout(AIO_TIMEOUT):
            res = await self.request(
                "GET",
                endpoint="/Device/Devices",
                headers={"Accept": ACCEPT_DATA},
            )
            res.raise_for_status()
        return await res.json()

    async def get_device_latest_data(self, device_id: str) -> dict[str, Any]:
        """Get data for a specific device."""
        async with asyncio.timeout(AIO_TIMEOUT):
            res = await self.request(
                "GET",
                endpoint=f"/DeviceData/LatestValue/?deviceKey={device_id}",
                headers={"Accept": ACCEPT_DATA},
            )
            res.raise_for_status()
        return await res.json()

    async def get_account_id(self) -> dict[str, Any]:
        """Get current account_id from api."""
        try:
            res = await self.request(
                "GET",
                endpoint="/User/GetAccountId",
                headers={"Accept": ACCEPT_DATA},
            )
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

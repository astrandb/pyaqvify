"""Library for Aqvify API."""

import asyncio
import logging
from typing import Any

from aiohttp import ClientResponse, ClientSession

from .const import AIO_TIMEOUT, AQVIFY_API as AQVIFY_API
from .model import (
    AqvifyAccount,
    AqvifyDeviceData,
    AqvifyDevices,
    AqvifyHourAggregatedValues,
)

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
        if res.status == 401:
            raise AqvifyAuthException("Authentication failure")
        res.raise_for_status()
        return res

    async def async_authenticate(self) -> bool:
        """Test if we can authenticate with the host."""
        try:
            await self.async_get_account_id()
        except AqvifyAuthException:
            return False
        return True

    async def async_get_devices(self) -> AqvifyDevices:
        """Get all devices."""
        async with asyncio.timeout(AIO_TIMEOUT):
            res = await self.request(
                "GET",
                endpoint="/Device/Devices",
                headers={"Accept": ACCEPT_DATA},
            )
        return AqvifyDevices(await res.json())

    async def async_get_device_latest_data(self, device_id: str) -> AqvifyDeviceData:
        """Get data for a specific device."""
        async with asyncio.timeout(AIO_TIMEOUT):
            res = await self.request(
                "GET",
                endpoint=f"/DeviceData/LatestValue?deviceKey={device_id}",
                headers={"Accept": ACCEPT_DATA},
            )
        return AqvifyDeviceData(await res.json())

    async def async_get_hour_aggregation(
        self, device_id: str, begin_time: str, end_time: str
    ) -> list[AqvifyHourAggregatedValues]:
        """Get data for a specific device."""
        async with asyncio.timeout(AIO_TIMEOUT):
            res = await self.request(
                "GET",
                endpoint=(
                    "/DeviceData/HourAggregateValues?deviceKey="
                    f"{device_id}&beginTime={begin_time}&endTime={end_time}"
                ),
                headers={"Accept": ACCEPT_DATA},
            )
        json_data = await res.json()
        return [AqvifyHourAggregatedValues(data) for data in json_data]

    async def async_get_account_id(self) -> AqvifyAccount:
        """Get current account_id from api."""
        async with asyncio.timeout(AIO_TIMEOUT):
            res = await self.request(
                "GET",
                endpoint="/User/GetAccountId",
                headers={"Accept": ACCEPT_DATA},
            )
        return AqvifyAccount(await res.json())


class AqvifyException(Exception):
    """Generic aqvify exception."""


class AqvifyAuthException(AqvifyException):
    """Authentication failure."""

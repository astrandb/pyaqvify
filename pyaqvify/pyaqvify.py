"""Library for Aqvify API."""

import asyncio
import datetime as dt
from datetime import datetime
import logging
import random
from typing import Any

from aiohttp import ClientResponse, ClientSession, ClientTimeout

from .const import AIO_TIMEOUT, AQVIFY_API as AQVIFY_API
from .model import (
    AqvifyAccount,
    AqvifyDeviceData,
    AqvifyDevices,
    AqvifyHourAggregatedValueList,
)

_LOGGER = logging.getLogger(__name__)

MAX_RATE_LIMIT_ATTEMPTS = 2

ACCEPT_DATA = "application/json"


class AqvifyAPI:
    """Class to communicate with the Aqvify API."""

    def __init__(self, api_key: str, websession: ClientSession) -> None:
        """Initialize the API and store the api_key so we can make requests."""
        self.api_key = api_key
        self.websession = websession
        self._rate_limit_attempt = 0

    async def request(
        self, method: str, endpoint: str, **kwargs: Any
    ) -> ClientResponse:
        """Make a request."""
        if headers := kwargs.pop("headers", {}):
            headers = dict(headers)

        headers["x-api-key"] = self.api_key
        _LOGGER.debug("Request: %s | %s", method, f"{AQVIFY_API}{endpoint}")
        res = await self.websession.request(
            method,
            f"{AQVIFY_API}{endpoint}",
            **kwargs,
            headers=headers,
            timeout=ClientTimeout(total=AIO_TIMEOUT),
        )
        if res.status >= 400:
            _LOGGER.debug("Response status: %s", res.status)
        if res.status == 401:
            raise AqvifyAuthException("Authentication failure")
        if res.status == 429:
            if self._rate_limit_attempt >= MAX_RATE_LIMIT_ATTEMPTS:
                _LOGGER.error(
                    "Rate limit exceeded: max attempts (%d) reached",
                    MAX_RATE_LIMIT_ATTEMPTS,
                )
                res.raise_for_status()
            retry_after = res.headers.get("Retry-After")
            wait_time = self._calculate_429_wait_time(retry_after)
            wait_time = max(wait_time, 10)

            _LOGGER.warning(
                "Rate limited (429), waiting %.2f seconds before retry (attempt %d/%d)",
                wait_time,
                self._rate_limit_attempt + 1,
                MAX_RATE_LIMIT_ATTEMPTS,
            )
            await asyncio.sleep(wait_time)

            self._rate_limit_attempt += 1
            return await self.request(method=method, endpoint=endpoint, **kwargs)

        res.raise_for_status()
        self._rate_limit_attempt = 0
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
        res = await self.request(
            "GET",
            endpoint="/Device/Devices",
            headers={"Accept": ACCEPT_DATA},
        )
        return AqvifyDevices(await res.json())

    async def async_get_device_latest_data(self, device_id: str) -> AqvifyDeviceData:
        """Get data for a specific device."""
        res = await self.request(
            "GET",
            endpoint=f"/DeviceData/LatestValue?deviceKey={device_id}",
            headers={"Accept": ACCEPT_DATA},
        )
        return AqvifyDeviceData(await res.json())

    async def async_get_hour_aggregation(
        self, device_id: str, begin_time: str | datetime, end_time: str | datetime
    ) -> AqvifyHourAggregatedValueList:
        """Get data for a specific device."""
        date_time_fmt = "%Y-%m-%dT%H:%MZ"
        begin_str = (
            begin_time.strftime(date_time_fmt)
            if isinstance(begin_time, datetime)
            else begin_time
        )
        end_str = (
            end_time.strftime(date_time_fmt)
            if isinstance(end_time, datetime)
            else end_time
        )
        res = await self.request(
            "GET",
            endpoint=(
                "/DeviceData/HourAggregateValues?deviceKey="
                f"{device_id}&beginTime={begin_str}&endTime={end_str}"
            ),
            headers={"Accept": ACCEPT_DATA},
        )
        return AqvifyHourAggregatedValueList(await res.json())

    async def async_get_account_id(self) -> AqvifyAccount:
        """Get current account_id from api."""
        res = await self.request(
            "GET",
            endpoint="/User/GetAccountId",
            headers={"Accept": ACCEPT_DATA},
        )
        return AqvifyAccount(await res.json())

    def _calculate_429_wait_time(self, retry_after: str | None) -> float:
        """
        Calculate wait time for 429 rate limiting.

        :param retry_after: Retry-After header value (seconds or HTTP-date).
        :return: Wait time in seconds.
        """
        if retry_after:
            wait_seconds: int | float | None
            try:
                wait_seconds = int(float(retry_after))
            except ValueError:
                try:
                    retry_time = dt.datetime.fromisoformat(retry_after)
                    if retry_time.tzinfo is None:
                        retry_time = retry_time.replace(tzinfo=dt.UTC)
                    else:
                        retry_time = retry_time.astimezone(dt.UTC)
                    now = dt.datetime.now(dt.UTC)
                    wait_seconds = max(0, (retry_time - now).total_seconds())
                except ValueError:
                    wait_seconds = None

            if wait_seconds is not None:
                wait_seconds = min(wait_seconds, 10 * 60)
                jitter = random.uniform(0, 1)
                return wait_seconds + jitter

        base = 1.0
        max_wait = base * (2**self._rate_limit_attempt)
        max_wait = min(max_wait, 10 * 60)
        return random.uniform(0, 30) + max_wait


class AqvifyException(Exception):
    """Generic aqvify exception."""


class AqvifyAuthException(AqvifyException):
    """Authentication failure."""

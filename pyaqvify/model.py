"""Data models for Aqvify API."""


class AqvifyDevice:
    """Metaata for a single device from API."""

    def __init__(self, raw_data: dict) -> None:
        """Initialize AqvifyDevice."""
        self.raw_data = raw_data

    @property
    def raw(self) -> dict:
        """Return raw data."""
        return self.raw_data

    @property
    def device_key(self) -> str | None:
        """Return the device ID."""
        return self.raw_data.get("deviceKey")

    @property
    def name(self) -> str | None:
        """Return the name."""
        return self.raw_data.get("name")


class AqvifyDevices:
    """Data for all devices from API."""

    def __init__(self, raw_data: dict) -> None:
        """Initialize AqvifyDevices."""
        self.raw_data = raw_data

    @property
    def raw(self) -> dict:
        """Return raw data."""
        return self.raw_data

    @property
    def devices(self) -> dict[str, AqvifyDevice]:
        """Return list of all devices."""

        return {
            AqvifyDevice(device).device_key: AqvifyDevice(device)
            for device in self.raw_data
        }


class AqvifyDeviceData:
    """Data for a single device from API."""

    def __init__(self, raw_data: dict) -> None:
        """Initialize AqvifyDeviceData."""
        self.raw_data = raw_data

    @property
    def raw(self) -> dict:
        """Return raw data."""
        return self.raw_data

    @property
    def date_time(self) -> str | None:
        """Return the date and time."""
        return self.raw_data.get("dateTime")

    @property
    def water_level(self) -> int | float | None:
        """Return the water level."""
        return self.raw_data.get("waterLevel")

    @property
    def meter_value(self) -> int | float | None:
        """Return the meter value."""
        return self.raw_data.get("meterValue")

    @property
    def status(self) -> str | None:
        """Return the status."""
        return self.raw_data.get("status")


class AqvifyAccount:
    """Data for account from API."""

    def __init__(self, raw_data: dict) -> None:
        """Initialize AqvifyAccount."""
        self.raw_data = raw_data

    @property
    def raw(self) -> dict:
        """Return raw data."""
        return self.raw_data

    @property
    def account_id(self) -> str:
        """Return the account ID."""
        return self.raw_data.get("accountId", "")

"""DataUpdateCoordinator for Rinnai Water Heater."""

import asyncio
import logging
import time
from typing import Any

from homeassistant.components.network import async_get_source_ip
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import RinnaiWaterHeaterApi, RinnaiWaterHeaterApiError
from .const import DOMAIN, UPDATE_INTERVAL

_LOGGER = logging.getLogger(__name__)


class RinnaiWaterHeaterCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Class to manage fetching Rinnai Water Heater data."""

    config_entry: ConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        api: RinnaiWaterHeaterApi,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            config_entry=config_entry,
            name=DOMAIN,
            update_interval=UPDATE_INTERVAL,
        )
        self.api = api
        self.mac_address: str = ""
        self.model: str = ""
        self._pause_until: float | None = None
        self._consecutive_failures: int = 0
        self._last_discovery_time: float = 0.0
        self.lock = asyncio.Lock()

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from API."""
        if self._pause_until is not None and time.time() < self._pause_until:
            return self.data

        async with self.lock:
            if self._pause_until is not None and time.time() < self._pause_until:
                return self.data
            try:
                data = await self.api.async_get_bus_data()
                self._consecutive_failures = 0
                return data
            except RinnaiWaterHeaterApiError as err:
                self._consecutive_failures += 1
                now = time.time()
                if (
                    self._consecutive_failures >= 3
                    and (now - self._last_discovery_time) >= 60.0
                ):
                    self._last_discovery_time = now
                    _LOGGER.warning(
                        "Connection to Rinnai Water Heater at %s failed %d times. Attempting UDP discovery...",
                        self.api.host,
                        self._consecutive_failures,
                    )
                    discovered_ip = await self._async_discover_and_update_ip()
                    if discovered_ip:
                        try:
                            data = await self.api.async_get_bus_data()
                            self._consecutive_failures = 0
                            return data
                        except RinnaiWaterHeaterApiError:
                            pass

                raise UpdateFailed(f"Error communicating with API: {err}") from err

    async def _async_discover_and_update_ip(self) -> str | None:
        """Discover new IP via UDP broadcast and update config entry if MAC matches."""
        try:
            local_ip = await async_get_source_ip(self.hass)
        except (OSError, HomeAssistantError):
            local_ip = None

        candidate_ips = await self.api.async_discover_devices_udp(self.hass, local_ip)
        _LOGGER.debug("UDP discovery candidate IPs: %s", candidate_ips)

        for candidate_ip in candidate_ips:
            try:
                temp_api = RinnaiWaterHeaterApi(candidate_ip, self.api.session)
                candidate_mac = await temp_api.async_get_mac()
                if candidate_mac.strip().lower() == self.mac_address.strip().lower():
                    _LOGGER.info(
                        "Rinnai Water Heater found at new IP: %s (MAC: %s)",
                        candidate_ip,
                        self.mac_address,
                    )
                    self.api.update_host(candidate_ip)
                    if self.config_entry is not None:
                        self.hass.config_entries.async_update_entry(
                            self.config_entry,
                            data={**self.config_entry.data, CONF_HOST: candidate_ip},
                        )
                    return candidate_ip
            except RinnaiWaterHeaterApiError:
                continue

        _LOGGER.warning(
            "UDP discovery could not locate device with MAC %s", self.mac_address
        )
        return None

    def update_cached_data(self, data_updates: dict[str, Any]) -> None:
        """Update cached coordinator data with updates from control response."""
        if self.data is None:
            self.data = {}
        self.data.update(data_updates)

    def pause_polling(self, duration: float) -> None:
        """Pause polling for a specified duration in seconds."""
        self._pause_until = time.time() + duration

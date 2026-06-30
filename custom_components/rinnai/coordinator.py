"""DataUpdateCoordinator for Rinnai Water Heater."""

import logging
import time
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import RinnaiWaterHeaterApi, RinnaiWaterHeaterApiError
from .const import DOMAIN, UPDATE_INTERVAL

_LOGGER = logging.getLogger(__name__)


class RinnaiWaterHeaterCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Class to manage fetching Rinnai Water Heater data."""

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
        self._pause_until: float | None = None

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from API."""
        if self._pause_until is not None and time.time() < self._pause_until:
            return self.data
        try:
            return await self.api.async_get_bus_data()
        except RinnaiWaterHeaterApiError as err:
            raise UpdateFailed(f"Error communicating with API: {err}") from err

    def update_cached_data(self, data_updates: dict[str, Any]) -> None:
        """Update cached coordinator data with updates from control response."""
        if self.data is None:
            self.data = {}
        self.data.update(data_updates)

    def pause_polling(self, duration: float) -> None:
        """Pause polling for a specified duration in seconds."""
        self._pause_until = time.time() + duration

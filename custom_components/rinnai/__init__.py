"""The Rinnai Water Heater Integration integration."""

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import RinnaiWaterHeaterApi, RinnaiWaterHeaterApiError
from .coordinator import RinnaiWaterHeaterCoordinator

_LOGGER = logging.getLogger(__name__)

_PLATFORMS: list[Platform] = [
    Platform.BINARY_SENSOR,
    Platform.SENSOR,
    Platform.WATER_HEATER,
]

type RinnaiWaterHeaterConfigEntry = ConfigEntry[RinnaiWaterHeaterCoordinator]


async def async_setup_entry(
    hass: HomeAssistant, entry: RinnaiWaterHeaterConfigEntry
) -> bool:
    """Set up Rinnai Water Heater Integration from a config entry."""
    host = entry.data[CONF_HOST]
    session = async_get_clientsession(hass)
    api = RinnaiWaterHeaterApi(host, session)

    mac: str | None = None
    model: str | None = None

    try:
        mac = await api.async_get_mac()
        model = await api.async_get_model()
    except RinnaiWaterHeaterApiError as err:
        _LOGGER.warning(
            "Connection to Rinnai Water Heater at %s failed: %s. Attempting UDP discovery",
            host,
            err,
        )
        candidate_ips = await api.async_discover_devices_udp(hass)
        _LOGGER.debug("UDP discovery candidate IPs during setup: %s", candidate_ips)

        for candidate_ip in candidate_ips:
            try:
                temp_api = RinnaiWaterHeaterApi(candidate_ip, session)
                candidate_mac = await temp_api.async_get_mac()
                candidate_model = await temp_api.async_get_model()

                if (
                    entry.unique_id
                    and candidate_mac.strip().lower() != entry.unique_id.strip().lower()
                ):
                    continue

                mac = candidate_mac
                model = candidate_model
                api.update_host(candidate_ip)
                hass.config_entries.async_update_entry(
                    entry, data={**entry.data, CONF_HOST: candidate_ip}
                )
                _LOGGER.info(
                    "Discovered Rinnai Water Heater at new IP: %s (MAC: %s)",
                    candidate_ip,
                    mac,
                )
                break
            except RinnaiWaterHeaterApiError:
                continue

        if not mac or not model:
            raise ConfigEntryNotReady(
                f"Timeout or error connecting to water heater at {host}: {err}"
            ) from err

    coordinator = RinnaiWaterHeaterCoordinator(hass, api, entry)
    coordinator.mac_address = mac
    coordinator.model = model

    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, _PLATFORMS)

    return True


async def async_unload_entry(
    hass: HomeAssistant, entry: RinnaiWaterHeaterConfigEntry
) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, _PLATFORMS)

"""The Rinnai Water Heater Integration integration."""

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import RinnaiWaterHeaterApi, RinnaiWaterHeaterApiError
from .coordinator import RinnaiWaterHeaterCoordinator

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

    try:
        mac = await api.async_get_mac()
        model = await api.async_get_model()
    except RinnaiWaterHeaterApiError as err:
        raise ConfigEntryNotReady(
            f"Timeout or error connecting to water heater: {err}"
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

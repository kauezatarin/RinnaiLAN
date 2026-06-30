"""Platform for Rinnai Water Heater binary sensor integration."""

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import CONNECTION_NETWORK_MAC, DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import RinnaiWaterHeaterCoordinator


@dataclass(frozen=True, kw_only=True)
class RinnaiBinarySensorEntityDescription(BinarySensorEntityDescription):
    """Class describing Rinnai binary sensor entities."""

    is_on_fn: Callable[[dict[str, Any]], bool]


BINARY_SENSORS: tuple[RinnaiBinarySensorEntityDescription, ...] = (
    RinnaiBinarySensorEntityDescription(
        key="combustion_active",
        translation_key="combustion_active",
        device_class=BinarySensorDeviceClass.HEAT,
        is_on_fn=lambda data: bool(data.get("combustion_active")),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry[RinnaiWaterHeaterCoordinator],
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Rinnai Water Heater binary sensors from a config entry."""
    coordinator = config_entry.runtime_data
    async_add_entities(
        RinnaiBinarySensorEntity(coordinator, description)
        for description in BINARY_SENSORS
    )


class RinnaiBinarySensorEntity(
    CoordinatorEntity[RinnaiWaterHeaterCoordinator], BinarySensorEntity
):
    """Representation of a Rinnai Water Heater Binary Sensor."""

    entity_description: RinnaiBinarySensorEntityDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: RinnaiWaterHeaterCoordinator,
        description: RinnaiBinarySensorEntityDescription,
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{coordinator.mac_address}_{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.mac_address)},
            name=coordinator.config_entry.title,
            manufacturer="Rinnai",
            model=coordinator.model,
            connections={(CONNECTION_NETWORK_MAC, coordinator.mac_address)},
        )

    @property
    def is_on(self) -> bool:
        """Return true if the binary sensor is on."""
        return self.entity_description.is_on_fn(self.coordinator.data)

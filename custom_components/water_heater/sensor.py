"""Platform for Rinnai Water Heater sensor integration."""

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
    UnitOfTemperature,
    UnitOfTime,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import CONNECTION_NETWORK_MAC, DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.typing import StateType
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import RinnaiWaterHeaterCoordinator


@dataclass(frozen=True, kw_only=True)
class RinnaiSensorEntityDescription(SensorEntityDescription):
    """Class describing Rinnai sensor entities."""

    value_fn: Callable[[dict[str, Any]], StateType]


SENSORS: tuple[RinnaiSensorEntityDescription, ...] = (
    RinnaiSensorEntityDescription(
        key="inlet_temp",
        translation_key="inlet_temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        value_fn=lambda data: data.get("inlet_temp"),
    ),
    RinnaiSensorEntityDescription(
        key="outlet_temp",
        translation_key="outlet_temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        value_fn=lambda data: data.get("outlet_temp"),
    ),
    RinnaiSensorEntityDescription(
        key="actual_flow",
        translation_key="water_flow_rate",
        native_unit_of_measurement="L/min",
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        value_fn=lambda data: data.get("actual_flow"),
    ),
    RinnaiSensorEntityDescription(
        key="number_of_activations",
        translation_key="activations_count",
        state_class=SensorStateClass.TOTAL_INCREASING,
        suggested_display_precision=0,
        value_fn=lambda data: data.get("number_of_activations"),
    ),
    RinnaiSensorEntityDescription(
        key="combustion_hours",
        translation_key="combustion_hours",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.HOURS,
        state_class=SensorStateClass.TOTAL_INCREASING,
        suggested_display_precision=0,
        value_fn=lambda data: data.get("combustion_hours"),
    ),
    RinnaiSensorEntityDescription(
        key="standby_hours",
        translation_key="standby_hours",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.HOURS,
        state_class=SensorStateClass.TOTAL_INCREASING,
        suggested_display_precision=0,
        value_fn=lambda data: data.get("standby_hours"),
    ),
    RinnaiSensorEntityDescription(
        key="wifi_signal",
        translation_key="wifi_signal",
        device_class=SensorDeviceClass.SIGNAL_STRENGTH,
        native_unit_of_measurement=SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
        value_fn=lambda data: data.get("wifi_signal"),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry[RinnaiWaterHeaterCoordinator],
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Rinnai Water Heater sensors from a config entry."""
    coordinator = config_entry.runtime_data
    async_add_entities(
        RinnaiSensorEntity(coordinator, description) for description in SENSORS
    )


class RinnaiSensorEntity(CoordinatorEntity[RinnaiWaterHeaterCoordinator], SensorEntity):
    """Representation of a Rinnai Water Heater Sensor."""

    entity_description: RinnaiSensorEntityDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: RinnaiWaterHeaterCoordinator,
        description: RinnaiSensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
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
    def native_value(self) -> StateType:
        """Return the state of the sensor."""
        return self.entity_description.value_fn(self.coordinator.data)

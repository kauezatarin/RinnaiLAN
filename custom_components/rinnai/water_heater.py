"""Platform for Rinnai Water Heater integration."""

import asyncio
from typing import Any

from homeassistant.components.water_heater import (
    WaterHeaterEntity,
    WaterHeaterEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_TEMPERATURE, PRECISION_WHOLE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import CONNECTION_NETWORK_MAC, DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, SUPPORTED_TEMPS, UPDATE_INTERVAL
from .coordinator import RinnaiWaterHeaterCoordinator

SUPPORT_FEATURES = (
    WaterHeaterEntityFeature.TARGET_TEMPERATURE
    | WaterHeaterEntityFeature.ON_OFF
    | WaterHeaterEntityFeature.OPERATION_MODE
)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry[RinnaiWaterHeaterCoordinator],
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Rinnai Water Heater entity from a config entry."""
    coordinator = config_entry.runtime_data
    async_add_entities([RinnaiWaterHeaterEntity(coordinator)])


class RinnaiWaterHeaterEntity(
    CoordinatorEntity[RinnaiWaterHeaterCoordinator], WaterHeaterEntity
):
    """Representation of a Rinnai Water Heater Entity."""

    _attr_has_entity_name = True
    _attr_name = None
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_supported_features = SUPPORT_FEATURES
    _attr_min_temp = 35.0
    _attr_max_temp = 60.0
    _attr_target_temperature_step = 1.0
    _attr_precision = PRECISION_WHOLE

    def __init__(self, coordinator: RinnaiWaterHeaterCoordinator) -> None:
        """Initialize the water heater entity."""
        super().__init__(coordinator)
        self._attr_operation_list = ["on", "off"]
        self._attr_unique_id = coordinator.mac_address
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.mac_address)},
            name=coordinator.config_entry.title,
            manufacturer="Rinnai",
            model=coordinator.model,
            connections={(CONNECTION_NETWORK_MAC, coordinator.mac_address)},
        )

    @property
    def current_temperature(self) -> float | None:
        """Return the current outlet water temperature."""
        return self.coordinator.data.get("outlet_temp")

    @property
    def target_temperature(self) -> float | None:
        """Return the target water temperature."""
        return self.coordinator.data.get("target_temp")

    @property
    def current_operation(self) -> str | None:
        """Return the current operation mode."""
        if self.coordinator.data.get("is_on"):
            return "on"
        return "off"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the optional state attributes."""
        data = self.coordinator.data
        return {
            "combustion_active": data.get("combustion_active"),
            "inlet_temperature": data.get("inlet_temp"),
            "water_flow_rate_l_min": data.get("actual_flow"),
            "activations_count": data.get("number_of_activations"),
            "combustion_hours": data.get("combustion_hours"),
            "standby_hours": data.get("standby_hours"),
            "wifi_signal_dbm": data.get("wifi_signal"),
            "fan_rotation_hz": data.get("fan_rotation_hz"),
            "pov_current_ma": data.get("pov_current_ma"),
            "power_kcal_min": data.get("power_kcal_min"),
            "fan_self_diagnostic": data.get("fan_self_diagnostic"),
            "min_flow_activation": data.get("min_flow_activation"),
            "min_flow_deactivation": data.get("min_flow_deactivation"),
        }

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set new target temperature."""
        async with self.coordinator.lock:
            target_temp = kwargs.get(ATTR_TEMPERATURE)
            if target_temp is None:
                return

            current_target_temp = self.coordinator.data.get("target_temp")
            if current_target_temp is None:
                return

            # Ensure current_target_temp is in SUPPORTED_TEMPS
            if current_target_temp not in SUPPORTED_TEMPS:
                current_target_temp = min(
                    SUPPORTED_TEMPS, key=lambda x: abs(x - current_target_temp)
                )

            # Find target supported temperature, rounding in the direction of change
            target_supported_temp = target_temp
            if target_temp not in SUPPORTED_TEMPS:
                if target_temp > current_target_temp:
                    # Find first supported temp >= target_temp
                    target_supported_temp = next(
                        (t for t in SUPPORTED_TEMPS if t >= target_temp),
                        SUPPORTED_TEMPS[-1],
                    )
                else:
                    # Find last supported temp <= target_temp
                    target_supported_temp = next(
                        (t for t in reversed(SUPPORTED_TEMPS) if t <= target_temp),
                        SUPPORTED_TEMPS[0],
                    )

            current_idx = SUPPORTED_TEMPS.index(current_target_temp)
            target_idx = SUPPORTED_TEMPS.index(target_supported_temp)
            diff = target_idx - current_idx

            if diff == 0:
                return

            # Pause automatic polling during command execution
            self.coordinator.pause_polling(60.0)

            try:
                if diff > 0:
                    for _ in range(diff):
                        updates = await self.coordinator.api.async_increment_temp()
                        self.coordinator.update_cached_data(updates)
                        await asyncio.sleep(0.2)
                else:
                    for _ in range(abs(diff)):
                        updates = await self.coordinator.api.async_decrement_temp()
                        self.coordinator.update_cached_data(updates)
                        await asyncio.sleep(0.2)
            finally:
                # Set pause for exactly UPDATE_INTERVAL seconds after the commands finish, and notify UI listeners
                self.coordinator.pause_polling(UPDATE_INTERVAL.seconds)
                self.coordinator.async_update_listeners()

    async def async_set_operation_mode(self, operation_mode: str) -> None:
        """Set new target operation mode."""
        if operation_mode not in self._attr_operation_list:
            raise ValueError(f"Unsupported operation mode: {operation_mode}")

        async with self.coordinator.lock:
            current_mode = self.current_operation
            if current_mode == operation_mode:
                return

            # Pause automatic polling
            self.coordinator.pause_polling(60.0)

            try:
                updates = await self.coordinator.api.async_toggle_power()
                self.coordinator.update_cached_data(updates)
            finally:
                # Set pause for exactly UPDATE_INTERVAL seconds and notify UI listeners
                self.coordinator.pause_polling(UPDATE_INTERVAL.seconds)
                self.coordinator.async_update_listeners()

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the water heater on."""
        await self.async_set_operation_mode("on")

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the water heater off."""
        await self.async_set_operation_mode("off")

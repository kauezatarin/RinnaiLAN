"""Common fixtures for the Rinnai Water Heater Integration tests."""

from collections.abc import Generator
from unittest.mock import AsyncMock, patch

import pytest


@pytest.fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Override async_setup_entry."""
    with patch(
        "custom_components.rinnai.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        yield mock_setup_entry


@pytest.fixture(autouse=True)
def mock_api() -> Generator[AsyncMock]:
    """Mock RinnaiWaterHeaterApi methods."""
    with patch(
        "custom_components.rinnai.config_flow.RinnaiWaterHeaterApi",
        autospec=True,
    ) as mock_api_class:
        mock_instance = mock_api_class.return_value
        mock_instance.async_get_mac.return_value = "3c:e9:0e:e1:75:58"
        mock_instance.async_get_model.return_value = "REUE271FEHGN3"
        mock_instance.async_get_bus_data.return_value = {
            "status_code": 41,
            "is_on": True,
            "combustion_active": False,
            "number_of_activations": 4700,
            "combustion_hours": 135,
            "standby_hours": 19188,
            "fan_self_diagnostic": 10000,
            "fan_rotation_hz": 0,
            "pov_current_ma": 0,
            "power_kcal_min": 0,
            "inlet_temp": 18.37,
            "outlet_temp": 28.56,
            "actual_flow": 0.0,
            "min_flow_activation": 2.65,
            "min_flow_deactivation": 1.95,
            "target_temp": 38.0,
            "mac_address": "3c:e9:0e:e1:75:58",
            "wifi_signal": -62,
        }
        yield mock_instance

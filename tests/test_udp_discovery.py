"""Test Rinnai Water Heater UDP discovery and automatic IP update."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import UpdateFailed

from custom_components.rinnai.api import (
    RinnaiWaterHeaterApi,
    RinnaiWaterHeaterApiError,
    discover_devices_udp_sync,
)
from custom_components.rinnai.coordinator import RinnaiWaterHeaterCoordinator


def test_discover_devices_udp_sync() -> None:
    """Test sync UDP broadcast discovery mocked socket."""
    with patch("socket.socket") as mock_socket_class:
        mock_sock = MagicMock()
        mock_socket_class.return_value = mock_sock
        mock_sock.recvfrom.side_effect = [
            (b"IP_RESPONSE", ("192.168.0.177", 8080)),
            TimeoutError(),
        ]

        ips = discover_devices_udp_sync("192.168.0.10", timeout=1.0)
        assert ips == ["192.168.0.177"]
        mock_sock.sendto.assert_called_once_with(b"IP", ("<broadcast>", 8080))


async def test_udp_discovery_recovers_ip(hass: HomeAssistant) -> None:
    """Test coordinator triggers UDP discovery on consecutive failures and updates config entry."""
    entry = MagicMock()
    entry.data = {CONF_HOST: "192.168.0.50"}

    session = AsyncMock()
    api = RinnaiWaterHeaterApi("192.168.0.50", session)
    coordinator = RinnaiWaterHeaterCoordinator(hass, api, entry)
    coordinator.mac_address = "3c:e9:0e:e1:75:58"

    bus_data_success = {
        "status_code": 41,
        "is_on": True,
        "mac_address": "3c:e9:0e:e1:75:58",
    }

    # Simulate 3 consecutive API failures on original IP
    with patch.object(
        api, "async_get_bus_data", side_effect=RinnaiWaterHeaterApiError("Timeout")
    ):
        # 1st failure
        with pytest.raises(UpdateFailed):
            await coordinator._async_update_data()
        assert coordinator._consecutive_failures == 1

        # 2nd failure
        with pytest.raises(UpdateFailed):
            await coordinator._async_update_data()
        assert coordinator._consecutive_failures == 2

    # 3rd failure: triggers UDP rediscovery
    with (
        patch.object(
            api,
            "async_get_bus_data",
            side_effect=[RinnaiWaterHeaterApiError("Timeout"), bus_data_success],
        ),
        patch(
            "custom_components.rinnai.coordinator.async_get_source_ip",
            return_value="192.168.0.10",
        ),
        patch.object(
            api,
            "async_discover_devices_udp",
            return_value=["192.168.0.177"],
        ),
        patch(
            "custom_components.rinnai.coordinator.RinnaiWaterHeaterApi.async_get_mac",
            return_value="3c:e9:0e:e1:75:58",
        ),
        patch.object(hass.config_entries, "async_update_entry") as mock_update_entry,
    ):
        data = await coordinator._async_update_data()
        assert data == bus_data_success
        assert api.host == "192.168.0.177"
        assert coordinator._consecutive_failures == 0
        mock_update_entry.assert_called_once_with(
            entry, data={CONF_HOST: "192.168.0.177"}
        )

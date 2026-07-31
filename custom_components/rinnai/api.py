"""API client for Rinnai Water Heater."""

import logging
from typing import Any

import aiohttp

from .const import RAW_TO_TEMP

_LOGGER = logging.getLogger(__name__)


class RinnaiWaterHeaterApiError(Exception):
    """Exception to indicate an API error."""


class RinnaiWaterHeaterApi:
    """Client to communicate with the Rinnai Water Heater API."""

    def __init__(self, host: str, session: aiohttp.ClientSession) -> None:
        """Initialize the API client."""
        self.host = host
        self.session = session
        self.base_url = f"http://{host}"

    async def _async_request(self, endpoint: str) -> str:
        """Make an HTTP request and return the response text."""
        url = f"{self.base_url}{endpoint}"
        try:
            async with self.session.get(url, timeout=5) as response:
                if response.status != 200:
                    raise RinnaiWaterHeaterApiError(
                        f"HTTP error {response.status} from {url}"
                    )
                return await response.text()
        except (TimeoutError, aiohttp.ClientError) as err:
            raise RinnaiWaterHeaterApiError(
                f"Connection error to {url}: {err}"
            ) from err

    async def async_get_mac(self) -> str:
        """Get the MAC address of the device."""
        mac = await self._async_request("/connect")
        return mac.strip()

    async def async_get_model(self) -> str:
        """Get the model of the device."""
        model = await self._async_request("/read_modelo")
        return model.strip()

    async def async_get_bus_data(self) -> dict[str, Any]:
        """Fetch status data from the device /bus endpoint."""
        data_str = await self._async_request("/bus")
        parts = [p.strip() for p in data_str.split(",")]
        if len(parts) < 38:
            raise RinnaiWaterHeaterApiError(
                f"Unexpected response format from /bus: {data_str}"
            )

        try:
            status_code = int(parts[0])
            combustion_active = parts[2] == "1"
            number_of_activations = int(parts[3])
            combustion_hours = int(parts[4])
            standby_hours = int(parts[5])
            fan_self_diagnostic = int(parts[6]) / 10.0
            fan_rotation_hz = int(parts[7]) / 10.0
            pov_current_ma = int(parts[8]) / 10.0
            power_kcal_min = int(parts[9]) / 100.0
            inlet_temp = int(parts[10]) / 100.0
            outlet_temp = int(parts[11]) / 100.0
            actual_flow = int(parts[12]) / 100.0
            min_flow_activation = int(parts[13]) / 100.0
            min_flow_deactivation = int(parts[14]) / 100.0
            target_temp = int(parts[15]) / 100.0
            mac_address = parts[25]
            wifi_signal = int(parts[37])
        except (ValueError, IndexError) as err:
            raise RinnaiWaterHeaterApiError(
                f"Error parsing /bus payload: {err}"
            ) from err

        return {
            "status_code": status_code,
            "is_on": status_code in (41, 42),
            "combustion_active": combustion_active,
            "number_of_activations": number_of_activations,
            "combustion_hours": combustion_hours,
            "standby_hours": standby_hours,
            "fan_self_diagnostic": fan_self_diagnostic,
            "fan_rotation_hz": fan_rotation_hz,
            "pov_current_ma": pov_current_ma,
            "power_kcal_min": power_kcal_min,
            "inlet_temp": inlet_temp,
            "outlet_temp": outlet_temp,
            "actual_flow": actual_flow,
            "min_flow_activation": min_flow_activation,
            "min_flow_deactivation": min_flow_deactivation,
            "target_temp": target_temp,
            "mac_address": mac_address,
            "wifi_signal": wifi_signal,
        }

    def update_host(self, new_host: str) -> None:
        """Update host and base url for API client."""
        self.host = new_host
        self.base_url = f"http://{new_host}"

    async def async_toggle_power(self) -> dict[str, Any]:
        """Toggle power status and return parsed response."""
        res_str = await self._async_request("/lig")
        return parse_tela_data(res_str)

    async def async_increment_temp(self) -> dict[str, Any]:
        """Increment target temperature by 1 degree and return parsed response."""
        res_str = await self._async_request("/inc")
        return parse_tela_data(res_str)

    async def async_decrement_temp(self) -> dict[str, Any]:
        """Decrement target temperature by 1 degree and return parsed response."""
        res_str = await self._async_request("/dec")
        return parse_tela_data(res_str)

    async def async_discover_devices_udp(
        self, hass: Any, local_ip: str | None = None
    ) -> list[str]:
        """Perform UDP broadcast discovery to find Rinnai device IPs."""
        return await hass.async_add_executor_job(
            discover_devices_udp_sync, local_ip, 5.0
        )


def discover_devices_udp_sync(
    local_ip: str | None = None, timeout: float = 5.0
) -> list[str]:
    """Perform a UDP broadcast to discover Rinnai water heater IPs on port 8080."""
    import socket

    discovered_ips: list[str] = []
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        if local_ip:
            sock.bind((local_ip, 0))
        else:
            sock.bind(("", 0))
        sock.settimeout(timeout)
        _LOGGER.debug("Sending UDP broadcast 'IP' to port 8080...")
        sock.sendto(b"IP", ("<broadcast>", 8080))

        while True:
            try:
                data, addr = sock.recvfrom(1024)
                ip = addr[0]
                _LOGGER.debug("Received UDP broadcast response from %s: %r", ip, data)
                if ip not in discovered_ips:
                    discovered_ips.append(ip)
            except TimeoutError:
                break
    except OSError as err:
        _LOGGER.warning("Error during UDP broadcast discovery: %s", err)
    finally:
        sock.close()

    return discovered_ips


def parse_tela_data(data_str: str) -> dict[str, Any]:
    """Parse comma-separated data from control endpoints (same as /tela_)."""
    parts = [p.strip() for p in data_str.split(",")]
    if len(parts) < 11:
        raise RinnaiWaterHeaterApiError(
            f"Unexpected response format from control endpoint: {data_str}"
        )

    try:
        status_code = int(parts[0])
        combustion_active = parts[2] == "1"
        combustion_hours = int(parts[3])
        standby_hours = int(parts[4])
        # Position 7 is configured temperature
        raw_temp = int(parts[7])
        target_temp = RAW_TO_TEMP.get(raw_temp, float(raw_temp + 32))
    except (ValueError, IndexError) as err:
        raise RinnaiWaterHeaterApiError(
            f"Error parsing control payload: {err}"
        ) from err

    return {
        "status_code": status_code,
        "is_on": status_code in (41, 42),
        "combustion_active": combustion_active,
        "combustion_hours": combustion_hours,
        "standby_hours": standby_hours,
        "target_temp": target_temp,
    }

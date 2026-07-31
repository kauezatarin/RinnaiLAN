"""Config flow for the Rinnai Water Heater Integration integration."""

import logging
import re
from typing import Any

import voluptuous as vol
from homeassistant.components.network import async_get_source_ip
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_HOST
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import RinnaiWaterHeaterApi, RinnaiWaterHeaterApiError
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


def parse_invite_code(invite_code: str, local_ip: str | None) -> str:
    """Parse invite code and construct device IP using Home Assistant's local IP prefix.

    Raises InvalidInviteCode or NetworkPrefixError.
    """
    if not invite_code or not re.match(r"^\d{6}$", invite_code):
        raise InvalidInviteCode

    last_octet_str = invite_code[:3]
    try:
        last_octet = int(last_octet_str)
    except ValueError:
        raise InvalidInviteCode from None

    if not (0 <= last_octet <= 255):
        raise InvalidInviteCode

    if not local_ip:
        raise NetworkPrefixError

    parts = local_ip.split(".")
    if len(parts) != 4:
        raise NetworkPrefixError

    return f"{parts[0]}.{parts[1]}.{parts[2]}.{last_octet}"


class RinnaiWaterHeaterConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Rinnai Water Heater Integration."""

    VERSION = 1

    async def _async_validate_and_create(self, host: str) -> ConfigFlowResult | None:
        """Validate the host, check unique ID, and create entry."""
        try:
            session = async_get_clientsession(self.hass)
            api = RinnaiWaterHeaterApi(host, session)
            mac = await api.async_get_mac()
        except RinnaiWaterHeaterApiError:
            return None

        await self.async_set_unique_id(mac)
        self._abort_if_unique_id_configured()

        return self.async_create_entry(
            title=f"Aquecedor {host}",
            data={
                CONF_HOST: host,
            },
        )

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step where user selects configuration method."""
        return self.async_show_menu(
            step_id="user",
            menu_options=["manual", "invite"],
        )

    async def async_step_manual(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle manual configuration."""
        errors: dict[str, str] = {}
        if user_input is not None:
            host = user_input[CONF_HOST].strip()
            if not host:
                errors["base"] = "cannot_connect"
            else:
                result = await self._async_validate_and_create(host)
                if result is not None:
                    return result
                errors["base"] = "cannot_connect"

        return self.async_show_form(
            step_id="manual",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_HOST): str,
                }
            ),
            errors=errors,
        )

    async def async_step_invite(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle configuration via invite code."""
        errors: dict[str, str] = {}
        if user_input is not None:
            invite_code = user_input["invite_code"].strip()
            try:
                local_ip = await async_get_source_ip(self.hass)
                host = parse_invite_code(invite_code, local_ip)
            except InvalidInviteCode:
                errors["base"] = "invalid_invite_code"
            except NetworkPrefixError:
                errors["base"] = "network_prefix_not_found"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception(
                    "Unexpected exception during invite code verification"
                )
                errors["base"] = "unknown"
            else:
                result = await self._async_validate_and_create(host)
                if result is not None:
                    return result
                errors["base"] = "cannot_connect"

        return self.async_show_form(
            step_id="invite",
            data_schema=vol.Schema(
                {
                    vol.Required("invite_code"): str,
                }
            ),
            errors=errors,
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidInviteCode(HomeAssistantError):
    """Error to indicate the invite code is invalid."""


class NetworkPrefixError(HomeAssistantError):
    """Error to indicate the network prefix could not be found."""

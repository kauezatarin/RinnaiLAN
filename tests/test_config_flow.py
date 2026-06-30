"""Test the Rinnai Water Heater Integration config flow."""

from unittest.mock import AsyncMock, patch

from custom_components.rinnai.const import DOMAIN
import pytest

from homeassistant import config_entries
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType


async def test_manual_flow_success(
    hass: HomeAssistant, mock_setup_entry: AsyncMock
) -> None:
    """Test manual configuration flow is successful."""
    # Initialize the flow
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.MENU
    assert result["step_id"] == "user"

    # Select the manual configuration step
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"next_step_id": "manual"},
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "manual"
    assert result["errors"] == {}

    # Submit valid manual input
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_HOST: "192.168.0.50",
        },
    )
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Aquecedor 192.168.0.50"
    assert result["data"] == {
        CONF_HOST: "192.168.0.50",
    }
    assert len(mock_setup_entry.mock_calls) == 1


async def test_manual_flow_empty_host(
    hass: HomeAssistant, mock_setup_entry: AsyncMock
) -> None:
    """Test manual flow shows error for empty host and then recovers."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"next_step_id": "manual"},
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "manual"

    # Submit empty host
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_HOST: "   ",
        },
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "cannot_connect"}

    # Recover with valid input
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_HOST: "192.168.0.50",
        },
    )
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Aquecedor 192.168.0.50"
    assert result["data"] == {
        CONF_HOST: "192.168.0.50",
    }
    assert len(mock_setup_entry.mock_calls) == 1


@pytest.mark.parametrize(
    ("invite_code", "expected_ip"),
    [
        pytest.param("177839", "192.168.0.177", id="valid_invite_177"),
        pytest.param("005123", "192.168.0.5", id="valid_invite_leading_zeros"),
        pytest.param("255999", "192.168.0.255", id="valid_invite_max_octet"),
    ],
)
async def test_invite_flow_success(
    hass: HomeAssistant,
    mock_setup_entry: AsyncMock,
    invite_code: str,
    expected_ip: str,
) -> None:
    """Test configuration via invite code is successful."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    # Select the invite step
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"next_step_id": "invite"},
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "invite"

    with patch(
        "custom_components.rinnai.config_flow.async_get_source_ip",
        return_value="192.168.0.10",
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"invite_code": invite_code},
        )
        await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == f"Aquecedor {expected_ip}"
    assert result["data"] == {
        CONF_HOST: expected_ip,
    }
    assert len(mock_setup_entry.mock_calls) == 1


@pytest.mark.parametrize(
    ("invalid_code", "error_key"),
    [
        pytest.param("123", "invalid_invite_code", id="too_short"),
        pytest.param("1234567", "invalid_invite_code", id="too_long"),
        pytest.param("17a839", "invalid_invite_code", id="non_numeric"),
        pytest.param("256839", "invalid_invite_code", id="invalid_octet_256"),
    ],
)
async def test_invite_flow_invalid_code(
    hass: HomeAssistant,
    mock_setup_entry: AsyncMock,
    invalid_code: str,
    error_key: str,
) -> None:
    """Test invite flow handles invalid codes and recovers."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"next_step_id": "invite"},
    )
    assert result["type"] is FlowResultType.FORM

    with patch(
        "custom_components.rinnai.config_flow.async_get_source_ip",
        return_value="192.168.0.10",
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"invite_code": invalid_code},
        )
        assert result["type"] is FlowResultType.FORM
        assert result["errors"] == {"base": error_key}

        # Recover with valid input
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"invite_code": "177839"},
        )
        await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Aquecedor 192.168.0.177"
    assert result["data"] == {
        CONF_HOST: "192.168.0.177",
    }
    assert len(mock_setup_entry.mock_calls) == 1


@pytest.mark.parametrize(
    ("local_ip", "error_key"),
    [
        pytest.param(None, "network_prefix_not_found", id="no_local_ip"),
        pytest.param("invalid_ip", "network_prefix_not_found", id="invalid_format"),
        pytest.param("fe80::1", "network_prefix_not_found", id="ipv6_unsupported"),
    ],
)
async def test_invite_flow_network_prefix_error(
    hass: HomeAssistant,
    mock_setup_entry: AsyncMock,
    local_ip: str | None,
    error_key: str,
) -> None:
    """Test invite flow handles missing or invalid network prefix."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"next_step_id": "invite"},
    )
    assert result["type"] is FlowResultType.FORM

    with patch(
        "custom_components.rinnai.config_flow.async_get_source_ip",
        return_value=local_ip,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"invite_code": "177839"},
        )
        assert result["type"] is FlowResultType.FORM
        assert result["errors"] == {"base": error_key}

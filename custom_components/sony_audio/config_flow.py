"""Config flow for Sony Audio."""

from __future__ import annotations

import asyncio
from typing import Any
from urllib.parse import urlparse

from songpal import Device, SongpalException
import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.helpers.service_info.ssdp import SsdpServiceInfo

from .const import CONF_ENDPOINT, DOMAIN


async def _async_validate_endpoint(endpoint: str) -> tuple[str, str]:
    """Validate an endpoint and return device title and stable ID."""
    device = Device(endpoint)
    async with asyncio.timeout(10):
        await device.get_supported_methods()
        interface_info, system_info = await asyncio.gather(
            device.get_interface_information(), device.get_system_info()
        )
    hardware_id = (
        system_info.macAddr or system_info.wirelessMacAddr or endpoint
    ).lower()
    return interface_info.modelName, hardware_id


class SonyAudioConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a Sony Audio config flow."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle manual setup."""
        errors: dict[str, str] = {}
        if user_input is not None:
            endpoint = user_input[CONF_ENDPOINT].strip().rstrip("/")
            try:
                title, hardware_id = await _async_validate_endpoint(endpoint)
            except (SongpalException, TimeoutError, ValueError):
                errors["base"] = "cannot_connect"
            else:
                await self.async_set_unique_id(hardware_id)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=title, data={CONF_ENDPOINT: endpoint}
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_ENDPOINT,
                        default=(user_input or {}).get(CONF_ENDPOINT, ""),
                    ): str
                }
            ),
            errors=errors,
        )

    async def async_step_ssdp(
        self, discovery_info: SsdpServiceInfo
    ) -> ConfigFlowResult:
        """Handle SSDP discovery."""
        scalar_info = discovery_info.upnp.get("X_ScalarWebAPI_DeviceInfo")
        if not scalar_info:
            return self.async_abort(reason="not_supported")

        service_types = scalar_info["X_ScalarWebAPI_ServiceList"][
            "X_ScalarWebAPI_ServiceType"
        ]
        if "videoScreen" in service_types or "video" in service_types:
            return self.async_abort(reason="not_supported")

        endpoint = scalar_info["X_ScalarWebAPI_BaseURL"]
        try:
            title, hardware_id = await _async_validate_endpoint(endpoint)
        except (SongpalException, TimeoutError, ValueError):
            return self.async_abort(reason="cannot_connect")

        await self.async_set_unique_id(hardware_id)
        self._abort_if_unique_id_configured()
        self.context["title_placeholders"] = {
            "name": title,
            "host": urlparse(endpoint).hostname or endpoint,
        }
        self._discovered_endpoint = endpoint
        self._discovered_title = title
        return await self.async_step_confirm()

    async def async_step_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Confirm an SSDP-discovered receiver."""
        if user_input is not None:
            return self.async_create_entry(
                title=self._discovered_title,
                data={CONF_ENDPOINT: self._discovered_endpoint},
            )
        return self.async_show_form(step_id="confirm")

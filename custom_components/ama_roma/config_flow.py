"""Asks for street and house number, and checks AMA has a schedule for them."""
from __future__ import annotations

from typing import Any

import aiohttp
import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import AmaClient, AmaError
from .const import CONF_NUMBER, CONF_STREET, DOMAIN


class AmaConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            client = AmaClient(async_get_clientsession(self.hass))
            number = user_input[CONF_NUMBER].strip()
            try:
                street = await client.find_street(user_input[CONF_STREET])
                if street is None:
                    errors[CONF_STREET] = "street_not_found"
                else:
                    await client.schedule(street, number)
            except AmaError:
                errors["base"] = "no_schedule"
            except (aiohttp.ClientError, TimeoutError):
                errors["base"] = "cannot_connect"

            if not errors:
                await self.async_set_unique_id(f"{street}_{number}".lower())
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=f"{street.title()} {number}",
                    data={CONF_STREET: street, CONF_NUMBER: number},
                )

        return self.async_show_form(
            step_id="user",
            data_schema=self.add_suggested_values_to_schema(
                vol.Schema({vol.Required(CONF_STREET): str, vol.Required(CONF_NUMBER): str}),
                user_input,
            ),
            errors=errors,
        )

"""Config flow voor Moto Onderhoud."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.const import CONF_NAME
from homeassistant.core import callback
from homeassistant.helpers import selector

from .const import (
    CONF_NOTIFY_SERVICE,
    CONF_ODOMETER,
    CONF_WARN_DAYS,
    CONF_WARN_KM,
    DEFAULT_WARN_DAYS,
    DEFAULT_WARN_KM,
    DOMAIN,
)

KM_SELECTOR = selector.NumberSelector(
    selector.NumberSelectorConfig(
        min=0,
        max=1_000_000,
        step=1,
        mode=selector.NumberSelectorMode.BOX,
        unit_of_measurement="km",
    )
)
DAYS_SELECTOR = selector.NumberSelector(
    selector.NumberSelectorConfig(
        min=0,
        max=365,
        step=1,
        mode=selector.NumberSelectorMode.BOX,
        unit_of_measurement="d",
    )
)


class MotoConfigFlow(ConfigFlow, domain=DOMAIN):
    """Voeg een motor toe."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            name = user_input[CONF_NAME].strip()
            await self.async_set_unique_id(name.lower())
            self._abort_if_unique_id_configured()
            return self.async_create_entry(
                title=name,
                data={CONF_ODOMETER: float(user_input[CONF_ODOMETER])},
                options={
                    CONF_NOTIFY_SERVICE: (user_input.get(CONF_NOTIFY_SERVICE) or "").strip()
                },
            )

        schema = vol.Schema(
            {
                vol.Required(CONF_NAME, default="Motor"): selector.TextSelector(),
                vol.Required(CONF_ODOMETER, default=0): KM_SELECTOR,
                vol.Optional(CONF_NOTIFY_SERVICE): selector.TextSelector(),
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        return MotoOptionsFlow()


class MotoOptionsFlow(OptionsFlow):
    """Opties: meldingen en drempels."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            user_input[CONF_NOTIFY_SERVICE] = (
                user_input.get(CONF_NOTIFY_SERVICE) or ""
            ).strip()
            return self.async_create_entry(data=user_input)

        options = self.config_entry.options
        schema = vol.Schema(
            {
                vol.Optional(
                    CONF_NOTIFY_SERVICE,
                    description={
                        "suggested_value": options.get(CONF_NOTIFY_SERVICE, "")
                    },
                ): selector.TextSelector(),
                vol.Required(
                    CONF_WARN_KM, default=options.get(CONF_WARN_KM, DEFAULT_WARN_KM)
                ): KM_SELECTOR,
                vol.Required(
                    CONF_WARN_DAYS,
                    default=options.get(CONF_WARN_DAYS, DEFAULT_WARN_DAYS),
                ): DAYS_SELECTOR,
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema)

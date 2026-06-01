from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

import pypowerwall
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import CONF_GW_PWD, CONF_HOST, CONF_SCAN_INTERVAL, CONF_TIMEZONE, DEFAULT_SCAN_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)


class PowerwallCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self._entry = entry
        self.pw: pypowerwall.Powerwall | None = None
        interval = entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=interval),
        )

    def _create_powerwall(self) -> pypowerwall.Powerwall:
        gw_pwd = self._entry.data[CONF_GW_PWD]
        return pypowerwall.Powerwall(
            host=self._entry.data[CONF_HOST],
            password=gw_pwd[-5:],  # enables local JSON API for energy accumulation data
            gw_pwd=gw_pwd,         # also enables TEDAPI for vitals
            timezone=self._entry.data[CONF_TIMEZONE],
        )

    async def _async_update_data(self) -> dict[str, Any]:
        if self.pw is None:
            self.pw = await self.hass.async_add_executor_job(self._create_powerwall)
        try:
            aggregates = await self.hass.async_add_executor_job(
                self.pw.poll, "/api/meters/aggregates"
            )
            level = await self.hass.async_add_executor_job(self.pw.level)
            grid_status = await self.hass.async_add_executor_job(
                self.pw.grid_status, "string"
            )
            time_remaining = await self.hass.async_add_executor_job(
                self.pw.get_time_remaining
            )
            reserve = await self.hass.async_add_executor_job(self.pw.get_reserve)
            mode = await self.hass.async_add_executor_job(self.pw.get_mode)
        except Exception as err:
            raise UpdateFailed(f"Error communicating with Powerwall: {err}") from err

        return {
            "aggregates": aggregates,
            "level": level,
            "grid_status": grid_status,
            "time_remaining": time_remaining,
            "reserve": reserve,
            "mode": mode,
        }

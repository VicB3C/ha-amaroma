"""Fetches the schedule once a month and reports when AMA changes it."""
from __future__ import annotations

from dataclasses import asdict
from datetime import timedelta
import logging

import aiohttp

from homeassistant.components import persistent_notification
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.storage import Store
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import AmaClient, AmaError, Collection
from .const import CONF_NUMBER, CONF_STREET, DOMAIN

_LOGGER = logging.getLogger(__name__)
MONTHLY = timedelta(days=30)
RETRY = timedelta(hours=1)


class AmaCoordinator(DataUpdateCoordinator[list[Collection]]):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=MONTHLY, config_entry=entry)
        self.client = AmaClient(async_get_clientsession(hass))
        # Last schedule seen, kept across restarts so a change is never missed.
        self.store: Store[list[dict]] = Store(hass, 1, f"{DOMAIN}.{entry.entry_id}")

    async def _async_update_data(self) -> list[Collection]:
        entry = self.config_entry
        try:
            new = await self.client.schedule(entry.data[CONF_STREET], entry.data[CONF_NUMBER])
        except (AmaError, aiohttp.ClientError, TimeoutError) as err:
            # Without this a single failed monthly check would wait another 30 days.
            self.update_interval = RETRY
            raise UpdateFailed(str(err)) from err
        self.update_interval = MONTHLY

        rows = [asdict(c) for c in new]
        old = await self.store.async_load()
        if old is not None and old != rows:
            _LOGGER.info("AMA schedule changed for %s", entry.title)
            persistent_notification.async_create(
                self.hass,
                f"AMA ha cambiato il calendario di raccolta per {entry.title}. "
                "Il calendario in Home Assistant è già aggiornato.",
                title="AMA Roma: calendario cambiato",
                notification_id=f"{DOMAIN}_{entry.entry_id}_changed",
            )
        if old != rows:
            await self.store.async_save(rows)
        return new

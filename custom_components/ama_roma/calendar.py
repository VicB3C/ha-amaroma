"""Calendar with one all-day event per collection."""
from __future__ import annotations

from collections.abc import Iterator
from datetime import date, datetime, timedelta

from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from .api import Collection
from .const import DOMAIN
from .coordinator import AmaCoordinator


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    async_add_entities([AmaCalendar(entry.runtime_data, entry)])


def _event(c: Collection, day: date) -> CalendarEvent:
    if c.expose_by:
        description = f"Esporre entro le {c.expose_by} (raccolta porta a porta)"
    else:
        description = f"Svuotamento cassonetti {c.start}–{c.end}"
    return CalendarEvent(start=day, end=day + timedelta(days=1), summary=c.fraction, description=description)


class AmaCalendar(CoordinatorEntity[AmaCoordinator], CalendarEntity):
    _attr_has_entity_name = True
    _attr_name = None
    _attr_icon = "mdi:trash-can"

    def __init__(self, coordinator: AmaCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = entry.entry_id
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=f"Raccolta rifiuti {entry.title}",
            manufacturer="AMA Roma",
            entry_type=DeviceEntryType.SERVICE,
        )

    def _events(self, first: date, last: date) -> Iterator[CalendarEvent]:
        day = first
        while day <= last:
            for c in self.coordinator.data:
                if c.weekday == day.weekday():
                    yield _event(c, day)
            day += timedelta(days=1)

    @property
    def event(self) -> CalendarEvent | None:
        today = dt_util.now().date()
        return next(self._events(today, today + timedelta(days=7)), None)

    async def async_get_events(
        self, hass: HomeAssistant, start_date: datetime, end_date: datetime
    ) -> list[CalendarEvent]:
        return list(self._events(start_date.date(), end_date.date()))

"""Calendar with one timed event per collection."""
from __future__ import annotations

from datetime import date, datetime, time, timedelta

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


# AMA times are Rome local time, whatever time zone Home Assistant is set to.
ROME = dt_util.get_time_zone("Europe/Rome")
EVENT_DURATION = timedelta(hours=2)
# AMA bin colours, as a "color:" line that dashboard cards (e.g. ha-separate-garbage-collection-card) read.
COLORS = {
    "Carta": "#2196F3",
    "Organico": "#795548",
    "Plastica e metalli": "#FFC107",
    "Indifferenziato": "#9E9E9E",
}


def _at(day: date, hhmm: str) -> datetime:
    return datetime.combine(day, time.fromisoformat(hhmm), tzinfo=ROME)


def _event(c: Collection, day: date) -> CalendarEvent:
    # Starts at the "expose by" deadline shown on amaroma.it (street bins: when emptying starts).
    start = _at(day, c.expose_by or c.start)
    end = start + EVENT_DURATION
    if c.expose_by:
        description = f"Esporre entro le {c.expose_by} (raccolta porta a porta)"
    else:
        description = f"Svuotamento cassonetti {c.start}–{c.end}"
    if color := COLORS.get(c.fraction):
        description += f"\ncolor: {color}"
    return CalendarEvent(start=start, end=end, summary=c.fraction, description=description)


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

    def _events(self, start: datetime, end: datetime) -> list[CalendarEvent]:
        """Events overlapping [start, end), sorted by start."""
        events = []
        # Start a day early: yesterday's late pickup may still be running.
        day = start.astimezone(ROME).date() - timedelta(days=1)
        while day <= end.astimezone(ROME).date():
            events += [_event(c, day) for c in self.coordinator.data if c.weekday == day.weekday()]
            day += timedelta(days=1)
        return sorted((e for e in events if e.end > start and e.start < end), key=lambda e: e.start)

    @property
    def event(self) -> CalendarEvent | None:
        """The collection in progress, or the next one."""
        now = dt_util.now()
        return next(iter(self._events(now, now + timedelta(days=8))), None)

    async def async_get_events(
        self, hass: HomeAssistant, start_date: datetime, end_date: datetime
    ) -> list[CalendarEvent]:
        return self._events(start_date, end_date)

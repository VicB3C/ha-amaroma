"""Run: pip install pytest-homeassistant-custom-component && python3 -m pytest tests"""
import json
import pathlib
from datetime import timedelta

import pytest
from homeassistant import config_entries
from homeassistant.util import dt as dt_util
from pytest_homeassistant_custom_component.common import async_fire_time_changed

from custom_components.ama_roma.const import DOMAIN

HERE = pathlib.Path(__file__).parent
API = "https://www.amaroma.it/api/v0"


@pytest.fixture(autouse=True)
def _custom(enable_custom_integrations):
    yield


def mock_api(aioclient_mock, schedule_file):
    aioclient_mock.clear_requests()
    aioclient_mock.get(f"{API}/portal/stradario", json={"result": [{"id": "x", "label": "VIA NOMENTANA"}]})
    aioclient_mock.get(f"{API}/differenziata", json=json.loads((HERE / schedule_file).read_text()))


async def test_setup_calendar_and_change(hass, aioclient_mock):
    await hass.config.async_set_time_zone("Europe/Rome")
    mock_api(aioclient_mock, "nomentana_44.json")
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"street": "via nomentana", "number": "44"}
    )
    assert result["type"] == "create_entry"
    assert result["title"] == "Via Nomentana 44"
    assert result["data"] == {"street": "VIA NOMENTANA", "number": "44"}
    await hass.async_block_till_done()

    entity_id = "calendar.raccolta_rifiuti_via_nomentana_44"
    assert hass.states.get(entity_id) is not None
    events = await get_events(hass, entity_id, "2026-11-02 00:00:00", "2026-11-08 23:59:00")
    assert events == [
        ("2026-11-02T06:30:00+01:00", "2026-11-02T12:40:00+01:00", "Indifferenziato"),
        ("2026-11-02T14:00:00+01:00", "2026-11-02T19:55:00+01:00", "Organico"),
        ("2026-11-03T06:30:00+01:00", "2026-11-03T12:40:00+01:00", "Carta"),
        ("2026-11-04T06:30:00+01:00", "2026-11-04T12:40:00+01:00", "Plastica e metalli"),
        ("2026-11-04T14:00:00+01:00", "2026-11-04T19:55:00+01:00", "Organico"),
        ("2026-11-05T06:30:00+01:00", "2026-11-05T12:40:00+01:00", "Indifferenziato"),
        ("2026-11-06T06:30:00+01:00", "2026-11-06T12:40:00+01:00", "Carta"),
        ("2026-11-06T14:00:00+01:00", "2026-11-06T19:55:00+01:00", "Organico"),
        ("2026-11-07T06:30:00+01:00", "2026-11-07T12:40:00+01:00", "Plastica e metalli"),
    ]

    # A month later AMA returns a different schedule: calendar follows, user is notified.
    mock_api(aioclient_mock, "tuscolana_100.json")
    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(days=31))
    await hass.async_block_till_done()
    assert aioclient_mock.call_count == 1
    notes = hass.data["persistent_notification"]
    assert any("cambiato" in n["title"] for n in notes.values())

    # Street bins emptied 22:00–04:00: the event runs past midnight and is found from either day.
    after_midnight = await get_events(hass, entity_id, "2026-11-03 01:00:00", "2026-11-03 02:00:00")
    assert ("2026-11-02T22:00:00+01:00", "2026-11-03T04:00:00+01:00", "Indifferenziato") in after_midnight


async def get_events(hass, entity_id, start, end):
    resp = await hass.services.async_call(
        "calendar", "get_events",
        {"entity_id": entity_id, "start_date_time": start, "end_date_time": end},
        blocking=True, return_response=True,
    )
    return [(e["start"], e["end"], e["summary"]) for e in resp[entity_id]["events"]]


async def test_unknown_street(hass, aioclient_mock):
    aioclient_mock.get(f"{API}/portal/stradario", json={"result": []})
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"street": "via inesistente", "number": "1"}
    )
    assert result["errors"] == {"street": "street_not_found"}

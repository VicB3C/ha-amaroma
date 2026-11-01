"""Run: python3 -m pytest tests (needs only aiohttp + pytest, not Home Assistant)."""
import importlib.util
import json
import pathlib
import sys

import pytest

HERE = pathlib.Path(__file__).parent
# Load api.py alone: putting its folder on sys.path would let our calendar.py shadow the stdlib one.
_spec = importlib.util.spec_from_file_location("ama_api", HERE.parent / "custom_components/ama_roma/api.py")
api = sys.modules["ama_api"] = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(api)
AmaError, parse = api.AmaError, api.parse


def load(name):
    return json.loads((HERE / name).read_text())


def test_door_to_door():
    got = {(c.weekday, c.fraction, c.expose_by) for c in parse(load("nomentana_44.json"))}
    assert got == {
        (0, "Indifferenziato", "06:30"), (3, "Indifferenziato", "06:30"),
        (1, "Carta", "06:30"), (4, "Carta", "06:30"),
        (2, "Plastica e metalli", "06:30"), (5, "Plastica e metalli", "06:30"),
        (0, "Organico", "14:00"), (2, "Organico", "14:00"), (4, "Organico", "14:00"),
    }


def test_street_bins():
    got = parse(load("tuscolana_100.json"))
    assert got and all(c.expose_by is None and c.start for c in got)


def test_unknown_address():
    payload = {"result": [{"RESPONSE": [{"ESITO": "KO", "MESSAGE": "Tratta non definita"}], "PAP": []}]}
    with pytest.raises(AmaError, match="Tratta non definita"):
        parse(payload)

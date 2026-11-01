"""Client for the AMA Roma waste-collection API (the one behind amaroma.it/it/servizi/calendario-svuotamento-contenitori)."""
from __future__ import annotations

from dataclasses import dataclass

import aiohttp

BASE_URL = "https://www.amaroma.it/api/v0"
# Every list the API can return: door-to-door (PAP*) and street bins (RACC_STRAD*).
SECTIONS = ("PAP", "DUALE_PAP", "PAP_DUALE_STRAD", "RACC_STRAD", "RACC_STRAD_NEW")
FRACTIONS = {
    "RIFIUTO INDIFFERENZIATO": "Indifferenziato",
    "RIFIUTO RD CARTA": "Carta",
    "RIFIUTO RD MULTIMATERIALE": "Plastica e metalli",
    "RIFIUTO RD UMIDO": "Organico",
}


class AmaError(Exception):
    """The API answered, but has no schedule for this address."""


@dataclass(frozen=True)
class Collection:
    fraction: str
    weekday: int  # 0 = Monday, like date.weekday()
    expose_by: str | None  # "20:00" for door-to-door, None for street bins
    start: str  # "HH:MM"
    end: str


def _hhmm(value: str | None) -> str:
    return f"{value[:2]}:{value[2:4]}" if value else ""


def parse(payload: dict) -> list[Collection]:
    result = payload["result"][0]
    found = {
        Collection(
            fraction=FRACTIONS.get(row["DESCR_FRAZIONE"], row["DESCR_FRAZIONE"].removeprefix("RIFIUTO ").title()),
            # API uses 1 = Monday; % 7 also maps a possible 0 or 7 to Sunday.
            weekday=(int(row["GIORNO_RACCOLTA"]) - 1) % 7,
            expose_by=row.get("ORARIO_FINE_ESP") or None,
            start=_hhmm(row.get("ORA_INIZIO")),
            end=_hhmm(row.get("ORA_FINE")),
        )
        for section in SECTIONS
        for row in result.get(section) or []
    }
    if not found:
        messages = {r.get("MESSAGE") for r in result.get("RESPONSE") or []}
        raise AmaError(", ".join(filter(None, messages)) or "Nessun calendario per questo indirizzo")
    return sorted(found, key=lambda c: (c.weekday, c.fraction))


class AmaClient:
    def __init__(self, session: aiohttp.ClientSession) -> None:
        self._session = session

    async def _get(self, path: str, **params: str) -> dict:
        async with self._session.get(
            f"{BASE_URL}/{path}", params=params, timeout=aiohttp.ClientTimeout(total=30)
        ) as resp:
            resp.raise_for_status()
            return await resp.json(content_type=None)

    async def find_street(self, text: str) -> str | None:
        """Return AMA's official street name for what the user typed."""
        data = await self._get("portal/stradario", via=text.strip(), size="5")
        labels = [s["label"] for s in data.get("result") or []]
        exact = [l for l in labels if l.casefold() == text.strip().casefold()]
        return (exact or labels or [None])[0]

    async def schedule(self, street: str, number: str) -> list[Collection]:
        return parse(await self._get("differenziata", via=street, civico=number.strip()))

"""Lokale TCP-Kommunikation mit dem 4Heat-WLAN-Modul.

Protokoll (aus der App "RW Smart Fire" abgeleitet):
- TCP, Port 80, pro Anfrage eine eigene Verbindung
- Anfrage/Antwort sind JSON-Listen aus Strings, z. B. ["SEL","0"]
- Werte sind 18-stellige Codes: <Marker><Typ+ID 5-stellig><Wert 12-stellig>
  z. B. "J30017000000000045" = Parameter 30017, Wert 45
  Typziffer 5 = Dezimalwert (x100), "-" im Wertteil = negativ
- Schreiben: ["SEC","<anzahl>","B20813000000000004", ...]
"""

from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass, field

_LOGGER = logging.getLogger(__name__)

CONNECT_TIMEOUT = 5
READ_TIMEOUT = 8
SEND_DELAY = 0.5  # die App wartet nach dem Verbinden 500 ms vor dem Senden
RETRIES = 3
PAUSE_BETWEEN = 1.5  # Pause zwischen zwei Verbindungen – das Modul verkraftet keine schnelle Folge


class FourHeatError(Exception):
    """Allgemeiner Kommunikationsfehler."""


class FourHeatConnectError(FourHeatError):
    """Verbindung kam nicht zustande – es wurde nichts gesendet."""


@dataclass
class Reading:
    """Ein einzelner Wert aus der SEL-Antwort."""

    marker: str
    pid: str
    raw: str
    value: float | int

    @property
    def code(self) -> str:
        return f"{self.marker}{self.pid}{self.raw}"


@dataclass
class StoveData:
    """Alle aktuell gemeldeten Werte."""

    readings: dict[str, Reading] = field(default_factory=dict)

    def get(self, pid: str) -> float | int | None:
        r = self.readings.get(pid)
        return None if r is None else r.value


def parse_code(code: str) -> Reading | None:
    """18-stelligen Code zerlegen."""
    if len(code) != 18:
        return None
    marker, pid, raw = code[0], code[1:6], code[6:]
    if not pid.isdigit():
        return None
    neg = "-" in raw
    digits = raw.replace("-", "")
    if not digits.isdigit():
        return None
    num: float | int = int(digits)
    if pid[0] == "5":
        num = num / 100
    if neg:
        num = -num
    return Reading(marker=marker, pid=pid, raw=raw, value=num)


def build_write_code(pid: str, value: int, marker: str = "B") -> str:
    """Schreib-Code bauen (nur ganze, nicht negative Werte)."""
    if value < 0 or value > 999_999_999_999:
        raise ValueError("Wert außerhalb des gültigen Bereichs")
    if len(pid) != 5 or not pid.isdigit():
        raise ValueError("Ungültige Parameter-ID")
    return f"{marker}{pid}{value:012d}"


def _parse_list(text: str) -> list[str]:
    text = text.strip().strip("\x00")
    try:
        data = json.loads(text)
    except json.JSONDecodeError as err:
        raise FourHeatError(f"Ungültige Antwort: {text[:80]!r}") from err
    if not isinstance(data, list) or not data:
        raise FourHeatError(f"Unerwartete Antwort: {text[:80]!r}")
    return [str(x) for x in data]


class FourHeatClient:
    """Client für ein 4Heat-Modul."""

    def __init__(self, host: str, port: int = 80) -> None:
        self.host = host
        self.port = port
        self._lock = asyncio.Lock()

    async def _exchange_once(self, payload: str, allow_empty: bool = False) -> list[str]:
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(self.host, self.port), CONNECT_TIMEOUT
            )
        except (OSError, asyncio.TimeoutError) as err:
            raise FourHeatConnectError(f"Verbindung fehlgeschlagen: {err}") from err
        try:
            await asyncio.sleep(SEND_DELAY)
            writer.write(payload.encode("ascii"))
            await writer.drain()
            buf = b""
            loop = asyncio.get_running_loop()
            deadline = loop.time() + READ_TIMEOUT
            while True:
                remaining = deadline - loop.time()
                if remaining <= 0:
                    break
                try:
                    chunk = await asyncio.wait_for(reader.read(4096), remaining)
                except asyncio.TimeoutError:
                    break
                if not chunk:
                    break
                buf += chunk
                if buf.rstrip().endswith(b"]"):
                    try:
                        json.loads(buf.decode("ascii", "replace"))
                        break
                    except json.JSONDecodeError:
                        continue
            if not buf.strip():
                if allow_empty:
                    # Das Modul führt Befehle oft aus, ohne zu antworten
                    _LOGGER.debug("Leere Antwort auf %s – gilt als angenommen", payload)
                    return []
                raise FourHeatError("Leere Antwort")
            return _parse_list(buf.decode("ascii", "replace"))
        finally:
            writer.close()
            try:
                await writer.wait_closed()
            except Exception:  # noqa: BLE001
                pass

    async def exchange(self, payload: str, is_command: bool = False) -> list[str]:
        """Anfrage senden. Anfragen laufen nie parallel.

        Lesen wird bei Fehlern wiederholt. Befehle werden nur wiederholt,
        wenn die Verbindung gar nicht zustande kam – sonst könnte der Ofen
        einen Befehl doppelt bekommen.
        """
        async with self._lock:
            last: Exception | None = None
            for attempt in range(1, RETRIES + 1):
                try:
                    try:
                        resp = await self._exchange_once(payload, allow_empty=is_command)
                    finally:
                        await asyncio.sleep(PAUSE_BETWEEN)
                    if resp and resp[0] == "ERR":
                        raise FourHeatError(f"Modul meldet Fehler: {resp}")
                    return resp
                except FourHeatConnectError as err:
                    last = err
                except (OSError, asyncio.TimeoutError, FourHeatError) as err:
                    if is_command:
                        raise FourHeatError(f"Befehl fehlgeschlagen: {err}") from err
                    last = err
                    _LOGGER.debug("Versuch %s/%s fehlgeschlagen: %s", attempt, RETRIES, err)
                    await asyncio.sleep(3 * attempt)
            raise FourHeatError(f"Keine Antwort von {self.host}: {last}")

    async def read_all(self, extra: list[str] | None = None) -> StoveData:
        resp = await self.exchange('["SEL","0"]')
        if not resp or resp[0] != "SEL":
            raise FourHeatError(f"Unerwartete Antwort auf SEL: {resp[:3]}")
        data = StoveData()
        for code in resp[2:]:
            r = parse_code(code)
            if r is not None:
                data.readings[r.pid] = r
        if extra:
            missing = [p for p in extra if p not in data.readings]
            if missing:
                try:
                    codes = [f"I{p}000000000000" for p in missing]
                    payload = json.dumps(["SEC", str(len(codes)), *codes], separators=(",", ":"))
                    ext = await self.exchange(payload)
                    for code in ext[2:] if ext and ext[0] == "SEC" else []:
                        r = parse_code(code)
                        if r is not None and r.pid in missing:
                            data.readings[r.pid] = r
                except FourHeatError as err:
                    _LOGGER.debug("Zusatzwerte nicht gelesen: %s", err)
        return data

    async def send_codes(self, *codes: str) -> list[str]:
        """Einen oder mehrere Codes schreiben (SEC)."""
        payload = json.dumps(["SEC", str(len(codes)), *codes], separators=(",", ":"))
        _LOGGER.info("Sende an 4Heat: %s", payload)
        return await self.exchange(payload, is_command=True)

    async def read_codes(self, pids: list[str]) -> dict[str, float | int | None]:
        """Einzelne Info-Werte gezielt lesen (wie die App: SEC mit I-Codes).

        Nur Lese-Anfragen (I-Code), Bereich 1xxxx–6xxxx. Schreibt nie.
        """
        for pid in pids:
            if len(pid) != 5 or not pid.isdigit() or pid[0] not in "123456":
                raise ValueError(f"Nur Parameter 1xxxx–6xxxx erlaubt: {pid}")
        codes = [f"I{pid}000000000000" for pid in pids]
        payload = json.dumps(["SEC", str(len(codes)), *codes], separators=(",", ":"))
        resp = await self.exchange(payload)
        result: dict[str, float | int | None] = {pid: None for pid in pids}
        values = resp[2:] if resp and resp[0] == "SEC" else []
        for code in values:
            r = parse_code(code)
            if r is not None and r.pid in result:
                result[r.pid] = r.value
        if not any(v is not None for v in result.values()):
            _LOGGER.debug("Antwort auf %s: %s", payload, resp)
        return result


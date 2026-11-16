"""Konstanten für die Robin-Wood-/4Heat-Integration."""

from __future__ import annotations

DOMAIN = "robinwood"

CONF_SCAN_INTERVAL = "scan_interval"
DEFAULT_PORT = 80
DEFAULT_SCAN_INTERVAL = 30  # Sekunden
MIN_SCAN_INTERVAL = 15

# Lokale Befehle (aus der App "RW Smart Fire" abgeleitet)
CMD_READ_ALL = '["SEL","0"]'
CODE_ON = "J30253000000000001"
CODE_OFF = "J30254000000000001"
CODE_UNLOCK = "J30255000000000001"

# Parameter-IDs (5-stellig, inkl. Typziffer)
P_STATUS = "30001"
P_ERROR = "30002"
P_EXHAUST = "30005"
P_PUFFER = "30012"
P_WATER = "30017"
P_AIRFLOW = "30026"
P_DEPRESSION = "30033"
P_RETURN = "30040"
P_OUTDOOR = "30044"
P_POWER_SET = "20813"  # Verbrennungsleistung Pellet
P_POWER_MAX = "20211"  # Anzahl Leistungsstufen
P_POWER_MIN = "20212"
P_POWER_WOOD = "20803"
P_THERMOSTAT = "20180"
P_COMBUSTION = "30011"

# 20813: Rohwert 1..n = P1..Pn, n+1 = Auto (n = Parameter 20211)

STATUS_TEXT: dict[int, str] = {
    0: "Aus",
    1: "Check-Up",
    2: "Zündung",
    3: "Stabilisierung",
    4: "Zündung",
    5: "Normalbetrieb",
    6: "Modulation",
    7: "Abschaltung",
    8: "Sicherheit",
    9: "Störung (Block)",
    10: "Wiederzündung",
    11: "Standby",
    30: "Zündung",
    31: "Zündung",
    32: "Zündung",
    33: "Zündung",
    34: "Zündung",
}

# Status, in denen der Ofen als "eingeschaltet" gilt
STATUS_ON = {1, 2, 3, 4, 5, 6, 10, 11, 30, 31, 32, 33, 34}
STATUS_BLOCK = 9

ERROR_TEXT: dict[int, str] = {
    0: "Kein Fehler",
    3: "Abschaltung wegen sinkender Abgastemperatur (keine Pellets?)",
}

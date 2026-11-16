# Robin Wood Pellet Stove (4Heat local) for Home Assistant

[![Validate](https://github.com/TeyPay-oss/robinwood-ha/actions/workflows/validate.yml/badge.svg)](https://github.com/TeyPay-oss/robinwood-ha/actions/workflows/validate.yml)

Local control of **Robin Wood pellet stoves / boilers** that use the **4Heat Wi‑Fi module** (the module behind the *RW Smart Fire* app). No cloud: Home Assistant talks to the module directly over TCP port 80 in your home network.

*Deutsch: siehe [unten](#deutsch).*

> ⚠️ **Unofficial project.** Not affiliated with Robin Wood, 4Heat or Tiemme. The protocol was derived from the official app for interoperability. This integration can switch your heating appliance on and off and change its power level — **use at your own risk** and only on equipment you are responsible for.

## Features

| Entity | Description |
|---|---|
| `switch` **Stove** | on / off |
| `select` **Combustion power** | P1 … P5 or Auto (as on the display); attribute `aktuell` shows the level currently running |
| `sensor` **Combustion power (current)** | level the stove actually runs at, also in Auto mode |
| `button` **Acknowledge fault** | unlock after a "Block" |
| `binary_sensor` **Fault** | on when an error or block is active |
| `sensor` status, error | as text |
| `sensor` temperatures | boiler, buffer, exhaust, return, outdoor sensor |
| `sensor` fan speed (rpm), auger run time (s), air flow, draught | |
| `button` **Refresh now** | immediate poll |
| Diagnostics | every other parameter the module reports, as raw values (disabled by default) |
| Action `robinwood.parameter_lesen` | read arbitrary info parameters (3xxxx/5xxxx) – read only, useful to map other models |

Tested with a Robin Wood RW 8‑35 pellet boiler. Other stoves with a 4Heat module may work but parameter numbers can differ — issues with your findings are welcome.

## Installation

1. Home Assistant 2026.11+: **Settings → Marketplace**, search for *Robin Wood*.
   (Until the repository is in the default catalog: add `https://github.com/TeyPay-oss/robinwood-ha` as a custom repository of type *Integration*.)
2. Install and restart Home Assistant.
3. **Settings → Devices & services → Add integration → Robin Wood** and enter the IP address of the 4Heat module.

**Tip:** give the module a fixed IP address in your router. Host and polling interval can be changed later under *Configure*.

## Notes

- The module accepts only one client at a time and does not like rapid connections. Close the app while HA polls and keep the polling interval at 60 s or more if you see gaps.
- Do not run this integration together with other 4Heat integrations against the same module.

## Protocol (short)

- Read all configured values: `["SEL","0"]` → list of 18‑character codes `<marker><5-digit id><12-digit value>` (type digit 5 = value ×100, `-` = negative).
- Read specific info values: `["SEC","n","I30025000000000000",…]`
- Write: `["SEC","1","B20813000000000004"]`; on `J30253…1`, off `J30254…1`, unlock `J30255…1`.

---

## Deutsch

Lokale Integration für Robin-Wood-Pelletöfen/-kessel mit **4Heat-WLAN-Modul** (das Modul der App *RW Smart Fire*). Keine Cloud – HA spricht direkt per TCP (Port 80) mit dem Modul.

> ⚠️ **Inoffizielles Projekt**, ohne Verbindung zu Robin Wood, 4Heat oder Tiemme. Die Integration kann die Heizung ein-/ausschalten und die Leistung ändern – **Nutzung auf eigene Gefahr**.

**Installation:** Einstellungen → Marketplace → „Robin Wood“ installieren, HA neu starten, dann unter *Geräte & Dienste → Integration hinzufügen → Robin Wood* die IP des Moduls eintragen. Am besten im Router eine feste IP für das Modul vergeben; IP und Abfrageintervall lassen sich später unter *Konfigurieren* ändern.

**Hinweise:** Das Modul verträgt nur einen Client gleichzeitig und keine schnellen Verbindungsfolgen – App beim Betrieb schließen, Abfrageintervall ≥ 60 s.

## License

MIT – see [LICENSE](LICENSE).

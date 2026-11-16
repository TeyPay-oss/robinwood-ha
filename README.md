# Robin Wood Pelletofen (4Heat lokal) für Home Assistant

Lokale Integration für Robin-Wood-Pelletöfen mit dem **4Heat-WLAN-Modul**, also dem Modul, das auch die App „RW Smart Fire“ nutzt. Es gibt keine Cloud: HA spricht direkt per TCP (Port 80) mit dem Modul im Heimnetz.

## Funktionen

| Entität | Funktion |
|---|---|
| `switch` **Ofen** | Ein / Aus |
| `select` **Leistungsstufe** | Stufe 1 … n (n vom Ofen gemeldet) |
| `button` **Störung quittieren** | Entsperren nach „Block“ |
| `binary_sensor` **Störung** | an bei Fehler oder Block |
| `sensor` Status, Fehler | als Klartext |
| `sensor` Temperaturen | Wasser, Puffer, Abgas, Rücklauf, Außenfühler |
| `sensor` Luftstrom, Abgasunterdruck | |
| Diagnose | alle weiteren gemeldeten Parameter als Rohwerte (standardmäßig deaktiviert) |

## Installation

1. Im Marketplace (bzw. HACS) dieses Repository als **benutzerdefiniertes Repository** vom Typ *Integration* hinzufügen.
2. **Robin Wood Pelletofen** installieren und Home Assistant neu starten.
3. Unter *Einstellungen → Geräte & Dienste → Integration hinzufügen* **Robin Wood** wählen und die IP des 4Heat-Moduls eintragen.

## Protokoll

- Lesen: `["SEL","0"]`. Die Antwort ist eine Liste aus 18-stelligen Codes `<Marker><ID 5-stellig><Wert 12-stellig>`.
- Schreiben: `["SEC","1","B20813000000000004"]`
- Ein `J30253…1`, Aus `J30254…1`, Entsperren `J30255…1`

Das Modul liefert nur die Parameter, die in seiner Abfrageliste eingetragen sind.

## Hinweis

Inoffizielles Projekt, ohne Verbindung zu Robin Wood oder 4Heat/Tiemme. Benutzung auf eigene Gefahr.

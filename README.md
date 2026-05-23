# TrimUI Web Transfer

Web-basierter Datei-Manager und P2P-Transfer für TrimUI Smart Pro / Brick.

Läuft direkt auf dem Handheld als Python-HTTP-Server. Bedienung vom Laptop-Browser aus.

## Features

- **Datei-Upload** — Dateien vom PC auf die SD-Karte des TrimUI hochladen
- **Cover Manager** — Thumbnails/Covern zu ROMs zuweisen und hochladen
- **P2P Transfer** — Dateien direkt zwischen zwei TrimUIs übertragen (ohne PC)
- **Storage-Übersicht** — Speicherbelegung der SD-Karte
- **Multi-File Upload** — Mehrere Dateien gleichzeitig hochladen
- **Subfolder-Navigation** — Ordnerstruktur dynamisch durchsuchen

## Setup

1. Die Dateien nach `/mnt/SDCARD/Apps/ftp/` auf dem TrimUI kopieren
2. `launch.sh` ausführen (oder über das App-Menü starten)
3. Browser öffnen: `http://<trimui-ip>:8000`

## API Endpunkte

| Methode | Pfad | Beschreibung |
|---------|------|-------------|
| GET | `/api/roms` | ROM-Liste nach Konsole gruppiert |
| GET | `/api/status` | Speicherbelegung |
| GET | `/api/peers` | Gefundene TrimUIs im Netzwerk |
| GET | `/api/dirs?path=...` | Unterordner eines Pfads |
| GET | `/api/files?path=...` | Dateien in einem Ordner |
| GET | `/api/cover?console=...&rom=...` | Cover-Bild einer ROM |
| POST | `/post_upload` | Datei-Upload (multipart) |
| POST | `/api/transfer_start` | P2P-Transfer starten |

## Technik

- Python `http.server` + `ThreadingMixIn` (keine Abhängigkeiten)
- Kein Framework — serverseitiges Template-Rendering
- P2P via direkter HTTP-Verbindung zwischen den Geräten
- Läuft auf dem TrimUI unter `/mnt/SDCARD`
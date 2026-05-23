<div align="center">

# TrimUI Web Transfer

**A browser-based file manager for the TrimUI Smart Pro & Brick**

[![Python](https://img.shields.io/badge/Python-3.x-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![No Dependencies](https://img.shields.io/badge/dependencies-none-brightgreen)](./web_transfer.py)
[![Platform](https://img.shields.io/badge/platform-TrimUI%20Smart%20Pro%20%7C%20Brick-orange)](https://trimui.com)
[![Port](https://img.shields.io/badge/server-port%208000-lightgrey)](#setup)
[![License](https://img.shields.io/badge/license-MIT-blue)](#)

*Runs directly on the handheld as a Python HTTP server.  
No installation on your PC needed — open a browser and go.*

</div>

---

## Screenshots

| File Upload | Cover Manager | P2P Transfer |
|:-----------:|:-------------:|:------------:|
| ![File Upload](docs/screenshots/upload.png) | ![Cover Manager](docs/screenshots/covers.png) | ![P2P Transfer](docs/screenshots/p2p.png) |

---

## Features

| | Feature | Description |
|---|---------|-------------|
| ⬆️ | **File Upload** | Upload ROMs and files from your PC directly to the SD card |
| 🖼️ | **Cover Manager** | Browse ROMs by console, assign and upload thumbnail covers (600×800 PNG) |
| 🔁 | **P2P Transfer** | Send files directly between two TrimUI devices via ARP discovery — no PC needed *(experimental, untested)* |
| 💾 | **Storage Dashboard** | Live SD card usage bar with used / total display |
| 📂 | **Subfolder Navigation** | Dynamically browse the full folder structure before uploading |
| 🗂️ | **Multi-File Upload** | Select and upload multiple files at once |

---

## Compatibility

Built and tested on the **TrimUI Smart Pro S running Stock OS**. Because I don't own other handhelds or use custom firmwares, I cannot verify whether it works the same way on different devices or setups. Feedback from other configurations is welcome.

---

## Security Notice

This server has **no authentication** and allows uploading, renaming and
deleting files under `/mnt/SDCARD`. It is intended for use on a **trusted
local network only** (your home Wi-Fi). Do not expose port `8000` to the
public internet, and do not run it on untrusted networks (cafés, hotels,
conferences).

---

## Setup

**1.** Copy all files to your TrimUI:
```
/mnt/SDCARD/Apps/ftp/
```

**2.** Launch the app — either run `launch.sh` directly or open it from the TrimUI app menu.

**3.** Find your TrimUI's IP address in the Wi-Fi settings, then open your browser:
```
http://<trimui-ip>:8000
```

---

## Directory Layout

| Path | Purpose |
|------|---------|
| `/mnt/SDCARD/Roms/` | ROM files, browsed and targeted in the Upload tab |
| `/mnt/SDCARD/Imgs/{console}/` | Cover art — one PNG per ROM, named after the ROM file |
| `/mnt/SDCARD/Apps/ftp/` | App installation directory |

---

## API Reference

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/roms` | ROM list grouped by console |
| GET | `/api/status` | SD card storage usage |
| GET | `/api/peers` | TrimUI devices discovered on the network |
| GET | `/api/dirs?path=...` | Subdirectories of a given path |
| GET | `/api/files?path=...` | Files inside a directory |
| GET | `/api/cover?console=...&rom=...` | Cover image for a ROM |
| POST | `/post_upload` | File upload (multipart/form-data) |
| POST | `/api/transfer_start` | Start a P2P transfer |
| POST | `/api/rom/delete` | Delete a ROM (and its cover) |
| POST | `/api/rom/rename` | Rename a ROM (and its cover) |

## Technical Details

- **Zero dependencies** — pure Python `http.server` + `ThreadingMixIn`, minimal footprint
- **No framework** — server-side template rendering with vanilla HTML / CSS / JS
- **P2P** — direct HTTP connection between devices, peers found via ARP cache scan
- **Security** — path traversal protection on all file operations, `os.path.basename()` on uploads
- **Dark theme UI** — responsive layout, works on any modern browser

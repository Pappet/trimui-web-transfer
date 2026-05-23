# TrimUI Web Transfer

A web-based file manager and P2P transfer tool for the TrimUI Smart Pro and Brick handhelds.

Runs directly on the handheld as a Python HTTP server — no extra software needed. Operated from any browser on your laptop or PC.

## Features

- **File Upload** — Upload files from your PC to the TrimUI's SD card
- **Cover Manager** — Assign and upload thumbnail covers for your ROMs
- **P2P Transfer** — Transfer files directly between two TrimUI devices (no PC required)
- **Storage Dashboard** — Visual overview of SD card usage
- **Multi-File Upload** — Upload multiple files simultaneously
- **Subfolder Navigation** — Dynamically browse the folder structure before uploading

## Setup

1. Copy the files to `/mnt/SDCARD/Apps/ftp/` on your TrimUI
2. Run `launch.sh` (or launch the app from the TrimUI app menu)
3. Open your browser and navigate to `http://<trimui-ip>:8000`

## API Endpoints

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

## Technical Details

- Pure Python `http.server` + `ThreadingMixIn` — zero external dependencies
- No framework: server-side template rendering with vanilla HTML/CSS/JS
- P2P transfer via direct HTTP connection between devices
- Peer discovery using ARP cache scanning on the local network
- Path traversal protection on all file operations
- Runs entirely on the TrimUI under `/mnt/SDCARD`

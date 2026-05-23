#!/usr/bin/env python3
import http.server
import socketserver
import os
import cgi
import json
import urllib.parse
import urllib.request
import shutil
import tempfile
import html
import uuid
import socket

# --- KONFIGURATION ---
PORT = 8000
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = "/mnt/SDCARD"
ROMS_DIR = os.path.join(ROOT_DIR, "Roms")
IMGS_DIR = os.path.join(ROOT_DIR, "Imgs")
TEMPLATE_FILE = os.path.join(BASE_DIR, "template.html")

tempfile.tempdir = ROOT_DIR

# --- CLIENT LOGIK (P2P Transfer) ---
class PeerClient:
    """Übernimmt das Senden von Dateien an einen anderen Trimui"""
    
    @staticmethod
    def is_port_open(ip, port, timeout=0.2):
        """Prüft schnell, ob der Port offen ist (Handshake)"""
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        try:
            s.connect((ip, port))
            s.close()
            return True
        except:
            return False

    @staticmethod
    def get_active_peers():
        """Findet Geräte im ARP-Cache UND prüft, ob die App dort läuft"""
        candidates = []
        try:
            with open('/proc/net/arp', 'r') as f:
                lines = f.readlines()[1:] # Header überspringen
                for line in lines:
                    parts = line.split()
                    if len(parts) >= 4:
                        ip = parts[0]
                        mac = parts[3]
                        # Filter: Nur lokale IPs, ignorieren unvollständige Einträge
                        if ip.startswith("192.168.") and mac != "00:00:00:00:00:00":
                            candidates.append({"ip": ip, "mac": mac})
        except Exception:
            pass
            
        # Aktive Filterung: Wir pingen den Port 8000 an
        real_peers = []
        for peer in candidates:
            # Wir prüfen kurz, ob Port 8000 offen ist.
            # Das verhindert, dass Fritzboxen oder PCs in der Liste landen.
            if PeerClient.is_port_open(peer['ip'], PORT):
                real_peers.append(peer)
                
        return real_peers

    @staticmethod
    def send_file(local_path, target_ip, target_folder_name):
        target_url = f"http://{target_ip}:{PORT}/post_upload"
        filename = os.path.basename(local_path)
        
        boundary = str(uuid.uuid4())
        lines = []
        
        lines.append(f'--{boundary}')
        lines.append('Content-Disposition: form-data; name="target_folder"')
        lines.append('')
        lines.append(target_folder_name)
        
        lines.append(f'--{boundary}')
        lines.append(f'Content-Disposition: form-data; name="file"; filename="{filename}"')
        lines.append('Content-Type: application/octet-stream')
        lines.append('')
        
        body_start = '\r\n'.join(lines).encode('utf-8') + b'\r\n'
        body_end = f'\r\n--{boundary}--\r\n'.encode('utf-8')
        
        try:
            with open(local_path, 'rb') as f:
                file_data = f.read()
            
            full_body = body_start + file_data + body_end
            
            req = urllib.request.Request(target_url, data=full_body)
            req.add_header('Content-Type', f'multipart/form-data; boundary={boundary}')
            req.add_header('Content-Length', len(full_body))
            
            with urllib.request.urlopen(req, timeout=10) as response:
                return response.status == 200, response.read().decode()
                
        except Exception as e:
            return False, str(e)

# --- THREADING SERVER ---
class ThreadingHTTPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    daemon_threads = True
    allow_reuse_address = True

class UltimateHandler(http.server.SimpleHTTPRequestHandler):
    
    def validate_path(self, target_path, base=ROOT_DIR):
        try:
            abs_base = os.path.abspath(base)
            abs_target = os.path.abspath(target_path)
            if abs_target.startswith(abs_base):
                return abs_target
        except Exception:
            pass
        return None

    def get_disk_usage(self):
        try:
            total, used, free = shutil.disk_usage(ROOT_DIR)
            return {"total": total, "used": used, "free": free}
        except:
            return {"total": 0, "used": 0, "free": 0}

    def get_roms_dict(self):
        roms_structure = {}
        if os.path.exists(ROMS_DIR):
            for console in sorted(os.listdir(ROMS_DIR)):
                console_path = os.path.join(ROMS_DIR, console)
                if os.path.isdir(console_path) and not console.startswith('.'):
                    roms = []
                    for f in sorted(os.listdir(console_path)):
                        if not f.startswith('.') and os.path.isfile(os.path.join(console_path, f)):
                            roms.append(f)
                    if roms:
                        roms_structure[console] = roms
        return roms_structure

    def get_dirs(self, path):
        safe_path = self.validate_path(path)
        if not safe_path or not os.path.isdir(safe_path): return []
        dirs = []
        try:
            for d in sorted(os.listdir(safe_path)):
                full_path = os.path.join(safe_path, d)
                if os.path.isdir(full_path) and not d.startswith('.'):
                    dirs.append(d)
        except OSError: pass
        return dirs
        
    def get_files_in_dir(self, path):
        safe_path = self.validate_path(path)
        files = []
        if safe_path and os.path.isdir(safe_path):
             for f in sorted(os.listdir(safe_path)):
                if os.path.isfile(os.path.join(safe_path, f)) and not f.startswith('.'):
                    files.append(f)
        return files

    def _cover_path(self, console, rom):
        base_name = os.path.splitext(rom)[0]
        img_path = os.path.join(IMGS_DIR, console, base_name + ".png")
        return self.validate_path(img_path, base=IMGS_DIR)

    def do_GET(self):
        # API Endpoints
        if self.path == '/api/roms':
            self.send_json(self.get_roms_dict())
        elif self.path == '/api/status':
            self.send_json(self.get_disk_usage())
        elif self.path == '/api/peers':
            self.send_json(PeerClient.get_active_peers())
        elif self.path.startswith('/api/dirs'):
            query = urllib.parse.urlparse(self.path).query
            params = urllib.parse.parse_qs(query)
            req_path = params.get('path', [ROOT_DIR])[0]
            safe_path = self.validate_path(req_path) or ROOT_DIR
            self.send_json(self.get_dirs(safe_path))
        elif self.path.startswith('/api/files'):
            query = urllib.parse.urlparse(self.path).query
            params = urllib.parse.parse_qs(query)
            req_path = params.get('path', [ROMS_DIR])[0]
            self.send_json(self.get_files_in_dir(req_path))
        
        # --- NEU: Endpunkt zum Abrufen von Cover-Bildern ---
        elif self.path.startswith('/api/cover'):
            query = urllib.parse.urlparse(self.path).query
            params = urllib.parse.parse_qs(query)
            console = params.get('console', [''])[0]
            rom = params.get('rom', [''])[0]
            
            if console and rom:
                # Dateinamen-Logik
                base_name = os.path.splitext(rom)[0]
                img_name = base_name + ".png"
                img_path = os.path.join(IMGS_DIR, console, img_name)
                
                # Security Check
                safe_path = self.validate_path(img_path, base=IMGS_DIR)
                
                if safe_path and os.path.exists(safe_path):
                    self.send_response(200)
                    self.send_header('Content-type', 'image/png')
                    self.end_headers()
                    try:
                        with open(safe_path, 'rb') as f:
                            shutil.copyfileobj(f, self.wfile)
                    except BrokenPipeError:
                        pass
                    return
            
            self.send_error(404, "Kein Cover gefunden")
        # ---------------------------------------------------

        # UI Pages
        elif self.path.startswith('/thumbnails'):
            self.send_ui("thumbnail")
        elif self.path.startswith('/sync'):
            self.send_ui("sync")
        elif self.path.startswith('/inventory'):
            self.send_ui("inventory")
        elif self.path == '/' or self.path.startswith('/?') or self.path == '/index.html':
            self.send_ui("upload")
        elif self.path == '/favicon.ico':
            self.send_error(404)
        else:
            self.send_error(404, "Seite nicht gefunden")

    def send_json(self, data):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def send_ui(self, mode):
        try:
            with open(TEMPLATE_FILE, 'r', encoding='utf-8') as f:
                content = f.read()
        except FileNotFoundError:
            self.send_error(500, "Template-Datei nicht gefunden!")
            return

        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        
        # Status-Meldung aus Query-Parametern (nach 303 Redirect)
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)
        status_msg = html.escape(params.get('msg', [''])[0])
        status_type = html.escape(params.get('status', [''])[0])
        status_visible = "block" if status_msg else "none"
        
        base_folders = self.get_dirs(ROOT_DIR)
        base_opts = f'<option value="{ROOT_DIR}">Hauptverzeichnis (/)</option>'
        for d in base_folders:
            sel = "selected" if d == "Roms" else ""
            base_opts += f'<option value="{os.path.join(ROOT_DIR, d)}" {sel}>{d}</option>'

        replacements = {
            '{{BASE_OPTS}}': base_opts,
            '{{ROOT_DIR}}': ROOT_DIR,
            '{{NAV_UPLOAD_ACTIVE}}': 'active' if mode == 'upload' else '',
            '{{NAV_THUMB_ACTIVE}}': 'active' if mode == 'thumbnail' else '',
            '{{NAV_SYNC_ACTIVE}}': 'active' if mode == 'sync' else '',
            '{{NAV_INV_ACTIVE}}': 'active' if mode == 'inventory' else '',
            '{{DISPLAY_UPLOAD}}': 'block' if mode == 'upload' else 'none',
            '{{DISPLAY_THUMB}}': 'block' if mode == 'thumbnail' else 'none',
            '{{DISPLAY_SYNC}}': 'block' if mode == 'sync' else 'none',
            '{{DISPLAY_INV}}': 'block' if mode == 'inventory' else 'none',
            '{{STATUS_MSG}}': status_msg,
            '{{STATUS_TYPE}}': status_type,
            '{{STATUS_VISIBLE}}': status_visible
        }
        
        for key, value in replacements.items():
            content = content.replace(key, value)

        self.wfile.write(content.encode('utf-8'))

    def _read_json_body(self):
        length = int(self.headers.get('content-length', 0))
        return json.loads(self.rfile.read(length)) if length else {}

    def do_POST(self):
        # ROM Delete
        if self.path == '/api/rom/delete':
            try:
                data = self._read_json_body()
                console = data.get('console', '')
                rom = data.get('rom', '')
                if not console or not rom or '/' in console or '/' in rom or '..' in console or '..' in rom:
                    raise ValueError("Ungültige Parameter")
                rom_path = self.validate_path(os.path.join(ROMS_DIR, console, rom), base=ROMS_DIR)
                if not rom_path or not os.path.isfile(rom_path):
                    raise ValueError("ROM nicht gefunden")
                os.remove(rom_path)
                cover = self._cover_path(console, rom)
                cover_removed = False
                if cover and os.path.isfile(cover):
                    os.remove(cover)
                    cover_removed = True
                self.send_json({"success": True, "cover_removed": cover_removed})
            except Exception as e:
                self.send_json({"success": False, "message": str(e)})
            return

        # ROM Rename
        if self.path == '/api/rom/rename':
            try:
                data = self._read_json_body()
                console = data.get('console', '')
                old_name = data.get('old_name', '')
                new_name = data.get('new_name', '')
                if not console or not old_name or not new_name:
                    raise ValueError("Ungültige Parameter")
                if '/' in console or '..' in console:
                    raise ValueError("Ungültige Konsole")
                if '/' in new_name or '..' in new_name or new_name.startswith('.'):
                    raise ValueError("Ungültiger neuer Name")
                if '/' in old_name or '..' in old_name:
                    raise ValueError("Ungültiger alter Name")
                old_path = self.validate_path(os.path.join(ROMS_DIR, console, old_name), base=ROMS_DIR)
                new_path = self.validate_path(os.path.join(ROMS_DIR, console, new_name), base=ROMS_DIR)
                if not old_path or not os.path.isfile(old_path):
                    raise ValueError("ROM nicht gefunden")
                if not new_path:
                    raise ValueError("Ungültiges Ziel")
                if os.path.exists(new_path):
                    raise ValueError("Zielname existiert bereits")
                os.rename(old_path, new_path)
                # Cover mitziehen
                old_cover = self._cover_path(console, old_name)
                new_cover = self._cover_path(console, new_name)
                cover_renamed = False
                if old_cover and new_cover and os.path.isfile(old_cover) and not os.path.exists(new_cover):
                    os.rename(old_cover, new_cover)
                    cover_renamed = True
                self.send_json({"success": True, "cover_renamed": cover_renamed})
            except Exception as e:
                self.send_json({"success": False, "message": str(e)})
            return

        # P2P Transfer Start
        if self.path == '/api/transfer_start':
            try:
                length = int(self.headers['content-length'])
                data = json.loads(self.rfile.read(length))
                
                source_file = data.get('file_path')
                target_ip = data.get('target_ip')
                target_folder = data.get('target_folder')
                
                safe_source = self.validate_path(source_file)
                if not safe_source or not os.path.isfile(safe_source):
                     raise ValueError("Lokale Datei ungültig")

                success, msg = PeerClient.send_file(safe_source, target_ip, target_folder)
                self.send_json({"success": success, "message": msg})
                
            except Exception as e:
                self.send_json({"success": False, "message": str(e)})
            return

        # Upload Handler
        if self.path == '/post_upload':
            mode = "normal"
            try:
                ctype, pdict = cgi.parse_header(self.headers['Content-Type'])
                if ctype == 'multipart/form-data':
                    pdict['boundary'] = bytes(pdict['boundary'], "utf-8")
                    form = cgi.FieldStorage(fp=self.rfile, headers=self.headers,
                        environ={'REQUEST_METHOD': 'POST', 'CONTENT_TYPE': self.headers['Content-Type']})
                    
                    mode = form.getvalue("mode") if "mode" in form else "normal"
                    
                    if mode == "thumbnail":
                        console_folder = form.getvalue("console_folder")
                        if not console_folder or "/" in console_folder or ".." in console_folder:
                             raise ValueError("Ungültiger Konsolen-Ordner")
                        target_dir = os.path.join(IMGS_DIR, console_folder)
                        if not os.path.exists(target_dir): os.makedirs(target_dir, exist_ok=True)
                        
                        fileitem = form["file"]
                        if fileitem.filename:
                            fn = os.path.basename(fileitem.filename)
                            safe_fn = html.escape(fn)
                            with open(os.path.join(target_dir, fn), 'wb') as f:
                                shutil.copyfileobj(fileitem.file, f)
                            msg = f"<span style='color:#28a745'>Erfolg! Gespeichert: {safe_fn}</span>"
                        else: msg = "Fehler: Keine Datei."
                        self.send_response(200); self.end_headers(); self.wfile.write(msg.encode())
                    
                    else:
                        # Normaler Upload
                        target_path_raw = form.getvalue("target_folder") or ROOT_DIR
                        target_path = self.validate_path(target_path_raw)
                        if not target_path: raise ValueError("Ungültiger Zielpfad")
                        
                        if not os.path.exists(target_path):
                            os.makedirs(target_path, exist_ok=True)
                        
                        file_items = form["file"]
                        if not isinstance(file_items, list): file_items = [file_items]
                        
                        count = 0
                        for fileitem in file_items:
                            if fileitem.filename:
                                fn = os.path.basename(fileitem.filename)
                                with open(os.path.join(target_path, fn), 'wb') as f:
                                    shutil.copyfileobj(fileitem.file, f)
                                count += 1
                        
                        msg = urllib.parse.quote(f"{count} Datei(en) empfangen")
                        self.send_response(303)
                        self.send_header('Location', f'/?status=success&msg={msg}')
                        self.end_headers()

            except Exception as e:
                error_msg = html.escape(str(e))
                if mode == "thumbnail":
                    self.send_response(500); self.end_headers(); self.wfile.write(f"Error: {error_msg}".encode())
                else:
                    self.send_response(303)
                    self.send_header('Location', f'/?status=error&msg={urllib.parse.quote(error_msg)}')
                    self.end_headers()
        else:
            self.send_error(404, "Pfad nicht gefunden")

# --- SERVER START ---
os.chdir(ROOT_DIR)
if not os.path.exists(IMGS_DIR): os.makedirs(IMGS_DIR, exist_ok=True)
with ThreadingHTTPServer(("", PORT), UltimateHandler) as httpd:
    print(f"Server läuft auf Port {PORT}")
    httpd.serve_forever()
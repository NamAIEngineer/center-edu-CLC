"""Read-only fixture server. No app/DB/auth; baseline bytes read from pinned Git."""
import http.server
import subprocess
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
BASE = subprocess.check_output(['git', 'show', 'e4d2bea13e678918b77fa6fb5d98deb2384a685f:static/modules/training_routes.js'], cwd=ROOT)
class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs): super().__init__(*args, directory=str(ROOT), **kwargs)
    def do_GET(self):
        if self.path == '/baseline-training.js':
            self.send_response(200); self.send_header('Content-Type','text/javascript'); self.end_headers(); self.wfile.write(BASE)
        else: super().do_GET()
    def log_message(self, *args): pass
server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), Handler)
print(f'http://127.0.0.1:{server.server_port}', flush=True)
server.serve_forever()

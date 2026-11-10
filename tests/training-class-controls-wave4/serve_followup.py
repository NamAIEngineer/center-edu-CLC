"""Disposable, empty-data shell/renderer replay; no app DB or authentication.

Copies canonical support assets read-only, then overlays only this worker's
module. Before uses the exact canonical module, never the stale Git base.
All local API responses are empty and non-authenticated. No POST is accepted.
"""
import hashlib
import http.server
import json
import shutil
import tempfile
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[2]
CANONICAL = Path('/Users/nam/Documents/System-Agentic_AI/products/center-edu-rebuild')
RUNTIME = Path(tempfile.mkdtemp(prefix='cedu-class-followup-'))
shutil.copytree(CANONICAL / 'static', RUNTIME / 'static')
shutil.copyfile(CANONICAL / 'static/modules/training_routes.js', RUNTIME / 'baseline-training.js')
shutil.copyfile(ROOT / 'static/modules/training_routes.js', RUNTIME / 'static/modules/training_routes.js')
shutil.copyfile(ROOT / 'tests/training-class-controls-wave4/harness.html', RUNTIME / 'harness.html')

pins = {'runtime': str(RUNTIME), 'canonical': str(CANONICAL), 'files': {}}
for name in ['app.js', 'app.css', 'index.html', 'nav-config.js', 'modules/training_routes.js']:
    pins['files'][name] = {
        'canonical': hashlib.sha256((CANONICAL / 'static' / name).read_bytes()).hexdigest(),
        'runtime': hashlib.sha256((RUNTIME / 'static' / name).read_bytes()).hexdigest(),
    }

html = (RUNTIME / 'static/index.html').read_text()
html = html.replace('</body>', '''
<script>
window.addEventListener('load', async () => {
  try {
    await new Promise(resolve => setTimeout(resolve, 200));
    state.route = '/training/class'; state.screen = 'classes';
    const source = new URLSearchParams(location.search).has('before')
      ? '/baseline-training.js' : '/static/modules/training_routes.js';
    const lane = await import(source);
    lane.register(window.CenterEdu);
    document.querySelector('#login-view').hidden = true;
    document.querySelector('#main-view').hidden = false;
    buildReferenceNav(); await render();
    document.title = 'Local empty-data class shell replay; auth not exercised';
    window.ready = true;
  } catch (error) { window.replayError = String(error); }
});
</script></body>''')
(RUNTIME / 'visual.html').write_text(html)




class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(RUNTIME), **kwargs)

    def do_GET(self):
        path = urlsplit(self.path).path
        if path == '/runtime-pins.json':
            data = pins
        elif path == '/api/auth/me':
            data = {'authenticated': False}
        elif path == '/api/screen-spec':
            data = {'data': {'filters': [], 'tabs': []}}
        elif path.startswith('/api/'):
            data = {'data': []}
        else:
            if path in ['/app.css', '/app.js', '/nav-config.js']:
                self.path = '/static' + self.path
            return super().do_GET()
        payload = json.dumps(data).encode()
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, *_args):
        pass


server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), Handler)
print(json.dumps({'base': f'http://127.0.0.1:{server.server_port}', **pins}), flush=True)
try:
    server.serve_forever()
finally:
    server.server_close()
    shutil.rmtree(RUNTIME)

import fs from 'node:fs';
import assert from 'node:assert/strict';

const app = fs.readFileSync('static/app.js', 'utf8');
const w6 = fs.readFileSync('static/modules/w6_screen_utils.js', 'utf8');
assert.match(app, /version:x\.version,updated_at:x\.updated_at,full_body:true/);
assert.match(app, /function conflictMessage\(err, wrap, reload\)/);
assert.match(app, /box\.textContent=err\.message\|\|'Bản ghi đã được thay đổi\.'/);
assert.match(app, /err\?\.status!==409 && err\?\.status!==428/);
assert.match(app, /conflict-reload/);
assert.match(w6, /version: record\.version, updated_at: record\.updated_at, full_body: true/);
assert.match(w6, /error\?\.status === 409 \|\| error\?\.status === 428/);
assert.match(w6, /textContent = 'Tải lại'/);
console.log('optimistic concurrency UI contract: PASS');

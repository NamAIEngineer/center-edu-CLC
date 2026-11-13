import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';

const crm = readFileSync('static/modules/crm_customer_views.js', 'utf8');
const center = readFileSync('static/modules/w6_center_views.js', 'utf8');
const w6 = readFileSync('static/modules/w6_screen_utils.js', 'utf8');

assert.match(crm, /record\.updated_at\?\?data\.updated_at/);
assert.match(crm, /record\.version\?\?data\.version/);
assert.match(crm, /const rawDeletePath = \(route, row\)/);
assert.equal((crm.match(/rawDeletePath\(RAW,row\)/g) || []).length, 2);
assert.doesNotMatch(crm, /generated\/screens\/\$\{id\}\?route=\$\{encodeURIComponent\(RAW\)\}/);
assert.match(center, /new URLSearchParams\(\{ route,[\s\S]*record\.updated_at/);
assert.match(w6, /new URLSearchParams\(\{ route,[\s\S]*record\.updated_at/);
assert.match(w6, /w6-criteria-delete[\s\S]*new URLSearchParams\(\{ route/);
console.log('generated-screen delete CAS UI contracts: PASS');

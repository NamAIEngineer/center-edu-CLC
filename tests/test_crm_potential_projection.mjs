import assert from 'node:assert/strict';
import fs from 'node:fs';

const source = fs.readFileSync(new URL('../static/modules/crm_routes.js', import.meta.url), 'utf8');
assert.match(source, /summary\?\.remove\(\)/);
assert.match(source, /Khách hàng thô/);
assert.match(source, /potentialBound/);
assert.match(source, /\/api\/care-appointments/);
assert.match(source, /showCareHistory/);
console.log('crm potential projection regression: PASS');

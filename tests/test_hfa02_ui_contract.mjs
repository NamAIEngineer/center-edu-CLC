import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { W6_OVERRIDE_CONFIGS } from '../static/modules/w6_overrides.js';

const config = W6_OVERRIDE_CONFIGS['/cso/customer-care'];
const renderer = readFileSync(new URL('../static/modules/w6_screen_utils.js', import.meta.url), 'utf8');
assert.ok(config, 'customer-care override config exists');
const filters = config.filters || [];
const named = new Map(filters.map((filter) => [filter.name, filter]));

for (const [name, placeholder] of [
  ['action', 'Chọn hành động'],
  ['result', 'Chọn kết quả'],
  ['purpose', 'Chọn mục đích'],
]) {
  const filter = named.get(name);
  assert.ok(filter, `${name} filter exists`);
  assert.equal(filter.multiple, true, `${name} uses native multiple transport`);
  assert.equal(filter.compact_input, true, `${name} renders one compact visible control`);
  assert.equal(filter.placeholder, placeholder);
  assert.equal(named.has(`${name}_search`), false, `${name}_search is not a duplicate visible control`);
}

assert.equal(filters.filter((filter) => filter.compact_input).length, 3);
assert.match(renderer, /const careTitle = route === '\/cso\/customer-care'/, 'care title is owned by screen composition');
assert.match(renderer, /const referenceRoute = .*route === '\/cso\/customer-care'/, 'customer-care uses reference layout');
assert.match(renderer, /const heading = route === '\/cso\/customer-care' \? ''/, 'generic duplicate title is suppressed');
assert.doesNotMatch(renderer, /const title = config\.careActionColumns/, 'table renderer does not add a second care title');
console.log('customer-care visible filter/title contract: PASS');

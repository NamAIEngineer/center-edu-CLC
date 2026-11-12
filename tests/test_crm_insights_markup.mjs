import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';
import test from 'node:test';

const source = fs.readFileSync(new URL('../static/app.js', import.meta.url), 'utf8');
const markupSource = source.slice(source.indexOf('function potentialInsightsMarkup('), source.indexOf('\nasync function potentialCustomers('));
const context = vm.createContext({
  esc: value => String(value ?? '').replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('"', '&quot;'),
  document: {querySelector: () => null},
});
vm.runInContext(markupSource, context);
const markup = summary => context.potentialInsightsMarkup(summary);

test('empty and malformed data produce finite SVG coordinates without colored slices', () => {
  for (const summary of [{}, {total: Infinity, new: NaN, contacted: -3, successful: 'bad', cancelled: -1}]) {
    const html = markup(summary);
    assert.match(html, /Chưa có dữ liệu/);
    assert.doesNotMatch(html, /NaN|Infinity|undefined/);
    assert.equal((html.match(/<g class="potential-chart-slice"/g) || []).length, 0);
    assert.match(html, /aria-expanded="false"/);
  }
});

test('one nonzero bucket uses a complete two-arc ring', () => {
  const html = markup({total: 1, new: 1});
  assert.equal((html.match(/A 161 161/g) || []).length, 2);
  assert.equal((html.match(/A 96\.6 96\.6/g) || []).length, 2);
  assert.match(html, /Khách hàng mới: 1/);
});

test('unique customer count and care count retain distinct scales', () => {
  const html = markup({total: 47, new: 9, contacted: 8, successful: 44, cancelled: 2});
  assert.match(html, /Số khách 47, Chuỗi chăm sóc 63/);
  for (const color of ['#36a3f7', '#f4516c', '#34bfa3', '#c4c5d6', '#3366ff', '#ff751a']) assert(html.includes(color));
  assert.match(html, /fill="#7cb5ec">56<\/text>/);
  assert.match(html, /fill="#ff751a">67<\/text>/);
  assert.doesNotMatch(html, /NaN|Infinity/);
});

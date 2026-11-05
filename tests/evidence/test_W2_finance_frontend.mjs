import assert from 'node:assert/strict';
import { readdir, readFile } from 'node:fs/promises';

const manifest = [
  '/finance/contract',
  '/finance/bill/index',
  '/finance/revenue',
  '/finance/spend/index',
  '/finance/appointment_date',
  '/finance/assessment',
  '/finance/reserve',
  '/finance/history_move_student',
  '/finance/transfer/index',
  '/finance/accumulate_points',
  '/finance/item',
  '/finance/bill/debit_item/index',
  '/finance/wallet_co/index',
  '/dashboard/finance',
];

const files = (await readdir(new URL('../../static/modules/', import.meta.url)))
  .filter((name) => /^finance.*\.js$/.test(name))
  .sort();
// `finance_parity.js` is a shared post-render seam and intentionally has no
// route of its own. Keep the test resilient as worker utility modules are
// added without weakening the route manifest below.
assert.ok(files.length >= 14, 'all owned finance static modules must be present');

const registered = new Map();
const host = {
  registerScreen(route, renderer) {
    assert.equal(typeof renderer, 'function', `${route}: renderer must be callable`);
    registered.set(route, renderer);
    return true;
  },
};

for (const filename of files) {
  const module = await import(`../../static/modules/${filename}`);
  assert.equal(typeof module.register, 'function', `${filename}: missing register()`);
  module.register(host);
  const source = await readFile(new URL(`../../static/modules/${filename}`, import.meta.url), 'utf8');
  assert.equal(source.includes('UNKNOWN'), false, `${filename}: UNKNOWN must not reach customer UI`);
  assert.equal(source.includes('Chưa cập nhật'), false, `${filename}: placeholder label must not reach customer UI`);
}

for (const route of manifest) assert.equal(registered.has(route), true, `${route}: missing registerScreen hook`);

const dashboard = await import('../../static/modules/finance_dashboard.js');
const labels = dashboard.financeDashboard.metricLabels;
assert.deepEqual(labels, {
  contract_count: 'Số hợp đồng',
  bill_count: 'Số hóa đơn',
  revenue_count: 'Số khoản thu',
  spend_count: 'Số khoản chi',
  reserve_count: 'Số bảo lưu',
  wallet_count: 'Số ví CO',
  appointment_count: 'Số lịch hẹn',
  total_collected_vnd: 'Tổng đã thu',
  total_spend_vnd: 'Tổng đã chi',
  net_cash_vnd: 'Dòng tiền ròng',
});

console.log(`W2 finance frontend registry PASS: ${files.length} modules, ${registered.size} routes`);

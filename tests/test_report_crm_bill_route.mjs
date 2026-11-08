import assert from 'node:assert/strict';
import fs from 'node:fs';
import { crmBillCellValue, crmBillSummaryMarkup, normalizeCrmBillColumns } from '../static/modules/report_crm_center.js';
const source = fs.readFileSync(new URL('../static/modules/report_crm_center.js', import.meta.url), 'utf8');
const action = source.match(/['"]\/report\/crm\/bill\/index['"]:\s*\[([^\]]*)\]/)?.[1] || '';
assert.match(action, /['"]Excel['"]/);
assert.doesNotMatch(action, /Chọn đối tượng|Chọn khóa học/);
assert.match(source, /const activeTabIndex = ctx\.route === '\/report\/crm\/bill\/index' \? 1 : 0/);
assert.match(source, /const tabStrip = tabs \?/);
assert.match(source, /filter-strip/);
assert.match(source, /page-actions/);
console.log('report crm bill route regression: PASS');

assert.match(source, /Người tạo/);
assert.match(source, /crmBillSummaryMarkup/);
assert.match(source, /Đã Đóng/);
assert.match(source, /Hình thức thanh toán/);
assert.match(source, /observedAutoFilters = ctx\.route === '\/report\/crm\/contract\/index' \|\| ctx\.route === '\/report\/crm\/bill\/index'/);

const summary = crmBillSummaryMarkup({ total_paid: 1250000, customer_count: 3 });
assert.match(summary, /Đã Đóng:<\/b> 1\.250\.000/);
assert.match(summary, /Số lượng khách hàng:<\/b> 3/);
assert.match(crmBillSummaryMarkup({}), /Đã Đóng:<\/b> —/);
assert.match(crmBillSummaryMarkup({}), /Số lượng khách hàng:<\/b> —/);
assert.match(crmBillSummaryMarkup({}, [
  { paid_amount: 7000, customer_name: 'A' },
  { paid_amount: 3000, customer_name: 'A' },
  { paid_amount: 2000, customer_name: 'B' },
]), /Đã Đóng:<\/b> 12\.000/);
assert.match(crmBillSummaryMarkup({}, [
  { paid_amount: 7000, customer_name: 'A' },
  { paid_amount: 3000, customer_name: 'A' },
  { paid_amount: 2000, customer_name: 'B' },
]), /Số lượng khách hàng:<\/b> 2/);

const columns = normalizeCrmBillColumns([
  { key: 'hinh_thuc_thanh_toan', label: 'Hình thức thanh toán' },
  { key: 'thuc_thu_theo_hoa_on', label: 'Thực thu (Theo hóa đơn)' },
  { key: 'a_ong', label: 'Đã Đóng' },
  { key: 'thoi_gian_ong', label: 'Thời gian đóng' },
  { key: 'so_hoa_on', label: 'Số hóa đơn' },
]);
assert.deepEqual(columns.map(column => column.key), ['thuc_thu_theo_hoa_on', 'a_ong', 'thoi_gian_ong', 'so_hoa_on', 'hinh_thuc_thanh_toan']);
assert.equal(crmBillCellValue({ payment_amount: 7000, invoice_date: '2026-09-24', invoice_code: 'INV-1', payment_method: 'Tiền mặt' }, { key: 'a_ong' }), 7000);
assert.equal(crmBillCellValue({ payment_amount: 7000, invoice_date: '2026-09-24', invoice_code: 'INV-1', payment_method: 'Tiền mặt' }, { key: 'thoi_gian_ong' }), '2026-09-24');
assert.equal(crmBillCellValue({ payment_amount: 7000, invoice_date: '2026-09-24', invoice_code: 'INV-1', payment_method: 'Tiền mặt' }, { key: 'so_hoa_on' }), 'INV-1');
assert.equal(crmBillCellValue({ payment_amount: 7000, invoice_date: '2026-09-24', invoice_code: 'INV-1', payment_method: 'Tiền mặt' }, { key: 'hinh_thuc_thanh_toan' }), 'Tiền mặt');

import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';

const finance = await readFile(new URL('../static/modules/report_finance.js', import.meta.url), 'utf8');
const crm = await readFile(new URL('../static/modules/report_crm_center.js', import.meta.url), 'utf8');

assert.match(finance, /name === 'filter_3' && route === '\/report\/finance\/student_finance'.*Chọn trạng thái học phí/s);
assert.match(finance, /display:inline-flex;align-items:center;height:36px;padding:0 13px;border-radius:4px;background:#21a889;color:#fff/);
assert.match(finance, /data-report-action=\"refresh\"/);
assert.match(finance, /'\/report\/finance\/debt': \['Excel', 'Cập nhật dữ liệu'\]/);
assert.match(finance, /'\/report\/finance\/student_finance': \['Excel', 'Cập nhật dữ liệu'\]/);
assert.match(finance, /'\/report\/finance\/debt': Object\.freeze\(\[\]\)/);
assert.match(finance, /'\/report\/finance\/student_finance': Object\.freeze\(\[\]\)/);
assert.match(crm, /from_date: 'From date', to_date: 'To date'/);
assert.match(crm, /from_date_2: 'From date', to_date_2: 'To date'/);
assert.match(crm, /'\/report\/crm\/contract\/index': \['Excel'\]/);
assert.doesNotMatch(crm, /'\/report\/crm\/contract\/index': \['Excel', 'Cập nhật dữ liệu'\]/);
console.log('Report finance/CRM control contracts PASS');

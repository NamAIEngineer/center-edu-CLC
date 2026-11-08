import assert from 'node:assert/strict';
import { summaryValue } from '../static/modules/report_finance.js';

const payload = {
  summary: {
    total_amount: '1.234.567',
    paid_amount: 234567,
    debt_amount: 1000000,
    student_count: 12,
  },
};
assert.equal(summaryValue(payload, 'Tổng thu', []), 1234567);
assert.equal(summaryValue(payload, 'Tổng đã đóng', []), 234567);
assert.equal(summaryValue(payload, 'Tổng còn nợ', []), 1000000);
assert.equal(summaryValue(payload, 'Tổng số học viên', []), 12);

const absent = { summary: {} };
assert.equal(summaryValue(absent, 'Tổng nợ xấu', []), null);
assert.equal(summaryValue(absent, 'Số tiền hoàn trả', []), null);
assert.equal(summaryValue(absent, 'Tiền chưa sử dụng', []), null);

assert.equal(summaryValue({ summary: { total_amount: 9 } }, 'Tổng thu', [{ total_amount: 2 }]), 9);
console.log('Finance report summary backend-key mapping PASS');

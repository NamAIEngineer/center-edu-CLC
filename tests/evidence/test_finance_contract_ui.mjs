import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';

import {
  financeContractExtension,
  financeContractUpload,
} from '../../static/modules/finance_contract.js';

const source = await readFile(
  new URL('../../static/modules/finance_contract.js', import.meta.url),
  'utf8',
);

// Upload preview mapping is positional: every observed header must have one
// source field, with STT as the only display-only column.
assert.equal(financeContractUpload.headers.length, 21);
assert.deepEqual(financeContractUpload.headers.slice(-6), [
  'Tổng tiền trước giảm giá',
  'Giảm giá trực tiếp',
  'Tổng tiền sau giảm giá',
  'Ghi chú hợp đồng',
  'Mã lớp học',
  'Ngày bắt đầu học',
]);
assert.equal(financeContractUpload.fields.length, financeContractUpload.headers.length);
assert.match(source, /financeContractUpload\.fields\.map\(field =>/);
assert.match(source, /<th>STT<\/th>\$\{financeContractUpload\.headers\.map/);
assert.match(source, /<tr><td colspan="22">Không tìm thấy dữ liệu<\/td><\/tr>/);

// Renewal is a truthful tab/panel boundary. Preserve the observed duplicate
// label and require accessible controls plus the class selector.
assert.deepEqual(financeContractExtension.tabs, [
  'Gia hạn nhiều hợp đồng',
  'Tạo hợp đồng lên khóa',
  'Gia hạn theo khóa thu theo tháng lên lớp',
  'Gia hạn theo khóa thu theo tháng lên lớp',
]);
assert.match(source, /role="tablist"/);
assert.match(source, /role="tab"/);
assert.match(source, /aria-controls="contract-extension-panel-\$\{index\}"/);
assert.match(source, /role="tabpanel"/);
assert.match(source, /data-contract-extension-class/);
assert.match(source, /data-contract-extension-tab.*addEventListener\('click'/s);
assert.match(source, /data-contract-extension-panel.*panel\.hidden/s);
assert.equal(financeContractUpload.canCommit, false);

console.log('Finance contract UI mapping/tabs PASS');

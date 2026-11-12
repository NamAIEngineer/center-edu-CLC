import assert from 'node:assert/strict';
import { classRevenuePresentation } from '../static/modules/report_finance.js';

const leaf = (key, label = key) => ({ key, label, source_status: 'OBSERVED' });
const classicColumns = [leaf('thong_tin_chung', 'Thông tin chung'), ...Array.from({length:12}, (_,i)=>leaf(`thang_${i+1}`,`Tháng ${i+1}`)), ...Array.from({length:11}, (_,i)=>leaf(i===0?'stt':`field_${i}`,i===0?'STT':`Cột ${i}`)), ...Array.from({length:12}, (_,m)=>Array.from({length:7},(_,i)=>leaf(`month_${m+1}_${i+1}`))).flat()];
const newerColumns = [leaf('thong_tin_lop_hoc','Thông tin lớp học'),leaf('thong_tin_chung','Thông tin chung'), ...Array.from({length:12}, (_,i)=>leaf(`thang_${i+1}`,`Tháng ${i+1}`)), ...Array.from({length:13}, (_,i)=>leaf(i===0?'stt':`new_field_${i}`,i===0?'STT':`Cột ${i}`)), ...Array.from({length:12}, (_,m)=>Array.from({length:7},(_,i)=>leaf(`new_month_${m+1}_${i+1}`))).flat()];
const row = { stt: 1, khoa_hoc: 'Khóa A', ten_lop: 'Lớp A', phai_thu: 1200000 };

for (const [columns, staticGroups, expectedLeaves] of [[classicColumns,1,95],[newerColumns,2,97]]) {
  const result = classRevenuePresentation([row], columns);
  assert.equal(result.groups.length, 12 + staticGroups);
  assert.equal(result.columns.length, expectedLeaves);
  assert.deepEqual(result.groups.slice(-12).map(column=>column.label), Array.from({length:12},(_,i)=>`Tháng ${i+1}`));
  assert.deepEqual(result.columns[0], columns[12 + staticGroups]);
  assert.equal(result.columns[0].source_status, 'OBSERVED');
  assert.strictEqual(result.rows[0], row);
  assert.equal(result.rows[0].remaining_amount, undefined);
}
console.log('class revenue observed grouped columns and source rows: PASS');

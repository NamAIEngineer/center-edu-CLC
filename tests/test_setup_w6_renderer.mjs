import assert from 'node:assert/strict';
import { setupDailyEvaluationHtml, setupCriteriaHtml } from '../static/modules/w6_screen_utils.js';

const evaluations = setupDailyEvaluationHtml([
  { id: 7, data: { name: 'Đánh giá thử', criteria_count: 3 } },
  { id: 8, data: { name: 'Đánh giá chưa liên kết' } },
], {});
assert.match(evaluations, /data-record-id="7"/);
assert.match(evaluations, /Đánh giá thử/);
assert.match(evaluations, /3 Tiêu chí/);
assert.match(evaluations, /— Tiêu chí/);
assert.doesNotMatch(evaluations, /0 Tiêu chí/);

const criteria = setupCriteriaHtml([]);
assert.match(criteria, /Bài test/);
assert.match(criteria, /data-w6-action="create-test"/);
assert.doesNotMatch(criteria, /Tạm thời chưa khả dụng/);
assert.match(criteria, /Tạo tiêu chí/);
assert.match(criteria, /Không tìm thấy dữ liệu/);
console.log('setup evaluation and criteria render contracts: PASS');

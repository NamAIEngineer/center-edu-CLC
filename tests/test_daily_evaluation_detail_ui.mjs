import assert from 'node:assert/strict';
import { dailyEvaluationDetailHtml } from '../static/modules/w6_screen_utils.js';
const html = dailyEvaluationDetailHtml({ id: 9, data: { name: 'Đánh giá thử', description: 'Theo dõi tiến bộ', status: 'Hoạt động', course_ids: ['1'], criteria: JSON.stringify([{ name: 'Điểm danh', assessment_type: 'Nhập điểm', max_value: 10, status: 'Hoạt động' }]) } }, [{ value: '1', label: 'English Foundation' }]);
assert.match(html, /Sửa/); assert.match(html, /Xóa/); assert.match(html, /English Foundation/); assert.match(html, /Tạo/); assert.match(html, /Tiêu chí/); assert.match(html, /Điểm tối đa: 10/); assert.match(html, /w6-daily-criterion-edit/); assert.match(html, /w6-daily-criterion-delete/);
console.log('daily evaluation detail UI contract: PASS');

import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';

const app = readFileSync('static/app.js', 'utf8');
assert.match(app, /api\(`\/api\/classes\/\$\{classId\}\/students\?status=ENROLLED`\)/);
assert.match(app, /new Set\(\(enrolledPayload\.data\?\.rows\|\|\[\]\)\.map\(row=>String\(row\.student_id\)\)\)/);
assert.match(app, /filter\(student=>!enrolledIds\.has\(String\(student\.id\)\)\)/);
assert.match(app, /error\.code==='DUPLICATE_ENROLLMENT'\?'Học viên đã được ghi danh trong lớp này\.'/);
console.log('r19b enrollment UI contract: PASS');

import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';

const source = readFileSync('static/modules/training_routes.js', 'utf8');
for (const marker of [
  "'/training/announcement': [",
  "'/training/event': [",
  'openTrainingMutationModal',
  'openTrainingDeleteModal',
  "data.branch_id = Number(branchSelect.value)",
  'full_body: true',
  "reason?.code === 'CONFLICT'",
  "data-action=\"edit\"",
  "data-action=\"delete\"",
  "route === '/training/announcement' || route === '/training/event'",
]) assert.ok(source.includes(marker), `missing UI contract marker: ${marker}`);
assert.match(source, /name = 'branch_id'/);
assert.match(source, /branchSelect\.required = true/);
assert.match(source, /document\.querySelector\('#branch-manager-scope select'\)\?\.value/);
assert.match(source, /new URLSearchParams\(\{ route, \.\.\.\(row\.version/);
assert.match(source, /save\.setAttribute\('form', form\.id/);
assert.match(source, /form\.append\(actions\)/);
assert.match(source, /save\.type = 'submit'/);
assert.match(source, /form\.addEventListener\('submit'/);
const shell = readFileSync('static/app.js', 'utf8');
assert.match(shell, /Tất cả chi nhánh \(ADMIN\)/);
assert.match(shell, /danh sách lớp xem tất cả chi nhánh/);
console.log('r19c announcement/event UI contract: PASS');

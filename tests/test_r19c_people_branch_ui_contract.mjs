import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';

const people = readFileSync('static/modules/w6_screen_utils.js', 'utf8');
const training = readFileSync('static/modules/training_routes.js', 'utf8');

assert.match(people, /name: 'branch_id', label: 'Chi nhánh'/);
assert.match(people, /required: branchOptions\.length > 1/);
assert.match(people, /api\('\/api\/branch-manager\/scope'\)/);
assert.match(people, /name: 'branch_id'[\s\S]*value:/);
assert.match(training, /lifecycle\('COMPLETED', 'Đóng', 'close'\)/);
assert.match(training, /lifecycle\('CANCELLED', 'Hủy', 'cancel'\)/);
assert.match(training, /study_status: \['OPEN'\]/);
assert.match(training, /localStudyStatusRows\(baseRows, state\.filters\)/);
assert.match(training, /rows = localStudyStatusRows\(rows, state\.filters\)/);
console.log('r19c people branch + class status UI contract: PASS');

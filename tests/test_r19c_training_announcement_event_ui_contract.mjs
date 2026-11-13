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
console.log('r19c announcement/event UI contract: PASS');

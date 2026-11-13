import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';

const app = readFileSync('static/app.js', 'utf8');
const training = readFileSync('static/modules/training_routes.js', 'utf8');

function sliceBetween(source, start, end) {
  const from = source.indexOf(start);
  assert.notEqual(from, -1, `missing ${start}`);
  const to = source.indexOf(end, from);
  return source.slice(from, to === -1 ? source.length : to);
}

const detailLifecycle = sliceBetween(app, 'const transition = (endpoint, label) => {', "el.querySelector('#class-detail-close')");
const rowLifecycle = sliceBetween(training, 'const lifecycle = (status, label, endpoint) => {', 'const close = lifecycle(');
for (const source of [detailLifecycle, rowLifecycle]) {
  assert.doesNotMatch(source, /window\.prompt|globalThis\.alert|window\.alert/, 'lifecycle uses browser prompt/alert');
  assert.match(source, /role=\\"dialog\\"|role=\"dialog\"/, 'lifecycle has an in-page dialog');
  assert.match(source, /name=\\"apply_from\\"|name=\"apply_from\"/, 'lifecycle captures apply_from');
  assert.match(source, /lifecycle-error/, 'lifecycle has an inline error line');
  assert.match(source, /version: detail\.version, updated_at: detail\.updated_at/, 'lifecycle sends CAS fields');
}
console.log('r19c lifecycle UI contract: PASS');

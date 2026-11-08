import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { reportPageSizes } from '../static/modules/report_table.js';

const specs = JSON.parse(await readFile(new URL('../screen_specs/reference-screen-specs.json', import.meta.url), 'utf8'));
const byRoute = new Map(specs.screens.map(screen => [screen.route, screen]));

// The due-date screen is the only requested candidate with a retained,
// route-owned selector. Its observed values are the complete pager contract.
const dueDate = byRoute.get('/report/training/due_date_student');
assert.ok(dueDate, 'due-date report remains in the reference catalog');
assert.deepEqual(reportPageSizes(dueDate.filters), {
  values: ['10', '20', '50'],
  observed: true,
  name: 'course_table_length',
});

// Row counts cannot establish capacity. These candidates have no observed
// page-size selector, so the renderer must preserve all rows and omit a pager.
for (const route of [
  '/report/finance/debt',
  '/report/finance/student_finance',
  '/report/crm/bill/index',
  '/report/crm/customer_care/index',
]) {
  const screen = byRoute.get(route);
  assert.ok(screen, `${route} remains in the reference catalog`);
  assert.deepEqual(reportPageSizes(screen.filters), { values: [], observed: false, name: '' }, route);
}

console.log('Report pagination contracts PASS');

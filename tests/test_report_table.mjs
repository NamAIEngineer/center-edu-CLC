import assert from 'node:assert/strict';
import test from 'node:test';
import {
  createReportTable,
  mountReportTable,
  paginateReportRows,
  reportPageSizes,
} from '../static/modules/report_table.js';
import { TRAINING_AUTO_FILTER_ROUTES, TRAINING_REPORT_PAGINATION } from '../static/modules/report_training.js';

const columns = [{ key: 'id', label: 'Mã' }];

function rows(count) {
  return Array.from({ length: count }, (_, id) => ({ id: id + 1 }));
}

function mounted(options = {}) {
  const body = { innerHTML: '' };
  const footer = { innerHTML: '' };
  const listeners = {};
  const parentListeners = {};
  const parent = {
    addEventListener(type, handler) { parentListeners[type] = handler; },
    querySelectorAll() { return options.controls || []; },
  };
  const root = {
    dataset: {},
    parentElement: parent,
    addEventListener(type, handler) { listeners[type] = handler; },
    querySelector(selector) {
      if (selector.includes('body')) return body;
      if (selector.includes('footer')) return footer;
      return null;
    },
  };
  const controller = mountReportTable(root, { columns, ...options });
  return { body, footer, listeners, parentListeners, root, controller };
}

function click(view, dataset) {
  view.listeners.click({ target: { closest: () => ({ dataset, disabled: false }) } });
}

test('selector metadata stays authoritative and normalizes numeric values', () => {
  assert.deepEqual(
    reportPageSizes([{ name: 'course-table_length', label: '10 20 50', options: ['10', '20', '50'] }]),
    { values: ['10', '20', '50'], observed: true, name: 'course-table_length' },
  );
  assert.equal(paginateReportRows(rows(21), 2, '10').rows[0].id, 11);
  assert.equal(paginateReportRows(rows(21), 2, 10).rows.length, 10);
});

test('explicit pager-only config slices rows without adding a page-size selector', () => {
  const source = rows(21);
  const html = createReportTable({ columns, rows: source, pagination: { enabled: true, pageSize: 10 } });
  assert.equal((html.match(/<td>/g) || []).length, 10);
  assert.match(html, /data-report-table-footer/);
  assert.match(html, /Hiển thị 1 đến 10 của 21 bản ghi/);
  assert.doesNotMatch(html, /<select/);
  assert.equal(source.length, 21);
});

test('unproven routes keep all API rows and preserve no-footer semantics', () => {
  const source = rows(100);
  const html = createReportTable({ columns, rows: source });
  assert.equal((html.match(/<td>/g) || []).length, 100);
  assert.doesNotMatch(html, /data-report-table-footer|<select/);
  assert.equal(reportPageSizes([{ name: 'status', options: ['10', '20'] }]).observed, false);
  assert.equal(source.length, 100);
});

test('pager-only next, numbered, previous and last-page navigation expose every row', () => {
  const view = mounted({ rows: rows(61), pagination: { enabled: true, pageSize: 10 } });
  assert.match(view.body.innerHTML, /<td>1<\/td>/);
  click(view, { reportPageAction: 'next' });
  assert.match(view.body.innerHTML, /<td>11<\/td>/);
  click(view, { reportPage: '4' });
  assert.match(view.body.innerHTML, /<td>31<\/td>/);
  click(view, { reportPageAction: 'prev' });
  assert.match(view.body.innerHTML, /<td>21<\/td>/);
  click(view, { reportPage: '7' });
  assert.match(view.body.innerHTML, /<td>61<\/td>/);
  assert.match(view.footer.innerHTML, /Hiển thị 61 đến 61 của 61 bản ghi/);
  assert.equal(view.root.dataset.reportPage, '7');
});

test('setRows resets page and empty-state footer semantics', () => {
  const view = mounted({ rows: rows(21), pagination: { enabled: true, pageSize: 10 } });
  click(view, { reportPage: '2' });
  assert.match(view.body.innerHTML, /<td>11<\/td>/);
  view.controller.setRows([{ id: '<unsafe>' }]);
  assert.equal(view.root.dataset.reportPage, '1');
  assert.match(view.body.innerHTML, /&lt;unsafe&gt;/);
  view.controller.setRows([]);
  assert.match(view.body.innerHTML, /class="empty"/);
  assert.match(view.footer.innerHTML, /Hiển thị 0 đến 0 của 0 bản ghi/);
});

test('All selector preserves all rows and selected replacement controls', () => {
  const selected = { name: 'report_table_length', value: 'All' };
  const view = mounted({
    rows: rows(31),
    pageSizes: ['10', '25', 'All'],
    pageSizeControl: { name: selected.name },
    controls: [selected],
  });
  assert.equal((view.body.innerHTML.match(/<tr>/g) || []).length, 1 + 0 + 30);
  assert.match(view.footer.innerHTML, /Hiển thị 1 đến 31 của 31 bản ghi/);
  selected.value = '25';
  view.parentListeners.change({ target: selected });
  assert.equal((view.body.innerHTML.match(/<tr>/g) || []).length, 25);
  assert.match(view.footer.innerHTML, /Hiển thị 1 đến 25 của 31 bản ghi/);
});

test('training metadata limits explicit pager defaults to the seven observed routes', () => {
  const expected = [
    '/report/training/allocation_student/index',
    '/report/training/change_class/index',
    '/report/training/reserve_training/index',
    '/report/training/using_course/index',
    '/report/training/enroll/index',
    '/report/training/allocation_hours/index',
    '/report/training/class/v2',
    '/report/training/due_date_student',
    '/report/training/schedule/index',
  ];
  assert.deepEqual(Object.keys(TRAINING_REPORT_PAGINATION).sort(), expected.sort());
  assert.deepEqual(TRAINING_REPORT_PAGINATION['/report/training/allocation_student/index'], { enabled: true, pageSize: 20 });
  assert.deepEqual(TRAINING_REPORT_PAGINATION['/report/training/allocation_hours/index'], { enabled: true, pageSize: 20 });
  for (const route of expected.filter(route => !['/report/training/allocation_student/index', '/report/training/allocation_hours/index', '/report/training/due_date_student'].includes(route))) {
    assert.deepEqual(TRAINING_REPORT_PAGINATION[route], { enabled: true, pageSize: 10 });
  }
  assert.deepEqual(TRAINING_REPORT_PAGINATION['/report/training/due_date_student'], { enabled: true, pageSize: 15 });
});

test('training report routes retain observed update-only filter behavior', () => {
  assert.deepEqual(TRAINING_AUTO_FILTER_ROUTES, [
    '/report/training/test',
    '/report/training/class/v2',
    '/report/training/allocation_student/index',
    '/report/training/homework_ratio/index',
    '/report/training/due_date_student',
  ]);
});

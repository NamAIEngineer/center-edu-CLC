import assert from 'node:assert/strict';
import test from 'node:test';

import { tenantConfigHtml } from '../static/modules/w6_screen_utils.js';

const catalog = [
  { title: 'Báo cáo mới', route: '/report/training/new' },
  { title: 'Báo cáo đã tắt', route: '/report/training/off' },
  { title: 'Báo cáo trùng', route: '/report/finance/duplicate-a' },
  { title: 'Báo cáo trùng', route: '/report/finance/duplicate-b' },
];

function reportRow(html, title) {
  const escaped = title.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  return html.match(new RegExp(`<tr class="w6-tenant-report-row"[^>]*data-report-name="${escaped}"[^>]*>[\\s\\S]*?<\\/tr>`))?.[0] || '';
}

test('tenant config defaults unique missing records on and preserves persisted off', () => {
  const html = tenantConfigHtml(catalog, [
    { id: 7, data: { report_name: 'Báo cáo đã tắt', enabled: 'Không' } },
  ], { writable: true, settingsReadable: true });

  const missing = reportRow(html, 'Báo cáo mới');
  const persistedOff = reportRow(html, 'Báo cáo đã tắt');
  assert.match(missing, /data-w6-tenant-toggle[^>]*checked/);
  assert.doesNotMatch(persistedOff, /data-w6-tenant-toggle[^>]*checked/);
});

test('tenant config keeps duplicate titles disabled and master disabled', () => {
  const html = tenantConfigHtml(catalog, [], { writable: true, settingsReadable: true });
  const duplicateRows = [...html.matchAll(/<tr class="w6-tenant-report-row"[^>]*data-report-name="Báo cáo trùng"[^>]*>[\s\S]*?<\/tr>/g)].map((match) => match[0]);
  assert.equal(duplicateRows.length, 2);
  for (const row of duplicateRows) {
    assert.match(row, /data-w6-tenant-toggle disabled/);
    assert.doesNotMatch(row, /data-w6-tenant-toggle[^>]*checked/);
  }
  assert.match(html, /data-w6-tenant-master="true" disabled/);
  assert.doesNotMatch(html, /data-w6-tenant-master="true"[^>]*checked/);
});

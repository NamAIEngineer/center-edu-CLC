import assert from 'node:assert/strict';
import fs from 'node:fs';

const source = fs.readFileSync(new URL('../static/modules/report_crm_center.js', import.meta.url), 'utf8');

const routes = [
  '/report/crm/customer_care_result',
  '/report/crm/customer_care_result_by_center',
  '/report/crm/customer_care_result_by_district',
  '/report/crm/customer_care_result_by_dob',
  '/report/crm/customer_care_result_by_source',
  '/report/crm/customer_care_result_by_sale',
];
const targets = [
  '/report/crm/customer_care_result_by_center',
  '/report/crm/customer_care_result_by_district',
  '/report/crm/customer_care_result_by_dob',
  '/report/crm/customer_care_result_by_source',
  '/report/crm/customer_care_result_by_sale',
];

for (const route of routes) {
  assert.match(source, new RegExp(`['"]${route.replaceAll('/', '\\/')}['"]`), `route tab metadata missing: ${route}`);
}
for (const target of targets) {
  assert.match(source, new RegExp(`['"]${target.replaceAll('/', '\\/')}['"]`), `sibling route target missing: ${target}`);
}
assert.match(source, /CUSTOMER_CARE_RESULT_TAB_INDEX/);
assert.match(source, /screen\.__birthdayViewHandler\s*=\s*index\s*=>/, 'birthday lens callback must request the selected persisted view');
assert.match(source, /bindReportTabNavigation\(screen, ctx\.route\)/, 'report routes must use the shared tab binding');
assert.match(source, /onBirthdayView\?\.\(index\)/, 'birthday tab click must invoke its view callback');

console.log('CRM customer-care result tabs: route metadata and navigation bindings present');

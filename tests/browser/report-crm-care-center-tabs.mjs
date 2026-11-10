import assert from 'node:assert/strict';
import { createRequire } from 'node:module';

const base = process.env.CENTER_EDU_TEST_BASE;
const password = process.env.CENTER_EDU_TEST_PASSWORD;
const browserModule = process.env.CENTER_EDU_TEST_BROWSER_MODULE || 'playwright';
if (!base || !password) throw new Error('CENTER_EDU_TEST_BASE and CENTER_EDU_TEST_PASSWORD are required');
const require = createRequire(import.meta.url);
const { chromium } = require(browserModule);
const browser = await chromium.launch({ headless: true, ...(process.env.CENTER_EDU_TEST_BROWSER_EXE ? { executablePath: process.env.CENTER_EDU_TEST_BROWSER_EXE } : {}) });
try {
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
  await page.goto(base, { waitUntil: 'domcontentloaded' });
  await page.locator('input[name="login"]').fill(process.env.CENTER_EDU_TEST_LOGIN || 'admin');
  await page.locator('input[type="password"]').fill(password);
  await page.locator('button[type="submit"]').click();
  await page.waitForTimeout(500);
  await page.goto(`${base}/report/crm/customer_care_result_by_center`, { waitUntil: 'networkidle' });
  await page.waitForTimeout(600);

  const expectedTabs = ['Trung tâm', 'Nhóm sale', 'Sale'];
  assert.deepEqual(await page.locator('#screen .ref-tabs .ref-tab').allTextContents(), expectedTabs);
  assert.deepEqual(await page.locator('#screen thead th').allTextContents(), ['Trung tâm', 'Tổng KH', 'Đã xử lý', 'Chưa xử lý', 'Tỷ lệ xử lý']);
  const centerTotals = await page.locator('#screen tbody tr').evaluateAll(rows => rows.map(row => [...row.cells].map(cell => cell.textContent.trim())));
  assert.ok(centerTotals.length > 0);
  assert.ok(centerTotals.every(row => row.length === 5));

  await page.getByRole('tab', { name: 'Sale', exact: true }).click();
  await page.waitForTimeout(350);
  assert.equal(await page.locator('#screen .ref-tabs .ref-tab.active').textContent(), 'Sale');
  assert.equal((await page.locator('#screen thead th').first().textContent()).trim(), 'Nhân viên sale');
  assert.ok(await page.locator('#screen tbody tr').count() > 0);

  await page.getByRole('tab', { name: 'Nhóm sale', exact: true }).click();
  await page.waitForTimeout(350);
  assert.equal(await page.locator('#screen .ref-tabs .ref-tab.active').textContent(), 'Nhóm sale');
  assert.equal((await page.locator('#screen thead th').first().textContent()).trim(), 'Nhóm sale');
  assert.match(await page.locator('#screen tbody').innerText(), /Chưa có dữ liệu nhóm sale/);
} finally {
  await browser.close();
}

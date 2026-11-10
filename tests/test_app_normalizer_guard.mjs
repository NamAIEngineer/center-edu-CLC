import assert from 'node:assert/strict';
import test from 'node:test';
import { createRequire } from 'node:module';

// Opt-in browser regression against a disposable local server. Dependencies and
// synthetic login are supplied by the caller; this test never starts a server.
test('class-owned real controls survive normalization; unmarked screens retain fallback', { skip: !process.env.CENTER_EDU_TEST_BROWSER_MODULE }, async () => {
  const require = createRequire(import.meta.url);
  const { chromium } = require(process.env.CENTER_EDU_TEST_BROWSER_MODULE);
  const browser = await chromium.launch({ headless: true, executablePath: process.env.CENTER_EDU_TEST_BROWSER_EXE });
  try {
    const page = await browser.newPage();
    await page.goto(process.env.CENTER_EDU_TEST_BASE);
    await page.locator('input[name="login"]').fill('admin');
    await page.locator('input[type="password"]').fill(process.env.CENTER_EDU_TEST_PASSWORD);
    await page.locator('button[type="submit"]').click();
    await page.waitForTimeout(700);
    await page.goto(process.env.CENTER_EDU_TEST_BASE + '/training/class', { waitUntil: 'networkidle' });
    await page.waitForTimeout(900);
    const result = await page.evaluate(async () => {
      const screen = document.querySelector('#screen');
      const controls = [...screen.querySelectorAll('.filter-strip input,.filter-strip select')];
      const snapshot = control => JSON.stringify({ name: control.name, type: control.type, value: control.value, options: control.options ? [...control.options].map(o => [o.value, o.textContent, o.selected, o.disabled]) : null });
      const before = controls.map(snapshot);
      let eventCount = 0;
      controls[0].addEventListener('normalizer-regression', () => eventCount++);
      const original = observedSpec;
      let calls = 0;
      observedSpec = async () => { calls++; return { filters: [] }; };
      try {
        await normalizeObservedControls(screen, '/training/class');
        const after = [...screen.querySelectorAll('.filter-strip input,.filter-strip select')];
        const preserved = controls.length === after.length && controls.every((control, index) => control === after[index] && before[index] === snapshot(control));
        after[0].dispatchEvent(new Event('normalizer-regression'));
        const ownedCalls = calls;
        delete screen.dataset.trainingObservedRoute;
        const fallback = document.createElement('div');
        await normalizeObservedControls(fallback, '/training/class');
        return { semanticKeys: [...screen.querySelectorAll('[data-class-filter]')].map(control => control.dataset.classFilter), preserved, eventCount, ownedCalls, fallbackCalls: calls };
      } finally { observedSpec = original; }
    });
    assert.deepEqual(result.semanticKeys, ['status', 'course_id', 'q', 'manager', 'study_status', 'teacher', 'start_from', 'start_to', 'end_from', 'end_to']);
    assert.equal(result.preserved, true);
    assert.equal(result.eventCount, 1);
    assert.equal(result.ownedCalls, 0);
    assert.equal(result.fallbackCalls, 1);
  } finally { await browser.close(); }
});

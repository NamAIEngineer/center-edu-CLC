import { createRequire } from 'node:module';
const require = createRequire(import.meta.url);
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
let playwright;
try {
  playwright = require('playwright');
} catch {
  playwright = require('/Users/nam/claude-center-audit/node_modules/playwright');
}
const { chromium } = playwright;

const BASE = process.env.LOCAL_BASE || 'http://127.0.0.1:19888';
const PASSWORD = process.env.LOCAL_PASS || '';
const STAGE = process.env.CSS_STAGE || 'after';
const OUT = path.resolve(process.env.CSS_EVIDENCE_DIR || 'plans/center-edu-rebuild-20261030/evidence/visual/shared-control-css-lane-20261108');
const CSS_PATH = path.resolve(process.env.CSS_SOURCE_FILE || 'static/app.css');
const CHROME = process.env.CHROME_BIN || '/Users/nam/Library/Caches/ms-playwright/chromium_headless_shell-1248/chrome-headless-shell-mac-arm64/chrome-headless-shell';
const WIDTHS = [
  { width: 1280, height: 900, name: '1280x900' },
  { width: 1440, height: 900, name: '1440x900' },
  { width: 1920, height: 900, name: '1920x900' },
  { width: 390, height: 844, name: '390x844' },
];
const ROUTES = [
  { path: '/center/student/index', name: 'center-student' },
  { path: '/center/upload_address', name: 'center-tabs-and-wide-table' },
  { path: '/report/crm/contract/index', name: 'ref-tabs-and-filters' },
  { path: '/report/finance/student_finance', name: 'wide-table-scroll' },
  { path: '/report/center/birth_day/index', name: 'center-report-tabs' },
  { path: '/setup/daily-evaluation', name: 'textarea-form' },
];
const FAILURES = [];
const CHECKS = [];

function failure(message) { FAILURES.push(message); }
function verify(condition, message) {
  CHECKS.push({ status: condition ? 'PASS' : 'FAIL', message });
  if (!condition && STAGE === 'after') failure(message);
}

async function main() {
  if (!PASSWORD) throw new Error('LOCAL_PASS must be set outside the evidence artifacts');
  fs.mkdirSync(path.join(OUT, STAGE, 'screenshots'), { recursive: true });
  const cssHash = crypto.createHash('sha256').update(fs.readFileSync(CSS_PATH)).digest('hex');
  const browser = await chromium.launch({ headless: true, executablePath: CHROME });
  const results = [];

  try {
    for (const viewport of WIDTHS) {
      const context = await browser.newContext({ viewport: { width: viewport.width, height: viewport.height }, locale: 'vi-VN' });
      const page = await context.newPage();
      const consoleErrors = [];
      page.on('console', message => { if (message.type() === 'error') consoleErrors.push(message.text().slice(0, 160)); });
      await page.goto(`${BASE}/`, { waitUntil: 'networkidle', timeout: 20000 });
      const login = page.locator('input[name="login"], input[name="username"], input[type="text"], input[type="email"]').first();
      if (await login.count()) {
        if (!PASSWORD) throw new Error('LOCAL_PASS must be set outside the evidence artifacts');
        await login.fill('admin');
        await page.locator('input[type="password"]').first().fill(PASSWORD);
        await page.locator('button[type="submit"], button:has-text("Đăng nhập")').first().click();
        await page.waitForLoadState('networkidle').catch(() => {});
        await page.waitForTimeout(500);
      }
      const stylesheetSyntax = await page.evaluate(css => {
        const parsed = new CSSStyleSheet();
        parsed.replaceSync(css);
        return parsed.cssRules.length;
      }, fs.readFileSync(CSS_PATH, 'utf8'));
      verify(stylesheetSyntax > 0, `${viewport.name}: static/app.css parses as a stylesheet`);

      for (const route of ROUTES) {
        await page.goto(`${BASE}${route.path}`, { waitUntil: 'networkidle', timeout: 20000 });
        await page.waitForTimeout(650);
        let formTextarea = false;
        if (route.path === '/setup/daily-evaluation') {
          await page.evaluate(() => {
            const fixture = document.createElement('label');
            fixture.className = 'css-regression-textarea-fixture';
            fixture.innerHTML = 'Mô tả<textarea></textarea>';
            document.querySelector('#screen')?.append(fixture);
          });
          formTextarea = await page.locator('#screen .css-regression-textarea-fixture textarea').count() > 0;
        }

        const measurements = await page.evaluate(() => {
          const box = element => {
            const rect = element.getBoundingClientRect();
            const style = getComputedStyle(element);
            return {
              tag: element.tagName,
              cls: String(element.className || ''),
              x: Math.round(rect.x * 100) / 100,
              y: Math.round(rect.y * 100) / 100,
              width: Math.round(rect.width * 100) / 100,
              height: Math.round(rect.height * 100) / 100,
              right: Math.round(rect.right * 100) / 100,
              scrollWidth: element.scrollWidth,
              clientWidth: element.clientWidth,
              scrollHeight: element.scrollHeight,
              clientHeight: element.clientHeight,
              overflowX: style.overflowX,
              overflowY: style.overflowY,
              minWidth: style.minWidth,
              maxWidth: style.maxWidth,
              boxSizing: style.boxSizing,
              resize: style.resize,
              widthStyle: style.width,
              flexWrap: style.flexWrap,
            };
          };
          const screen = document.querySelector('#screen');
          const strip = document.querySelector('.filter-strip');
          const filterControls = [...(strip ? strip.querySelectorAll('input, select, textarea, button, .select2-container, .select2-selection--multiple') : [])]
            .filter(el => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; })
            .map(el => {
              let cell = el;
              while (cell.parentElement && cell.parentElement !== strip) cell = cell.parentElement;
              return { control: box(el), cell: box(cell) };
            });
          const textareas = [...document.querySelectorAll('textarea')].filter(el => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; }).map(box);
          const tabs = [...document.querySelectorAll('.ref-tabs')].map(box);
          const tableWraps = [...document.querySelectorAll('.table-wrap')].map(box);
          const strayScroll = [...document.querySelectorAll('.content *')].filter(el => {
            if (el.closest('.table-wrap, .modal, .nav-flyout')) return false;
            const style = getComputedStyle(el);
            const scrollY = el.scrollHeight - el.clientHeight > 4;
            const scrollX = el.scrollWidth - el.clientWidth > 4;
            return ((style.overflowY === 'auto' || style.overflowY === 'scroll') && scrollY) || ((style.overflowX === 'auto' || style.overflowX === 'scroll') && scrollX);
          }).map(box);
          const root = document.scrollingElement || document.documentElement;
          const sidebar = document.querySelector('.sidebar');
          return {
            route: location.pathname,
            viewport: { width: innerWidth, height: innerHeight },
            document: { scrollWidth: root.scrollWidth, clientWidth: root.clientWidth },
            screen: screen ? box(screen) : null,
            filterStrip: strip ? box(strip) : null,
            filterControls,
            textareas,
            tabs,
            tableWraps,
            strayScroll,
            sidebar: sidebar ? box(sidebar) : null,
          };
        });
        const screenshot = path.join(OUT, STAGE, 'screenshots', `${route.name}-${viewport.name}.png`);
        await page.screenshot({ path: screenshot, fullPage: false });

        for (const item of measurements.filterControls) {
          verify(item.control.minWidth === '0px' && item.control.maxWidth !== 'none' && item.control.boxSizing === 'border-box', `${route.name} ${viewport.name}: filter control has bounded min/max width and border-box sizing`);
          verify(item.control.x >= item.cell.x - 1 && item.control.right <= item.cell.right + 2, `${route.name} ${viewport.name}: ${item.control.tag}.${item.control.cls} stays inside its filter grid cell`);
        }
        for (const tab of measurements.tabs) {
          verify(tab.overflowX === 'visible' && tab.overflowY === 'visible' && tab.flexWrap === 'wrap', `${route.name} ${viewport.name}: ref-tabs wrap without an inner scroll area`);
          verify(tab.scrollWidth <= tab.clientWidth + 2, `${route.name} ${viewport.name}: ref-tabs do not overflow horizontally`);
        }
        for (const wrap of measurements.tableWraps) {
          verify(wrap.overflowX === 'auto' && wrap.overflowY === 'hidden', `${route.name} ${viewport.name}: table-wrap keeps horizontal scroll only`);
          if (route.path === '/report/finance/student_finance') verify(wrap.scrollWidth > wrap.clientWidth, `${viewport.name}: wide report table remains horizontally scrollable`);
        }
        if (route.path === '/center/student/index') {
          verify(measurements.strayScroll.length === 0, `${viewport.name}: center/student has no nested content scrollbar outside table-wrap`);
          verify(measurements.sidebar?.overflowY === (viewport.width > 900 ? 'auto' : 'visible'), `${viewport.name}: sidebar keeps its intended responsive behavior`);
        }
        if (route.path === '/setup/daily-evaluation') {
          verify(formTextarea, `${viewport.name}: setup form opens a textarea editor`);
          verify(measurements.textareas.length > 0, `${viewport.name}: textarea is visible for resize verification`);
          for (const textarea of measurements.textareas) {
            verify(textarea.resize === 'vertical' && textarea.maxWidth === '100%' && textarea.minWidth === '0px' && textarea.boxSizing === 'border-box', `${viewport.name}: textarea resizes vertically within its parent width`);
            const form = await page.locator('#screen .css-regression-textarea-fixture textarea').first().evaluate(el => ({ right: el.getBoundingClientRect().right, parentRight: el.parentElement.getBoundingClientRect().right }));
            verify(form.right <= form.parentRight + 2, `${viewport.name}: textarea stays within its form cell`);
          }
        }
        verify(measurements.document.scrollWidth <= viewport.width + 1, `${route.name} ${viewport.name}: document has no horizontal overflow`);
        results.push({ ...measurements, routeName: route.name, stage: STAGE, screenshot, formTextarea, consoleErrors });
      }
      await context.close();
    }
  } finally {
    await browser.close();
  }

  const summary = {
    stage: STAGE,
    capturedAt: new Date().toISOString(),
    baseUrl: BASE,
    source: { commit: process.env.SOURCE_COMMIT || 'UNSET', staticAppCssSha256: cssHash },
    widths: WIDTHS,
    routes: ROUTES.map(route => route.path),
    checks: CHECKS,
    failures: FAILURES,
    results,
    limitations: ['Synthetic isolated SQLite and demo session only.', 'No live/reference browser state touched.', 'Screenshots demonstrate CSS geometry only; no reference parity claim.'],
  };
  fs.writeFileSync(path.join(OUT, STAGE, 'ui-css-regressions.json'), JSON.stringify(summary, null, 2) + '\n');
  console.log(JSON.stringify({ stage: STAGE, routes: results.length, checks: CHECKS.length, failures: FAILURES.length, cssSha256: cssHash, evidence: path.join(OUT, STAGE) }, null, 2));
  if (FAILURES.length) process.exit(1);
}

main().catch(error => { console.error(`CSS_REGRESSION_ERROR: ${error.message}`); process.exit(1); });

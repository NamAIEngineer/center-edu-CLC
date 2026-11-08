// Automated UI defect sweep across all screens of the rebuild.
// Detects: horizontal overflow (vỡ layout), sidebar overlapping header/content on scroll,
// content hidden behind fixed sidebar, elements past viewport, console errors.
const fs = require('fs'); const path = require('path');
const { chromium } = require('/Users/nam/claude-center-audit/node_modules/playwright');
const EXE = '/Users/nam/Library/Caches/ms-playwright/chromium_headless_shell-1248/chrome-headless-shell-mac-arm64/chrome-headless-shell';
const ROOT = __dirname;
const BASE = process.env.LOCAL_BASE || 'http://127.0.0.1:18990';
const PASS = process.env.LOCAL_PASS || '';
const PATHS = fs.readFileSync(path.join(ROOT, 'all_paths.txt'), 'utf8').trim().split(',');
const STAGE = process.env.CSS_STAGE || 'after';
const EVIDENCE_ROOT = path.resolve(process.env.CSS_EVIDENCE_DIR || ROOT);
const OUT = path.join(EVIDENCE_ROOT, STAGE, 'ui-sweep');
const SHOTS = path.join(OUT, 'shots');

(async () => {
  if (!PASS) throw new Error('LOCAL_PASS must be set outside the evidence artifacts');
  fs.mkdirSync(SHOTS, { recursive: true });
  const b = await chromium.launch({ headless: true, executablePath: EXE });
  const ctx = await b.newContext({ viewport: { width: 1440, height: 900 }, locale: 'vi-VN' });
  const page = await ctx.newPage();
  await page.goto(BASE + '/', { waitUntil: 'networkidle' }).catch(()=>{});
  const login = page.locator('input[name="login"], input[type="text"], input[type="email"]').first();
  if (await login.count()) {
    await login.fill('admin'); await page.locator('input[type="password"]').first().fill(PASS);
    await page.locator('button[type="submit"], button:has-text("Đăng nhập")').first().click().catch(()=>{});
    await page.waitForLoadState('networkidle').catch(()=>{}); await page.waitForTimeout(1500);
  }
  const results = [];
  for (const p of PATHS) {
    const errs = [];
    const onErr = m => { if (m.type() === 'error') errs.push(m.text().slice(0,120)); };
    page.on('console', onErr);
    try {
      await page.goto(BASE + p, { waitUntil: 'networkidle', timeout: 20000 }).catch(()=>{});
      await page.waitForTimeout(700);
      const m = await page.evaluate(() => {
        const de = document.scrollingElement || document.documentElement;
        const vw = window.innerWidth, vh = window.innerHeight;
        const pageOverflowX = Math.max(0, de.scrollWidth - vw);
        // find sidebar: fixed/sticky element on far left, tall
        let sb = null; let sbInfo = null;
        document.querySelectorAll('aside, nav, [class*="sidebar"], [class*="side-"], [class*="menu"]').forEach(el => {
          const r = el.getBoundingClientRect(); const cs = getComputedStyle(el);
          if (r.height > vh*0.5 && r.left < 120 && r.width > 40 && r.width < 320) {
            if (!sb || r.height > sb.getBoundingClientRect().height) { sb = el; sbInfo = { left: r.left, top: r.top, width: r.width, height: r.height, pos: cs.position, z: cs.zIndex }; }
          }
        });
        // header: top bar
        let hdInfo = null;
        document.querySelectorAll('header, [class*="header"], [class*="topbar"], [class*="navbar"]').forEach(el => {
          const r = el.getBoundingClientRect(); const cs = getComputedStyle(el);
          if (r.top < 80 && r.width > vw*0.4 && r.height > 30 && r.height < 120) { if (!hdInfo || r.width > hdInfo.width) hdInfo = { top: r.top, width: r.width, height: r.height, z: cs.zIndex, left: r.left }; }
        });
        // elements overflowing viewport horizontally
        let overEls = 0; let worst = 0;
        document.querySelectorAll('body *').forEach(el => {
          const r = el.getBoundingClientRect();
          if (r.width > 0 && r.right > vw + 2) { let a=el.parentElement, clipped=false; while(a&&a!==document.body){const o=getComputedStyle(a).overflowX; if(o==='auto'||o==='scroll'||o==='hidden'){const ar=a.getBoundingClientRect(); if(ar.right<=vw+2){clipped=true;break;}} a=a.parentElement;} if(!clipped){ overEls++; worst = Math.max(worst, r.right - vw);} }
        });
        // main content left (is it clear of sidebar?)
        let mainLeft = null;
        const main = document.querySelector('main, [class*="content"], [class*="main"]');
        if (main) mainLeft = Math.round(main.getBoundingClientRect().left);
        return { vw, vh, pageOverflowX, sbInfo, hdInfo, overEls, worst: Math.round(worst), mainLeft, docH: de.scrollHeight };
      });
      // scroll to bottom, re-check sidebar vs header overlap
      await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
      await page.waitForTimeout(400);
      const scrolled = await page.evaluate(() => {
        const vw = window.innerWidth, vh = window.innerHeight;
        let sbTopAfter = null, sbPos = null;
        document.querySelectorAll('aside, nav, [class*="sidebar"], [class*="menu"]').forEach(el => {
          const r = el.getBoundingClientRect(); const cs = getComputedStyle(el);
          if (r.height > vh*0.4 && r.left < 120 && r.width > 40 && r.width < 320) { sbTopAfter = Math.round(r.top); sbPos = cs.position; }
        });
        const de = document.scrollingElement || document.documentElement;
        return { sbTopAfter, sbPos, scrollY: Math.round(window.scrollY), overflowXAfter: Math.max(0, de.scrollWidth - vw) };
      });
      // severity scoring
      const flags = [];
      if (m.pageOverflowX > 4) flags.push('PAGE_OVERFLOW_X=' + m.pageOverflowX);
      if (m.overEls > 0) flags.push('ELEMS_PAST_VIEWPORT=' + m.overEls + '(+' + m.worst + 'px)');
      // sidebar scrolls away (not fixed) => content overlap risk when scrolling
      if (m.sbInfo && m.sbInfo.pos !== 'fixed' && m.sbInfo.pos !== 'sticky') flags.push('SIDEBAR_NOT_FIXED(pos=' + m.sbInfo.pos + ')'); if (!m.sbInfo) flags.push('SIDEBAR_NOT_FOUND');
      if (scrolled.scrollY > 50 && scrolled.sbTopAfter != null && scrolled.sbTopAfter > 80 && (scrolled.sbPos === 'fixed')) flags.push('SIDEBAR_DRIFT_top=' + scrolled.sbTopAfter);
      if (errs.length) flags.push('JS_ERR=' + errs.length);
      const sev = (m.pageOverflowX>4?2:0) + (m.overEls>0?2:0) + (flags.some(f=>f.startsWith('SIDEBAR'))?3:0) + (errs.length?1:0);
      results.push({ path: p, sev, flags, pageOverflowX: m.pageOverflowX, overEls: m.overEls, worst: m.worst, sb: m.sbInfo, hd: m.hdInfo, scrolled, errs: errs.slice(0,3) });
      if (sev >= 3) { const f = p.replace(/[^a-z0-9]+/gi,'_').replace(/^_|_$/g,'')||'root'; await page.screenshot({ path: path.join(SHOTS, 'S'+sev+'_'+f+'.png'), fullPage: false }).catch(()=>{}); }
    } catch (e) { results.push({ path: p, sev: 9, flags: ['NAV_ERR'], err: e.message }); }
    page.off('console', onErr);
  }
  results.sort((a,b)=>b.sev-a.sev);
  fs.writeFileSync(path.join(OUT, 'ui-sweep.json'), JSON.stringify(results, null, 2));
  const bad = results.filter(r=>r.sev>0);
  console.log('TOTAL', results.length, 'WITH_ISSUES', bad.length);
  console.log('TOP', JSON.stringify(results.slice(0,25).map(r=>({p:r.path,sev:r.sev,f:r.flags})), null, 0).slice(0,2500));
  await b.close();
})().catch(e => { console.error('ERR', e.message); process.exit(1); });

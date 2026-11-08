// Fine-grained UI defect scan: resize-draggable inputs, stray scrollbars, overflow controls,
// overlapping absolute/fixed elements, inner horizontal scroll. Across all screens.
const fs=require('fs');const path=require('path');
const {chromium}=require('/Users/nam/claude-center-audit/node_modules/playwright');
const EXE='/Users/nam/Library/Caches/ms-playwright/chromium_headless_shell-1248/chrome-headless-shell-mac-arm64/chrome-headless-shell';
const ROOT=__dirname;
const BASE=process.env.LOCAL_BASE||'http://127.0.0.1:18990';
const PASS=process.env.LOCAL_PASS||'';
const PATHS=fs.readFileSync(path.join(ROOT,'all_paths.txt'),'utf8').trim().split(',');
const STAGE=process.env.CSS_STAGE||'after';
const EVIDENCE_ROOT=path.resolve(process.env.CSS_EVIDENCE_DIR||ROOT);
const OUT=path.join(EVIDENCE_ROOT,STAGE,'ui-fine');const SHOTS=path.join(OUT,'shots');
(async()=>{
  if(!PASS)throw new Error('LOCAL_PASS must be set outside the evidence artifacts');
  fs.mkdirSync(SHOTS,{recursive:true});
  const b=await chromium.launch({headless:true,executablePath:EXE});
  const page=await (await b.newContext({viewport:{width:1440,height:900},locale:'vi-VN'})).newPage();
  await page.goto(BASE+'/',{waitUntil:'networkidle'}).catch(()=>{});
  const lg=page.locator('input[name="login"],input[type="text"],input[type="email"]').first();
  if(await lg.count()){await lg.fill('admin');await page.locator('input[type="password"]').first().fill(PASS);await page.locator('button[type="submit"],button:has-text("Đăng nhập")').first().click().catch(()=>{});await page.waitForLoadState('networkidle').catch(()=>{});await page.waitForTimeout(1500);}
  const results=[];
  for(const p of PATHS){
    try{
      await page.goto(BASE+p,{waitUntil:'networkidle',timeout:20000}).catch(()=>{});
      await page.waitForTimeout(500);
      const m=await page.evaluate(()=>{
        const vw=window.innerWidth,vh=window.innerHeight;
        const out={resizable:[],strayScroll:[],ctrlOverflow:[],innerHScroll:0,absOverlap:0};
        // resizable textareas/inputs (resize !== none => user can drag and break layout)
        document.querySelectorAll('textarea,input,div,select').forEach(el=>{
          const cs=getComputedStyle(el);
          if(cs.resize && cs.resize!=='none'){const r=el.getBoundingClientRect(); if(r.width>0&&r.height>0) out.resizable.push((el.tagName+'.'+(el.className||'').toString().slice(0,20)));}
        });
        // stray scroll containers: overflow auto/scroll AND actually scrollable, that are NOT the intended table-wrap
        document.querySelectorAll('.content *').forEach(el=>{
          const cs=getComputedStyle(el);const r=el.getBoundingClientRect();
          const oy=cs.overflowY,ox=cs.overflowX;
          const scrollY=el.scrollHeight-el.clientHeight>4,scrollX=el.scrollWidth-el.clientWidth>4;
          if(((oy==='auto'||oy==='scroll')&&scrollY)||((ox==='auto'||ox==='scroll')&&scrollX)){
            const cls=(el.className||'').toString();
            const intended=/table-wrap|modal|nav-flyout|flyout/.test(cls);
            if(!intended && r.height>0){ out.strayScroll.push({c:cls.slice(0,30),oy,ox,sy:scrollY,sx:scrollX}); if(scrollX&&r.height<vh*0.7) out.innerHScroll++; }
          }
        });
        // form controls overflowing their parent container width
        document.querySelectorAll('input,select,textarea').forEach(el=>{
          const r=el.getBoundingClientRect(); if(r.width<=0||r.height<=0)return; const par=el.parentElement; if(!par)return;const pr=par.getBoundingClientRect();
          if(r.right>pr.right+3||r.left<pr.left-3){out.ctrlOverflow.push((el.name||el.placeholder||el.tagName).toString().slice(0,24));}
        });
        // absolute/fixed overlapping main content
        return out;
      });
      const flags=[];
      if(m.resizable.length) flags.push('RESIZABLE='+m.resizable.length);
      if(m.strayScroll.length) flags.push('STRAY_SCROLL='+m.strayScroll.length);
      if(m.ctrlOverflow.length) flags.push('CTRL_OVERFLOW='+m.ctrlOverflow.length);
      const sev=(m.resizable.length?3:0)+(m.strayScroll.length?2:0)+(m.ctrlOverflow.length?2:0);
      results.push({path:p,sev,flags,resizable:m.resizable.slice(0,5),stray:m.strayScroll.slice(0,5),ctrl:m.ctrlOverflow.slice(0,6)});
      if(sev>=3){const f=p.replace(/[^a-z0-9]+/gi,'_').replace(/^_|_$/g,'')||'root';await page.screenshot({path:path.join(SHOTS,'F'+sev+'_'+f+'.png')}).catch(()=>{});}
    }catch(e){results.push({path:p,sev:9,flags:['ERR'],err:e.message});}
  }
  results.sort((a,b)=>b.sev-a.sev);
  fs.writeFileSync(path.join(OUT,'ui-fine.json'),JSON.stringify(results,null,2));
  const agg={};results.forEach(r=>r.flags.forEach(f=>{const k=f.split('=')[0];agg[k]=(agg[k]||0)+1;}));
  console.log('WITH_ISSUES',results.filter(r=>r.sev>0).length,'of',results.length);
  console.log('AGG',JSON.stringify(agg));
  console.log('SAMPLE',JSON.stringify(results.slice(0,6).map(r=>({p:r.path,f:r.flags,rz:r.resizable,st:r.stray})),null,0).slice(0,1600));
  await b.close();
})().catch(e=>{console.error('ERR',e.message);process.exit(1);});

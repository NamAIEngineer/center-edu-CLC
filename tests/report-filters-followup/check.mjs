import assert from 'node:assert/strict';
import { createRequire } from 'node:module';
const require = createRequire(import.meta.url);
const { chromium } = require(process.env.CENTER_EDU_TEST_BROWSER_MODULE || 'playwright');
const base = process.env.CENTER_EDU_TEST_BASE;
if (!base) throw new Error('CENTER_EDU_TEST_BASE is required');
const browser = await chromium.launch({headless:true, ...(process.env.CENTER_EDU_TEST_BROWSER_EXECUTABLE ? {executablePath:process.env.CENTER_EDU_TEST_BROWSER_EXECUTABLE} : {})});
const failures = [];
const page = await browser.newPage({viewport:{width:1440,height:900}});
page.on('pageerror', error => failures.push(`pageerror: ${error.message}`));
const checks = [];
async function check(name, run) { try { await run(); checks.push({name,result:'PASS'}); } catch(error) { failures.push(`${name}: ${error.message}`); checks.push({name,result:'FAIL',error:error.message}); } }
async function open(route) { await page.goto(base + route,{waitUntil:'networkidle'}); await page.waitForTimeout(500); }
try {
 await check('paired training date labels retain exact observed text; no generated suffixes', async()=>{
  await open('/report/training/allocation_student/index');
  const placeholders = await page.locator('.filter-strip input').evaluateAll(xs=>xs.map(x=>x.placeholder));
  assert.equal(placeholders.filter(value=>value==='Ngày đăng kí học').length,2);
  assert.equal(placeholders.filter(value=>value==='Ngày kết thúc').length,2);
  assert.ok(!placeholders.some(value=>/\(\d+\)/.test(value)));
  assert.equal(await page.locator('[data-report-form] button[type=submit],[data-report-form] button[type=reset]').count(),0);
 });
 await check('training test keeps observed class/test placeholders and Excel only', async()=>{
  await open('/report/training/test');
  assert.equal(await page.locator('select[name=filter_2]').inputValue(),'Chọn lớp học');
  assert.equal(await page.locator('select[name=filter_3]').inputValue(),'Chọn bài kiểm tra');
  assert.equal(await page.locator('[data-report-form] button').count(),0);
  assert.deepEqual(await page.locator('.page-actions .report-action').allTextContents(),['Excel']);
 });
 await check('class summary route has search only, no invented Excel/filter/reset', async()=>{
  await open('/report/training/class/v2');
  assert.equal(await page.locator('.filter-strip input').count(),1);
  assert.equal(await page.locator('.report-action,[data-report-form] button').count(),0);
 });
 await check('contract class retains its observed first option and repeated English dates', async()=>{
  await open('/report/crm/contract/index');
  const select = page.locator('select[name=class_id]');
  assert.equal(await select.inputValue(),'Chọn lớp học');
  assert.equal(await select.locator('option').first().textContent(),'Chọn lớp học');
  assert.equal(await page.locator('input[placeholder="From date"]').count(),2);
  assert.equal(await page.locator('input[placeholder="To date"]').count(),2);
  assert.equal(await page.locator('[data-report-form] button').count(),0);
  assert.deepEqual(await page.locator('.page-actions .report-action').allTextContents(),['Excel']);
 });
 for (const route of ['/report/finance/debt','/report/finance/student_finance']) {
  await check(`${route}: filters then observed actions then truthful summary`, async()=>{
   await open(route);
   const order = await page.evaluate(()=>{
    const strip=document.querySelector('[data-report-filter-shell]'), summary=document.querySelector('[data-report-summary]');
    return !!(strip.compareDocumentPosition(summary)&Node.DOCUMENT_POSITION_FOLLOWING);
   });
   assert.equal(order,true);
   assert.deepEqual(await page.locator('[data-report-filter-actions] button').allTextContents(),['Excel','Cập nhật dữ liệu']);
   assert.equal(await page.locator('[data-report-run],[data-report-reset]').count(),0);
   assert.equal(await page.locator('input[name=from_end_date_timetable]').getAttribute('placeholder'),'Từ ngày (Thời khóa biểu)');
   assert.ok((await page.locator('[data-report-summary] span').allTextContents()).every(x=>x==='—'));
  });
 }
 await check('blank invoice rendering is column-scoped; unknown/zero/escaping preserved', async()=>{
  await open('/report/finance/debt');
  const values = await page.evaluate(async()=>{
   const renderers = new Map();
   const module = await import('/modules/report_finance.js');
   await module.register({registerScreen:(route,render)=>renderers.set(route,render)});
   const screen=document.createElement('div');
   const payload={columns:[{key:'ma_hoa_on'},{key:'ngay_tao_hoa_on'},{key:'other'},{key:'zero'},{key:'text'}],filters:[{name:'q',type:'text',label:'Query'}],rows:[{ma_hoa_on:null,ngay_tao_hoa_on:'',other:null,zero:0,text:'<script>unit</script>'},{ma_hoa_on:'UNKNOWN',ngay_tao_hoa_on:'Chưa cập nhật',other:null,zero:0,text:'x'}]};
   await renderers.get('/report/finance/debt')(screen,{route:'/report/finance/debt',api:async()=>({data:payload})});
   const debt=[...screen.querySelectorAll('tbody tr')].map(row=>[...row.cells].map(cell=>cell.textContent));
   if(screen._financeRepairTimer) clearInterval(screen._financeRepairTimer);
   return debt;
  });
  assert.deepEqual(values,[['','','—','0','<script>unit</script>'],['—','—','—','0','x']]);
 });
 await check('unrelated finance report retains pre-existing actions', async()=>{
  await open('/report/finance/class_revenue_tracking/index');
  assert.deepEqual(await page.locator('.screen-actions button').allTextContents(),['Lọc','Excel']);
  assert.equal(await page.locator('[data-report-run],[data-report-reset]').count(),2);
 });
} finally { await browser.close(); }
console.log(JSON.stringify({checks,failures},null,2));
if (failures.length) process.exitCode=1;

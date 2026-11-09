/* Finance tabs own distinct projections. Keep the domain table and its event
 * listeners intact while a secondary view is open; never turn inventory into
 * receipts or ordinary bank transfers into online invoices. */
const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const rowsOf = payload => Array.isArray(payload) ? payload : Array.isArray(payload?.data) ? payload.data : payload?.data?.items || payload?.items || [];
const fold = value => String(value ?? '').normalize('NFD').replace(/[\u0300-\u036f]/g,'').replace(/đ/g,'d').toLowerCase().trim();
const navigate = route => { history.pushState({}, '', route); window.dispatchEvent(new PopStateEvent('popstate')); };
const money = value => value == null || value === '' ? '' : `${Number(value).toLocaleString('vi-VN')} VND`;
const date = value => { const m = String(value || '').match(/^(\d{4})-(\d{2})-(\d{2})/); return m ? `${m[3]}/${m[2]}/${m[1]}` : value || ''; };

export function itemCategories(items = []) {
  return [...new Set(items.map(row => String(row.category || '').trim()).filter(Boolean))].map(name => ({name}));
}
export function spendCategories(items = []) {
  return [...new Set(items.map(row => String(row.category || '').trim()).filter(Boolean))].map(name => ({name}));
}
export function billView(row) {
  const kind = fold(row.invoice_type || row.bill_type || row.kind || row.view);
  if (['online','hoa don online'].includes(kind)) return 2;
  if (['advance','prepaid','dong truoc','hoa don dong tien truoc'].includes(kind)) return 1;
  return 0;
}
export function reserveView(row) { return fold(row.status) === 'da hoan tra' ? 0 : 1; }

const layouts = {
  item: {
    initial: 1, endpoint:'/api/finance/items',
    views: [
      {headers:['No.','Danh mục vật phẩm'], project: rows => itemCategories(rows).map((row,i)=>[i+1,row.name])},
      null,
      {headers:['No.','Mã phiếu nhập','Ngày nhập','Vật phẩm','Số lượng','Người tạo'], project: rows => rows.filter(row=>['in','import','nhap'].includes(fold(row.movement_type || row.direction))).map((row,i)=>[i+1,row.receipt_code,date(row.movement_date),row.fullname,row.quantity,row.created_by])},
      {headers:['No.','Mã phiếu xuất','Ngày xuất','Vật phẩm','Số lượng','Người tạo'], project: rows => rows.filter(row=>['out','export','xuat'].includes(fold(row.movement_type || row.direction))).map((row,i)=>[i+1,row.receipt_code,date(row.movement_date),row.fullname,row.quantity,row.created_by])},
    ],
  },
  spend: {initial:1,endpoint:'/api/finance/spends',views:[{headers:['No.','Danh mục'],project:rows=>spendCategories(rows).map((row,i)=>[i+1,row.name])},null]},
  reserve: {initial:1,endpoint:'/api/finance/reserves',views:[{headers:['Mã hoàn trả','Học viên','Ngày hoàn trả','Số tiền hoàn trả','Hợp đồng','Người tạo','Trạng thái','Công cụ'],project:rows=>rows.filter(row=>reserveView(row)===0).map(row=>[row.reserve_code,row.student_name,date(row.reserve_date),money(row.amount_or_days),row.contract_code,row.created_by,row.status,''])},null]},
  bill: {initial:0,endpoint:'/api/finance/bills',views:[null,...[1,2].map(index=>({headers:['No.','Mã hóa đơn','Mã hợp đồng','Lớp học','Đối tượng','Khách hàng','Thanh toán','Nhân viên sale','Người tạo','Trạng thái xác nhận','Hình thức thanh toán','Ghi chú','Công cụ'],project:rows=>rows.filter(row=>billView(row)===index).map((row,i)=>[i+1,row.invoice_code,row.contract_code,row.class_code,row.subject,row.customer_name,money(row.payment_amount),row.sales_owner,row.created_by,row.confirmation_status,row.payment_method,row.note,''])}))]},
};

export function financePresentation(screen, kind) {
  let panel = screen.querySelector('.finance-owned-panel');
  if (!panel) { panel = document.createElement('section'); panel.className = 'finance-owned-panel'; panel.append(...screen.childNodes); screen.append(panel); }
  const heading = panel.querySelector('.screen-head');
  panel.dataset.financeKind = kind;
  const tabs = panel.querySelector('.ref-tabs');
  if (tabs && panel.firstElementChild !== tabs) panel.prepend(tabs);
  let filters = panel.querySelector('.filter-strip');
  if (!filters) { filters=document.createElement('div');filters.className='filter-strip';tabs?.after(filters); }
  if (heading) {
    const actions = document.createElement('div');actions.className='finance-view-actions';
    actions.append(...heading.querySelectorAll('button'));filters.append(actions);heading.remove();
  }
  const search = panel.querySelector('.table-toolbar .table-search');
  if (search && !filters.querySelector('input:not([type=hidden])')) {
    const label=document.createElement('label');label.append(search);filters.prepend(label);
    search.placeholder='Tìm trong bảng...';
  }
  filters.querySelectorAll('label').forEach(label => [...label.childNodes].filter(node => node.nodeType===3).forEach(node=>node.remove()));
  panel.querySelectorAll('.table-toolbar h2').forEach(node=>node.remove());
  if (filters.querySelector('input:not([type=hidden])')) panel.querySelectorAll('.table-toolbar .table-search').forEach(node=>node.remove());
  panel.querySelectorAll('input[type=date], input[data-date-input]').forEach(node=>{node.type='text';node.setAttribute('data-date-input','');node.dataset.dateText='1';node.inputMode='numeric';node.placeholder=node.id.includes('from')?'Từ ngày':'Đến ngày';});
  if (!document.querySelector('#finance-owned-presentation')) {
    const style=document.createElement('style');style.id='finance-owned-presentation';
    style.textContent=`.finance-owned-panel>.ref-tabs{padding:0 0 20px;gap:24px;margin:0;border-bottom:1px solid #eceef5;min-height:50px}.finance-owned-panel>.filter-strip{display:flex;align-items:center;flex-wrap:wrap;margin:0;padding:32px 0;gap:16px}.finance-owned-panel>.filter-strip label{order:0;flex:0 1 200px;min-width:0;margin:0}.finance-owned-panel>.filter-strip input,.finance-owned-panel>.filter-strip select{height:35px;max-width:100%;box-sizing:border-box}.finance-owned-panel .finance-view-actions{order:100;display:flex;gap:5px;margin-left:auto}.finance-owned-panel .finance-view-actions button{height:35px;border-radius:3px;padding:0 12px}.finance-owned-panel>.table-card{padding:0;margin:0;border:0;box-shadow:none}.finance-owned-panel .table-toolbar:empty{display:none}.finance-owned-panel table{border-collapse:collapse}.finance-owned-panel th,.finance-owned-panel td{padding:15px 9px;font-size:13px;border:1px solid #edf0f6;vertical-align:middle;white-space:normal}.finance-owned-panel .table-footer{display:flex;align-items:center;gap:12px;padding:20px 0 0}.finance-owned-panel .finance-page-count{margin-right:auto}.finance-owned-panel .table-page-size{display:flex;align-items:center;gap:4px;white-space:nowrap}.finance-owned-panel .table-page-size select{width:auto;padding:4px 10px;border:1px solid #e5e9f2;border-radius:3px}.finance-owned-panel textarea{resize:vertical;max-width:100%;box-sizing:border-box}.finance-owned-panel .finance-view-actions button[id*=export]{background:#2bbf9a;color:white;border:0}.finance-owned-panel .ref-tab{font-weight:400;color:#191c26;padding:20px 8px}.finance-owned-panel .ref-tab:before{content:'▤';color:#9296a4;padding-right:8px}.finance-owned-panel .ref-tab.active{color:#635ce4}.finance-owned-panel th{background:#fff;color:#15191f;font-weight:600}.finance-owned-panel[data-finance-kind=assessment]>.filter-strip{padding:24px 0}.finance-owned-panel[data-finance-kind=assessment] .finance-view-actions button{background:#2bbf9a;color:white}.finance-owned-panel[data-finance-kind=assessment] .filter-strip>label{flex-basis:250px}.finance-owned-panel[data-finance-kind=reserve] .filter-strip>label{flex-basis:232px}.finance-owned-panel[data-finance-kind=reserve] th:first-child{min-width:90px}.finance-owned-panel[data-finance-kind=spend]>.filter-strip{gap:20px}.finance-owned-panel[data-finance-kind=spend]>.filter-strip label{flex:0 1 130px}.finance-owned-panel[data-finance-kind=spend] .finance-view-actions #export-finance-spends{background:#6869dc}.finance-owned-panel[data-finance-kind=spend] .finance-view-actions #add-finance-spend{background:#2bbf9a}.finance-owned-panel .finance-spend-total{padding:10px 0;color:#343944}.finance-owned-panel .badge{padding:5px 9px;border-radius:14px}`;
    document.head.append(style);
  }
  if(kind==='spend'){
    const actions=filters.querySelector('.finance-view-actions');const excel=actions?.querySelector('[id*=export]');if(excel)actions.prepend(excel);
    const card=panel.querySelector('[data-table-card]');const source=globalThis.CenterEdu?.state?.tableRegistry?.[card?.dataset.tableCard];
    if(source&&!panel.querySelector('.finance-spend-total')){const summary=document.createElement('div');summary.className='finance-spend-total';summary.textContent=`Tổng các khoản chi: ${source.rows.reduce((sum,row)=>sum+Number(row.amount_vnd||0),0).toLocaleString('vi-VN')} VND`;card.before(summary);}
  }
  if(kind==='bill' && !filters.querySelector('.finance-filter-commands')) {
    const commands=document.createElement('div');commands.className='finance-filter-commands';
    commands.append(...filters.querySelectorAll(':scope > button'));
    filters.append(commands);
  }
  if(kind==='bill' && !document.querySelector('#finance-bill-presentation')) {
    const style=document.createElement('style');style.id='finance-bill-presentation';
    style.textContent=`.finance-owned-panel[data-finance-kind=bill]>.filter-strip{display:grid;grid-template-columns:repeat(7,minmax(0,1fr));gap:24px 6px;padding:24px 0 18px}.finance-owned-panel[data-finance-kind=bill]>.filter-strip>label:nth-of-type(5){grid-row:2;grid-column:1}.finance-owned-panel[data-finance-kind=bill]>.filter-strip>label:nth-of-type(6){grid-row:2;grid-column:2}.finance-owned-panel[data-finance-kind=bill]>.filter-strip>label:nth-of-type(7){grid-row:2;grid-column:3}.finance-owned-panel[data-finance-kind=bill] .finance-view-actions{grid-row:2;grid-column:6/8;justify-self:end}.finance-owned-panel[data-finance-kind=bill] .finance-filter-commands{grid-row:2;grid-column:4/6;display:flex;gap:5px;justify-self:start}.finance-owned-panel[data-finance-kind=bill] .finance-filter-commands button{height:35px;width:auto;min-width:0;padding:0 10px}.finance-owned-panel[data-finance-kind=bill] .finance-summary{margin:0 0 24px}.finance-owned-panel[data-finance-kind=bill] td{padding:22px 9px}@media(max-width:900px){.finance-owned-panel[data-finance-kind=bill]>.filter-strip{display:flex}}`;
    document.head.append(style);
  }
  const card=panel.querySelector('[data-table-card]');
  const registry=globalThis.CenterEdu?.state?.tableRegistry?.[card?.dataset.tableCard];
  if(registry){registry.pageSizes=[5,10,25,50];card.dataset.pageSize ||= '10';registry.pageSizeLabel='Hiển thị';registry.render?.();}
  const update=()=>{
    const footer=card?.querySelector('.table-footer');
    const registry=globalThis.CenterEdu?.state?.tableRegistry?.[card?.dataset.tableCard];
    if (!footer || !registry) return;
    let count=footer.querySelector('.finance-page-count');if(!count){count=document.createElement('span');count.className='finance-page-count';footer.prepend(count);}
    const total=registry.rows.length,size=Number(card.dataset.pageSize||10),page=Number(card.dataset.page||0);
    const sizeSelect=footer.querySelector('.table-page-size select');if(sizeSelect&&sizeSelect.value!==String(size))sizeSelect.value=String(size);
    const text=`Hiển thị ${total?page*size+1:0} đến ${Math.min((page+1)*size,total)} của ${total} bản ghi`;
    if(count.textContent!==text)count.textContent=text;
  };
  if(card){new MutationObserver(update).observe(card,{childList:true,subtree:true});queueMicrotask(update);}
}

export function bindFinanceViews(screen, kind, context = {}) {
  financePresentation(screen, kind);
  const layout = layouts[kind];
  const tabs = [...screen.querySelectorAll('.ref-tabs .ref-tab')];
  if (!layout || !tabs.length) return;
  const base = [...screen.querySelectorAll('[data-table-card], .table-wrap')].filter(node => !node.parentElement.closest('[data-table-card], .table-wrap'));
  const card=screen.querySelector('[data-table-card]');
  const registry=globalThis.CenterEdu?.state?.tableRegistry?.[card?.dataset.tableCard];
  if(registry && (kind==='bill'||kind==='reserve')) {
    registry.rows=registry.rows.filter(row=>kind==='bill'?billView(row)===0:reserveView(row)===1);
    registry.render?.();
  }
  const anchors = base.map(node => { const anchor=document.createComment('finance-base-table');node.before(anchor);return anchor; });
  const panel = document.createElement('section');panel.className='finance-tab-panel';
  let version=0;
  const select = async index => {
    const ticket=++version;
    tabs.forEach((tab,i)=>{tab.classList.toggle('active',i===index);tab.setAttribute('aria-selected',String(i===index));});
    screen.dataset.activeFinanceTab=String(index);
    screen.dataset.activeFinanceView=tabs[index]?.textContent.trim() || '';
    base.forEach((node,i)=>{if(index===layout.initial){if(!node.isConnected)anchors[i].after(node);}else{node.remove();}});
    screen.querySelectorAll('.finance-view-actions button').forEach(button=>{ if(!/excel|xuất/i.test(button.textContent)) button.hidden=index!==layout.initial; });
    if(index===layout.initial){panel.remove();return;}
    if(!panel.isConnected)anchors[0] ? anchors[0].after(panel) : screen.append(panel);
    panel.innerHTML='<div class="empty">Đang tải dữ liệu…</div>';
    try {
      const payload=await (context.api || globalThis.CenterEdu.api)(layout.endpoint);
      if(ticket!==version || !panel.isConnected)return;
      const view=layout.views[index], rows=view.project(rowsOf(payload));
      panel.innerHTML=`<div class="table-wrap"><table><thead><tr>${view.headers.map(header=>`<th>${esc(header)}</th>`).join('')}</tr></thead><tbody>${rows.length?rows.map(row=>`<tr>${row.map(value=>`<td>${esc(value)}</td>`).join('')}</tr>`).join(''):`<tr><td class="empty" colspan="${view.headers.length}">Không tìm thấy dữ liệu</td></tr>`}</tbody></table></div><div class="table-footer">Hiển thị ${rows.length?1:0} đến ${rows.length} của ${rows.length} bản ghi</div>`;
      screen.dispatchEvent(new CustomEvent('finance-tab-change',{detail:{index,rows:rows.length,view:screen.dataset.activeFinanceView}}));
    }catch(error){if(ticket===version)panel.innerHTML=`<div class="error">${esc(error.message)}</div>`;}
  };
  tabs.forEach((tab,index)=>tab.addEventListener('click',event=>{event.preventDefault();event.stopImmediatePropagation();select(index);},true));
  select(layout.initial);
}

const routeHandlers = new WeakMap();
export function bindFinanceRouteTabs(screen, kind) {
  const pricing = ['/crm/discount','/crm/packet','/finance/assessment','/finance/assessment?view=packet'];
  const transfers = ['/finance/transfer/index','/finance/transfer/index?view=item','/finance/history_move_student'];
  const labels = kind==='assessment' ? ['Ưu đãi - Khuyến mãi','Gói học phí','Định giá','Định giá gói học phí'] : ['Chuyển nhượng hợp đồng','Chuyển nhượng khoản thu vật phẩm','Danh sách hợp đồng chênh lệch phí khi chuyển lớp'];
  const routes = kind==='assessment' ? pricing : transfers;
  const initial = kind==='assessment' ? (new URLSearchParams(location.search).get('view')==='packet'?3:2) : kind==='history' ? 2 : new URLSearchParams(location.search).get('view')==='item'?1:0;
  let strip=screen.querySelector('.ref-tabs');
  if(!strip){strip=document.createElement('div');strip.className='ref-tabs';strip.setAttribute('role','tablist');strip.innerHTML=labels.map(label=>`<button type="button" class="ref-tab" role="tab">${esc(label)}</button>`).join('');screen.querySelector('.card')?.prepend(strip);}
  strip?.querySelectorAll('.ref-tab').forEach((tab,index)=>{tab.classList.toggle('active',index===initial);tab.setAttribute('aria-selected',String(index===initial));});
  if(routeHandlers.has(screen))screen.removeEventListener('click',routeHandlers.get(screen),true);
  const handler=event=>{const tab=event.target.closest('.ref-tabs .ref-tab');if(!tab||!screen.contains(tab))return;const index=labels.indexOf(tab.textContent.trim());if(index<0)return;event.preventDefault();event.stopImmediatePropagation();if(index!==initial && routes[index])navigate(routes[index]);};
  routeHandlers.set(screen,handler);screen.addEventListener('click',handler,true);
}

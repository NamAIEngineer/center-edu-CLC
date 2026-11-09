/* Finance accumulate-points local screen contract. */
export const pointsScreen = {
  route: '/finance/accumulate_points', entity: 'finance_point_rules',
  tabs: ['Thiết lập tích điểm', 'Thống kê tích điểm'],
  filters: [{name:'q', type:'text', placeholder:'Tìm trong bảng...'},{name:'page_size', type:'select', options:[5,10,25,50]}],
  columns: ['No.','Mã tích điểm','Tên','Trạng thái','Số tiền tích 1 điểm','Tỉ lệ quy đổi','Trung tâm áp dụng','Công cụ'],
  actions: ['Tạo mã tích điểm','Excel'],
  form: [
    {name:'code', label:'Mã tích điểm', required:true}, {name:'name', label:'Tên', required:true},
    {name:'status', label:'Trạng thái', type:'select', options:[['active','Hoạt động'],['inactive','Ngừng hoạt động']], required:true},
    {name:'amount_per_point', label:'Số tiền tích 1 điểm', required:true},
    {name:'conversion_rate', label:'Tỉ lệ quy đổi', required:true},
    {name:'center_id', label:'Trung tâm áp dụng', required:true}
  ], permissions: {read:['ADMIN','STAFF','TEACHER'], write:['ADMIN','STAFF']}
};
export const statusLabel = s => s === 'active' ? 'Hoạt động' : 'Ngừng hoạt động';
export const formatVnd = v => `${Number(v || 0).toLocaleString('vi-VN')} VND`;
export function renderPointRows(items = []) { return items.map((r,i) => ({no:i+1, code:r.code, name:r.name, status:statusLabel(r.status), amountPerPoint:formatVnd(r.amount_per_point), conversionRate:formatVnd(r.conversion_rate), center:r.center_name, action:'…'})); }
export async function loadPointRules(apiFetch, filters = {}) { const p = new URLSearchParams(filters); return apiFetch(`/api/finance/point-rules?${p}`); }
export async function exportPointRules(apiFetch, filters = {}) { const p = new URLSearchParams(filters); return apiFetch(`/api/export/finance-point-rules?${p}`); }

function bindFinanceTabState(screen) {
  const tabs = [...screen.querySelectorAll('[role="tab"], .ref-tab')];
  if (!tabs.length) return;
  tabs.forEach((tab, index) => {
    if (tab.dataset.financeTabBound === 'true') return;
    tab.dataset.financeTabBound = 'true';
    tab.addEventListener('click', () => {
      tabs.forEach((node, i) => {
        const active = i === index;
        node.classList.toggle('active', active);
        node.setAttribute('aria-selected', String(active));
      });
      const label = tab.textContent.trim();
      screen.dataset.activeFinanceTab = String(index);
      screen.dataset.activeFinanceView = label;
      // Filter only rows carrying a persisted view/type/scope marker.
      // Unmarked rows stay visible because the backing contract does not
      // authorize inventing a tab-to-record mapping.
      screen.querySelectorAll('tbody tr').forEach((row) => {
        const marker = String(row.dataset.view || row.dataset.type || row.dataset.scope || row.dataset.kind || '').trim().toLowerCase();
        if (!marker) { row.hidden = false; return; }
        row.hidden = !(marker === label.toLowerCase() || marker.includes(label.toLowerCase()) || label.toLowerCase().includes(marker));
      });
      screen.dispatchEvent(new CustomEvent('finance-tab-change', { detail: { index, label, view: label } }));
    });
  });
}

export function register(global) {
  const host = global || {};
  host.financePoints = pointsScreen;
  const render = async (screen, context) => {
    const fn = globalThis.financePoints;
    if (typeof fn !== 'function') return false;
    await fn(screen, context);
    bindFinanceTabState(screen);
    return true;
  };
  if (typeof host.registerScreen === 'function') host.registerScreen(pointsScreen.route, render);
  return pointsScreen;
}

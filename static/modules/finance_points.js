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
const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
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
  const render = async (screen, context = {}) => {
    const api = context.api || global?.api;
    if (typeof api !== 'function') return false;
    if (screen.dataset.financePointsTabsBound === 'true') return false;
    screen.dataset.financePointsTabsBound = 'true';
    screen.addEventListener('click', async event => {
      const tab = event.target.closest('.ref-tabs .ref-tab');
      if (!tab || !screen.contains(tab)) return;
      const tabs = [...screen.querySelectorAll('.ref-tabs .ref-tab')];
      const index = tabs.indexOf(tab);
      if (index !== 0 && index !== 1) return;
      event.preventDefault(); event.stopImmediatePropagation();
      tabs.forEach((node, i) => { node.classList.toggle('active', i === index); node.setAttribute('aria-selected', String(i === index)); });
      const filters = [...screen.querySelectorAll('.filter-strip')];
      const card = screen.querySelector('[data-table-card], .table-card');
      if (!card) return;
      card.hidden = index === 1;
      filters.forEach(node => { node.hidden = index === 1; });
      screen.querySelectorAll('#add-finance-point,#export-finance-points').forEach(node => { node.hidden = index === 1; });
      let statisticsPanel = screen.querySelector('.finance-points-statistics');
      if (index === 0) { statisticsPanel?.remove(); return; }
      if (!statisticsPanel) {
        statisticsPanel = document.createElement('section');
        statisticsPanel.className = 'card table-card finance-points-statistics';
        card.after(statisticsPanel);
      }
      statisticsPanel.innerHTML = '<div class="empty">Đang tải dữ liệu…</div>';
      try {
        const response = await api('/api/finance/point-rules');
        const stats = response?.data?.statistics || { items: [], total: 0 };
        const headers = ['No.', 'Học viên', 'Mã học viên', 'Điểm thay đổi', 'Loại giao dịch', 'Thời gian'];
        const rows = Array.isArray(stats.items) ? stats.items : [];
        const body = rows.length ? rows.map((row, i) => `<tr><td>${i + 1}</td><td>${esc(row.student_name)}</td><td>${esc(row.student_code)}</td><td>${esc(row.points_delta)}</td><td>${esc(row.event_type)}</td><td>${esc(row.occurred_at)}</td></tr>`).join('') : `<tr><td colspan="${headers.length}" class="empty">Chưa có giao dịch tích điểm</td></tr>`;
        statisticsPanel.innerHTML = `<div class="table-wrap"><table><thead><tr>${headers.map(label => `<th>${esc(label)}</th>`).join('')}</tr></thead><tbody>${body}</tbody></table></div><div class="table-footer">Hiển thị ${rows.length ? 1 : 0} đến ${rows.length} của ${Number(stats.total || 0)} bản ghi</div>`;
      } catch (error) { statisticsPanel.innerHTML = `<div class="empty">${esc(error.message)}</div>`; }
    }, true);
    return false;
  };
  if (typeof host.registerScreen === 'function') host.registerScreen(pointsScreen.route, render);
  return pointsScreen;
}

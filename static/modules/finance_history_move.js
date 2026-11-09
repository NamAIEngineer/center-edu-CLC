/* Customer-facing history-move screen contract for /finance/history_move_student. */
export const financeHistoryMove = {
  route: '/finance/history_move_student',
  tabs: ['Chuyển nhượng hợp đồng', 'Chuyển nhượng khoản thu vật phẩm', 'Danh sách hợp đồng chênh lệch phí khi chuyển lớp'],
  columns: ['Học viên', 'Khóa học ban đầu', 'Khóa học chuyển đến', 'Lớp học ban đầu', 'Lớp học chuyển đến', 'Còn lại', 'Số buổi', 'Giá tiền', 'Tiền trả thêm', 'Trạng thái', 'Hành động'],
  filters: ['q', 'status'], permissions: { read: ['ADMIN', 'STAFF', 'TEACHER'], write: ['ADMIN', 'STAFF'] },
  statuses: ['Chưa thực hiện-Đã xếp lớp', 'Đã xử lý', 'Đã hủy'],
};
export const historyMoveQuery = (filters = {}) => { const p = new URLSearchParams(); financeHistoryMove.filters.forEach(k => { const v = String(filters[k] ?? '').trim(); if (v) p.set(k, v); }); for (const key of ['page', 'page_size']) { const v = String(filters[key] ?? '').trim(); if (v) p.set(key, v); } return p; };
export const loadHistoryMoves = (apiFetch, filters = {}) => apiFetch(`/api/finance/history-move-student?${historyMoveQuery(filters)}`);
export const exportHistoryMoves = (apiFetch, filters = {}) => apiFetch(`/api/export/finance-history-move-student?${historyMoveQuery(filters)}`);

const escapeCell = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));

async function renderHistoryMove(screen, context = {}) {
  try {
    const render = async (filters = {}) => {
      const response = await context.api(`/api/finance/history-move-student?${historyMoveQuery(filters)}`);
      const payload = response?.data || {};
      const rows = Array.isArray(payload) ? payload : (payload.items || []);
      const tbody = screen.querySelector('tbody');
      if (tbody) tbody.innerHTML = rows.map(row => `<tr>${[row.student_name,row.original_course_name,row.destination_course_name,row.original_class_name,row.destination_class_name,row.remaining_amount,row.remaining_sessions,row.price_vnd,row.additional_amount,row.status,''].map(value => `<td>${escapeCell(value)}</td>`).join('')}</tr>`).join('') || `<tr><td colspan="${financeHistoryMove.columns.length}">Chưa có dữ liệu</td></tr>`;
      const count = screen.querySelector('[data-history-move-count]');
      if (count) count.textContent = String(payload.total ?? rows.length);
    };
    screen.innerHTML = `<section class="card finance-module-screen"><header><h1>Danh sách hợp đồng chênh lệch phí khi chuyển lớp</h1><p>Đối chiếu số tiền còn lại khi chuyển lớp.</p></header><div class="filter-strip" data-history-move-filters><label><input id="history-move-query" placeholder="Tìm trong bảng..." aria-label="Tìm trong bảng..."></label><label><select id="history-move-status" aria-label="Trạng thái"><option value="">Tất cả</option>${financeHistoryMove.statuses.map(status => `<option value="${escapeCell(status)}">${escapeCell(status)}</option>`).join('')}</select></label><label><span>Hiển thị</span><select id="history-move-page-size" aria-label="Số bản ghi mỗi trang"><option>10</option><option>25</option><option>50</option></select></label><button class="ghost" id="history-move-export" type="button">Xuất Excel</button><button class="ghost" id="history-move-filter-clear" type="button">Xóa lọc</button></div><div class="table-wrap"><table><thead><tr>${financeHistoryMove.columns.map(escapeCell).map(label => `<th>${label}</th>`).join('')}</tr></thead><tbody></tbody></table><div class="muted" data-history-move-count></div><div class="pagination" role="navigation" aria-label="Phân trang"><button type="button" id="history-move-prev">Trước</button><span id="history-move-page">Trang 1</span><button type="button" id="history-move-next">Sau</button></div></div></section>`;
    let page = 1;
    const apply = () => { page = 1; return render({ q: screen.querySelector('#history-move-query')?.value || '', status: screen.querySelector('#history-move-status')?.value || '', page, page_size: screen.querySelector('#history-move-page-size')?.value || '10' }).catch(() => {}); };
    screen.querySelector('#history-move-query')?.addEventListener('change', apply);
    screen.querySelector('#history-move-status')?.addEventListener('change', apply);
    screen.querySelector('#history-move-page-size')?.addEventListener('change', apply);
    screen.querySelector('#history-move-prev')?.addEventListener('click', () => { if (page > 1) { page -= 1; render({ q: screen.querySelector('#history-move-query')?.value || '', status: screen.querySelector('#history-move-status')?.value || '', page, page_size: screen.querySelector('#history-move-page-size')?.value || '10' }).catch(() => {}); } });
    screen.querySelector('#history-move-next')?.addEventListener('click', () => { page += 1; render({ q: screen.querySelector('#history-move-query')?.value || '', status: screen.querySelector('#history-move-status')?.value || '', page, page_size: screen.querySelector('#history-move-page-size')?.value || '10' }).catch(() => {}); });
    screen.querySelector('#history-move-export')?.addEventListener('click', () => { const q = historyMoveQuery({ q: screen.querySelector('#history-move-query')?.value || '', status: screen.querySelector('#history-move-status')?.value || '' }); window.location.href = `/api/export/finance-history-move-student?${q}`; });
    screen.querySelector('#history-move-filter-clear')?.addEventListener('click', () => { const q = screen.querySelector('#history-move-query'); const status = screen.querySelector('#history-move-status'); if (q) q.value = ''; if (status) status.value = ''; apply(); });
    await render();
    bindFinanceTabState(screen);
    return true;
  } catch (_) {
    return false;
  }
}

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
      screen.dataset.activeFinanceTab = String(index);
      screen.dispatchEvent(new CustomEvent('finance-tab-change', { detail: { index, label: tab.textContent.trim() } }));
    });
  });
}

export function register(global) {
  const host = global || {};
  host.financeHistoryMove = financeHistoryMove;
  if (typeof host.registerScreen === 'function') host.registerScreen(financeHistoryMove.route, renderHistoryMove);
  return financeHistoryMove;
}

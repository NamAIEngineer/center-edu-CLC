/* Customer-facing transfer screen for /finance/transfer/index.
 * Owns the observed shape: one search, three tabs, ten columns, one export.
 */
export const financeTransfer = {
  route: '/finance/transfer/index',
  tabs: ['Chuyển nhượng hợp đồng', 'Chuyển nhượng khoản thu vật phẩm', 'Danh sách hợp đồng chênh lệch phí khi chuyển lớp'],
  columns: ['No.', 'Mã chuyển nhượng', 'Ngày chuyển nhượng', 'Học viên chuyển', 'Hợp đồng', 'Khóa học', 'Học viên nhận', 'Số tiền nhận', 'Ghi chú', 'Action'],
  filters: ['q'],
  actions: ['Xuất Excel'],
  permissions: { read: ['ADMIN', 'STAFF'], write: ['ADMIN', 'STAFF'] },
  statusLabels: Object.freeze({ PENDING: 'Chưa xử lý', PROCESSED: 'Đã xử lý', CANCELLED: 'Đã hủy' }),
};

export const transferFields = [
  { name: 'transfer_code', label: 'Mã chuyển nhượng', required: true },
  { name: 'transfer_date', label: 'Ngày chuyển nhượng', type: 'date-text', required: true },
  { name: 'from_student_id', label: 'Học viên chuyển', required: true },
  { name: 'to_student_id', label: 'Học viên nhận', required: true },
  { name: 'contract_id', label: 'Hợp đồng' }, { name: 'course_id', label: 'Khóa học' },
  { name: 'amount_received', label: 'Số tiền nhận', type: 'number' },
  { name: 'status', label: 'Trạng thái', options: Object.entries(financeTransfer.statusLabels) },
  { name: 'note', label: 'Ghi chú' },
];

export const transferQuery = (filters = {}) => {
  const p = new URLSearchParams(); const value = String(filters.q ?? '').trim();
  if (value) p.set('q', value); return p;
};
export const loadTransfers = (apiFetch, filters = {}) => apiFetch(`/api/finance/transfers?${transferQuery(filters)}`);
export const exportTransfers = (apiFetch, filters = {}) => apiFetch(`/api/export/finance-transfers?${transferQuery(filters)}`);
export const transferStatusLabel = value => financeTransfer.statusLabels[String(value || '').toUpperCase()] || '';

const escapeHtml = value => String(value ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const displayDate = value => { const m = String(value || '').match(/^(\d{4})-(\d{2})-(\d{2})/); return m ? `${m[3]}/${m[2]}/${m[1]}` : escapeHtml(value || ''); };
const money = value => `${Number(value || 0).toLocaleString('vi-VN')} VND`;
const studentCell = (row, prefix) => {
  const lines = [row[`${prefix}_student_name`], row[`${prefix}_student_code`], row[`${prefix}_student_phone`]].filter(Boolean);
  return lines.map((line, index) => index === 0 ? `<b>${escapeHtml(line)}</b>` : `<small>${escapeHtml(line)}</small>`).join('');
};
const tableRow = (row, index) => `<tr><td>${index + 1}</td><td>${escapeHtml(row.transfer_code || '')}</td><td>${displayDate(row.transfer_date)}</td><td class="finance-transfer-person">${studentCell(row, 'from')}</td><td>${escapeHtml(row.contract_code || '')}</td><td>${escapeHtml(row.course_name || row.course_code || '')}</td><td class="finance-transfer-person">${studentCell(row, 'to')}</td><td><b>${money(row.amount_received)}</b></td><td>${escapeHtml(row.note || '')}</td><td><span class="finance-transfer-action" aria-hidden="true"></span></td></tr>`;

async function renderFinanceTransfers(screen, context = {}) {
  const response = await context.api('/api/finance/transfers');
  const rows = Array.isArray(response?.data) ? response.data : [];
  const tabs = financeTransfer.tabs.map((label, index) => `<button type="button" class="ref-tab${index === 0 ? ' active' : ''}" role="tab" aria-selected="${index === 0 ? 'true' : 'false'}">${escapeHtml(label)}</button>`).join('');
  const headers = financeTransfer.columns.map(label => `<th>${escapeHtml(label)}</th>`).join('');
  const pageRows = rows.slice(0, 5);
  screen.innerHTML = `<section class="card finance-transfer-screen"><div class="ref-tabs" role="tablist">${tabs}</div><div class="finance-transfer-toolbar"><div class="filter-strip"><label><input class="finance-transfer-query" placeholder="Tìm trong bảng..." aria-label="Tìm trong bảng..."></label></div><button class="primary" type="button" data-finance-transfer-export>Xuất Excel</button></div><div class="table-wrap"><table><thead><tr>${headers}</tr></thead><tbody>${pageRows.map(tableRow).join('')}</tbody></table></div><div class="finance-transfer-footer">Hiển thị ${pageRows.length ? 1 : 0} đến ${pageRows.length} của ${rows.length} bản ghi</div></section>`;
  const input = screen.querySelector('.finance-transfer-query');
  input?.addEventListener('input', async () => { const query = String(input.value || '').trim(); const next = await context.api(`/api/finance/transfers${query ? `?q=${encodeURIComponent(query)}` : ''}`); const body = screen.querySelector('tbody'); if (body) body.innerHTML = (Array.isArray(next?.data) ? next.data.slice(0, 5) : []).map(tableRow).join(''); });
  screen.querySelector('[data-finance-transfer-export]')?.addEventListener('click', () => { const query = String(input?.value || '').trim(); const link = document.createElement('a'); link.href = `/api/export/finance-transfers${query ? `?q=${encodeURIComponent(query)}` : ''}`; link.download = 'finance-transfers.csv'; document.body.append(link); link.click(); link.remove(); });
  return true;
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
  const host = global || {}; host.financeTransfer = financeTransfer;
  if (typeof host.registerScreen === 'function') host.registerScreen(financeTransfer.route, renderFinanceTransfers);
  return financeTransfer;
}

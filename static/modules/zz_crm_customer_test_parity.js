/* CRM customer-test screen: use the persisted customer-tests authority.
 * The generic W3 renderer reads generated-screen records; this route is backed
 * by /api/customer-tests and therefore needs a route-local renderer. */

const ROUTE = '/crm/customer_test';
const COLUMNS = [
  ['No.', null], ['Khách hàng', 'customer_name'], ['Phụ huynh', 'parent_name'],
  ['Ngày hẹn test', 'test_date'], ['Điểm test', 'score'],
  ['Nhân viên sale', 'sales_owner'], ['Thời gian', 'appointment_time'], ['Công cụ', null],
];

const escapeHtml = value => String(value ?? '').replace(/[&<>"']/g, c => ({ '&':'&amp;', '<':'&lt;', '>':'&gt;', '"':'&quot;', "'":'&#39;' })[c]);
const dateText = value => { const m = String(value || '').slice(0, 10).match(/^(\d{4})-(\d{2})-(\d{2})$/); return m ? `${m[3]}/${m[2]}/${m[1]}` : String(value || ''); };
const timeText = value => { const m = String(value || '').match(/(?:T|\s)(\d{2}:\d{2})/); return m ? m[1] : ''; };
const isoDate = value => {
  const text = String(value || '').trim();
  const vi = text.match(/^(\d{1,2})[/-](\d{1,2})[/-](\d{4})$/);
  if (vi) return `${vi[3]}-${vi[2].padStart(2, '0')}-${vi[1].padStart(2, '0')}`;
  return text.match(/^\d{4}-\d{2}-\d{2}$/) ? text : '';
};

function renderTable(screen, rows, canEdit) {
  const body = rows.length
    ? rows.map((row, index) => `<tr><td>${index + 1}</td><td>${escapeHtml(row.customer_name)}</td><td>${escapeHtml(row.parent_name)}</td><td>${dateText(row.test_date)}</td><td>${canEdit ? `<button type="button" class="link-button customer-test-score" data-id="${escapeHtml(row.id)}">${row.score == null ? 'Nhập điểm' : 'Cập nhật điểm'}</button>` : row.score == null ? '—' : escapeHtml(row.score)}</td><td>${escapeHtml(row.sales_owner)}</td><td></td><td>${canEdit ? '<button type="button" class="small-action customer-test-edit" data-id="' + escapeHtml(row.id) + '">Sửa</button>' : '—'}</td></tr>`).join('')
    : '<tr class="empty-row"><td colspan="8" class="empty">Chưa có dữ liệu.</td></tr>';
  const table = screen.querySelector('tbody');
  if (table) table.innerHTML = body;
  const count = screen.querySelector('[data-customer-test-count]');
  if (count) count.textContent = `${rows.length} mục`;
}

async function render(screen, context) {
  const { api, state } = context;
  const payload = await api('/api/customer-tests');
  const source = Array.isArray(payload.data) ? payload.data : [];
  const canEdit = ['ADMIN', 'STAFF'].includes(state.user?.role);
  let page = 1;
  screen.dataset.crmCustomerTestParity = '1';
  const owners = [...new Set(source.map(row => row.sales_owner).filter(Boolean))];
  screen.innerHTML = `<div class="screen-head"><div class="screen-title"><h1>Danh sách test / hẹn test</h1></div><div class="screen-actions"><button class="ghost" type="button" data-customer-test-export>Excel</button></div></div><div class="ref-tabs" role="tablist"><button type="button" class="ref-tab active" role="tab" aria-selected="true">Danh sách test / hẹn test</button></div><div class="filter-strip"><label><input data-customer-test-query placeholder="Tìm trong bảng..."></label><label><input data-customer-test-from type="text" data-date-input data-date-text="1" inputmode="numeric" placeholder="Từ ngày"></label><label><input data-customer-test-to type="text" data-date-input data-date-text="1" inputmode="numeric" placeholder="Đếm ngày"></label><label><select data-customer-test-owner><option value="">Tất cả</option>${owners.map(owner => `<option>${escapeHtml(owner)}</option>`).join('')}</select></label><label>Hiển thị <select data-customer-test-size><option>10</option><option>25</option><option>50</option><option>All</option></select> bản ghi</label></div><div class="table-card"><div class="table-toolbar"><h2 data-customer-test-count>${source.length} mục</h2></div><div class="table-wrap"><table><thead><tr>${COLUMNS.map(([label]) => `<th>${label}</th>`).join('')}</tr></thead><tbody></tbody></table></div></div>`;
  const apply = (resetPage = false) => {
    if (resetPage) page = 1;
    const q = String(screen.querySelector('[data-customer-test-query]')?.value || '').toLocaleLowerCase();
    const owner = screen.querySelector('[data-customer-test-owner]')?.value || '';
    const from = isoDate(screen.querySelector('[data-customer-test-from]')?.value);
    const to = isoDate(screen.querySelector('[data-customer-test-to]')?.value);
    const rows = source.filter(row => {
      const day = String(row.test_date || '').slice(0, 10);
      return (!owner || row.sales_owner === owner)
        && (!q || Object.values(row).some(value => String(value ?? '').toLocaleLowerCase().includes(q)))
        && (!from || !day || day >= from)
        && (!to || !day || day <= to);
    });
    const requestedSize = screen.querySelector('[data-customer-test-size]')?.value || '10';
    const pageSize = requestedSize === 'All' ? Math.max(rows.length, 1) : Math.max(Number(requestedSize) || 10, 1);
    const pageCount = Math.max(1, Math.ceil(rows.length / pageSize));
    page = Math.min(page, pageCount);
    renderTable(screen, rows.slice((page - 1) * pageSize, page * pageSize), canEdit);
    screen.querySelectorAll('tbody tr:not(.empty-row)').forEach((row, index) => {
      const number = row.querySelector('td'); if (number) number.textContent = String((page - 1) * pageSize + index + 1);
    });
    const start = rows.length ? (page - 1) * pageSize + 1 : 0;
    const end = Math.min(page * pageSize, rows.length);
    const pager = screen.querySelector('[data-customer-test-pager]');
    if (pager) pager.innerHTML = `<span>Hiển thị ${start} đến ${end} của ${rows.length} bản ghi</span><div class="customer-test-pager-actions"><button type="button" class="ghost" data-customer-test-page="-1" ${page <= 1 ? 'disabled' : ''}>‹</button><span>${page} / ${pageCount}</span><button type="button" class="ghost" data-customer-test-page="1" ${page >= pageCount ? 'disabled' : ''}>›</button></div>`;
  };
  screen.insertAdjacentHTML('beforeend', '<footer class="customer-test-pager" data-customer-test-pager></footer>');
  screen.querySelectorAll('[data-customer-test-query],[data-customer-test-from],[data-customer-test-to]').forEach(input => input.addEventListener('input', () => apply(true)));
  screen.querySelector('[data-customer-test-owner]')?.addEventListener('change', () => apply(true));
  screen.querySelector('[data-customer-test-size]')?.addEventListener('change', () => apply(true));
  screen.querySelector('[data-customer-test-export]')?.addEventListener('click', () => { window.location.href = '/api/export/customer-tests'; });
  screen.onclick = event => {
    const pageButton = event.target.closest('[data-customer-test-page]');
    if (pageButton && !pageButton.disabled) { page += Number(pageButton.dataset.customerTestPage); apply(); return; }
    const scoreButton = event.target.closest('.customer-test-score');
    if (scoreButton) { globalThis.customerTestEditModal?.(scoreButton.dataset.id); return; }
    const editButton = event.target.closest('.customer-test-edit');
    if (editButton) globalThis.customerTestEditModal?.(editButton.dataset.id);
  };
  apply();
  return true;
}

export function register(centerEdu = globalThis.CenterEdu) {
  if (!centerEdu?.registerScreen) return false;
  centerEdu.registerScreen(ROUTE, render);
  return { routes: [ROUTE], status: 'PERSISTED_CUSTOMER_TEST_AUTHORITY' };
}

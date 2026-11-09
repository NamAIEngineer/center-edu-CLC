/* Finance spend screen contract. Host app wires API base + auth/RBAC. */
export const spendScreen = {
  route: '/finance/spend/index',
  entity: 'finance_spends',
  tabs: ['Danh mục', 'Khoản chi tài chính'],
  filters: [
    {name:'center_id', type:'select', placeholder:'Chọn trung tâm'},
    {name:'category', type:'select', placeholder:'Chọn danh mục'},
    {name:'q', type:'text', placeholder:'Tìm trong bảng...'},
    {name:'from_date', type:'text', placeholder:'Từ ngày'},
    {name:'to_date', type:'text', placeholder:'Đến ngày'}
  ],
  columns: ['No.', 'Mã phiếu chi', 'Ngày lập phiếu', 'Trung tâm áp dụng', 'Nội dung', 'Ghi chú', 'Danh mục', 'Số tiền', 'Phương thức thanh toán', 'Người lập phiếu', 'Công cụ'],
  actions: ['Excel', 'Thêm phiếu chi'],
  form: [
    {name:'code', label:'Mã phiếu chi', required:true},
    {name:'spend_date', label:'Ngày lập phiếu', type:'date-text', required:true},
    {name:'center_id', label:'Trung tâm áp dụng', required:true},
    {name:'content', label:'Nội dung', required:true},
    {name:'note', label:'Ghi chú'},
    {name:'category', label:'Danh mục', required:true},
    {name:'amount_vnd', label:'Số tiền', required:true},
    {name:'payment_method', label:'Phương thức thanh toán', required:true}
  ],
  permissions: {read:['ADMIN','STAFF','TEACHER'], write:['ADMIN','STAFF']}
};

export const spendPaymentLabels = Object.freeze({
  cash: 'Tiền mặt',
  bank_transfer: 'Chuyển khoản',
  card: 'Thẻ',
});

export const spendCategoryOptions = Object.freeze(['CSVC', 'Lương', 'Marketing', 'Vận hành', 'Khác']);

/**
 * Build only the five observed server filters. Empty values stay out of the
 * query string so a cleared filter cannot accidentally narrow the result.
 */
export function spendQuery(filters = {}) {
  const params = new URLSearchParams();
  const fields = [
    ['center_id', filters.center_id], ['category', filters.category],
    ['q', filters.q], ['from_date', filters.from_date], ['to_date', filters.to_date],
  ];
  fields.forEach(([key, value]) => {
    const text = String(value ?? '').trim();
    if (text) params.set(key, text);
  });
  return params;
}

export function validateSpendForm(values = {}) {
  const errors = {};
  // center_id is the user-facing selector; center_name is resolved by the
  // host from that ID and must not make an otherwise valid form appear dead.
  ['code', 'spend_date', 'center_id', 'content', 'category', 'amount_vnd', 'payment_method']
    .forEach((field) => { if (!String(values[field] ?? '').trim()) errors[field] = 'Trường bắt buộc'; });
  if (values.category && !spendCategoryOptions.includes(values.category)) errors.category = 'Danh mục không hợp lệ';
  if (values.payment_method && !Object.prototype.hasOwnProperty.call(spendPaymentLabels, values.payment_method)) errors.payment_method = 'Phương thức thanh toán không hợp lệ';
  if (values.amount_vnd !== undefined && values.amount_vnd !== '' && (!Number.isInteger(Number(values.amount_vnd)) || Number(values.amount_vnd) < 0)) errors.amount_vnd = 'Số tiền phải là số nguyên không âm';
  return errors;
}

export function formatVnd(value) {
  return `${Number(value || 0).toLocaleString('vi-VN')} VND`;
}

export function renderSpendRows(items = []) {
  return items.map((row, i) => ({
    no: i + 1,
    code: row.code,
    date: row.spend_date,
    center: row.center_name,
    content: row.content,
    note: row.note || '',
    category: row.category,
    amount: formatVnd(row.amount_vnd),
    paymentMethod: spendPaymentLabels[row.payment_method] || '',
    createdBy: row.created_by,
    action: '…',
    actions: Object.freeze(['Xem', 'Sửa'])
  }));
}

/** Stable three-dot menu semantics. The host may render these labels in a
 * popover; no destructive action is exposed without a separate confirmation.
 */
export function spendRowActions(row = {}, { canEdit = false } = {}) {
  const actions = [{ id: 'view', label: 'Xem', recordId: row.id }];
  if (canEdit) actions.push({ id: 'edit', label: 'Sửa', recordId: row.id });
  return actions;
}

export async function loadSpend(apiFetch, filters = {}, page = 1, pageSize = 10) {
  const params = spendQuery(filters);
  params.set('page', String(page));
  params.set('page_size', String(pageSize));
  return apiFetch(`/api/finance/spends?${params.toString()}`);
}

export async function exportSpend(apiFetch, filters = {}) {
  const params = spendQuery(filters);
  return apiFetch(`/api/export/finance-spends?${params.toString()}`);
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
  host.financeSpend = spendScreen;
  const render = async (screen, context) => {
    const fn = globalThis.financeSpends;
    if (typeof fn !== 'function') return false;
    await fn(screen, context);
    bindFinanceTabState(screen);
    return true;
  };
  if (typeof host.registerScreen === 'function') host.registerScreen(spendScreen.route, render);
  return spendScreen;
}

/* Finance pricing assessment screen contract for /finance/assessment. */
export const financeAssessment = {
  route: '/finance/assessment',
  tabs: ['Ưu đãi - Khuyến mãi', 'Gói học phí', 'Định giá', 'Định giá gói học phí'],
  columns: ['No.', 'Tên', 'Ngày áp dụng', 'Nhân viên định giá', 'Khóa học liên quan'],
  filters: ['q', 'status'],
  pageSizes: [5, 10, 25, 50],
  statusLabels: Object.freeze({ ACTIVE: 'Đang áp dụng', INACTIVE: 'Tạm khóa' }),
  actions: ['Lưu định giá', 'Excel'],
  form: [
    { name: 'fullname', label: 'Tên định giá', required: true },
    { name: 'date_apply', label: 'Ngày áp dụng', type: 'date-text', required: true },
    { name: 'course_id', label: 'Khóa học liên quan', type: 'select' },
    { name: 'old_price', label: 'Giá cũ', type: 'number' },
    { name: 'new_price', label: 'Giá mới', type: 'number' },
  ],
  permissions: { read: ['ADMIN', 'STAFF', 'TEACHER'], write: ['ADMIN', 'STAFF'] },
};

export const assessmentQuery = (filters = {}) => {
  const params = new URLSearchParams();
  financeAssessment.filters.forEach((key) => {
    const value = String(filters[key] ?? '').trim();
    if (value) params.set(key, value);
  });
  return params;
};

export const assessmentStatusLabel = (value) =>
  financeAssessment.statusLabels[String(value || '').toUpperCase()] || '';

export const loadAssessments = (apiFetch, filters = {}) =>
  apiFetch(`/api/finance/assessments?${assessmentQuery(filters)}`);

export const exportAssessments = (apiFetch, filters = {}) =>
  apiFetch(`/api/export/finance-assessments?${assessmentQuery(filters)}`);

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
  host.financeAssessment = financeAssessment;
  const render = async (screen, context) => {
    const fn = globalThis.financeAssessments;
    if (typeof fn !== 'function') return false;
    await fn(screen, context);
    bindFinanceTabState(screen);
    return true;
  };
  if (typeof host.registerScreen === 'function') host.registerScreen(financeAssessment.route, render);
  return financeAssessment;
}


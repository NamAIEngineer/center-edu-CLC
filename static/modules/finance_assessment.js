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

export function register(global) {
  const host = global || {};
  host.financeAssessment = financeAssessment;
  const render = async (screen, context) => {
    const fn = globalThis.financeAssessments;
    if (typeof fn !== 'function') return false;
    await fn(screen, context);
    return true;
  };
  if (typeof host.registerScreen === 'function') host.registerScreen(financeAssessment.route, render);
  return financeAssessment;
}


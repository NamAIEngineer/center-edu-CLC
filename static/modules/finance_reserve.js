import { bindFinanceViews } from './finance_tab_views.js';
/* Finance reserve screen contract for /finance/reserve. */
export const financeReserve = {
  route: '/finance/reserve',
  tabs: ['Hoàn trả', 'Bảo lưu'],
  columns: ['Mã bảo lưu', 'Học viên', 'Ngày bảo lưu', 'Số tiền/Số ngày bảo lưu', 'Hợp đồng bảo lưu', 'Người tạo', 'Trạng thái', 'Công cụ'],
  filters: ['q', 'mode'],
  modes: ['Theo hợp đồng', 'Theo khóa học'],
  statuses: ['Chờ xử lý', 'Đã cộng vào ví', 'Đã hoàn trả'],
  pageSizes: [5, 10, 25, 50],
  actions: ['Tạo mới', 'Excel'],
  form: [
    { name: 'reserve_code', label: 'Mã bảo lưu' },
    { name: 'student_name', label: 'Học viên', required: true },
    { name: 'reserve_date', label: 'Ngày bảo lưu', type: 'date-text', required: true },
    { name: 'amount_or_days', label: 'Số tiền/Số ngày bảo lưu', type: 'number' },
    { name: 'contract_code', label: 'Hợp đồng bảo lưu' },
    { name: 'course_name', label: 'Khóa học liên quan' },
    { name: 'status', label: 'Trạng thái', type: 'select', options: ['Chờ xử lý', 'Đã cộng vào ví', 'Đã hoàn trả'] },
  ],
  permissions: { read: ['ADMIN', 'STAFF', 'TEACHER'], write: ['ADMIN', 'STAFF'] },
};

export const reserveQuery = (filters = {}) => {
  const params = new URLSearchParams();
  financeReserve.filters.forEach((key) => {
    const value = String(filters[key] ?? '').trim();
    if (value) params.set(key, value);
  });
  return params;
};

export const loadReserves = (apiFetch, filters = {}) =>
  apiFetch(`/api/finance/reserves?${reserveQuery(filters)}`);

export const exportReserves = (apiFetch, filters = {}) =>
  apiFetch(`/api/export/finance-reserves?${reserveQuery(filters)}`);

function bindFinanceTabState(screen, context) { bindFinanceViews(screen, 'reserve', context); }

export function register(global) {
  const host = global || {};
  host.financeReserve = financeReserve;
  const render = async (screen, context) => {
    const fn = globalThis.financeReserves;
    if (typeof fn !== 'function') return false;
    await fn(screen, context);
    bindFinanceTabState(screen, context);
    return true;
  };
  if (typeof host.registerScreen === 'function') host.registerScreen(financeReserve.route, render);
  return financeReserve;
}


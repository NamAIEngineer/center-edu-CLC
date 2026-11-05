/* Customer-facing revenue list contract for /finance/revenue. */
export const financeRevenue = {
  route: '/finance/revenue', tabs: [],
  columns: ['No.', 'Mã', 'Tên', 'Trạng thái', 'Giá', 'Kiểu giảm', 'Giá trị giảm', 'Giá phải thu', 'Trung tâm', 'Ghi chú', 'Công cụ'],
  filters: ['q', 'status', 'center'], actions: ['Tạo mới'],
  permissions: { read: ['ADMIN', 'STAFF'], write: ['ADMIN', 'STAFF'] },
  statusLabels: Object.freeze({ ACTIVE: 'Kích hoạt', INACTIVE: 'Tạm khóa' }),
  discountLabels: Object.freeze({ '': 'Không giảm', FIXED: 'Theo tiền', PERCENT: '%' }),
};
export const revenueFields = [
  { name: 'code', label: 'Mã', required: true }, { name: 'name', label: 'Tên', required: true }, { name: 'status', label: 'Trạng thái', options: Object.entries(financeRevenue.statusLabels) }, { name: 'price', label: 'Giá', type: 'number' }, { name: 'discount_type', label: 'Kiểu giảm', options: Object.entries(financeRevenue.discountLabels) }, { name: 'discount_value', label: 'Giá trị giảm', type: 'number' }, { name: 'amount_due', label: 'Giá phải thu', type: 'number' }, { name: 'center', label: 'Trung tâm' }, { name: 'note', label: 'Ghi chú' },
];
export const revenueQuery = (filters = {}) => { const p = new URLSearchParams(); financeRevenue.filters.forEach(k => { const v = String(filters[k] ?? '').trim(); if (v) p.set(k, v); }); return p; };
export const loadRevenues = (apiFetch, filters = {}) => apiFetch(`/api/finance/revenues?${revenueQuery(filters)}`);
export const exportRevenues = (apiFetch, filters = {}) => apiFetch(`/api/export/finance-revenues?${revenueQuery(filters)}`);

export function register(global) {
  const host = global || {};
  host.financeRevenue = financeRevenue;
  const render = async (screen, context) => {
    const fn = globalThis.financeRevenues;
    if (typeof fn !== 'function') return false;
    await fn(screen, context);
    return true;
  };
  if (typeof host.registerScreen === 'function') host.registerScreen(financeRevenue.route, render);
  return financeRevenue;
}

import { bindFinanceViews } from './finance_tab_views.js';
/* Customer-facing bill screen contract for /finance/bill/index. */
export const financeBill = {
  route: '/finance/bill/index',
  tabs: ['Hóa đơn đóng tiền', 'Hóa đơn đóng tiền trước', 'Hóa đơn online'],
  columns: ['No.', 'Mã hóa đơn', 'Mã hợp đồng', 'Lớp học', 'Đối tượng', 'Khách hàng', 'Thanh toán', 'Nhân viên sale', 'Người tạo', 'Trạng thái xác nhận', 'Hình thức thanh toán', 'Ghi chú', 'Công cụ'],
  filters: ['q', 'creator', 'date_from', 'date_to', 'center', 'branch', 'employee', 'confirmation_status'],
  actions: ['Lọc', 'Xóa lọc', 'Tạo hóa đơn', 'Excel'],
  permissions: { read: ['ADMIN', 'STAFF'], write: ['ADMIN', 'STAFF'] },
  statusLabels: Object.freeze({ PENDING: 'Cần xác nhận', CONFIRMED: 'Đã xác nhận', REJECTED: 'Không đồng ý' }),
  paymentLabels: Object.freeze({ cash: 'Tiền mặt', bank_transfer: 'Chuyển khoản', card: 'Quẹt thẻ', wallet: 'Ví CO', installment: 'Trả góp' }),
};
export const billFields = [
  { name: 'invoice_code', label: 'Mã hóa đơn', required: true }, { name: 'contract_code', label: 'Mã hợp đồng' }, { name: 'class_code', label: 'Lớp học' }, { name: 'subject', label: 'Đối tượng' }, { name: 'customer_name', label: 'Khách hàng' }, { name: 'payment_amount', label: 'Thanh toán', type: 'number' }, { name: 'sales_owner', label: 'Nhân viên sale' }, { name: 'center', label: 'Trung tâm' }, { name: 'branch', label: 'Chi nhánh' }, { name: 'employee', label: 'Nhân viên' }, { name: 'confirmation_status', label: 'Trạng thái xác nhận', options: Object.entries(financeBill.statusLabels) }, { name: 'payment_method', label: 'Hình thức thanh toán' }, { name: 'invoice_date', label: 'Ngày hóa đơn', type: 'date-text' }, { name: 'note', label: 'Ghi chú' },
];
export const billQuery = (filters = {}) => { const p = new URLSearchParams(); financeBill.filters.forEach(k => { const v = String(filters[k] ?? '').trim(); if (v) p.set(k, v); }); return p; };
export const loadBills = (apiFetch, filters = {}) => apiFetch(`/api/finance/bills?${billQuery(filters)}`);
export const exportBills = (apiFetch, filters = {}) => apiFetch(`/api/export/finance-bills?${billQuery(filters)}`);
export const confirmationLabel = status => financeBill.statusLabels[String(status || '').toUpperCase()] || '';
export const paymentMethodLabel = value => financeBill.paymentLabels[String(value || '')] || '';

function bindFinanceTabState(screen, context) { bindFinanceViews(screen, 'bill', context); }

export function register(global) {
  const host = global || {};
  host.financeBill = financeBill;
  const render = async (screen, context) => {
    const fn = globalThis.financeBills;
    if (typeof fn !== 'function') return false;
    await fn(screen, context);
    const card = screen.querySelector('[data-table-card]');
    const registry = globalThis.CenterEdu?.state?.tableRegistry?.[card?.dataset.tableCard];
    if (registry) {
      registry.columns = registry.columns.map(column => column.label === 'Trạng thái xác nhận'
        ? { ...column, render: row => {
          const status = String(row.confirmation_status || '').toUpperCase();
          const label = confirmationLabel(status);
          return `<span class="badge ${status === 'CONFIRMED' ? 'green' : status === 'REJECTED' ? 'red' : ''}">${label}</span>`;
        } } : column);
    }
    screen.querySelectorAll('#finance-bill-status-filter option').forEach(option => {
      const label = confirmationLabel(option.value);
      if (label) { option.value = option.value; option.textContent = label; }
    });
    bindFinanceTabState(screen, context);
    return true;
  };
  if (typeof host.registerScreen === 'function') host.registerScreen(financeBill.route, render);
  return financeBill;
}

/* Customer-facing payment appointment screen contract for /finance/appointment_date. */
export const financeAppointment = {
  route: '/finance/appointment_date', aliases: ['/sale/appointment_date'],
  columns: ['Trạng thái', 'Học viên', 'Phụ huynh', 'Ngày hẹn', 'Số tiền', 'Ghi chú', 'Kiểu/Mã', 'Hợp đồng liên quan', 'Công cụ'],
  filters: ['q', 'date_from', 'date_to', 'appointment_type'], actions: [],
  permissions: { read: ['ADMIN', 'STAFF', 'TEACHER', 'STUDENT'], write: ['ADMIN', 'STAFF'] },
  statuses: ['Chưa xử lý', 'Đã xử lý', 'Đã hủy'], types: ['Theo hóa đơn', 'Theo hợp đồng'],
};
export const appointmentFields = [
  { name: 'student_name', label: 'Học viên', required: true }, { name: 'parent_name', label: 'Phụ huynh' }, { name: 'appointment_date', label: 'Ngày hẹn', type: 'date-text', required: true }, { name: 'amount', label: 'Số tiền', type: 'number' }, { name: 'note', label: 'Ghi chú' }, { name: 'appointment_type', label: 'Kiểu hẹn', options: financeAppointment.types.map(value => [value, value]) }, { name: 'reference_code', label: 'Mã tham chiếu', required: true }, { name: 'contract_code', label: 'Hợp đồng liên quan' }, { name: 'status', label: 'Trạng thái', options: financeAppointment.statuses.map(value => [value, value]) },
];
export const appointmentQuery = (filters = {}) => { const p = new URLSearchParams(); financeAppointment.filters.forEach(k => { const v = String(filters[k] ?? '').trim(); if (v) p.set(k, v); }); return p; };
export const loadAppointments = (apiFetch, filters = {}) => apiFetch(`/api/finance/appointments?${appointmentQuery(filters)}`);
export const exportAppointments = (apiFetch, filters = {}) => apiFetch(`/api/export/finance-appointments?${appointmentQuery(filters)}`);

export function register(global) {
  const host = global || {};
  host.financeAppointment = financeAppointment;
  const render = async (screen, context) => {
    const fn = globalThis.financeAppointments;
    if (typeof fn !== 'function') return false;
    await fn(screen, context);
    return true;
  };
  if (typeof host.registerScreen === 'function') {
    [financeAppointment.route, ...financeAppointment.aliases]
      .filter((route, index, routes) => routes.indexOf(route) === index)
      .forEach(route => host.registerScreen(route, render));
  }
  return financeAppointment;
}

/* Local contract metadata for the payment-appointment screen.  The app registry
 * can mount this descriptor without coupling the screen to reference assets. */
export const financeAppointmentDate = {
  routes: ['/sale/appointment_date', '/finance/appointment_date'],
  title: 'Hẹn đóng tiền',
  columns: ['Trạng thái', 'Học viên', 'Phụ huynh', 'Ngày hẹn', 'Số tiền', 'Ghi chú', 'Kiểu/Mã', 'Hợp đồng liên quan', 'Công cụ'],
  filters: [
    { name: 'query', placeholder: 'Tìm trong bảng...', type: 'text' },
    { name: 'from_date', placeholder: 'Từ ngày', type: 'date-text' },
    { name: 'to_date', placeholder: 'Đến ngày', type: 'date-text' },
    { name: 'appointment_type', placeholder: 'Tất cả', options: ['Tất cả', 'Theo hóa đơn', 'Theo hợp đồng'] },
  ],
  pageSizes: [10, 25, 50, 100],
  actions: ['lọc', 'xóa lọc', 'excel'],
  permissions: { read: ['ADMIN', 'STAFF', 'TEACHER', 'STUDENT'], write: ['ADMIN', 'STAFF'] },
};

export function toAppointmentRow(item) {
  return [item.status, item.student_name, item.parent_name, item.appointment_date,
    `${Number(item.amount || 0).toLocaleString('vi-VN')} VND`, item.note,
    `${item.appointment_type} / ${item.reference_code}`, item.contract_code, '⋯'];
}

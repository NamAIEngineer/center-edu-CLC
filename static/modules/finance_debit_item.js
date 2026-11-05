export const financeDebitItem = {
  route: '/finance/bill/debit_item/index',
  title: 'Vật phẩm nợ',
  tab: 'Vật phẩm nợ',
  columns: ['No.', 'Hóa đơn', 'Ngày xuất HĐ', 'Khách hàng', 'Vật phẩm nợ', 'Số lượng', 'Tổng tiền', 'Trạng thái', 'Action'],
  filters: [
    { name: 'query', placeholder: 'Tìm trong bảng...', type: 'text' },
    { name: 'status', options: ['Tất cả', 'Chưa trả', 'Đã trả'] },
    { name: 'from_date', placeholder: 'Chọn từ ngày', type: 'date-text' },
    { name: 'to_date', placeholder: 'Chọn đến ngày', type: 'date-text' },
    { name: 'item_name', options: ['Tất cả', 'Ipad', 'iPhone', 'Sách ngữ pháp cơ bản'] },
  ],
  pageSizes: [10, 20, 50, 100],
  actions: ['lọc', 'xóa lọc', 'excel'],
  permissions: { read: ['ADMIN', 'STAFF', 'TEACHER', 'STUDENT'], write: ['ADMIN', 'STAFF'] },
};

export const formatDebitItemRow = item => [
  item.invoice_code, item.invoice_date, item.customer_name, item.item_name,
  item.quantity, `${Number(item.total_amount || 0).toLocaleString('vi-VN')}`,
  item.status, '⋯',
];

export function register(global) {
  const host = global || {};
  host.financeDebitItem = financeDebitItem;
  const render = async (screen, context) => {
    const fn = globalThis.financeDebitItems;
    if (typeof fn !== 'function') return false;
    await fn(screen, context);
    return true;
  };
  if (typeof host.registerScreen === 'function') host.registerScreen(financeDebitItem.route, render);
  return financeDebitItem;
}

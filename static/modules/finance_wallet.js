/* Read/export contract for the persisted Finance "Ví CO" screen. */
export const financeWallet = {
  route: '/finance/wallet_co/index',
  tabs: ['Ví CO'],
  columns: ['No.', 'Tên học viên', 'Trung tâm/chi nhánh', 'Tổng tiền', 'Đã dùng', 'Chưa dùng', 'Trạng thái', 'Công cụ'],
  filters: ['q', 'status'],
  statuses: Object.freeze({ '': 'Tất cả', 'Kích hoạt': 'Kích hoạt', 'Tạm khóa': 'Tạm khóa' }),
  pageSizes: [5, 10, 25, 50],
  permissions: { read: ['ADMIN', 'STAFF', 'TEACHER', 'STUDENT'], write: [] },
};

export const walletQuery = (filters = {}) => {
  const params = new URLSearchParams();
  financeWallet.filters.forEach((key) => {
    const value = String(filters[key] ?? '').trim();
    if (value) params.set(key, value);
  });
  return params;
};

export const loadWallets = (apiFetch, filters = {}) =>
  apiFetch(`/api/finance/wallets?${walletQuery(filters)}`);

export const exportWallets = (apiFetch, filters = {}) =>
  apiFetch(`/api/export/finance-wallets?${walletQuery(filters)}`);

export const formatWalletVnd = (value) =>
  `${Number(value || 0).toLocaleString('vi-VN')} VND`;

export const renderWalletRow = (row, index = 0) => ({
  no: index + 1,
  student: row.student_name || '',
  branch: row.branch || '',
  total: formatWalletVnd(row.total_amount),
  used: formatWalletVnd(row.used_amount),
  unused: formatWalletVnd(row.unused_amount),
  status: financeWallet.statuses[row.status] || '',
});

export function register(global) {
  const host = global || {};
  host.financeWallet = financeWallet;
  const render = async (screen, context) => {
    const fn = globalThis.financeWallets;
    if (typeof fn !== 'function') return false;
    await fn(screen, context);
    return true;
  };
  if (typeof host.registerScreen === 'function') host.registerScreen(financeWallet.route, render);
  return financeWallet;
}


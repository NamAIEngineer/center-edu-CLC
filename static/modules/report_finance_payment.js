/** Contract for /report/finance/payment/index.
 *
 * The page shell remains owned by static/app.js.  This module keeps the
 * route-specific Vietnamese columns, named filters, and export URL together so
 * a future shell can consume the same contract without guessing filter_1/2.
 */
export const financePaymentReport = {
  route: '/report/finance/payment/index',
  filters: [
    { name: 'from_date', label: 'Từ ngày', type: 'date' },
    { name: 'to_date', label: 'Đến ngày', type: 'date' },
  ],
  columns: [
    ['no', 'No.'], ['trung_tam', 'Trung tâm'], ['vi_co', 'Ví CO'],
    ['tien_mat', 'Tiền mặt'], ['chuyen_khoan', 'Chuyển khoản'],
    ['quet_the', 'Quẹt thẻ'], ['vimass', 'Vimass'], ['vnpay', 'VNPAY'],
    ['9pay', '9PAY'], ['tra_gop', 'Trả góp'], ['napas', 'NAPAS'],
    ['tong_doanh_thu', 'Tổng doanh thu'],
  ].map(([key, label]) => ({ key, label })),
  runUrl(filters = {}) {
    const query = new URLSearchParams({ route: this.route, ...filters });
    return `/api/reports/run?${query.toString()}`;
  },
  exportUrl(filters = {}) {
    const query = new URLSearchParams({ route: this.route, ...filters });
    return `/api/reports/export?${query.toString()}`;
  },
};

/** Register payment metadata at the frontend autoload seam.
 *
 * `report_finance.js` owns the shared finance renderer.  Keep this module's
 * registration metadata-only when that renderer is already present; the
 * guarded fallback prevents a direct module load from leaving the route
 * unhandled without replacing the finance screen.
 */
export async function register(centerEdu = globalThis.CenterEdu) {
  if (!centerEdu) return { routes: [financePaymentReport.route] };
  centerEdu.reportMetadata = { ...(centerEdu.reportMetadata || {}), financePaymentReport };
  if (!centerEdu.screenRenderers?.has?.(financePaymentReport.route)) {
    centerEdu.registerScreen?.(financePaymentReport.route, async () => false);
  }
  return { routes: [financePaymentReport.route] };
}


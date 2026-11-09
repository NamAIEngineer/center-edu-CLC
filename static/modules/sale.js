/* Sale lane metadata and display helpers.  The host binds these descriptors
 * to the persistent modules/sale_domain.py and modules/crm_routes.py stores. */
window.CENTER_EDU_SALE_ROUTES = {
  '/sale/potential/index': 'prospects',
  '/sale/contract': 'contracts',
  '/sale/bill/index': 'bills',
  '/sale/class_enroll_trail_wait': 'trials',
  '/sale/customer_test': 'customer_tests',
  '/sale/potential/appointment': 'care_appointments',
  '/sale/appointment_date': 'payment_appointments',
  '/sale/pending_enrollment/index': 'pending_enrollments',
  '/dashboard/sale': 'sale_dashboard',
};

window.CENTER_EDU_SALE_STATUS_LABELS = {
  'Khách hàng mới':'Khách hàng mới',
  'Đang chăm sóc':'Đang chăm sóc',
  'Đủ điều kiện':'Đủ điều kiện',
  'Đã chuyển đổi':'Đã chuyển đổi',
  'Đã hủy tư vấn':'Đã hủy tư vấn',
  'Chưa xử lý':'Chưa xử lý',
  'Đã xử lý':'Đã xử lý',
  'Đã hủy cuộc hẹn':'Đã hủy cuộc hẹn',
  'Còn nợ':'Còn nợ',
  'Đóng đủ':'Đóng đủ',
  'Đã xác nhận':'Đã xác nhận',
  'Cần xác nhận':'Cần xác nhận',
  'Không đồng ý':'Không đồng ý',
};

window.centerEduSaleMoney = function centerEduSaleMoney(value) {
  return `${Number(value || 0).toLocaleString('vi-VN')} VND`;
};

window.centerEduSaleRouteResource = function centerEduSaleRouteResource(route) {
  return window.CENTER_EDU_SALE_ROUTES[route] || null;
};

window.centerEduSaleContract = function centerEduSaleContract(route) {
  return window.CENTER_EDU_CRM_ROUTE_CONTRACTS?.[route] || null;
};

window.centerEduSaleList = async function centerEduSaleList(route, params = {}) {
  const resource = window.centerEduSaleRouteResource(route);
  const endpoints = {
    prospects: '/api/potential-customers', care_appointments: '/api/care-appointments',
    contracts: '/api/finance/contracts', bills: '/api/finance/bills',
    trials: '/api/trial-registrations', customer_tests: '/api/customer-tests',
    payment_appointments: '/api/finance/appointments', pending_enrollments: '/api/pending-enrollments'
  };
  const endpoint = endpoints[resource];
  if (!endpoint) throw new Error(`Route Sale chưa có API: ${route}`);
  const q = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => { if (value !== undefined && value !== null && String(value) !== '') q.set(key, value); });
  const response = await fetch(`${endpoint}${q.toString() ? `?${q}` : ''}`);
  const payload = await response.json();
  if (!response.ok || payload.ok === false) throw new Error(payload.error?.message || 'Không thể tải dữ liệu Sale');
  return payload.data;
};

// Sale potential has two observed views.  The shell paints the tab strip, but
// the route owner must connect the history tab to the persisted appointment
// view.  Bind after each render because the legacy renderer replaces #screen.
function bindSalePotentialTabs() {
  if (String(window.location.pathname || '').split('?')[0] !== '/sale/potential/index') return;
  const root = document.querySelector('#screen');
  const tabs = root?.querySelectorAll('.ref-tabs .ref-tab');
  if (!tabs?.length) return;
  tabs.forEach((tab, index) => {
    if (tab.dataset.salePotentialBound === 'true') return;
    tab.dataset.salePotentialBound = 'true';
    tab.addEventListener('click', (event) => {
      if (index !== 1) return;
      event.preventDefault();
      window.history.pushState({}, '', '/sale/potential/appointment');
      window.dispatchEvent(new PopStateEvent('popstate'));
    });
  });
}
if (typeof document !== 'undefined') {
  const root = document.querySelector('#screen') || document.body;
  if (typeof MutationObserver === 'function') new MutationObserver(bindSalePotentialTabs).observe(root, { childList: true, subtree: true });
  [0, 100, 400, 900].forEach(delay => setTimeout(bindSalePotentialTabs, delay));
}

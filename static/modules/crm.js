/* CRM lane client contract. The app shell owns auth and CSRF. */
(function registerCRMAdapter(global) {
  const STATUS_LABELS = {
    'Khách hàng mới': 'Khách hàng mới', 'Đang chăm sóc': 'Đang chăm sóc',
    'Đủ điều kiện': 'Đủ điều kiện', 'Đã chuyển đổi': 'Đã chuyển đổi',
    'Đã hủy tư vấn': 'Đã hủy tư vấn', 'Chưa xử lý': 'Chưa xử lý',
    'Đã xử lý': 'Đã xử lý', 'Đã hủy cuộc hẹn': 'Đã hủy cuộc hẹn'
  };
  const request = async (path, options = {}) => {
    const response = await fetch(path, { ...options, headers: {'Content-Type': 'application/json', ...(options.headers || {})} });
    const body = await response.json().catch(() => ({}));
    if (!response.ok || body.ok === false) throw new Error(body.error?.message || 'Không thể tải dữ liệu CRM');
    return body;
  };
  const query = (params = {}) => {
    const q = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => { if (value !== undefined && value !== null && String(value) !== '') q.set(key, value); });
    return q.toString();
  };
  const adapter = {
    routes: ['/crm/potential/index', '/crm/potential/appointment', '/sale/potential/index', '/sale/potential/appointment'],
    statuses: STATUS_LABELS,
    listProspects: (params) => request(`/api/potential-customers?${query(params)}`),
    getProspect: (id) => request(`/api/potential-customers/${encodeURIComponent(id)}`),
    createProspect: (data) => request('/api/potential-customers', {method: 'POST', body: JSON.stringify(data)}),
    updateProspect: (id, data) => request(`/api/potential-customers/${encodeURIComponent(id)}`, {method: 'POST', body: JSON.stringify(data)}),
    listAppointments: (params) => request(`/api/care-appointments?${query(params)}`),
    createFollowup: (id, data) => request(`/api/potential-customers/${encodeURIComponent(id)}/followups`, {method: 'POST', body: JSON.stringify(data)}),
    exportProspects: (params) => `/api/export/potential-customers?${query(params)}`,
    exportAppointments: (params) => `/api/export/care-appointments?${query(params)}`,
    formatMoney: (value) => `${Number(value || 0).toLocaleString('vi-VN')} VND`,
    formatStatus: (value) => STATUS_LABELS[value] || String(value || 'Chưa có trạng thái')
  };
  global.CENTER_EDU_CRM = adapter;
  global.centerEduCRM = adapter;
})(window);

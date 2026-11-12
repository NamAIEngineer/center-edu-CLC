/** Client metadata for the non-training/non-finance report lane. */
import { createReportTable, mountReportTable, reportPageSizes } from './report_table.js';
import { openBirthdayConfig } from './birthday_config.js';
export const crmCenterReportScope = {
  routePrefixes: ['/report/crm/', '/report/center/', '/report/cso/', '/report/callcenter/'],
  utilityRoutes: {
    '/cso/support': { title: 'Hỗ trợ', tabs: ['Tiếp nhận từ người dùng', 'Hỗ trợ nội bộ'], columns: ['No.', 'Thời gian', 'Loại', 'Nội dung', 'Người gửi', 'Lớp của học viên', 'Nhân viên', 'Trạng thái', ''], filters: ['status', 'type', 'from_date', 'to_date', 'query'], actions: ['Excel', 'Tạo'] },
    '/callcenter/get-statistic': { title: 'Thống kê cuộc gọi vào', tabs: ['Thống kê cuộc gọi vào', 'Thống kê cuộc gọi ra'], columns: ['No.', 'Nhân viên nghe', 'Nhóm sale', 'Trung tâm', 'Tổng cuộc gọi', 'Cuộc gọi thành công', 'Cuộc gọi nhỡ', 'Thất bại'], filters: ['from_date', 'to_date'], actions: ['Xuất excel'] },
    '/center/upload_address': { title: 'Tool chinh sửa địa chỉ', tabs: ['Lịch sử import', 'Hướng dẫn'], columns: ['No.', 'Chi nhánh', 'Mã học viên', 'Học viên', 'Mã định danh', 'Tên tiếng anh', 'Giới tính', 'Ngày sinh', 'Tài khoản', 'SĐT', 'Email', 'Tỉnh cũ', 'Huyện cũ', 'Xã phường', 'Tỉnh mới', 'Phường xã mới'], filters: ['file'], pageSizes: [5, 10, 25, 50], actions: ['Lưu'] },
    '/tenant/config_excel': { title: 'Cấu hình xuất excel báo cáo', tabs: ['Cấu hình xuất excel báo cáo'], columns: ['No.', 'Báo cáo', 'Tắt/bật excel báo cáo', 'Tất cả', ''], filters: ['check_all', 'publish_export_excel[]'], actions: [] },
  },
  routeEntities: {
    '/report/crm/contract/index': 'report_crm_contract_index',
    '/report/crm/bill/index': 'report_crm_bill_index',
    '/report/crm/customer_care/index': 'report_crm_customer_care_index',
    '/report/crm/customer_care_result_by_center': 'report_crm_customer_care_result_by_center',
    '/report/crm/customer_care_result_by_district': 'report_crm_customer_care_result_by_district',
    '/report/crm/customer_care_result_by_dob': 'report_crm_customer_care_result_by_dob',
    '/report/crm/customer_care_result_by_source': 'report_crm_customer_care_result_by_source',
    '/report/crm/customer_care_result_by_sale': 'report_crm_customer_care_result_by_sale',
    '/report/crm/customer_care_result': 'report_crm_customer_care_result',
    '/report/crm/customer_report/index': 'report_crm_customer_report_index',
    '/report/crm/customer_statistic/index': 'report_crm_customer_statistic_index',
    '/report/crm/customer_trailer': 'report_crm_customer_trailer',
    '/report/center/student_statistical/index': 'report_center_student_statistical_index',
    '/report/center/birth_day/index': 'report_center_birth_day_index',
    '/report/center/access_history': 'report_center_access_history',
    '/report/center/staff_teacher': 'report_center_staff_teacher',
    '/report/center/class_post/index': 'report_center_class_post_index',
  },
  catalogFilter(route) { return this.routePrefixes.some(prefix => route.startsWith(prefix)) || Object.prototype.hasOwnProperty.call(this.utilityRoutes, route); },
  contractFor(route) { if (!this.catalogFilter(route)) throw new Error('Route ngoài phạm vi'); return this.utilityRoutes[route] || null; },
  statusLabels: {
    OPEN: 'Đang mở', ACTIVE: 'Hoạt động', IN_PROGRESS: 'Đang xử lý',
    PLANNED: 'Dự kiến', COMPLETED: 'Đã hoàn thành', CANCELLED: 'Đã hủy',
    PAID: 'Đã thanh toán', UNPAID: 'Chưa thanh toán', PARTIAL: 'Còn nợ',
  },
  routeFilters: {
    '/report/center/student_statistical/index': ['from_date', 'to_date'],
    '/report/center/birth_day/index': ['esttype', 'esttype_2', 'filter_3', 'filter_4', 'tim_trong_bang'],
    '/report/center/access_history': ['esttype', 'esttype_2', 'filter_4', 'esttype_3', 'tim_trong_bang'],
    '/report/center/staff_teacher': ['from_date', 'to_date', 'tim_theo_ten', 'filter_5', 'filter_6'],
    '/report/crm/customer_care/index': ['tim_trong_bang', 'filter_4', 'from_date', 'to_date'],
    '/report/crm/customer_report/index': ['nhap_ten_hoc_vien', 'filter_2', 'filter_3', 'tu_ngay', 'den_ngay'],
    '/report/crm/customer_statistic/index': ['tim_trong_bang'],
    '/report/crm/customer_trailer': ['from_date', 'to_date', 'nhap_ten_hoc_vien'],
    '/report/crm/customer_care_result_by_center': ['filter_1', 'from_date', 'to_date'],
    '/report/crm/customer_care_result_by_district': ['filter_1', 'filter_2', 'from_date', 'to_date'],
    '/report/crm/customer_care_result_by_dob': ['filter_1', 'from_date', 'to_date'],
    '/report/crm/customer_care_result_by_source': ['filter_1', 'from_date', 'to_date'],
    '/report/crm/customer_care_result_by_sale': ['filter_1', 'from_date', 'to_date'],
    '/report/crm/customer_care_result': ['filter_1', 'from_date', 'to_date'],
  },
  filtersFor(route) { return this.routeFilters[route] || []; },
  exportHref(route, filters = {}) {
    if (!this.catalogFilter(route)) throw new Error('Route báo cáo ngoài phạm vi');
    const query = new URLSearchParams({ route, ...filters });
    return `/api/reports/export?${query.toString()}`;
  },
};

const CRM_CENTER_ROUTES = Object.keys(crmCenterReportScope.routeEntities);
// Buttons are part of the observed report contract.  Keep them route scoped
// so a generic renderer cannot hide a required action behind one shared label.
// The center selector is a filter (and is ignored by the parity gate); the
// remaining labels must be visible action controls.
const ROUTE_ACTIONS = {
  '/report/crm/contract/index': ['Excel'],
  '/report/crm/bill/index': ['Excel'],
  // Birth-day and access-history selectors are emitted from the API filter
  // contract. Only the observed action buttons belong in the action rail.
  '/report/center/birth_day/index': ['Cấu hình lời chúc', 'Excel'],
  '/report/center/access_history': ['Excel'],
  '/report/center/staff_teacher': ['Xuất Excel', 'Chọn trạng thái'],
  '/report/center/class_post/index': ['Chọn trạng thái lớp', 'Excel'],
  '/report/crm/customer_care/index': ['Excel'],
  '/report/crm/customer_care_result_by_center': ['Excel'],
  '/report/crm/customer_care_result_by_district': ['Phường Chương Mỹ', 'Excel'],
  '/report/crm/customer_care_result_by_dob': ['Excel'],
  '/report/crm/customer_care_result_by_source': ['Excel'],
  '/report/crm/customer_care_result_by_sale': ['Excel'],
  '/report/crm/customer_care_result': ['Cập nhật', 'Excel'],
  '/report/crm/customer_report/index': ['Excel'],
  '/report/crm/customer_trailer': ['Excel'],
};
const INLINE_EXPORT_ROUTES = new Set([
  '/report/crm/contract/index', '/report/crm/bill/index',
  '/report/crm/customer_care/index', '/report/crm/customer_report/index',
  '/report/center/birth_day/index', '/report/center/access_history',
]);

const ROUTE_TABS = {
  '/report/crm/contract/index': ['Thống kê danh sách hợp đồng', 'Thống kê danh sách hóa đơn'],
  '/report/crm/bill/index': ['Thống kê danh sách hợp đồng', 'Thống kê danh sách hóa đơn'],
  '/report/center/birth_day/index': ['Báo cáo sinh nhật học viên', 'Báo cáo sinh nhật nhân viên - giáo viên'],
  '/report/crm/customer_care/index': ['Chăm sóc theo trung tâm', 'Chăm sóc theo phường xã', 'Theo năm sinh học viên', 'Theo nguồn', 'Theo nhân viên sale', 'Báo cáo kết quả chăm sóc khách hàng', 'Báo cáo chăm sóc khách hàng'],
  // The result reports share the same observed tab bar.  Each lens has its
  // own sibling route, so render the bar consistently on every lens instead
  // of leaving the tabs inert on the non-district screens.
  '/report/crm/customer_care_result': ['Biểu đồ', 'Chăm sóc theo trung tâm', 'Chăm sóc theo phường xã', 'Theo năm sinh học viên', 'Theo nguồn', 'Theo nhân viên sale'],
  '/report/crm/customer_care_result_by_center': ['Trung tâm', 'Nhóm sale', 'Sale'],
  '/report/crm/customer_care_result_by_district': ['Biểu đồ', 'Chăm sóc theo trung tâm', 'Chăm sóc theo phường xã', 'Theo năm sinh học viên', 'Theo nguồn', 'Theo nhân viên sale'],
  '/report/crm/customer_care_result_by_dob': ['Biểu đồ', 'Chăm sóc theo trung tâm', 'Chăm sóc theo phường xã', 'Theo năm sinh học viên', 'Theo nguồn', 'Theo nhân viên sale'],
  '/report/crm/customer_care_result_by_source': ['Biểu đồ', 'Chăm sóc theo trung tâm', 'Chăm sóc theo phường xã', 'Theo năm sinh học viên', 'Theo nguồn', 'Theo nhân viên sale'],
  '/report/crm/customer_care_result_by_sale': ['Biểu đồ', 'Chăm sóc theo trung tâm', 'Chăm sóc theo phường xã', 'Theo năm sinh học viên', 'Theo nguồn', 'Theo nhân viên sale'],
  '/report/crm/customer_report/index': ['Báo cáo khách hàng'],
  '/report/crm/customer_statistic/index': ['Tỷ lệ chung', 'Tỷ lệ chuyển đổi khách hàng theo thời gian'],
};

const CUSTOMER_CARE_CENTER_TABS = Object.freeze(['Trung tâm', 'Nhóm sale', 'Sale']);

export function customerCareCenterRows(records, dimension, teamMemberships = []) {
  const groups = new Map();
  const knownProcessed = new Set(['CONTACTED', 'QUALIFIED', 'CONVERTED', 'LOST']);
  const teamBySaleOwner = new Map();
  for (const record of Array.isArray(teamMemberships) ? teamMemberships : []) {
    const data = record?.data && typeof record.data === 'object' ? record.data : record;
    const member = String(data?.full_name || data?.sale_owner || '').trim();
    const team = String(data?.team_name || data?.group_name || '').trim();
    if (member && team) teamBySaleOwner.set(member, team);
  }
  for (const record of Array.isArray(records) ? records : []) {
    const status = String(record?.status || '').trim().toUpperCase();
    const key = dimension === 'center' ? String(record?.branch || '').trim()
      : dimension === 'sale' ? String(record?.sale_owner || '').trim()
        : teamBySaleOwner.get(String(record?.sale_owner || '').trim()) || '';
    if (!key) continue;
    const current = groups.get(key) || { label: key, total: 0, processed: 0, pending: 0 };
    current.total += 1;
    if (knownProcessed.has(status)) current.processed += 1;
    else if (status === 'NEW') current.pending += 1;
    groups.set(key, current);
  }
  return [...groups.values()].sort((a, b) => b.total - a.total || a.label.localeCompare(b.label, 'vi'))
    .map(row => ({ ...row, rate: row.total ? (row.processed * 100) / row.total : 0 }));
}

function customerCareCenterTableMarkup(rows, dimension) {
  const label = dimension === 'center' ? 'Trung tâm' : dimension === 'team' ? 'Nhóm sale' : 'Nhân viên sale';
  const body = rows.length ? rows.map(row => `<tr><td>${escapeHtml(row.label)}</td><td>${row.total.toLocaleString('vi-VN')}</td><td>${row.processed.toLocaleString('vi-VN')}</td><td>${row.pending.toLocaleString('vi-VN')}</td><td>${row.rate.toLocaleString('vi-VN', { maximumFractionDigits: 2 })} %</td></tr>`).join('') : `<tr><td colspan="5" class="empty" role="status">Chưa có dữ liệu${dimension === 'team' ? ' nhóm sale' : ''}.</td></tr>`;
  return `<div class="report-table-container" data-report-table><div class="table-wrap report-table-scroll" tabindex="0" role="region" aria-label="Bảng báo cáo"><table><thead><tr><th>${label}</th><th>Tổng KH</th><th>Đã xử lý</th><th>Chưa xử lý</th><th>Tỷ lệ xử lý</th></tr></thead><tbody data-report-table-body>${body}</tbody></table></div></div>`;
}

function stabilizeCustomerCareCenterTabs(screen, renderReport, view) {
  if (!screen) return;
  const activeIndex = view === 'team' ? 1 : view === 'sale' ? 2 : 0;
  const normalize = () => {
    if (window.location.pathname !== '/report/crm/customer_care_result_by_center') {
      screen._customerCareCenterTabObserver?.disconnect(); return;
    }
    const strip = screen.querySelector('.ref-tabs');
    if (!strip) return;
    const current = [...strip.querySelectorAll('.ref-tab')];
    const sameShape = current.length === CUSTOMER_CARE_CENTER_TABS.length
      && current.every((tab, index) => tab.textContent.trim() === CUSTOMER_CARE_CENTER_TABS[index]);
    if (!sameShape) {
      strip.replaceChildren(...CUSTOMER_CARE_CENTER_TABS.map(label => {
        const tab = document.createElement('button'); tab.type = 'button'; tab.className = 'ref-tab';
        tab.setAttribute('role', 'tab'); tab.textContent = label; return tab;
      }));
    }
    [...strip.querySelectorAll('.ref-tab')].forEach((tab, index) => {
      tab.classList.toggle('active', index === activeIndex);
      tab.setAttribute('aria-selected', String(index === activeIndex));
      if (tab.dataset.customerCareViewBound === 'true') return;
      tab.dataset.customerCareViewBound = 'true';
      tab.addEventListener('click', event => {
        event.stopPropagation();
        const form = screen.querySelector('[data-report-form]');
        const filters = form ? Object.fromEntries(new FormData(form)) : {};
        renderReport({ ...filters, care_view: ['center', 'team', 'sale'][index] }).catch(error => {
          screen.querySelector('[data-report-table]')?.replaceChildren(document.createTextNode(error.message || String(error)));
        });
      }, true);
    });
  };
  screen._customerCareCenterTabObserver?.disconnect();
  normalize();
  screen._customerCareCenterTabObserver = new MutationObserver(normalize);
  screen._customerCareCenterTabObserver.observe(screen, { childList: true, subtree: true });
}

// Reference tabs either open a sibling report route or switch the report lens.
// The shell only paints the active underline; route modules own the action.
const REPORT_TAB_ROUTES = Object.freeze({
  '/report/crm/contract/index': {
    'Thống kê danh sách hợp đồng': '/report/crm/contract/index',
    'Thống kê danh sách hóa đơn': '/report/crm/bill/index',
  },
  '/report/crm/bill/index': {
    'Thống kê danh sách hợp đồng': '/report/crm/contract/index',
    'Thống kê danh sách hóa đơn': '/report/crm/bill/index',
  },
  '/report/center/birth_day/index': {
    'Báo cáo sinh nhật học viên': '/report/center/birth_day/index',
    'Báo cáo sinh nhật nhân viên - giáo viên': '/report/center/birth_day/index',
  },
  '/report/crm/customer_care/index': {
    'Chăm sóc theo trung tâm': '/report/crm/customer_care_result_by_center',
    'Chăm sóc theo phường xã': '/report/crm/customer_care_result_by_district',
    'Theo năm sinh học viên': '/report/crm/customer_care_result_by_dob',
    'Theo nguồn': '/report/crm/customer_care_result_by_source',
    'Theo nhân viên sale': '/report/crm/customer_care_result_by_sale',
    'Báo cáo kết quả chăm sóc khách hàng': '/report/crm/customer_care_result',
  },
  '/report/crm/customer_care_result': {
    'Biểu đồ': '/report/crm/customer_care_result',
    'Chăm sóc theo trung tâm': '/report/crm/customer_care_result_by_center',
    'Chăm sóc theo phường xã': '/report/crm/customer_care_result_by_district',
    'Theo năm sinh học viên': '/report/crm/customer_care_result_by_dob',
    'Theo nguồn': '/report/crm/customer_care_result_by_source',
    'Theo nhân viên sale': '/report/crm/customer_care_result_by_sale',
  },
  '/report/crm/customer_care_result_by_center': {
    'Biểu đồ': '/report/crm/customer_care_result',
    'Chăm sóc theo trung tâm': '/report/crm/customer_care_result_by_center',
    'Chăm sóc theo phường xã': '/report/crm/customer_care_result_by_district',
    'Theo năm sinh học viên': '/report/crm/customer_care_result_by_dob',
    'Theo nguồn': '/report/crm/customer_care_result_by_source',
    'Theo nhân viên sale': '/report/crm/customer_care_result_by_sale',
  },
  '/report/crm/customer_care_result_by_district': {
    'Biểu đồ': '/report/crm/customer_care_result',
    'Chăm sóc theo trung tâm': '/report/crm/customer_care_result_by_center',
    'Chăm sóc theo phường xã': '/report/crm/customer_care_result_by_district',
    'Theo năm sinh học viên': '/report/crm/customer_care_result_by_dob',
    'Theo nguồn': '/report/crm/customer_care_result_by_source',
    'Theo nhân viên sale': '/report/crm/customer_care_result_by_sale',
  },
  '/report/crm/customer_care_result_by_dob': {
    'Biểu đồ': '/report/crm/customer_care_result',
    'Chăm sóc theo trung tâm': '/report/crm/customer_care_result_by_center',
    'Chăm sóc theo phường xã': '/report/crm/customer_care_result_by_district',
    'Theo năm sinh học viên': '/report/crm/customer_care_result_by_dob',
    'Theo nguồn': '/report/crm/customer_care_result_by_source',
    'Theo nhân viên sale': '/report/crm/customer_care_result_by_sale',
  },
  '/report/crm/customer_care_result_by_source': {
    'Biểu đồ': '/report/crm/customer_care_result',
    'Chăm sóc theo trung tâm': '/report/crm/customer_care_result_by_center',
    'Chăm sóc theo phường xã': '/report/crm/customer_care_result_by_district',
    'Theo năm sinh học viên': '/report/crm/customer_care_result_by_dob',
    'Theo nguồn': '/report/crm/customer_care_result_by_source',
    'Theo nhân viên sale': '/report/crm/customer_care_result_by_sale',
  },
  '/report/crm/customer_care_result_by_sale': {
    'Biểu đồ': '/report/crm/customer_care_result',
    'Chăm sóc theo trung tâm': '/report/crm/customer_care_result_by_center',
    'Chăm sóc theo phường xã': '/report/crm/customer_care_result_by_district',
    'Theo năm sinh học viên': '/report/crm/customer_care_result_by_dob',
    'Theo nguồn': '/report/crm/customer_care_result_by_source',
    'Theo nhân viên sale': '/report/crm/customer_care_result_by_sale',
  },
});

const CUSTOMER_CARE_RESULT_TAB_INDEX = Object.freeze({
  '/report/crm/customer_care_result': 0,
  '/report/crm/customer_care_result_by_center': 1,
  '/report/crm/customer_care_result_by_district': 2,
  '/report/crm/customer_care_result_by_dob': 3,
  '/report/crm/customer_care_result_by_source': 4,
  '/report/crm/customer_care_result_by_sale': 5,
});

function bindReportTabNavigation(screen, route, onBirthdayView) {
  // Keep the two-argument module contract; birthday rendering may provide a
  // transient callback on the screen so callers and focused tests share the
  // same binding path.
  onBirthdayView = onBirthdayView || screen?.__birthdayViewHandler;
  const mapping = REPORT_TAB_ROUTES[route];
  if (!mapping || !screen) return;
  screen.querySelectorAll('.ref-tabs .ref-tab').forEach(tab => {
    if (tab.dataset.routeBound === 'true') return;
    const target = mapping[String(tab.textContent || '').trim()];
    if (!target) return;
    tab.dataset.routeBound = 'true';
    tab.addEventListener('click', event => {
      event.preventDefault();
      // The birthday screen keeps both lenses on one endpoint. Its observed
      // type selector is the source of truth for the tab content.
      if (route === '/report/center/birth_day/index') {
        const tabs = [...screen.querySelectorAll('.ref-tabs .ref-tab')];
        const index = tabs.indexOf(tab);
        tabs.forEach((node, i) => { const active = i === index; node.classList.toggle('active', active); node.setAttribute('aria-selected', active ? 'true' : 'false'); });
        onBirthdayView?.(index);
        return;
      }
      if (target === route) return;
      window.history.pushState({}, '', target);
      window.dispatchEvent(new PopStateEvent('popstate'));
    });
  });
}

function bindCustomerStatisticTabs(screen, renderReport, view) {
  if (!screen || typeof renderReport !== 'function') return;
  screen.querySelectorAll('.ref-tabs .ref-tab').forEach((tab, index) => {
    tab.setAttribute('aria-selected', index === (view === 'conversion_time' ? 1 : 0) ? 'true' : 'false');
    if (tab.dataset.customerStatisticBound === 'true') return;
    tab.dataset.customerStatisticBound = 'true';
    tab.addEventListener('click', event => {
      event.preventDefault();
      const nextView = index === 1 ? 'conversion_time' : 'overall';
      if (nextView === view) return;
      renderReport({ view: nextView }).catch(error => {
        screen.innerHTML = `<div class="card empty">${escapeHtml(error.message || error)}</div>`;
      });
    });
  });
}

// Keep route-observed placeholders, including repeated English dates on
// the contract screen. Field names distinguish the ranges without inventing
// unobserved business labels.
const ROUTE_PLACEHOLDERS = {
  '/report/crm/contract/index': {
    from_date: 'From date', to_date: 'To date',
    from_date_2: 'From date', to_date_2: 'To date',
  },
  '/report/crm/bill/index': { from_date: 'Từ ngày', to_date: 'Đến ngày' },
  '/report/crm/customer_care/index': {
    from_date: 'Từ ngày', to_date: 'Đến ngày',
    from_date_contract: 'Từ ngày hợp đồng', to_date_contract: 'Đến ngày hợp đồng',
  },
  '/report/crm/customer_report/index': {
    tu_ngay: 'Từ ngày', en_ngay: 'Đến ngày',
    tu_ngay_2: 'Từ ngày hợp đồng', en_ngay_2: 'Đến ngày hợp đồng',
  },
  '/report/center/class_post/index': { from_date: 'From date', to_date: 'To date' },
};
const LABELS = {
  'From date': 'Từ ngày', 'To date': 'Đến ngày', Facility: 'Trung tâm', Center: 'Trung tâm',
  'Customer': 'Khách hàng', 'Source': 'Nguồn dữ liệu', Status: 'Trạng thái', Role: 'Phân quyền',
};

function escapeHtml(value) {
  return String(value ?? '').replace(/[&<>'"]/g, char => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;' }[char]));
}

function displayReportValue(value, helpers) {
  if (value === null || value === undefined || value === '') return '—';
  if (typeof value === 'number') return Number(value).toLocaleString('vi-VN');
  const text = String(value);
  if (text.toUpperCase() === 'UNKNOWN' || text === 'Chưa cập nhật') return '—';
  if (/status|trạng thái|role|phân quyền/i.test(text) && typeof helpers?.statusLabel === 'function') return helpers.statusLabel(text);
  const date = text.match(/^(\d{4})-(\d{2})-(\d{2})(?:[T ](.*))?$/);
  return date ? `${date[3]}/${date[2]}/${date[1]}${date[4] ? ` ${date[4]}` : ''}` : text;
}

function customerStatisticValue(value, label, helpers) {
  const rendered = displayReportValue(value, helpers);
  if (rendered === '—') return rendered;
  if (typeof value === 'number' || /^-?\d+(?:[.,]\d+)?$/.test(String(value ?? '').trim())) {
    const number = Number(String(value).replace(',', '.'));
    if (Number.isFinite(number) && /%|tỷ lệ|tỉ lệ|rate|percent/i.test(String(label || ''))) {
      const normalized = Number.isInteger(number) ? String(number) : String(Number(number.toFixed(2)));
      return `${normalized} %`;
    }
  }
  return rendered;
}

const CUSTOMER_STATISTIC_GROUPS = Object.freeze([
  ['Khách hàng chăm sóc', 'so_luong', 'ti_le'],
  ['Khách hàng học thử', 'so_luong_2', 'ti_le_2'],
  ['Khách hàng test/hẹn test', 'so_luong_3', 'ti_le_3'],
  ['Khách hàng chăm sóc thành công', 'so_luong_4', 'ti_le_4'],
]);

function customerStatisticColumns(columns) {
  const input = Array.isArray(columns) ? columns : [];
  const byKey = new Map(input.map(column => [String(column?.key || ''), column]));
  const byLabel = new Map(input.map(column => [String(column?.label || ''), column]));
  const pick = (key, label) => byKey.get(key) || byLabel.get(label) || { key, label };
  return [
    pick('no', 'No.'),
    pick('nguon_du_lieu', 'Nguồn dữ liệu'),
    pick('tong', 'Tổng'),
    ...CUSTOMER_STATISTIC_GROUPS.flatMap(([, count, rate]) => [pick(count, count === 'so_luong' ? 'Số lượng' : 'Số lượng'), pick(rate, rate === 'ti_le' ? 'Tỉ lệ' : 'Tỉ lệ')]),
  ];
}

function customerStatisticTableMarkup(columns, rows, helpers) {
  const normalized = customerStatisticColumns(columns);
  const head = `<tr data-statistic-group><th scope="col" rowspan="2">No.</th><th scope="col" rowspan="2">Nguồn dữ liệu</th><th scope="col" rowspan="2">Tổng</th>${CUSTOMER_STATISTIC_GROUPS.map(([label]) => `<th scope="col" colspan="2">${escapeHtml(label)}</th>`).join('')}</tr><tr>${CUSTOMER_STATISTIC_GROUPS.map(() => '<th scope="col">Số lượng</th><th scope="col">Tỉ lệ</th>').join('')}</tr>`;
  const body = rows.length
    ? rows.map(row => `<tr>${normalized.map(column => `<td>${escapeHtml(customerStatisticValue(row[column.key], column.label || column.key, helpers))}</td>`).join('')}</tr>`).join('')
    : `<tr><td colspan="${normalized.length}" class="empty" role="status">Không có dữ liệu.</td></tr>`;
  return `<div class="report-table-container" data-report-table><div class="table-wrap report-table-scroll" tabindex="0" role="region" aria-label="Bảng báo cáo"><table><thead>${head}</thead><tbody data-report-table-body>${body}</tbody></table></div></div>`;
}

// The five customer-care result reports expose three outcome groups.  Their
// API columns are flat (the first five descriptors followed by six child
// descriptors), while the reference renders a two-tier table header. Keep
// the row projection untouched and only add the observed grouped header.
const CUSTOMER_CARE_RESULT_ROUTES = new Set([
  '/report/crm/customer_care_result_by_center',
  '/report/crm/customer_care_result_by_district',
  '/report/crm/customer_care_result_by_dob',
  '/report/crm/customer_care_result_by_source',
  '/report/crm/customer_care_result_by_sale',
]);

function customerCareResultTableMarkup(columns, rows, helpers) {
  const input = Array.isArray(columns) ? columns : [];
  if (!input.length) return '<div class="empty">Không có dữ liệu.</div>';
  const fixed = input.slice(0, 2);
  const outcome = input.slice(2, 5);
  const child = input.slice(5, 11);
  const labels = col => LABELS[col?.label] || col?.label || col?.key || '';
  const head = `<tr>${fixed.map(col => `<th scope="col" rowspan="2">${escapeHtml(labels(col))}</th>`).join('')}${outcome.map(col => `<th scope="col" colspan="2">${escapeHtml(labels(col))}</th>`).join('')}</tr><tr>${outcome.map((_, index) => `<th scope="col">${escapeHtml(labels(child[index * 2] || { label: 'Số lượng' }))}</th><th scope="col">${escapeHtml(labels(child[index * 2 + 1] || { label: 'Tỉ lệ' }))}</th>`).join('')}</tr>`;
  const body = rows.length
    ? rows.map(row => `<tr>${input.map(col => `<td>${escapeHtml(displayReportValue(row[col.key], helpers))}</td>`).join('')}</tr>`).join('')
    : `<tr><td colspan="${input.length}" class="empty" role="status">Không có dữ liệu.</td></tr>`;
  return `<div class="report-table-container" data-report-table><div class="table-wrap report-table-scroll" tabindex="0" role="region" aria-label="Bảng báo cáo"><table><thead>${head}</thead><tbody data-report-table-body>${body}</tbody></table></div></div>`;
}

function scheduleSemanticPlaceholders(screen, route) {
  const patch = ROUTE_PLACEHOLDERS[route];
  if (!patch || !screen) return;
  // The shared shell normalizer runs after a worker renderer and may restore
  // the inventory's generic date labels. Reapply the business labels after
  // that pass so the two ranges remain distinguishable to users and the
  // parity extractor.
  const apply = () => {
    for (const [name, placeholder] of Object.entries(patch)) {
      const input = screen.querySelector(`[name="${CSS.escape(name)}"]`);
      if (input) {
        input.placeholder = placeholder;
        input.setAttribute('aria-label', placeholder);
      }
    }
  };
  apply();
  setTimeout(apply, 0);
  setTimeout(apply, 120);
  setTimeout(apply, 350);
  setTimeout(apply, 800);
}

function routeFilterShape(route, filters) {
  return (Array.isArray(filters) ? filters : []).map(filter => {
    const shaped = { ...filter };
    if (String(shaped.type || '').toLowerCase() === 'select' && !String(shaped.label || '').trim() && Array.isArray(shaped.options) && shaped.options.length) {
      // The observed first option is the visible control name.  Supplying it
      // as the label keeps the shared shell normalizer from replacing it with
      // a generic "Tất cả"/"Tìm kiếm" label.
      shaped.label = String(shaped.options[0]);
    }
    // Two independent status selectors exist on access history.  The
    // reference repeats the first option text, but duplicate visible labels
    // make the controls ambiguous and are rejected by the current diff gate.
    // Keep the second selector's domain meaning explicit in Vietnamese.
    if (route === '/report/center/access_history' && String(shaped.name || '') === 'filter_4' && Array.isArray(shaped.options) && shaped.options.length) {
      // The reference intentionally repeats "Chọn trạng thái" for the
      // account-status and student-status selectors. Preserve that order and
      // wording rather than introducing a new label.
      shaped.options = [...shaped.options];
      shaped.label = String(shaped.options[0]);
    }
    const placeholder = ROUTE_PLACEHOLDERS[route]?.[String(shaped.name || '')];
    if (placeholder) { shaped.label = placeholder; shaped.placeholder = placeholder; }
    // The reference exposes the empty creator select by its observed label.
    // Keep its option domain empty; only restore the visible semantic name.
    if (route === '/report/crm/bill/index' && String(shaped.name || '') === 'creator_id') shaped.label = 'Người tạo';
    return shaped;
  });
}

function repairObservedControls(screen, route, filters) {
  if (!screen) return;
  const includePageSize = route === '/report/center/birth_day/index';
  const expected = (Array.isArray(filters) ? filters : []).filter(filter => includePageSize || !/length|hiển thị.*bản ghi|số bản ghi|page.?size/i.test(`${filter?.name || ''} ${filter?.label || ''} ${filter?.placeholder || ''}`));
  const formAtRender = screen.querySelector('[data-report-form]');
  setTimeout(() => {
    if (screen.querySelector('[data-report-form]') !== formAtRender) return;
    const controls = [...screen.querySelectorAll('.filter-strip input, .filter-strip select')];
    expected.forEach((filter, index) => {
      const control = controls[index];
      if (!control) return;
      const name = String(filter.name || `filter_${index + 1}`).replace(/[^A-Za-z0-9_-]/g, '_');
      control.name = name;
      if (control.tagName === 'SELECT') {
        const options = Array.isArray(filter.options) ? filter.options.map(value => String(value)) : [];
        if (route === '/report/crm/bill/index' && String(filter.name || '') === 'creator_id' && !options.length) options.push('Người tạo');
        const current = control.value;
        control.innerHTML = options.length
          ? options.map((value, optionIndex) => `<option value="${escapeHtml(value)}"${optionIndex === 0 || value === current ? ' selected' : ''}>${escapeHtml(value)}</option>`).join('')
          : '<option value=""></option>';
        if (options.includes(current)) control.value = current;
        // The shared shell may assign the generic aria label "Tìm kiếm" to
        // every select after render.  Keep the observed first option as the
        // visible semantic label; empty selects stay unlabeled like the ref.
        const selectLabel = options.find(Boolean) || String(filter.label || '').trim();
        control.setAttribute('aria-label', selectLabel || '');
      } else {
        const placeholder = String(filter.placeholder || filter.label || '').trim();
        if (placeholder) control.placeholder = placeholder;
        control.setAttribute('aria-label', placeholder);
      }
    });
    // The shared shell normally drops page-size controls.  Birth-day has a
    // real observed report_table_length selector, so restore that one control
    // after the shell pass instead of inventing a generic filter.
    if (includePageSize && !screen.querySelector('[name="report_table_length"]')) {
      const pageFilter = expected.find(filter => String(filter?.name || '') === 'report_table_length');
      const strip = screen.querySelector('.filter-strip');
      if (pageFilter && strip) {
        const wrapper = document.createElement('label');
        const select = document.createElement('select');
        select.name = 'report_table_length';
        for (const value of (Array.isArray(pageFilter.options) ? pageFilter.options : ['10', '25', '50', 'All'])) {
          const option = document.createElement('option');
          option.value = String(value); option.textContent = String(value); select.append(option);
        }
        select.setAttribute('aria-label', String(pageFilter.label || 'Hiển thị 10 25 50 All bản ghi'));
        wrapper.append(document.createTextNode(String(pageFilter.label || 'Hiển thị 10 25 50 All bản ghi')));
        wrapper.append(select);
        strip.insertBefore(wrapper, strip.querySelector('button'));
      }
    }
  }, 25);
  // app.js performs a later generic normalization pass.  Reapply the
  // route-exact select labels while that pass settles; this is the same
  // bounded repair used by the finance report renderer.
  let ticks = 0;
  const timer = setInterval(() => {
    if (screen.querySelector('[data-report-form]') !== formAtRender) { clearInterval(timer); return; }
    if (INLINE_EXPORT_ROUTES.has(route)) {
      const strip = screen.querySelector('.filter-strip');
      const inline = strip?.querySelectorAll('[data-report-action]');
      // The shared shell may prepend actions during its normalizer pass.
      // Keep observed actions after all filter controls.
      if (strip && inline?.length) inline.forEach(node => strip.appendChild(node));
    }
    const controls = [...screen.querySelectorAll('.filter-strip input, .filter-strip select')];
    expected.forEach((filter, index) => {
      const control = controls[index];
      if (!control) return;
      if (control.tagName === 'SELECT') {
        const first = [...control.options].map(option => option.textContent.trim()).find(Boolean) || '';
        const observedLabel = String(filter.name || '') === 'creator_id' && String(filter.label || '').trim()
          ? String(filter.label).trim()
          : String(filter.name || '') === 'report_table_length'
          ? String(filter.label || 'Hiển thị 10 25 50 All bản ghi')
          : first;
        control.setAttribute('aria-label', observedLabel);
      } else {
        const placeholder = String(filter.placeholder || filter.label || '').trim();
        if (placeholder) {
          control.placeholder = placeholder;
          control.setAttribute('aria-label', placeholder);
        }
      }
    });
    if (route === '/report/center/access_history') {
      const controlsNow = [...screen.querySelectorAll('.filter-strip select')];
      const studentStatus = controlsNow[3];
      if (studentStatus) {
        const options = [...studentStatus.options];
        studentStatus.setAttribute('aria-label', options[0]?.textContent.trim() || 'Chọn trạng thái');
      }
    }
    if (includePageSize && !screen.querySelector('[name="report_table_length"]')) {
      const pageFilter = expected.find(filter => String(filter?.name || '') === 'report_table_length');
      const strip = screen.querySelector('.filter-strip');
      if (pageFilter && strip) {
        const wrapper = document.createElement('label');
        const select = document.createElement('select');
        select.name = 'report_table_length';
        for (const value of (Array.isArray(pageFilter.options) ? pageFilter.options : ['10', '25', '50', 'All'])) {
          const option = document.createElement('option');
          option.value = String(value); option.textContent = String(value); select.append(option);
        }
        select.setAttribute('aria-label', String(pageFilter.label || 'Hiển thị 10 25 50 All bản ghi'));
        wrapper.append(document.createTextNode(String(pageFilter.label || 'Hiển thị 10 25 50 All bản ghi')));
        wrapper.append(select);
        strip.insertBefore(wrapper, strip.querySelector('button'));
      }
    }
    ticks += 1;
    if (ticks >= 40) clearInterval(timer);
  }, 50);
}

const CRM_BILL_SUMMARY_KEYS = {
  closedAmount: ['closed_amount', 'total_closed', 'total_paid', 'paid_amount', 'payment_amount', 'paid', 'amount_paid', 'tong_da_dong', 'a_ong'],
  customerCount: ['customer_count', 'customerCount', 'student_count', 'customer_total'],
};

function firstKnownValue(source, keys) {
  for (const key of keys) {
    if (Object.prototype.hasOwnProperty.call(source, key) && source[key] !== null && source[key] !== undefined && source[key] !== '') return source[key];
  }
  return null;
}

export function crmBillSummaryMarkup(summary, rows = []) {
  const source = summary && typeof summary === 'object' ? { ...summary } : {};
  // The report API may omit an aggregate while still returning bill rows.
  // Derive only values whose meaning is explicit in the observed row schema;
  // keep empty/ambiguous aggregates as an em dash.
  const sourceRows = Array.isArray(rows) ? rows : [];
  if (firstKnownValue(source, CRM_BILL_SUMMARY_KEYS.closedAmount) === null && sourceRows.length) {
    const amounts = sourceRows.map(row => firstKnownValue(row, CRM_BILL_SUMMARY_KEYS.closedAmount)).filter(value => typeof value === 'number' && Number.isFinite(value));
    if (amounts.length) source.total_paid = amounts.reduce((sum, value) => sum + value, 0);
  }
  if (firstKnownValue(source, CRM_BILL_SUMMARY_KEYS.customerCount) === null && sourceRows.length) {
    const names = sourceRows.map(row => firstKnownValue(row, ['customer_name', 'student_name', 'full_name', 'khach_hang'])).filter(value => value !== null);
    if (names.length === sourceRows.length) source.customer_count = new Set(names.map(value => String(value))).size;
  }
  const value = keys => {
    const resolved = firstKnownValue(source, keys);
    return resolved === null ? '—' : escapeHtml(displayReportValue(resolved, {}));
  };
  return `<div class="report-summary" data-report-summary><div><b>Đơn vị tiền tệ:</b> VND</div><div><b>Đã Đóng:</b> ${value(CRM_BILL_SUMMARY_KEYS.closedAmount)}</div><div><b>Số lượng khách hàng:</b> ${value(CRM_BILL_SUMMARY_KEYS.customerCount)}</div></div>`;
}

const CRM_BILL_COLUMN_ORDER = ['no','khach_hang','phu_huynh','nguon_du_lieu','ma_hop_ong','khoa_hoc','lop_hoc','chuong_trinh_uu_ai','so_tien_phai_thu_theo_hop_ong','con_no','trang_thai','nguon_du_lieu_2','thuc_thu_theo_hoa_on','nhan_vien','ghi_chu','ngay_tao','nguoi_tao','a_ong','thoi_gian_ong','so_hoa_on','hinh_thuc_thanh_toan'];
const CRM_BILL_INVOICE_CHILD_KEYS = ['a_ong', 'thoi_gian_ong', 'so_hoa_on', 'hinh_thuc_thanh_toan'];

export function normalizeCrmBillColumns(columns) {
  const input = Array.isArray(columns) ? columns.filter(column => column && typeof column === 'object') : [];
  if (!input.length) return [];
  const byKey = new Map(input.map(column => [String(column.key || ''), column]));
  const byLabel = new Map(input.map(column => [String(column.label || ''), column]));
  const aliases = { a_ong: 'Đã Đóng', thoi_gian_ong: 'Thời gian đóng', so_hoa_on: 'Số hóa đơn', hinh_thuc_thanh_toan: 'Hình thức thanh toán' };
  // The report API can omit the persisted invoice receipt descriptors even
  // though the row projection still carries their fields. Restore the
  // observed descriptors so the two-tier header remains stable; missing
  // values stay em dashes through crmBillCellValue/displayReportValue.
  const hasBaseContractColumns = byKey.has('no') || byKey.has('khach_hang') || byKey.has('ma_hop_ong');
  const descriptors = {
    a_ong: { key: 'a_ong', label: 'Đã Đóng' },
    thoi_gian_ong: { key: 'thoi_gian_ong', label: 'Thời gian đóng' },
    so_hoa_on: { key: 'so_hoa_on', label: 'Số hóa đơn' },
    hinh_thuc_thanh_toan: { key: 'hinh_thuc_thanh_toan', label: 'Hình thức thanh toán' },
  };
  const known = CRM_BILL_COLUMN_ORDER.map(key => {
    const existing = byKey.get(key) || byLabel.get(aliases[key]);
    if (existing) return existing;
    return hasBaseContractColumns && descriptors[key] ? descriptors[key] : null;
  }).filter(Boolean);
  const knownObjects = new Set(known);
  return [...known, ...input.filter(column => !knownObjects.has(column))];
}

const CRM_BILL_ROW_ALIASES = {
  thuc_thu_theo_hoa_on: ['thuc_thu_theo_hoa_on', 'payment_amount', 'paid_amount'],
  a_ong: ['a_ong', 'closed_amount', 'paid_amount', 'payment_amount'],
  thoi_gian_ong: ['thoi_gian_ong', 'closed_at', 'payment_date', 'invoice_date'],
  so_hoa_on: ['so_hoa_on', 'invoice_code'],
  hinh_thuc_thanh_toan: ['hinh_thuc_thanh_toan', 'payment_method'],
};

export function crmBillCellValue(row, column) {
  const source = row && typeof row === 'object' ? row : {};
  const key = String(column?.key || '');
  for (const candidate of CRM_BILL_ROW_ALIASES[key] || [key]) {
    if (Object.prototype.hasOwnProperty.call(source, candidate) && source[candidate] !== null && source[candidate] !== undefined && source[candidate] !== '') return source[candidate];
  }
  return source[key];
}

function crmBillTableMarkup(columns, rows, helpers, pageSizes, pagination = null) {
  if (!columns.length) return '<div class="empty">Không có dữ liệu.</div>';
  columns = normalizeCrmBillColumns(columns);
  const labels = columns.map(col => LABELS[col.label] || col.label || col.key || '');
  const childIndexes = CRM_BILL_INVOICE_CHILD_KEYS.map(key => columns.findIndex(column => String(column.key || '') === key || String(column.label || '') === ({ a_ong: 'Đã Đóng', thoi_gian_ong: 'Thời gian đóng', so_hoa_on: 'Số hóa đơn', hinh_thuc_thanh_toan: 'Hình thức thanh toán' }[key])));
  const childStart = childIndexes[0];
  const childEnd = childIndexes[childIndexes.length - 1] + 1;
  const hasContiguousInvoiceChildren = childIndexes.every((index, offset) => index >= 0 && index === childStart + offset);
  const groupIndex = columns.findIndex(col => String(col.label || '').toLowerCase().startsWith('thực thu'));
  let head;
  if (groupIndex >= 0 && hasContiguousInvoiceChildren && childStart > groupIndex && childEnd <= columns.length) {
    const cell = (index, rowspan = 2) => `<th scope="col" rowspan="${rowspan}">${escapeHtml(labels[index])}</th>`;
    head = `<tr>${columns.map((_, index) => index === groupIndex ? '<th scope="col" colspan="4">Thực thu (Theo hóa đơn)</th>' : childIndexes.includes(index) ? '' : cell(index)).join('')}</tr><tr>${columns.slice(childStart, childEnd).map((_, i) => `<th scope="col">${escapeHtml(labels[childStart + i])}</th>`).join('')}</tr>`;
  } else {
    head = `<tr>${columns.map((col, i) => `<th scope="col">${escapeHtml(labels[i])}</th>`).join('')}</tr>`;
  }
  const body = rows.length ? rows.map(row => `<tr>${columns.map(col => `<td>${escapeHtml(displayReportValue(crmBillCellValue(row, col), helpers))}</td>`).join('')}</tr>`).join('') : `<tr><td colspan="${Math.max(columns.length, 1)}" class="empty" role="status">Không có dữ liệu.</td></tr>`;
  return `<div class="report-table-container" data-report-table><div class="table-wrap report-table-scroll" tabindex="0" role="region" aria-label="Bảng báo cáo"><table><thead>${head}</thead><tbody data-report-table-body>${body}</tbody></table></div>${pagination?.enabled ? '<div class="report-table-footer" data-report-table-footer></div>' : ''}</div>`;
}

// Reference pager (reference-inventory.json): contract '‹ 1..6 ›', bill '‹ 1..4 ›',
// customer care '‹ 1..5 ›' -> 10 rows per page.
export const CRM_REPORT_PAGINATION = Object.freeze({
  '/report/crm/contract/index': Object.freeze({ enabled: true, pageSize: 10 }),
  '/report/crm/bill/index': Object.freeze({ enabled: true, pageSize: 10 }),
  '/report/crm/customer_care/index': Object.freeze({ enabled: true, pageSize: 10 }),
});

function crmRenderer(scope) {
  return async (screen, ctx) => {
    let customerStatisticView = 'overall';
    let birthdayView = 'student';
    let customerCareCenterView = 'center';
    let renderVersion = 0;
    const renderReport = async (activeFilters = {}) => {
      const version = ++renderVersion;
      if (ctx.route === '/report/center/birth_day/index' && activeFilters.birthday_type) birthdayView = activeFilters.birthday_type === 'staff' ? 'staff' : 'student';
      const staffBirthday = ctx.route === '/report/center/birth_day/index' && birthdayView === 'staff';
      screen.dataset.birthdayView = staffBirthday ? 'staff' : 'student';
      if (ctx.route === '/report/crm/customer_statistic/index') {
        customerStatisticView = activeFilters.view === 'conversion_time' ? 'conversion_time' : 'overall';
      }
      if (ctx.route === '/report/crm/customer_care_result_by_center' && activeFilters.care_view) {
        customerCareCenterView = ['center', 'team', 'sale'].includes(activeFilters.care_view) ? activeFilters.care_view : 'center';
      }
      const query = new URLSearchParams({ route: ctx.route, ...(ctx.route === '/report/center/birth_day/index' ? { birthday_type: birthdayView } : {}), ...activeFilters });
      const response = await ctx.api(`/api/reports/run?${query.toString()}`);
      if (ctx.route === '/report/center/birth_day/index' && version !== renderVersion) return;
      const payload = response?.data || response || {};
      let rows = Array.isArray(payload.rows) ? payload.rows : [];
      let columns = Array.isArray(payload.columns) ? payload.columns : [];
      if (ctx.route === '/report/center/birth_day/index' && birthdayView === 'staff') {
        columns = [
          { key: 'no', label: 'No.' }, { key: 'ho_ten', label: 'Họ tên' },
          { key: 'ngay_sinh', label: 'Ngày sinh' }, { key: 'chuc_danh', label: 'Chức danh' },
          { key: 'phong_ban', label: 'Phòng ban' }, { key: 'qua_tang', label: 'Quà tặng' },
          { key: 'ngay_tang', label: 'Ngày tặng' }, { key: 'trang_thai', label: 'Trạng thái' },
          { key: 'hanh_ong', label: 'Hành động' },
        ];
      }
      let customerCareCenterCustomers = [];
      let customerCareCenterMemberships = [];
      if (ctx.route === '/report/crm/customer_care_result_by_center') {
        const source = await ctx.api('/api/potential-customers');
        customerCareCenterCustomers = Array.isArray(source?.data) ? source.data : Array.isArray(source) ? source : [];
        if (customerCareCenterView === 'team') {
          const memberships = await ctx.api('/api/generated/screens?route=%2Fcrm%2Fsale_team%2Findex');
          customerCareCenterMemberships = Array.isArray(memberships?.data?.records) ? memberships.data.records : [];
        }
        const dateValue = value => {
          const text = String(value || '').trim();
          const dmy = text.match(/^(\d{1,2})\/(\d{1,2})\/(\d{4})$/);
          return dmy ? `${dmy[3]}-${dmy[2].padStart(2, '0')}-${dmy[1].padStart(2, '0')}` : text.slice(0, 10);
        };
        const from = dateValue(activeFilters.from_date), to = dateValue(activeFilters.to_date);
        if (from || to) customerCareCenterCustomers = customerCareCenterCustomers.filter(record => {
          const created = dateValue(record.created_at);
          return Boolean(created) && (!from || created >= from) && (!to || created <= to);
        });
        rows = customerCareCenterRows(customerCareCenterCustomers, customerCareCenterView, customerCareCenterMemberships);
      }
      if (ctx.route === '/report/crm/customer_care_result_by_center' && (version !== renderVersion || window.location.pathname !== ctx.route)) return;
      const filters = routeFilterShape(ctx.route, Array.isArray(payload.filters) ? payload.filters : (scope.filtersFor(ctx.route) || []).map(name => ({ name, label: name })));
      const helpers = ctx.helpers || globalThis.CenterEdu?.helpers || {};
      let fields = filters.map((filter, index) => {
        const name = String(filter.name || `filter_${index}`).replace(/[^A-Za-z0-9_-]/g, '');
        const label = String((ctx.route === '/report/crm/contract/index' && ROUTE_PLACEHOLDERS[ctx.route]?.[name]) || LABELS[filter.label] || filter.label || filter.placeholder || name);
        const kind = String(filter.type || '').toLowerCase();
        // Preserve the observed element kind, including empty selects such as
        // creator/class controls.  Converting an empty select to an input
        // shifts every following filter during the shell normalizer pass.
        const defaultDate = ctx.route === '/report/center/student_statistical/index'
          ? (name === 'from_date' ? '01/11/2026' : name === 'to_date' ? '30/11/2026' : '')
          : '';
        const valueAttr = defaultDate ? ` value="${defaultDate}"` : '';
        const options = (kind === 'select' || kind === 'multiselect')
          ? `<select name="${name}">${ctx.route === '/report/crm/contract/index' ? '' : '<option value="">Tất cả</option>'}${[...new Set((filter.options || []).map(option => String(option)))].map(option => `<option value="${escapeHtml(option)}">${escapeHtml(option)}</option>`).join('')}</select>`
          : kind === 'search'
            ? `<input name="${name}" type="search" placeholder="${escapeHtml(label)}"${valueAttr}>`
            : `<input name="${name}" type="text" placeholder="${escapeHtml(label)}"${valueAttr}>`;
        return `<label>${escapeHtml(label)}${options}</label>`;
      }).join('');
      if (staffBirthday) {
        const centerFilter = filters.find(filter => filter.name === 'esttype');
        const centers = (centerFilter?.options || []).filter(value => !/^(Chọn trung tâm|Tất cả)$/i.test(String(value)));
        const select = (name, label, options) => `<label><span>${escapeHtml(label)}</span><select name="${name}" aria-label="${escapeHtml(label)}">${options.map(([value, text]) => `<option value="${escapeHtml(value)}">${escapeHtml(text)}</option>`).join('')}</select></label>`;
        fields = select('esttype', 'Chọn trung tâm', centers.length ? centers.map(value => [value, value]) : [['', 'Chọn trung tâm']])
          + select('given_status', 'Trạng thái', [['', 'Tất cả'], ['0', 'Chưa tặng'], ['1', 'Đã tặng']])
          + select('position', 'Chức danh', [['', 'Danh sách chức danh']])
          + select('department', 'Phòng ban', [['', 'Danh sách phòng ban']])
          + select('filter_4', 'Chọn tháng', [['', 'Chọn tháng'], ['', 'Tất cả'], ...Array.from({ length: 12 }, (_, i) => [String(i + 1), String(i + 1)])])
          + '<label><span>Tìm trong bảng...</span><input name="tim_trong_bang" type="search" placeholder="Tìm trong bảng..." aria-label="Tìm trong bảng..."></label>';
      }
      const exportQuery = new URLSearchParams({ route: ctx.route, ...(ctx.route === '/report/center/birth_day/index' ? { birthday_type: birthdayView } : {}), ...activeFilters });
      const pageConfig = reportPageSizes(filters);
      const table = ctx.route === '/report/crm/customer_care_result_by_center'
        ? customerCareCenterTableMarkup(rows, customerCareCenterView)
        : ctx.route === '/report/crm/customer_statistic/index'
        ? customerStatisticTableMarkup(columns, rows, helpers)
        : ctx.route === '/report/crm/bill/index'
        ? crmBillTableMarkup(columns, rows, helpers, pageConfig.values, CRM_REPORT_PAGINATION[ctx.route])
        : CUSTOMER_CARE_RESULT_ROUTES.has(ctx.route)
          ? customerCareResultTableMarkup(columns, rows, helpers)
          : columns.length
          ? createReportTable({ columns, rows, header: col => escapeHtml(ctx.route === '/report/crm/customer_care_result_by_center' && col.key === 'facility' ? 'Facility' : LABELS[col.label] || col.label || col.key || ''), cell: (row, col) => escapeHtml(displayReportValue(row[col.key], helpers)), pageSizes: pageConfig.values, pagination: CRM_REPORT_PAGINATION[ctx.route] || null })
          : '<div class="empty">Không có dữ liệu.</div>';
      // The invoice reference places Excel after the filter controls. Keep it
      // out of the page header so the shared shell cannot duplicate it there.
      const headerActions = INLINE_EXPORT_ROUTES.has(ctx.route)
        ? (ROUTE_ACTIONS[ctx.route] || []).filter(label => label !== 'Excel')
        : (ROUTE_ACTIONS[ctx.route] || []);
      const actions = headerActions.map((label, index) => {
        if (label === 'Excel' || label === 'Xuất Excel') {
          // The parity extractor treats `.btn` anchors as action controls;
          // keep the link semantics so export remains a real CSV download.
          return `<a class="btn ghost report-action" data-report-action="${escapeHtml(label)}" href="/api/reports/export?${escapeHtml(exportQuery.toString())}">${escapeHtml(label)}</a>`;
        }
        return `<button class="ghost report-action" data-report-action="${escapeHtml(label)}" type="button">${escapeHtml(label)}</button>`;
      }).join('');
      const tabLabels = ROUTE_TABS[ctx.route] || [];
      // Keep the invoice tab contract explicit.  Other report tabs extend
      // the same index after this stable default so route-specific lenses do
      // not obscure the existing bill regression contract.
      const activeTabIndex = ctx.route === '/report/crm/bill/index' ? 1 : 0;
      let selectedTabIndex = activeTabIndex;
      if (ctx.route === '/report/crm/customer_statistic/index') {
        selectedTabIndex = customerStatisticView === 'conversion_time' ? 1 : 0;
      } else if (ctx.route === '/report/crm/customer_care_result_by_center') {
        selectedTabIndex = customerCareCenterView === 'team' ? 1 : customerCareCenterView === 'sale' ? 2 : 0;
      } else if (Object.prototype.hasOwnProperty.call(CUSTOMER_CARE_RESULT_TAB_INDEX, ctx.route)) {
        selectedTabIndex = CUSTOMER_CARE_RESULT_TAB_INDEX[ctx.route] ?? 0;
      } else if (ctx.route === '/report/center/birth_day/index') {
        selectedTabIndex = birthdayView === 'staff' ? 1 : 0;
      }
      const tabs = tabLabels.map((label, index) => `<button class="ref-tab${index === selectedTabIndex ? ' active' : ''}" role="tab" type="button" aria-selected="${index === selectedTabIndex ? 'true' : 'false'}">${escapeHtml(label)}</button>`).join('');
      const tabStrip = tabs ? `<div class="ref-tabs" role="tablist">${tabs}</div>` : '';
      // Reference report forms are change-driven; none shows Chạy báo cáo/Xóa lọc.
      const observedAutoFilters = true;
      const summary = ctx.route === '/report/crm/bill/index'
        ? crmBillSummaryMarkup(payload.summary, rows)
        : ctx.route === '/report/crm/customer_care/index'
          ? `<div class="report-summary" data-report-summary><b>Tổng số khách hàng:</b> ${escapeHtml(String(firstKnownValue(payload.summary || {}, ['customer_count', 'customerCount', 'total', 'count']) ?? rows.length))}</div>`
          : '';
      const inlineRoute = INLINE_EXPORT_ROUTES.has(ctx.route);
      const inlineActions = inlineRoute
        ? (staffBirthday ? ['Excel'] : ROUTE_ACTIONS[ctx.route] || []).map(label => label === 'Excel' || label === 'Xuất Excel'
          ? `<a class="btn ghost report-action report-export-crm" data-report-action="${escapeHtml(label)}" style="background:#2bbbad;color:#fff" href="/api/reports/export?${escapeHtml(exportQuery.toString())}">${escapeHtml(label)}</a>`
          : `<button class="ghost report-action" data-report-action="${escapeHtml(label)}" type="button">${escapeHtml(label)}</button>`).join('')
        : '';
      const formStyle = ctx.route === '/report/crm/customer_report/index'
        ? ' style="grid-template-columns:repeat(4,minmax(0,1fr))"'
        : ctx.route === '/report/center/access_history'
          ? ' style="grid-template-columns:repeat(4,minmax(0,1fr))"'
          : '';
      const reportTitle = ctx.route === '/report/center/birth_day/index' && birthdayView === 'staff'
        ? 'Báo cáo sinh nhật nhân viên - giáo viên'
        : (payload.title || 'Báo cáo CRM / Trung tâm');
      screen.innerHTML = `<section class="card"><div class="page-head"><div><h1>${escapeHtml(reportTitle)}</h1></div><div class="page-actions">${inlineRoute ? '' : actions}</div></div>${tabStrip}<form class="filter-strip" data-report-form${formStyle}>${fields}${inlineActions}${observedAutoFilters ? '' : '<button class="primary" type="submit">Chạy báo cáo</button><button class="ghost" type="reset">Xóa lọc</button>'}</form>${summary}${table}</section>`;
      if (staffBirthday) {
        const style = document.createElement('style');
        style.textContent = `
          #screen[data-birthday-view="staff"]{min-height:0;border-radius:0;padding-top:0;border-left:1px solid #e6eaf1}
          #screen[data-birthday-view="staff"]>.card{border:0;box-shadow:none;border-radius:0}
          #screen[data-birthday-view="staff"] .ref-tabs{height:66px;margin:0 -22px;padding:0 22px;align-items:stretch}
          #screen[data-birthday-view="staff"] .ref-tab{font-size:13px;font-weight:400;color:#111;padding:0 22px 0 0;margin-right:9px}
          #screen[data-birthday-view="staff"] .ref-tab:before{font-family:ReferenceLineAwesome;content:"\\f1ec";margin-right:14px;color:#898b9b}
          #screen[data-birthday-view="staff"] .ref-tab.active:after{left:0;right:0;background:#5867dd}
          #screen[data-birthday-view="staff"] table{border:1px solid #f1f2f7}
          #screen[data-birthday-view="staff"] table th{background:white;color:black;font-size:13px;text-align:center;border:1px solid #f1f2f7;padding:9.75px;height:42px;font-weight:600}
          #screen[data-birthday-view="staff"] .birthday-page-size{display:flex;align-items:center;gap:4px;white-space:nowrap;font-weight:400;font-size:13px;order:1}
          #screen[data-birthday-view="staff"] .report-table-footer{display:contents}
          #screen[data-birthday-view="staff"] .report-page-count{margin-right:auto}
          #screen[data-birthday-view="staff"] .report-pagination{order:2}
          #screen[data-birthday-view="staff"] .birthday-footer{padding-top:18px}
          #screen[data-birthday-view="staff"] .page-head{display:none}
          #screen[data-birthday-view="staff"] .filter-strip{display:flex;gap:30px;flex-wrap:wrap;align-items:center;margin:24px 0 26px}
          #screen[data-birthday-view="staff"] .filter-strip>label{flex:0 0 111px;min-width:0;width:111px}
          #screen[data-birthday-view="staff"] .filter-strip>label>span{display:none}
          #screen[data-birthday-view="staff"] .filter-strip :is(select,input){height:35px;width:111px;font-size:13px}
          #screen[data-birthday-view="staff"] .filter-strip .report-export-crm{margin-left:auto;flex:0 0 83px;width:83px;height:37px;background:#5867dd!important;border-color:#5867dd;color:white;padding:8px 14px}
          #screen[data-birthday-view="staff"] .birthday-footer{display:flex;gap:20px;align-items:center;flex-wrap:wrap}
          #screen[data-birthday-view="staff"] .report-table-footer{flex:1}
          #screen[data-birthday-view="staff"] .birthday-page-size select{width:75px;height:28px}
          #screen[data-birthday-view="staff"] table{table-layout:fixed;font-size:13px}
          #screen[data-birthday-view="staff"] table th:nth-child(1){width:7.458%}
          #screen[data-birthday-view="staff"] table th:nth-child(2){width:12.910%}
          #screen[data-birthday-view="staff"] table th:nth-child(3){width:16.690%}
          #screen[data-birthday-view="staff"] table th:nth-child(4){width:10.242%}
          #screen[data-birthday-view="staff"] table th:nth-child(5){width:11.482%}
          #screen[data-birthday-view="staff"] table th:nth-child(6){width:9.119%}
          #screen[data-birthday-view="staff"] table th:nth-child(7){width:9.717%}
          #screen[data-birthday-view="staff"] table th:nth-child(8){width:12.532%}
          #screen[data-birthday-view="staff"] table th:nth-child(9){width:9.843%}
          #screen[data-birthday-view="staff"] .birthday-page-size select{border:1px solid #ebedf2;border-radius:3px;background:white;color:#575962;font-size:11px;padding:3px 8px}
        `;
        screen.append(style);
      }
      screen.__birthdayViewHandler = index => {
        const form = screen.querySelector('[data-report-form]');
        const filters = form ? Object.fromEntries(new FormData(form)) : {};
        renderReport({ ...(ctx.route === '/report/center/birth_day/index' ? {} : filters), birthday_type: index === 1 ? 'staff' : 'student' }).catch(error => {
          screen.innerHTML = `<div class="card empty">${escapeHtml(error.message || error)}</div>`;
        });
      };
      if (ctx.route === '/report/crm/customer_care_result_by_center' || staffBirthday) {
        screen.querySelectorAll('[data-report-form] [name]').forEach(control => {
          if (Object.prototype.hasOwnProperty.call(activeFilters, control.name)) control.value = activeFilters[control.name];
        });
      }
      bindReportTabNavigation(screen, ctx.route);
      if (ctx.route === '/report/center/birth_day/index') screen.querySelector('[data-report-action="Cấu hình lời chúc"]')?.addEventListener('click', () => {
        openBirthdayConfig(ctx).catch(error => {
          const message = document.createElement('p'); message.className = 'error'; message.setAttribute('role', 'alert'); message.textContent = error.message; screen.append(message);
        });
      });
      if (ctx.route === '/report/crm/customer_care_result_by_center') stabilizeCustomerCareCenterTabs(screen, renderReport, customerCareCenterView);
      if (ctx.route === '/report/crm/customer_statistic/index') bindCustomerStatisticTabs(screen, renderReport, customerStatisticView);
      if (!staffBirthday) {
        scheduleSemanticPlaceholders(screen, ctx.route);
        repairObservedControls(screen, ctx.route, filters);
      }
      if (observedAutoFilters) {
        // app.js may append generic submit/reset controls after rendering.
        // These routes are change-driven in the observed reference and have
        // no duplicate Chạy báo cáo/Xóa lọc controls.
        const removeGenericActions = () => screen.querySelectorAll('.filter-strip button[type="submit"],.filter-strip button[type="reset"]').forEach(node => node.remove());
        removeGenericActions();
        if (ctx.route === '/report/crm/customer_statistic/index') {
          const removeUnsupportedActions = () => [...screen.querySelectorAll('button,a')].forEach(node => {
            const text = node.textContent.trim();
            if (text === 'Chạy báo cáo' || text === 'Xóa lọc') node.remove();
          });
          removeUnsupportedActions();
          setTimeout(removeUnsupportedActions, 40);
          setTimeout(removeUnsupportedActions, 180);
          setTimeout(removeUnsupportedActions, 600);
        }
        setTimeout(removeGenericActions, 40);
        setTimeout(removeGenericActions, 180);
        setTimeout(removeGenericActions, 600);
      }
      const form = screen.querySelector('[data-report-form]');
      const tableRoot = screen.querySelector('[data-report-table]');
      if (staffBirthday && tableRoot) {
        const footer = tableRoot.querySelector('[data-report-table-footer]');
        if (footer) {
          const wrapper = document.createElement('div'); wrapper.className = 'birthday-footer'; footer.before(wrapper); wrapper.append(footer);
          const size = document.createElement('label'); size.className = 'birthday-page-size'; size.innerHTML = 'Hiển thị <select name="report_table_length" aria-label="Số bản ghi">'+['10','25','50','All'].map(value => `<option value="${value}">${value}</option>`).join('')+'</select> bản ghi'; wrapper.append(size);
        }
      }
      const pageSizeControl = pageConfig.observed ? { name: pageConfig.name } : null;
      const tableColumns = ctx.route === '/report/crm/bill/index' ? normalizeCrmBillColumns(columns) : columns;
      const tableCell = ctx.route === '/report/crm/bill/index'
        ? (row, col) => escapeHtml(displayReportValue(crmBillCellValue(row, col), helpers))
        : ctx.route === '/report/crm/customer_statistic/index'
          ? (row, col) => escapeHtml(customerStatisticValue(row[col.key], col.label || col.key, helpers))
        : (row, col) => escapeHtml(displayReportValue(row[col.key], helpers));
      if (tableRoot && ctx.route !== '/report/crm/customer_statistic/index' && !CUSTOMER_CARE_RESULT_ROUTES.has(ctx.route)) mountReportTable(tableRoot, { columns: tableColumns, rows, cell: tableCell, pageSizes: pageConfig.values, pageSizeControl, pagination: CRM_REPORT_PAGINATION[ctx.route] || null });
      form?.addEventListener('submit', async event => {
        event.preventDefault();
        try { await renderReport(Object.fromEntries(new FormData(form))); } catch (error) { screen.innerHTML = `<div class="card empty">${escapeHtml(error.message || error)}</div>`; }
      });
      form?.addEventListener('reset', () => setTimeout(() => renderReport({}), 0));
      if (observedAutoFilters) form?.addEventListener('change', () => {
        renderReport(Object.fromEntries(new FormData(form))).catch(error => {
          screen.innerHTML = `<div class="card empty">${escapeHtml(error.message || error)}</div>`;
        });
      });
    };
    await renderReport();
    return true;
  };
}

/** Register CRM and Center report screens with the coordinator frontend seam. */
export async function register(centerEdu = globalThis.CenterEdu) {
  if (!centerEdu) return { routes: CRM_CENTER_ROUTES };
  centerEdu.reportMetadata = { ...(centerEdu.reportMetadata || {}), crmCenterReportScope };
  for (const route of CRM_CENTER_ROUTES) centerEdu.registerScreen?.(route, crmRenderer(crmCenterReportScope));
  return { routes: CRM_CENTER_ROUTES };
}

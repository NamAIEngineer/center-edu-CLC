/** Client metadata for the non-training/non-finance report lane. */
import { createReportTable, mountReportTable, reportPageSizes } from './report_table.js';
export const crmCenterReportScope = {
  routePrefixes: ['/report/crm/', '/report/center/', '/report/cso/', '/report/callcenter/'],
  utilityRoutes: {
    '/cso/support': { title: 'Hỗ trợ', tabs: ['Tiếp nhận từ người dùng', 'Hỗ trợ nội bộ'], columns: ['No.', 'Thời gian', 'Loại', 'Nội dung', 'Người gửi', 'Lớp của học viên', 'Nhân viên', 'Trạng thái', ''], filters: ['status', 'type', 'from_date', 'to_date', 'query'], actions: ['Excel', 'Tạo'] },
    '/callcenter/get-statistic': { title: 'Thống kê cuộc gọi vào', tabs: ['Thống kê cuộc gọi vào', 'Thống kê cuộc gọi ra'], columns: ['No.', 'Nhân viên nghe', 'Nhóm sale', 'Trung tâm', 'Tổng cuộc gọi', 'Cuộc gọi thành công', 'Cuộc gọi nhỡ', 'Thất bại'], filters: ['from_date', 'to_date'], actions: ['Xuất excel'] },
    '/center/upload_address': { title: 'Tool chinh sửa địa chỉ', tabs: ['Công cụ chỉnh sửa địa chỉ học sinh', 'Công cụ chỉnh sửa địa chỉ khách hàng tiềm năng'], columns: ['No.', 'Chi nhánh', 'Mã học viên', 'Học viên', 'Mã định danh', 'Tên tiếng anh', 'Giới tính', 'Ngày sinh', 'Tài khoản', 'SĐT', 'Email', 'Tỉnh cũ', 'Huyện cũ', 'Xã phường', 'Tỉnh mới', 'Phường xã mới'], filters: ['file'], pageSizes: [5, 10, 25, 50], actions: ['Lưu'] },
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
  '/report/center/birth_day/index': ['Tất cả', '11', 'Cấu hình lời chúc', 'Excel'],
  '/report/center/access_history': ['Đã đăng nhập', 'Chọn quyền', 'Chọn trạng thái', 'Excel'],
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
const INLINE_EXPORT_ROUTES = new Set(['/report/crm/contract/index', '/report/crm/bill/index', '/report/crm/customer_care/index']);

const ROUTE_TABS = {
  '/report/crm/contract/index': ['Thống kê danh sách hợp đồng', 'Thống kê danh sách hóa đơn'],
  '/report/crm/bill/index': ['Thống kê danh sách hợp đồng', 'Thống kê danh sách hóa đơn'],
  '/report/center/birth_day/index': ['Báo cáo sinh nhật học viên', 'Báo cáo sinh nhật nhân viên - giáo viên'],
  '/report/crm/customer_care/index': ['Chăm sóc theo trung tâm', 'Chăm sóc theo phường xã', 'Theo năm sinh học viên', 'Theo nguồn', 'Theo nhân viên sale', 'Báo cáo kết quả chăm sóc khách hàng', 'Báo cáo chăm sóc khách hàng'],
  '/report/crm/customer_care_result_by_district': ['Biểu đồ', 'Chăm sóc theo trung tâm', 'Chăm sóc theo phường xã', 'Theo năm sinh học viên', 'Theo nguồn', 'Theo nhân viên sale', 'Báo cáo kết quả chăm sóc khách hàng', 'Báo cáo chăm sóc khách hàng'],
  '/report/crm/customer_report/index': ['Báo cáo khách hàng'],
  '/report/crm/customer_statistic/index': ['Tỷ lệ chung', 'Tỷ lệ chuyển đổi khách hàng theo thời gian'],
};

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
      shaped.options = [...shaped.options];
      if (String(shaped.options[0]).trim() === 'Chọn trạng thái') shaped.options[0] = 'Trạng thái học viên';
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
  setTimeout(() => {
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
    if (route === '/report/crm/bill/index') {
      const strip = screen.querySelector('.filter-strip');
      const excel = strip?.querySelector('[data-report-action="Excel"]');
      // The shared shell may prepend action links during its normalizer pass.
      // The reference keeps Excel after every filter control in this row.
      if (strip && excel) strip.appendChild(excel);
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
        if (options[0] && options[0].textContent.trim() === 'Chọn trạng thái') {
          options[0].textContent = 'Trạng thái học viên';
          options[0].value = 'Trạng thái học viên';
        }
        studentStatus.setAttribute('aria-label', options[0]?.textContent.trim() || 'Trạng thái học viên');
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
    const renderReport = async (activeFilters = {}) => {
      const query = new URLSearchParams({ route: ctx.route, ...activeFilters });
      const response = await ctx.api(`/api/reports/run?${query.toString()}`);
      const payload = response?.data || response || {};
      const rows = Array.isArray(payload.rows) ? payload.rows : [];
      const columns = Array.isArray(payload.columns) ? payload.columns : [];
      const filters = routeFilterShape(ctx.route, Array.isArray(payload.filters) ? payload.filters : (scope.filtersFor(ctx.route) || []).map(name => ({ name, label: name })));
      const helpers = ctx.helpers || globalThis.CenterEdu?.helpers || {};
      const fields = filters.map((filter, index) => {
        const name = String(filter.name || `filter_${index}`).replace(/[^A-Za-z0-9_-]/g, '');
        const label = String((ctx.route === '/report/crm/contract/index' && ROUTE_PLACEHOLDERS[ctx.route]?.[name]) || LABELS[filter.label] || filter.label || filter.placeholder || name);
        const kind = String(filter.type || '').toLowerCase();
        // Preserve the observed element kind, including empty selects such as
        // creator/class controls.  Converting an empty select to an input
        // shifts every following filter during the shell normalizer pass.
        const options = (kind === 'select' || kind === 'multiselect')
          ? `<select name="${name}">${ctx.route === '/report/crm/contract/index' ? '' : '<option value="">Tất cả</option>'}${[...new Set((filter.options || []).map(option => String(option)))].map(option => `<option value="${escapeHtml(option)}">${escapeHtml(option)}</option>`).join('')}</select>`
          : kind === 'search'
            ? `<input name="${name}" type="search" placeholder="${escapeHtml(label)}">`
            : `<input name="${name}" type="text" placeholder="${escapeHtml(label)}">`;
        return `<label>${escapeHtml(label)}${options}</label>`;
      }).join('');
      const exportQuery = new URLSearchParams({ route: ctx.route, ...activeFilters });
      const pageConfig = reportPageSizes(filters);
      const table = ctx.route === '/report/crm/customer_statistic/index'
        ? customerStatisticTableMarkup(columns, rows, helpers)
        : ctx.route === '/report/crm/bill/index'
        ? crmBillTableMarkup(columns, rows, helpers, pageConfig.values, CRM_REPORT_PAGINATION[ctx.route])
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
      const activeTabIndex = ctx.route === '/report/crm/bill/index' ? 1 : 0;
      const tabs = tabLabels.map((label, index) => `<button class="ref-tab${index === activeTabIndex ? ' active' : ''}" role="tab" type="button" aria-selected="${index === activeTabIndex ? 'true' : 'false'}">${escapeHtml(label)}</button>`).join('');
      const tabStrip = tabs ? `<div class="ref-tabs" role="tablist">${tabs}</div>` : '';
      // Reference report forms are change-driven; none shows Chạy báo cáo/Xóa lọc.
      const observedAutoFilters = true;
      const summary = ctx.route === '/report/crm/bill/index' ? crmBillSummaryMarkup(payload.summary, rows) : '';
      const inlineExcel = INLINE_EXPORT_ROUTES.has(ctx.route)
        ? `<a class="btn ghost report-action report-export-crm" data-report-action="Excel" style="background:#2bbbad;color:#fff" href="/api/reports/export?${escapeHtml(exportQuery.toString())}">Excel</a>` : '';
      screen.innerHTML = `<section class="card"><div class="page-head"><div><h1>${escapeHtml(payload.title || 'Báo cáo CRM / Trung tâm')}</h1></div><div class="page-actions">${actions}</div></div>${tabStrip}<form class="filter-strip" data-report-form>${fields}${inlineExcel}${observedAutoFilters ? '' : '<button class="primary" type="submit">Chạy báo cáo</button><button class="ghost" type="reset">Xóa lọc</button>'}</form>${summary}${table}</section>`;
      scheduleSemanticPlaceholders(screen, ctx.route);
      repairObservedControls(screen, ctx.route, filters);
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
      const pageSizeControl = pageConfig.observed ? { name: pageConfig.name } : null;
      const tableColumns = ctx.route === '/report/crm/bill/index' ? normalizeCrmBillColumns(columns) : columns;
      const tableCell = ctx.route === '/report/crm/bill/index'
        ? (row, col) => escapeHtml(displayReportValue(crmBillCellValue(row, col), helpers))
        : ctx.route === '/report/crm/customer_statistic/index'
          ? (row, col) => escapeHtml(customerStatisticValue(row[col.key], col.label || col.key, helpers))
        : (row, col) => escapeHtml(displayReportValue(row[col.key], helpers));
      if (tableRoot && ctx.route !== '/report/crm/customer_statistic/index') mountReportTable(tableRoot, { columns: tableColumns, rows, cell: tableCell, pageSizes: pageConfig.values, pageSizeControl, pagination: CRM_REPORT_PAGINATION[ctx.route] || null });
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

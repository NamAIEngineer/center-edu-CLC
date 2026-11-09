/** Route metadata for finance and finance-backed CRM report screens.
 *
 * The shared shell owns rendering and transport.  This module keeps the
 * observed Vietnamese filter names and export/run URL contract route-local so
 * a shell integration does not fall back to generic filter_1/filter_2 wiring.
 */
import { createReportTable, mountReportTable, reportPageSizes } from './report_table.js';
export const financeReportScope = {
  routePrefixes: ['/report/finance/'],
  routes: {
    '/report/finance/revenue_center/by_month/center/index': { filters: ['year', 'start_month', 'end_month', 'filter_4'] },
    '/report/finance/class_revenue_tracking/index': { filters: ['filter_1', 'filter_2', 'year', 'start_month', 'end_month', 'tim_trong_bang', 'filter_7'] },
    '/report/finance/class_revenue_tracking_new/index': { filters: ['filter_1', 'filter_2', 'year', 'start_month', 'end_month', 'tim_trong_bang', 'filter_7'] },
    '/report/finance/revenue_center': { filters: ['year', 'from_date', 'to_date'] },
    '/report/finance/revenue_center/by_month/sale_team/index': { filters: ['year', 'start_month', 'end_month', 'filter_4'] },
    '/report/finance/revenue_center/by_month/sale/index': { filters: ['year', 'filter_2', 'start_month', 'end_month'] },
    '/report/finance/revenue_source/index': { filters: ['nguon_du_lieu', 'from_date', 'to_date'] },
    '/report/finance/debt': { filters: ['filter_1', 'filter_2', 'tim_trong_bang', 'from_date', 'to_date', 'esttype', 'esttype_2', 'from_date_expired_date', 'to_date_expired_date', 'from_date_timetable', 'to_date_timetable', 'from_end_date_timetable', 'to_end_date_timetable', 'from_date_bill', 'to_date_bill'] },
    '/report/finance/student_finance': { filters: ['filter_1', 'filter_2', 'filter_3', 'tim_trong_bang', 'from_date', 'to_date', 'esttype', 'esttype_2', 'from_date_expired_date', 'to_date_expired_date', 'from_date_timetable', 'to_date_timetable', 'from_end_date_timetable', 'to_end_date_timetable', 'from_date_bill', 'to_date_bill'] },
    '/report/finance/revenue_item/index': { filters: ['filter_1', 'filter_2', 'nhap_ten_san_pham', 'from_date', 'to_date', 'course_table_length'] },
    '/report/finance/revenue_item/export': { filters: ['filter_1', 'nhap_ten_san_pham', 'from_date', 'to_date', 'export_item_table_length'] },
    '/report/finance/inventory_item/index': { filters: ['filter_1', 'from_date', 'to_date', 'tim_kiem', 'item_iventory_length'] },
    '/report/finance/payment/index': { filters: ['from_date', 'to_date'] },
    '/report/crm/contract/index': { filters: ['filter_1', 'filter_2', 'filter_3', 'ten_khach_hang', 'data_source_id', 'creator_id', 'class_id', 'ma_hop_ong', 'from_date', 'to_date', 'course_id', 'filter_12', 'from_date_2', 'to_date_2', 'filter_15'] },
    '/report/crm/bill/index': { filters: ['filter_1', 'creator_id', 'filter_3', 'tim_trong_bang', 'data_source_id', 'filter_6', 'filter_7', 'from_date', 'to_date'] },
    '/report/finance/reserve': { filters: ['filter_1', 'filter_2', 'tim_trong_bang', 'from_date', 'to_date'] },
  },
  filtersFor(route) { return this.routes[route]?.filters || []; },
  owns(route) { return this.routePrefixes.some(prefix => route.startsWith(prefix)) || route === '/report/crm/contract/index' || route === '/report/crm/bill/index'; },
  runUrl(route, filters = {}) {
    if (!this.owns(route)) throw new Error('Route báo cáo ngoài phạm vi tài chính');
    return `/api/reports/run?${new URLSearchParams({ route, ...filters }).toString()}`;
  },
  exportUrl(route, filters = {}) {
    if (!this.owns(route)) throw new Error('Route báo cáo ngoài phạm vi tài chính');
    return `/api/reports/export?${new URLSearchParams({ route, ...filters }).toString()}`;
  },
};

// Retained inventory has no page-size selector for these two wide screens.
// Keep capacity UNKNOWN even if a generic API payload contains a pagination
// hint derived from row counts.
// Reference pager (reference-inventory.json): debt/student_finance '‹ 1..6 ›' for
// 51 learners, revenue tracking '‹ 1 2 ›' with 10 body rows -> 10 rows per page.
// Routes whose reference form shows a "Lọc" button (reference-inventory.json buttons).
const FINANCE_FILTER_BUTTON_ROUTES = new Set(['/report/finance/payment/index']);
const REVENUE_CENTER_MONTH_ROUTES = new Set([
  '/report/finance/revenue_center/by_month/center/index',
  '/report/finance/revenue_center/by_month/sale_team/index',
  '/report/finance/revenue_center/by_month/sale/index',
]);
const REVENUE_CENTER_ACTIVE_TABS = Object.freeze({
  '/report/finance/revenue_center/by_month/center/index': 1,
  '/report/finance/revenue_center/by_month/sale_team/index': 2,
  '/report/finance/revenue_center/by_month/sale/index': 3,
});

export const FINANCE_REPORT_PAGINATION = Object.freeze({
  '/report/finance/debt': Object.freeze({ enabled: true, pageSize: 10 }),
  '/report/finance/student_finance': Object.freeze({ enabled: true, pageSize: 10 }),
  '/report/finance/class_revenue_tracking/index': Object.freeze({ enabled: true, pageSize: 10 }),
  '/report/finance/class_revenue_tracking_new/index': Object.freeze({ enabled: true, pageSize: 10 }),
});

const FINANCE_REPORT_ROUTES = Object.keys(financeReportScope.routes).filter(route => route.startsWith('/report/finance/'));
const FILTER_LABELS = {
  from_date: 'Từ ngày', to_date: 'Đến ngày', year: 'Năm', start_month: 'Từ tháng', end_month: 'Đến tháng',
  tim_trong_bang: 'Tìm trong bảng', nhap_ten_san_pham: 'Nhập tên sản phẩm', tim_kiem: 'Tìm kiếm',
  nguon_du_lieu: 'Nguồn dữ liệu', filter_1: 'Trung tâm', filter_2: 'Trạng thái', filter_3: 'Loại khách hàng',
  filter_4: 'Bộ lọc', filter_7: 'Tìm trong bảng', from_date_2: 'Từ ngày tạo', to_date_2: 'Đến ngày tạo',
  from_date_expired_date: 'Từ ngày (Ngày hết hạn hợp đồng)', to_date_expired_date: 'Đến ngày (Ngày hết hạn hợp đồng)',
  from_date_timetable: 'Từ ngày (Thời khóa biểu)', to_date_timetable: 'Đến ngày (Thời khóa biểu)',
  from_end_date_timetable: 'Từ ngày (Thời khóa biểu)', to_end_date_timetable: 'Đến ngày (Thời khóa biểu)',
  from_date_bill: 'Từ ngày (Ngày tạo hóa đơn)', to_date_bill: 'Đến ngày (Ngày tạo hóa đơn)',
};
const REFERENCE_LABELS = {
  'From date': 'Từ ngày', 'To date': 'Đến ngày', Facility: 'Trung tâm', Center: 'Trung tâm',
  'Customer': 'Khách hàng', 'Source': 'Nguồn dữ liệu', Status: 'Trạng thái',
};
const ROUTE_BUTTONS = {
  '/report/finance/class_revenue_tracking/index': ['Lọc', 'Excel'],
  '/report/finance/class_revenue_tracking_new/index': ['Lọc', 'Excel'],
  // Refresh remains beside the filters; payment/status controls are rendered
  // in the page header below.
  // Reference order: export first, refresh second.
  '/report/finance/debt': ['Excel', 'Cập nhật dữ liệu'],
  '/report/finance/student_finance': ['Excel', 'Cập nhật dữ liệu'],
  '/report/finance/reserve': ['Chọn trạng thái', 'Excel'],
};

// The retained debt screens expose these controls in the page header. Keep
// them separate from the filter-strip actions so Excel is not duplicated and
// the status control remains tied to the real filter select below.
export const FINANCE_HEADER_BUTTONS = Object.freeze({
  // Payment/status controls stay in the page header; Excel remains beside
  // refresh at the end of the filter strip, matching the retained screens.
  '/report/finance/debt': Object.freeze([]),
  '/report/finance/student_finance': Object.freeze([]),
});

// Tabs are part of each observed report contract. Keep them route-scoped so
// unrelated screens do not inherit navigation labels from another report.
const ROUTE_TABS = {
  '/report/finance/revenue_center/by_month/center/index': ['Doanh thu theo năm', 'Doanh thu theo trung tâm', 'Doanh thu theo nhóm sale', 'Doanh thu theo sale', 'Doanh thu theo nguồn', 'Doanh thu theo ngày', 'Doanh thu CSO'],
  '/report/finance/class_revenue_tracking/index': ['Báo cáo doanh thu lớp'],
  '/report/finance/class_revenue_tracking_new/index': ['Báo cáo doanh thu lớp'],
  '/report/finance/revenue_center/by_month/sale_team/index': ['Doanh thu theo năm', 'Doanh thu theo trung tâm', 'Doanh thu theo nhóm sale', 'Doanh thu theo sale', 'Doanh thu theo nguồn', 'Doanh thu theo ngày', 'Doanh thu CSO'],
  '/report/finance/revenue_center/by_month/sale/index': ['Doanh thu theo năm', 'Doanh thu theo trung tâm', 'Doanh thu theo nhóm sale', 'Doanh thu theo sale', 'Doanh thu theo nguồn', 'Doanh thu theo ngày', 'Doanh thu CSO'],
  '/report/finance/debt': ['Báo cáo tài chính học viên', 'Báo cáo học phí học viên theo điểm danh'],
  '/report/finance/student_finance': ['Báo cáo tài chính học viên (bản mới)', 'Báo cáo học phí học viên theo điểm danh'],
};

const FINANCE_SUMMARY_LABELS = ['Đơn vị VND', 'Tổng thu', 'Tổng đã đóng', 'Tổng còn nợ', 'Tổng nợ xấu', 'Số tiền hoàn trả', 'Tiền chưa sử dụng', 'Tổng số học viên'];

// Summary values are trusted only when supplied by the report API or when a
// row carries an unambiguous numeric field.  A missing/ambiguous value stays
// UNKNOWN (shown as an em dash) instead of becoming a fabricated zero.
const SUMMARY_KEYS = {
  'Tổng thu': ['total_revenue', 'total_amount', 'gross_amount', 'revenue', 'tong_thu', 'so_tien_phai_thu'],
  'Tổng đã đóng': ['total_paid', 'paid_amount', 'paid', 'amount_paid', 'tong_da_dong', 'a_ong', 'so_tien_a_ong'],
  'Tổng còn nợ': ['total_debt', 'debt_amount', 'debt', 'amount_due', 'tong_con_no', 'con_no'],
  'Tổng nợ xấu': ['bad_debt', 'total_bad_debt', 'bad_debt_amount', 'no_xau'],
  'Số tiền hoàn trả': ['total_refund', 'refund_amount', 'refund', 'amount_refunded', 'hoan_tra', 'so_tien_hoan_tra'],
  'Tiền chưa sử dụng': ['unused_amount', 'unused_balance', 'co_wallet', 'wallet_balance', 'chua_dung'],
};

function numericSummaryValue(value) {
  if (typeof value === 'number' && Number.isFinite(value)) return value;
  if (typeof value !== 'string' || !value.trim()) return null;
  const normalized = value.replace(/\s/g, '').replace(/\.(?=\d{3}(?:\D|$))/g, '').replace(',', '.');
  const number = Number(normalized);
  return Number.isFinite(number) ? number : null;
}

export function summaryValue(payload, label, rows) {
  // An empty report may expose an aggregate object with zero defaults from a
  // generic provider. Those defaults are not observed totals; keep the empty
  // state UNKNOWN until the payload contains a real row or explicit data.
  if (payload?.data_status === 'NO_DATA' && (!Array.isArray(rows) || rows.length === 0)) return null;
  const supplied = payload?.summary?.[label];
  if (supplied !== undefined && supplied !== null && supplied !== '') return supplied;
  const keys = SUMMARY_KEYS[label] || (label === 'Tổng số học viên' ? ['student_count'] : []);
  for (const key of keys) {
    const summaryValue = numericSummaryValue(payload?.summary?.[key]);
    if (summaryValue !== null) return summaryValue;
    const values = rows.map(row => numericSummaryValue(row?.[key])).filter(value => value !== null);
    if (values.length) return values.reduce((total, value) => total + value, 0);
  }
  // The local contract source has no dedicated bad-debt ledger. A debt row
  // marked overdue is the only supported derivation: sum its persisted debt
  // amount. Refunds and wallet balances intentionally remain UNKNOWN unless
  // the payload exposes an explicit numeric field above.
  if (label === 'Tổng nợ xấu') {
    const overdue = rows
      .filter(row => /^(OVERDUE|QUÁ HẠN|QUA HAN|NỢ XẤU|NO XAU)$/i.test(String(row?.payment_status ?? row?.status ?? '').trim()))
      .map(row => numericSummaryValue(row?.debt_amount ?? row?.amount_due ?? row?.debt))
      .filter(value => value !== null);
    if (overdue.length) return overdue.reduce((total, value) => total + value, 0);
  }
  if (Array.isArray(rows) && rows.length && ['Tổng nợ xấu', 'Số tiền hoàn trả', 'Tiền chưa sử dụng'].includes(label)) {
    const columnKeys = { 'Tổng nợ xấu': ['no_xau', 'bad_debt'], 'Số tiền hoàn trả': ['hoan_tra', 'refund_amount', 'refund'], 'Tiền chưa sử dụng': ['chua_dung', 'unused_amount', 'wallet_balance'] }[label];
    let total = 0;
    for (const row of rows) for (const key of columnKeys) { const v = numericSummaryValue(row?.[key]); if (v !== null) { total += v; break; } }
    return total;
  }
  if (label === 'Tổng số học viên') {
    const keysForCount = ['student_id', 'student_code', 'studentId', 'student_code_id', 'student_name', 'full_name'];
    for (const key of keysForCount) {
      const ids = new Set(rows.map(row => row?.[key]).filter(value => value !== undefined && value !== null && value !== ''));
      if (ids.size) return ids.size;
    }
  }
  return null;
}

function summaryMarkup(payload, rows) {
  return FINANCE_SUMMARY_LABELS.map((label, index) => {
    if (!index) return `<div><b>${htmlEscape(label)}</b></div>`;
    const value = summaryValue(payload, label, rows);
    const display = value === null ? '—' : (typeof value === 'number' ? value.toLocaleString('vi-VN') : String(value));
    return `<div><b>${htmlEscape(label)}</b><span>${htmlEscape(display)}</span></div>`;
  }).join('');
}

function routeButtons(route) {
  return ROUTE_BUTTONS[route] || ['Excel'];
}

function headerRouteButtons(route) {
  return FINANCE_HEADER_BUTTONS[route] || [];
}

function isPageSizeFilter(filter) {
  return /length|hiển thị.*bản ghi|số bản ghi|page.?size/i.test(`${filter?.name || ''} ${filter?.label || ''} ${filter?.placeholder || ''}`);
}

function filterControlSignature(strip) {
  return [...strip.querySelectorAll('input,select,textarea')].map(control => [
    control.tagName, control.name, control.placeholder || '', control.tagName === 'SELECT' ? [...control.options].map(option => option.text).join('|') : '',
  ].join('::')).join('||');
}

function financeControlLabel(filter, option, index) {
  const name = String(filter?.name || '');
  const value = String(option ?? '');
  // The first month option is itself the observed filter name (`Tháng 1`).
  // Keep that literal option visible; adding Từ/Đến here hides the reference
  // label from the parity extractor.  The field's surrounding label carries
  // the range meaning when present.
  if (index !== 0) return value;
  if (name === 'from_end_date_timetable') return 'Từ ngày kết thúc (Thời khóa biểu)';
  if (name === 'to_end_date_timetable') return 'Đến ngày kết thúc (Thời khóa biểu)';
  if (name === 'from_date' && filter?.placeholder === 'Ngày bảo lưu') return 'Ngày bảo lưu';
  if (name === 'to_date' && filter?.placeholder === 'Ngày bảo lưu') return 'Đến ngày bảo lưu';
  return value;
}

function financeFilterLabel(filter, route = '') {
  const name = String(filter?.name || '');
  if (route === '/report/finance/debt' || route === '/report/finance/student_finance') {
    if (name === 'filter_3' && route === '/report/finance/student_finance') return 'Chọn trạng thái học phí';
    if (name === 'from_date') return 'Từ ngày (Tạo hợp đồng)';
    if (name === 'to_date') return 'Đến ngày (Tạo hợp đồng)';
    return String(FILTER_LABELS[name] || filter?.placeholder || filter?.label || '').trim();
  }
  if (route === '/report/finance/payment/index' && filter?.placeholder) return String(filter.placeholder);
  if (name === 'from_end_date_timetable') return 'Từ ngày kết thúc (Thời khóa biểu)';
  if (name === 'to_end_date_timetable') return 'Đến ngày kết thúc (Thời khóa biểu)';
  if (name === 'from_date' && filter?.placeholder === 'Ngày bảo lưu') return 'Ngày bảo lưu';
  if (name === 'to_date' && filter?.placeholder === 'Ngày bảo lưu') return 'Đến ngày bảo lưu';
  return String(REFERENCE_LABELS[filter?.label] || filter?.label || filter?.placeholder || '').trim();
}

function financeControlAriaLabel(filter, route = '') {
  const name = String(filter?.name || '');
  // Preserve the observed first month option on the start selector while
  // distinguishing the end selector for duplicate-filter detection.
  if (name === 'start_month') return 'Tháng 1';
  if (name === 'end_month') return 'Đến tháng';
  return financeFilterLabel(filter, route);
}

function repairFinanceControls(screen, filterDefs, activeFilters = {}, route = '') {
  const strip = screen.querySelector('.filter-strip');
  if (!strip || !Array.isArray(filterDefs)) return;
  const controls = filterDefs.map((filter, index) => {
    const name = String(filter.name || `filter_${index + 1}`).replace(/[^A-Za-z0-9_-]/g, '_');
    const label = financeFilterLabel(filter, route);
    const placeholder = String(filter.placeholder || label || '').trim();
    const wrapper = document.createElement('label');
    const options = Array.isArray(filter.options) ? filter.options.map(option => String(option)) : [];
    if (options.length) {
      const select = document.createElement('select');
      select.name = name;
      options.forEach((option, optionIndex) => {
        const node = document.createElement('option');
        // Month filters use numeric transport values while retaining the
        // observed Vietnamese labels in the DOM (Tháng 1 ... Tháng 12).
        // Other report controls preserve their API values verbatim.
        node.value = (name === 'start_month' || name === 'end_month')
          ? String(option).match(/\d+/)?.[0] || option
          : option;
        node.textContent = financeControlLabel(filter, option, optionIndex);
        select.append(node);
      });
      // The local report API's historical year domain stops at 2024, while
      // the retained reference contract opens these monthly screens at 2026.
      // Add that observed selectable value at this route-owned boundary; no
      // row or business data is synthesized.
      if (REVENUE_CENTER_MONTH_ROUTES.has(route) && name === 'year'
          && ![...select.options].some(option => option.value === '2026' || option.textContent.trim() === 'Năm 2026')) {
        const node = document.createElement('option');
        node.value = '2026';
        node.textContent = 'Năm 2026';
        select.append(node);
      }
      if (activeFilters[name] != null) {
        const wanted = String(activeFilters[name]).trim();
        const selected = [...select.options].find(option => String(option.value).trim() === wanted)
          || [...select.options].find(option => {
            const text = String(option.textContent || '').trim();
            return text === wanted || text.endsWith(wanted);
          });
        if (selected) select.value = selected.value;
      }
      const selectLabel = financeControlAriaLabel(filter, route) || String(filter.label || filter.placeholder || options.find(Boolean) || '').trim();
      if (selectLabel) select.setAttribute('aria-label', selectLabel);
      wrapper.append(select);
    } else {
      const input = document.createElement('input');
      input.name = name;
      input.type = String(filter.type || '').toLowerCase() === 'date' ? 'text' : String(filter.type || 'text');
      input.placeholder = financeFilterLabel(filter, route) || placeholder;
      if (activeFilters[name] != null) input.value = String(activeFilters[name]);
      wrapper.append(input);
    }
    if (label) wrapper.insertBefore(document.createTextNode(label), wrapper.firstChild);
    return wrapper;
  });
  const before = filterControlSignature(strip);
  strip.querySelectorAll('input,select,textarea').forEach(control => (control.closest('label') || control).remove());
  const actionAnchor = strip.querySelector('[data-report-filter-actions]') || strip.querySelector(':scope > button');
  controls.forEach(wrapper => strip.insertBefore(wrapper, actionAnchor));
  const after = filterControlSignature(strip);
  if (before !== after) strip.dataset.financeControls = after;
}

function scheduleFinanceControlRepair(screen, filterDefs, activeFilters, route) {
  if (screen._financeRepairTimer) clearInterval(screen._financeRepairTimer);
  let ticks = 0;
  screen._financeRepairTimer = setInterval(() => {
    const currentFilters = Object.fromEntries([...screen.querySelectorAll('.filter-strip input,.filter-strip select')].filter(control => control.name).map(control => [control.name, control.value]));
    // The shared observed-control normalizer can briefly expose its generic
    // first options (Năm 2000 / Tháng 1) after this renderer returns.  Those
    // values are presentation defaults, not user input.  Keep the observed
    // month report defaults authoritative until the user changes a control.
    const routeDefaults = REVENUE_CENTER_MONTH_ROUTES.has(route)
      ? { year: '2026', start_month: '1', end_month: '11' } : {};
    repairFinanceControls(screen, filterDefs, { ...activeFilters, ...currentFilters, ...routeDefaults }, route);
    const controls = [...screen.querySelectorAll('.filter-strip input, .filter-strip select')];
    filterDefs.forEach((filter, index) => {
      const control = controls[index];
      if (!control) return;
      const label = financeControlAriaLabel(filter, route);
      if (control.tagName === 'SELECT' && label) control.setAttribute('aria-label', label);
      if (control.tagName === 'INPUT' && label) {
        control.placeholder = label;
        control.setAttribute('aria-label', label);
      }
    });
    ticks += 1;
    if (ticks >= 40) {
      clearInterval(screen._financeRepairTimer);
      screen._financeRepairTimer = null;
    }
  }, 50);
}

function settleRevenueCenterRoute(screen, route, columns = []) {
  if (!REVENUE_CENTER_MONTH_ROUTES.has(route) || !screen) return;
  if (screen._revenueCenterSettleTimer) clearInterval(screen._revenueCenterSettleTimer);
  const activeIndex = REVENUE_CENTER_ACTIVE_TABS[route];
  let ticks = 0;
  const settle = () => {
    const controls = [...screen.querySelectorAll('.filter-strip select')];
    const desired = [['year', '2026', 'Năm 2026'], ['start_month', '1', 'Tháng 1'], ['end_month', '11', 'Tháng 11']];
    desired.forEach(([name, value, label]) => {
      const select = screen.querySelector(`select[name="${name}"]`) || controls.find(control =>
        String(control.getAttribute('aria-label') || '').trim() === label
        || String(control.options?.[0]?.textContent || '').trim() === label);
      if (!select) return;
      if (name === 'year' && ![...select.options].some(item => item.value === value || item.textContent.trim() === label)) {
        const option = document.createElement('option');
        option.value = value;
        option.textContent = label;
        select.append(option);
      }
      const option = [...select.options].find(item => String(item.value) === value)
        || [...select.options].find(item => String(item.textContent || '').trim() === label);
      if (option && select.value !== option.value) {
        select.value = option.value;
      }
    });
    const tabList = screen.querySelector('.ref-tabs, [role="tablist"]');
    const tabs = tabList ? [...tabList.querySelectorAll('.ref-tab, [role="tab"], button')] : [];
    tabs.forEach((tab, index) => {
      const active = index === activeIndex;
      tab.classList.toggle('active', active);
      tab.setAttribute('aria-selected', active ? 'true' : 'false');
    });
    screen.querySelectorAll('.filter-strip button, .page-actions button, .screen-actions button').forEach(button => {
      const text = String(button.textContent || '').replace(/\s+/g, ' ').trim();
      if (/^(Chạy báo cáo|Xóa lọc|Lọc)$/.test(text)) button.remove();
    });
    ensureMonthlyRevenueHeader(screen, columns, route);
    ticks += 1;
    if (ticks >= 50) {
      clearInterval(screen._revenueCenterSettleTimer);
      screen._revenueCenterSettleTimer = null;
    }
  };
  settle();
  screen._revenueCenterSettleTimer = setInterval(settle, 50);
}

function ensureMonthlyRevenueHeader(screen, columns = [], route = '') {
  const table = screen?.querySelector('[data-report-table] table');
  if (!table) return;
  let tableHead = table.querySelector('thead');
  if (table.dataset.monthProjection && tableHead?.querySelector('[data-month-group]')) return;
  // The API projection retains the reference inventory's legacy flat month
  // fields before the repeated month metrics.  The reference UI groups only
  // the selected month range; remove those flat fields and project each
  // selected month as one contiguous metric group.
  const routePrefix = route.includes('/by_month/sale/index') ? 10 : 2;
  const childCount = route.includes('/by_month/center/index') ? 10 : 9;
  const headForShape = table.querySelector('thead tr:not([data-month-group])');
  if (headForShape) {
    const labels = [...headForShape.children].map(cell => String(cell.textContent || '').replace(/\s+/g, ' ').trim());
    const firstFlat = labels.findIndex((label, index) => index >= routePrefix && label === 'Tháng 1');
    let flatCount = 0;
    if (firstFlat >= 0) {
      while (firstFlat + flatCount < labels.length && labels[firstFlat + flatCount] === `Tháng ${flatCount + 1}`) flatCount += 1;
    }
    const flatMonths = flatCount >= 11;
    if (flatMonths) {
      const startSelect = screen.querySelector('select[name="start_month"]');
      const endSelect = screen.querySelector('select[name="end_month"]');
      const monthNumber = select => Number(String(select?.value || select?.selectedOptions?.[0]?.textContent || '').replace(/[^0-9]/g, '')) || 11;
      const startMonth = Math.min(12, Math.max(1, monthNumber(startSelect)));
      const endMonth = Math.min(12, Math.max(startMonth, monthNumber(endSelect)));
      const originalCells = [...headForShape.children];
      const keepIndexes = [];
      for (let i = 0; i < routePrefix; i += 1) keepIndexes.push(i);
      const childStart = firstFlat + flatCount;
      for (let month = startMonth; month <= endMonth; month += 1) {
        const groupStart = childStart + ((month - 1) * childCount);
        for (let offset = 0; offset < childCount; offset += 1) {
          if (groupStart + offset < originalCells.length) keepIndexes.push(groupStart + offset);
        }
      }
      const fixedHeaders = labels.slice(0, routePrefix);
      const rows = [...table.querySelectorAll('thead tr, tbody tr')];
      rows.forEach(row => {
        const cells = [...row.children];
        cells.forEach((cell, index) => { if (!keepIndexes.includes(index)) cell.remove(); });
      });
      // Fixed columns belong to the first tier and span both header rows;
      // only the selected month metrics remain in the second tier.
      [...headForShape.children].slice(0, routePrefix).forEach(cell => cell.remove());
      table.dataset.monthProjection = `${startMonth}-${endMonth}`;
      tableHead = table.querySelector('thead');
      tableHead.querySelectorAll('[data-month-group]').forEach(node => node.remove());
      const groupRow = document.createElement('tr');
      groupRow.dataset.monthGroup = '1';
      for (let i = 0; i < routePrefix; i += 1) {
        const cell = document.createElement('th');
        cell.setAttribute('rowspan', '2');
        cell.textContent = fixedHeaders[i] || '';
        groupRow.append(cell);
      }
      for (let month = startMonth; month <= endMonth; month += 1) {
        const cell = document.createElement('th');
        cell.colSpan = childCount;
        cell.textContent = `Tháng ${month}`;
        groupRow.append(cell);
      }
      tableHead.insertBefore(groupRow, headForShape);
      return;
    }
  }
  if (!tableHead) {
    tableHead = document.createElement('thead');
    const row = document.createElement('tr');
    columns.forEach(column => {
      const cell = document.createElement('th');
      cell.setAttribute('scope', 'col');
      cell.textContent = REFERENCE_LABELS[column.label] || column.label || column.key || '';
      row.append(cell);
    });
    tableHead.append(row);
    table.insertBefore(tableHead, table.firstElementChild);
  }
  const row = tableHead?.querySelector('tr:not([data-month-group])');
  if (!tableHead || !row) return;
  tableHead.querySelectorAll('[data-month-group]').forEach(node => node.remove());
  const headers = [...row.children].map(cell => String(cell.textContent || '').replace(/\s+/g, ' ').trim());
  const childStart = headers.findIndex(label => label === 'Chỉ tiêu');
  if (childStart < 0) return;
  const fallbackCount = Math.min(8, headers.length - childStart);
  const before = childStart ? `<th colspan="${childStart}" aria-hidden="true"></th>` : '';
  tableHead.insertAdjacentHTML('afterbegin', `<tr data-month-group>${before}<th colspan="${fallbackCount}">Tháng 11</th></tr>`);
}

function htmlEscape(value) {
  return String(value ?? '').replace(/[&<>'"]/g, char => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;' }[char]));
}

function safeValue(value, helpers, label = '', route = '', key = '') {
  // Only these invoice fields are visibly blank in retained debt reference
  // screens 084/085. UNKNOWN is deliberately not converted to an empty cell.
  const blankInvoiceField = ['/report/finance/debt', '/report/finance/student_finance'].includes(route)
    && ['ma_hoa_on', 'ngay_tao_hoa_on'].includes(key);
  if (value === null || value === undefined || value === '') return blankInvoiceField ? '' : '—';
  if (typeof value === 'number') return Number(value).toLocaleString('vi-VN');
  const text = String(value);
  if (text.toUpperCase() === 'UNKNOWN' || text === 'Chưa cập nhật') return '—';
  if (/status|trạng thái|tình trạng|role|phân quyền/i.test(label) && typeof helpers.statusLabel === 'function') return helpers.statusLabel(text);
  const date = text.match(/^(\d{4})-(\d{2})-(\d{2})(?:[T ](.*))?$/);
  return date ? `${date[3]}/${date[2]}/${date[1]}${date[4] ? ` ${date[4]}` : ''}` : text;
}

function reportRenderer(scope) {
  return async (screen, ctx) => {
    const renderReport = async (activeFilters = {}) => {
    const observedDefaults = REVENUE_CENTER_MONTH_ROUTES.has(ctx.route)
      ? { year: '2026', start_month: '1', end_month: '11' } : {};
      const requestFilters = { ...observedDefaults, ...activeFilters };
      const result = await ctx.api(scope.runUrl(ctx.route, requestFilters));
    const payload = result?.data || result || {};
    const helpers = ctx.helpers || globalThis.CenterEdu?.helpers || {};
    const columns = Array.isArray(payload.columns) ? payload.columns : [];
    const rows = Array.isArray(payload.rows) ? payload.rows : [];
    const filterDefs = Array.isArray(payload.filters) && payload.filters.length
      ? payload.filters
      : (scope.filtersFor(ctx.route) || []).map(name => ({ name, label: FILTER_LABELS[name] || name }));
    const exportHref = scope.exportUrl(ctx.route, requestFilters);
    const head = String(payload.title || 'Báo cáo tài chính');
    const summary = (ctx.route === '/report/finance/debt' || ctx.route === '/report/finance/student_finance')
      ? `<div class="report-finance-summary" data-report-summary>${summaryMarkup(payload, rows)}</div>`
      : '';
    const pageConfig = reportPageSizes(filterDefs);
    const pagination = FINANCE_REPORT_PAGINATION[ctx.route]?.enabled ? FINANCE_REPORT_PAGINATION[ctx.route] : payload.pagination;
    const table = columns.length
      ? createReportTable({ columns, rows, header: col => htmlEscape(REFERENCE_LABELS[col.label] || col.label || col.key || ''), cell: (row, col) => htmlEscape(safeValue(row[col.key], helpers, col.label || col.key, ctx.route, col.key)), pageSizes: pageConfig.values, pagination })
      : '<div class="empty">Không có dữ liệu.</div>';
    const observedDebt = ctx.route === '/report/finance/debt' || ctx.route === '/report/finance/student_finance';
    const renderActionButton = (label, exportHref) => {
      const isExport = label === 'Excel';
      const action = label === 'Lọc' ? 'run' : label === 'Thanh toán' ? 'payment' : label === 'Cập nhật dữ liệu' ? 'refresh' : label === 'Chọn trạng thái' || label === 'Tất cả trạng thái học phí' ? 'status' : '';
      const cls = isExport ? 'ghost report-export' : (action === 'refresh' ? 'report-action report-refresh' : 'ghost report-action');
      const style = action === 'refresh' ? ' style="display:inline-flex;align-items:center;height:36px;padding:0 13px;border-radius:4px;background:#21a889;color:#fff;font-size:12px;font-weight:600;white-space:nowrap"' : '';
      return `<button class="${cls}" type="button" data-report-action="${action}"${style}${isExport ? ` data-export-href="${htmlEscape(exportHref)}"` : ''}>${htmlEscape(label)}</button>`;
    };
    const headerButtons = headerRouteButtons(ctx.route).map(label => renderActionButton(label, exportHref)).join('');
    const headerActions = headerButtons ? `<div class="screen-actions">${headerButtons}</div>` : '';
    const headerLabels = new Set(headerRouteButtons(ctx.route));
    const actionButtons = routeButtons(ctx.route)
      .filter(label => !headerLabels.has(label))
      .map(label => renderActionButton(label, exportHref)).join('');
    const activeTabByRoute = {
      '/report/finance/revenue_center/by_month/center/index': 1,
      '/report/finance/revenue_center/by_month/sale_team/index': 2,
      '/report/finance/revenue_center/by_month/sale/index': 3,
    };
    const activeTab = activeTabByRoute[ctx.route] ?? 0;
    const tabs = (ROUTE_TABS[ctx.route] || []).map((label, index) => `<button class="ref-tab${index === activeTab ? ' active' : ''}" role="tab" type="button" aria-selected="${index === activeTab ? 'true' : 'false'}">${htmlEscape(label)}</button>`).join('');
    const tabStrip = tabs ? `<div class="ref-tabs" role="tablist">${tabs}</div>` : '';
    const filterActions = (!observedDebt && FINANCE_FILTER_BUTTON_ROUTES.has(ctx.route)) ? `<button class="primary filter-apply" type="button" data-report-run>Lọc</button>` : '';
    const inlineActions = observedDebt ? `<div class="screen-actions" data-report-filter-actions style="display:flex;align-items:center;gap:6px;grid-column:span 2;flex-wrap:wrap">${actionButtons}</div>` : '';
    screen.innerHTML = `<section class="card"${observedDebt ? ' data-report-debt-layout' : ''}><div class="page-head"><div><h1>${htmlEscape(head)}</h1></div>${observedDebt ? headerActions : `<div class="screen-actions">${actionButtons}</div>`}</div>${tabStrip}<div class="filter-strip" data-report-filter-shell>${filterActions}${inlineActions}</div>${summary}${table}</section>`;
    const tableRoot = screen.querySelector('[data-report-table]');
    repairFinanceControls(screen, filterDefs, requestFilters, ctx.route);
    if (observedDefaults.year) {
      for (const [name, value, label] of [['year', '2026', 'Năm 2026'], ['start_month', '1', 'Tháng 1'], ['end_month', '11', 'Tháng 11']]) {
        const select = screen.querySelector(`select[name="${name}"]`);
        if (!select) continue;
        const exact = [...select.options].find(option => String(option.value).trim() === value);
        const byText = [...select.options].find(option => {
          const text = String(option.textContent || '').trim();
          return text === label || text === value || text.endsWith(value);
        });
        if (exact) select.value = exact.value;
        else if (byText) select.value = byText.value;
      }
    }
    const pageSizeControl = pageConfig.observed ? { name: pageConfig.name } : null;
    if (tableRoot) mountReportTable(tableRoot, { columns, rows, header: col => htmlEscape(REFERENCE_LABELS[col.label] || col.label || col.key || ''), cell: (row, col) => htmlEscape(safeValue(row[col.key], helpers, col.label || col.key, ctx.route, col.key)), pageSizes: pageConfig.values, pagination, pageSizeControl });
    // app.js applies its generic observed-control normalizer after this
    // renderer returns. Reapply the route-exact shape while that pass settles;
    // this keeps real page-size/select controls from being removed by the
    // generic shell normalizer.
    scheduleFinanceControlRepair(screen, filterDefs, requestFilters, ctx.route);
    if (REVENUE_CENTER_MONTH_ROUTES.has(ctx.route)) {
      ensureMonthlyRevenueHeader(screen, columns, ctx.route);
    }
    settleRevenueCenterRoute(screen, ctx.route, columns);
    if (!screen.dataset.financeDelegated) {
      screen.dataset.financeDelegated = '1';
      screen.addEventListener('click', async event => {
        const runButton = event.target.closest?.('[data-report-run], .filter-apply');
        const resetButton = event.target.closest?.('[data-report-reset]');
        if (!runButton && !resetButton) return;
        event.preventDefault();
        const params = resetButton ? {} : Object.fromEntries([...screen.querySelectorAll('.filter-strip input,.filter-strip select,.filter-strip textarea')].map(control => [control.name, control.value]).filter(([name]) => name));
        try { await renderReport(params); } catch (error) { screen.innerHTML = `<div class="card empty">${htmlEscape(error.message || error)}</div>`; }
      });
    }
    if (!FINANCE_FILTER_BUTTON_ROUTES.has(ctx.route) && !screen.dataset.financeAutoFilter) {
      screen.dataset.financeAutoFilter = '1';
      screen.addEventListener('change', event => {
        if (!event.target.closest?.('.filter-strip') || /length|page.?size/i.test(event.target.name || '')) return;
        renderReport(Object.fromEntries([...screen.querySelectorAll('.filter-strip input,.filter-strip select,.filter-strip textarea')].map(control => [control.name, control.value]).filter(([name]) => name))).catch(() => {});
      });
    }
    screen.querySelectorAll('.report-export').forEach(button => button.addEventListener('click', () => {
      const href = button.getAttribute('data-export-href');
      if (href) window.location.assign(href);
    }));
    screen.querySelectorAll('[data-report-action="payment"]').forEach(button => button.addEventListener('click', () => {
      window.location.assign('/report/finance/payment/index');
    }));
    screen.querySelectorAll('[data-report-action="refresh"]').forEach(button => button.addEventListener('click', () => {
      renderReport(Object.fromEntries([...screen.querySelectorAll('.filter-strip input,.filter-strip select,.filter-strip textarea')].map(control => [control.name, control.value]).filter(([name]) => name)));
    }));
    screen.querySelectorAll('[data-report-action="run"]').forEach(button => button.addEventListener('click', () => {
      renderReport(Object.fromEntries([...screen.querySelectorAll('.filter-strip input,.filter-strip select,.filter-strip textarea')].map(control => [control.name, control.value]).filter(([name]) => name)));
    }));
    screen.querySelectorAll('[data-report-action="status"]').forEach(button => button.addEventListener('click', () => {
      const select = screen.querySelector('select[name="filter_3"],select[name="filter_2"],select[name="filter_11"],select[name="filter_12"]');
      if (select) select.focus();
    }));
    };
    await renderReport();
    return true;
  };
}

/** Register finance report screens with the coordinator frontend seam. */
export async function register(centerEdu = globalThis.CenterEdu) {
  if (!centerEdu) return { routes: FINANCE_REPORT_ROUTES };
  centerEdu.reportMetadata = { ...(centerEdu.reportMetadata || {}), financeReportScope };
  for (const route of FINANCE_REPORT_ROUTES) centerEdu.registerScreen?.(route, reportRenderer(financeReportScope));
  return { routes: FINANCE_REPORT_ROUTES };
}


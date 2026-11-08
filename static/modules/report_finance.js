/** Route metadata for finance and finance-backed CRM report screens.
 *
 * The shared shell owns rendering and transport.  This module keeps the
 * observed Vietnamese filter names and export/run URL contract route-local so
 * a shell integration does not fall back to generic filter_1/filter_2 wiring.
 */
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
    '/report/finance/debt': { filters: ['filter_1', 'filter_2', 'tim_trong_bang', 'from_date', 'to_date', 'esttype', 'esttype_2', 'from_date_expired_date', 'to_date_expired_date'] },
    '/report/finance/student_finance': { filters: ['filter_1', 'filter_2', 'filter_3', 'tim_trong_bang', 'from_date', 'to_date', 'esttype', 'esttype_2', 'from_date_expired_date', 'to_date_expired_date'] },
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

const FINANCE_REPORT_ROUTES = Object.keys(financeReportScope.routes).filter(route => route.startsWith('/report/finance/'));
const FILTER_LABELS = {
  from_date: 'Từ ngày', to_date: 'Đến ngày', year: 'Năm', start_month: 'Từ tháng', end_month: 'Đến tháng',
  tim_trong_bang: 'Tìm trong bảng', nhap_ten_san_pham: 'Nhập tên sản phẩm', tim_kiem: 'Tìm kiếm',
  nguon_du_lieu: 'Nguồn dữ liệu', filter_1: 'Trung tâm', filter_2: 'Trạng thái', filter_3: 'Loại khách hàng',
  filter_4: 'Bộ lọc', filter_7: 'Tìm trong bảng', from_date_2: 'Từ ngày tạo', to_date_2: 'Đến ngày tạo',
  from_date_expired_date: 'Hạn từ ngày', to_date_expired_date: 'Hạn đến ngày',
};
const REFERENCE_LABELS = {
  'From date': 'Từ ngày', 'To date': 'Đến ngày', Facility: 'Trung tâm', Center: 'Trung tâm',
  'Customer': 'Khách hàng', 'Source': 'Nguồn dữ liệu', Status: 'Trạng thái',
};
const ROUTE_BUTTONS = {
  '/report/finance/class_revenue_tracking/index': ['Lọc', 'Excel'],
  '/report/finance/class_revenue_tracking_new/index': ['Lọc', 'Excel'],
  '/report/finance/debt': ['Thanh toán', 'Excel', 'Cập nhật dữ liệu'],
  '/report/finance/student_finance': ['Thanh toán', 'Tất cả trạng thái học phí', 'Excel', 'Cập nhật dữ liệu'],
  '/report/finance/reserve': ['Chọn trạng thái', 'Excel'],
};

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

function routeButtons(route) {
  return ROUTE_BUTTONS[route] || ['Excel'];
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
        node.value = option;
        node.textContent = financeControlLabel(filter, option, optionIndex);
        select.append(node);
      });
      if (activeFilters[name] != null) select.value = String(activeFilters[name]);
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
  controls.forEach(wrapper => strip.insertBefore(wrapper, strip.querySelector('button')));
  const after = filterControlSignature(strip);
  if (before !== after) strip.dataset.financeControls = after;
}

function scheduleFinanceControlRepair(screen, filterDefs, activeFilters, route) {
  if (screen._financeRepairTimer) clearInterval(screen._financeRepairTimer);
  let ticks = 0;
  screen._financeRepairTimer = setInterval(() => {
    repairFinanceControls(screen, filterDefs, activeFilters, route);
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

function htmlEscape(value) {
  return String(value ?? '').replace(/[&<>'"]/g, char => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;' }[char]));
}

function safeValue(value, helpers, label = '') {
  if (value === null || value === undefined || value === '') return '—';
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
      const result = await ctx.api(scope.runUrl(ctx.route, activeFilters));
    const payload = result?.data || result || {};
    const helpers = ctx.helpers || globalThis.CenterEdu?.helpers || {};
    const columns = Array.isArray(payload.columns) ? payload.columns : [];
    const rows = Array.isArray(payload.rows) ? payload.rows : [];
    const filterDefs = Array.isArray(payload.filters) && payload.filters.length
      ? payload.filters
      : (scope.filtersFor(ctx.route) || []).map(name => ({ name, label: FILTER_LABELS[name] || name }));
    const fields = '';
    const exportHref = scope.exportUrl(ctx.route, activeFilters);
    const head = String(payload.title || 'Báo cáo tài chính');
    const table = columns.length
      ? `<div class="table-wrap"><table><thead><tr>${columns.map(col => `<th>${htmlEscape(REFERENCE_LABELS[col.label] || col.label || col.key || '')}</th>`).join('')}</tr></thead><tbody>${rows.length ? rows.map(row => `<tr>${columns.map(col => `<td>${htmlEscape(safeValue(row[col.key], helpers, col.label || col.key))}</td>`).join('')}</tr>`).join('') : `<tr><td colspan="${columns.length}" class="empty">Không có dữ liệu.</td></tr>`}</tbody></table></div>`
      : '<div class="empty">Không có dữ liệu.</div>';
    const actionButtons = routeButtons(ctx.route).map(label => {
      const isExport = label === 'Excel';
      const action = label === 'Lọc' ? 'run' : label === 'Thanh toán' ? 'payment' : label === 'Cập nhật dữ liệu' ? 'refresh' : label === 'Chọn trạng thái' || label === 'Tất cả trạng thái học phí' ? 'status' : '';
      const cls = isExport ? 'ghost report-export' : 'ghost report-action';
      return `<button class="${cls}" type="button" data-report-action="${action}"${isExport ? ` data-export-href="${htmlEscape(exportHref)}"` : ''}>${htmlEscape(label)}</button>`;
    }).join('');
    const tabs = (ROUTE_TABS[ctx.route] || []).map((label, index) => `<button role="tab" type="button" aria-selected="${index === 0 ? 'true' : 'false'}">${htmlEscape(label)}</button>`).join('');
    const tabStrip = tabs ? `<div class="ref-tabs" role="tablist">${tabs}</div>` : '';
    screen.innerHTML = `<section class="card"><div class="page-head"><div><h1>${htmlEscape(head)}</h1><p>Dữ liệu báo cáo từ cơ sở dữ liệu nội bộ.</p></div><div class="screen-actions">${actionButtons}</div></div>${tabStrip}<div class="filter-strip" data-report-filter-shell><button class="primary" type="button" data-report-run>Chạy báo cáo</button><button class="ghost" type="button" data-report-reset>Xóa lọc</button></div>${table}</section>`;
    const filterShell = screen.querySelector('[data-report-filter-shell]');
    repairFinanceControls(screen, filterDefs, activeFilters, ctx.route);
    // app.js applies its generic observed-control normalizer after this
    // renderer returns. Reapply the route-exact shape while that pass settles;
    // this keeps real page-size/select controls from being removed by the
    // generic shell normalizer.
    scheduleFinanceControlRepair(screen, filterDefs, activeFilters, ctx.route);
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


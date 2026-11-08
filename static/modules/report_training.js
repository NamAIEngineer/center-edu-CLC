/** Semantic metadata for training report adapters. */
import { createReportTable, mountReportTable, reportPageSizes } from './report_table.js';
export const trainingTestReport = {
  route: '/report/training/test',
  title: 'Báo cáo kiểm tra',
  columns: [
    ['stt', 'STT'], ['ho_ten', 'Họ tên'], ['tieu_chi', 'Tiêu chí'], ['nhan_xet', 'Nhận xét'],
  ],
  filters: [
    { name: 'filter_1', label: '', placeholder: '', type: 'select' },
    { name: 'filter_2', label: '', placeholder: '', type: 'select' },
    { name: 'filter_3', label: '', placeholder: '', type: 'select' },
    { name: 'nhap_ten_hoc_vien', label: 'Nhập tên học viên', placeholder: 'Nhập tên học viên', type: 'text' },
  ],
  exportLabel: 'Excel',
};

export function trainingTestExportHref(filters = {}) {
  const query = new URLSearchParams({ route: trainingTestReport.route, ...filters });
  return `/api/reports/export?${query.toString()}`;
}

const trainingReportMetadata = {
  [trainingTestReport.route]: trainingTestReport,
  '/report/training/attendance': { route: '/report/training/attendance', title: 'Báo cáo điểm danh' },
  '/report/training/daily_evaluation/index': { route: '/report/training/daily_evaluation/index', title: 'Báo cáo đánh giá hàng ngày' },
  '/report/training/class/v2': { route: '/report/training/class/v2', title: 'Báo cáo lớp học' },
  '/report/training/tuition_class/index': { route: '/report/training/tuition_class/index', title: 'Báo cáo lớp học (Học phí)' },
  '/report/training/allocation_student/index': { route: '/report/training/allocation_student/index', title: 'Phân bổ buổi học của học viên' },
  '/report/training/change_class/index': { route: '/report/training/change_class/index', title: 'Báo cáo chuyển lớp' },
  '/report/training/reserve_training/index': { route: '/report/training/reserve_training/index', title: 'Báo cáo bảo lưu' },
  '/report/training/homework_ratio/index': { route: '/report/training/homework_ratio/index', title: 'Báo cáo tỷ lệ bài tập về nhà' },
  '/report/training/attendance_center/index': { route: '/report/training/attendance_center/index', title: 'Tỉ lệ chuyên cần của học viên' },
  '/report/training/using_course/index': { route: '/report/training/using_course/index', title: 'Báo cáo khóa học/chương trình' },
  '/report/training/enroll/index': { route: '/report/training/enroll/index', title: 'Báo cáo ghi danh' },
  '/report/training/allocation_hours/index': { route: '/report/training/allocation_hours/index', title: 'Phân bổ giờ học của học viên' },
  '/report/training/schedule/index': { route: '/report/training/schedule/index', title: 'Báo cáo lịch học' },
  '/report/training/diligence/index': { route: '/report/training/diligence/index', title: 'Báo cáo chuyên cần' },
  '/report/training/register_learning': { route: '/report/training/register_learning', title: 'Báo cáo đăng ký học học viên' },
  '/report/training/student_pause': { route: '/report/training/student_pause', title: 'Báo cáo danh sách học sinh tạm dừng' },
  '/report/training/student_training_v2': { route: '/report/training/student_training_v2', title: 'Báo cáo học viên' },
  '/report/training/due_date_student': { route: '/report/training/due_date_student', title: 'Báo cáo thống kê đến hạn học viên' },
  '/report/training/absent/classes': { route: '/report/training/absent/classes', title: 'Báo cáo vắng' },
  '/report/training/top_notebook': { route: '/report/training/top_notebook', title: 'Sổ đầu bài' },
  '/report/training/student_drop/index': { route: '/report/training/student_drop/index', title: 'Báo cáo drop' },
  '/report/training/new_enrollment/index': { route: '/report/training/new_enrollment/index', title: 'Báo cáo new enrollment' },
  '/report/training/require_support/index': { route: '/report/training/require_support/index', title: 'Báo cáo Yêu cầu hỗ trợ' },
  '/report/training/instead_teacher': { route: '/report/training/instead_teacher', title: 'Báo cáo Nghỉ - Dạy thay giáo viên' },
  '/report/training/examination_month/index': { route: '/report/training/examination_month/index', title: 'Danh sách bài kiểm tra' },
};

// These routes expose a pager in the reference inventory without a proven
// page-size selector. Keep the bounded observed capacity explicit so the
// shared renderer can paginate every API row without inventing controls.
export const TRAINING_REPORT_PAGINATION = Object.freeze({
  // The retained reference inventory shows a pager on these routes with the
  // following first-page sizes.  Keep the API row set intact; the shared
  // table controller slices only for presentation.
  '/report/training/class/v2': Object.freeze({ enabled: true, pageSize: 10 }),
  '/report/training/allocation_student/index': Object.freeze({ enabled: true, pageSize: 20 }),
  '/report/training/change_class/index': Object.freeze({ enabled: true, pageSize: 10 }),
  '/report/training/reserve_training/index': Object.freeze({ enabled: true, pageSize: 10 }),
  '/report/training/using_course/index': Object.freeze({ enabled: true, pageSize: 10 }),
  '/report/training/enroll/index': Object.freeze({ enabled: true, pageSize: 10 }),
  '/report/training/allocation_hours/index': Object.freeze({ enabled: true, pageSize: 20 }),
  '/report/training/schedule/index': Object.freeze({ enabled: true, pageSize: 10 }),
  '/report/training/due_date_student': Object.freeze({ enabled: true, pageSize: 15 }),
});

const TRAINING_ROUTE_ACTIONS = {
  '/report/training/attendance': ['M', 'CP', 'KP'],
  '/report/training/daily_evaluation/index': ['Cập nhật dữ liệu', 'M', 'CP', 'KP'],
  '/report/training/allocation_student/index': ['Phân bổ trên doanh thu phải đóng'],
  '/report/training/reserve_training/index': ['Chọn trạng thái', 'Bảo lưu', 'Ghi danh', 'Quá hạn'],
  '/report/training/homework_ratio/index': ['Cập nhật'],
  '/report/training/register_learning': ['Chọn trạng thái'],
  '/report/training/student_training_v2': ['Cơ sở Phổ Yên'],
  '/report/training/due_date_student': ['Cập nhật'],
  '/report/teacher/rest_learning': ['Chọn trạng thái nghỉ', 'Chọn trạng thái học viên', 'Chọn trạng thái học bù'],
  '/report/training/top_notebook': ['Chọn trạng thái'],
  '/report/training/student_drop/index': ['Chọn trạng thái'],
};

const TRAINING_ROUTE_TABS = {
  '/report/training/allocation_student/index': ['Phân bổ buổi học của học viên', 'Phân bổ giờ học của học viên'],
  '/report/training/enroll/index': ['Báo cáo ghi danh'],
  '/report/training/allocation_hours/index': ['Phân bổ buổi học của học viên', 'Phân bổ giờ học của học viên'],
  '/report/training/schedule/index': ['Báo cáo lịch học'],
  '/report/training/due_date_student': ['Báo cáo thống kê đến hạn học viên'],
  '/report/teacher/rest_learning': ['Danh sách học viên nghỉ học'],
};

// Date and course copy is route-specific in the observed report inventory.
// Keep these labels attached to the field names so duplicate date controls
// retain their business meaning instead of receiving generic placeholders.
export const TRAINING_ROUTE_PLACEHOLDERS = {
  '/report/training/attendance': { from_date: 'Từ ngày', to_date: 'Đến ngày' },
  '/report/training/daily_evaluation/index': { start_date: 'Ngày bắt đầu', end_date: 'Ngày kết thúc' },
  '/report/training/allocation_student/index': {
    from_date: 'Ngày đăng kí học', to_date: 'Ngày đăng kí học',
    from_end_date: 'Ngày kết thúc', to_end_date: 'Ngày kết thúc',
  },
  '/report/training/change_class/index': { from_date: 'Từ ngày', to_date: 'Đến ngày' },
  '/report/training/homework_ratio/index': { from_date: 'Từ ngày', to_date: 'Đến ngày' },
  '/report/training/using_course/index': { from_date: 'Thời gian bắt đầu', to_date: 'Thời gian bắt đầu' },
  '/report/training/enroll/index': { from_date: 'Từ ngày', to_date: 'Đến ngày' },
  '/report/training/register_learning': { from_date: 'From date', to_date: 'To date' },
  '/report/training/student_pause': { from_date: 'Từ ngày', to_date: 'Đến ngày' },
  '/report/training/student_drop/index': { from_date: 'From date', to_date: 'To date' },
  '/report/training/new_enrollment/index': { from_date: 'From date', to_date: 'To date' },
  '/report/training/examination_month/index': { from_date: 'From date', to_date: 'To date' },
  '/report/teacher/rest_learning': {
    from_date_enroll: 'Lọc ngày kết thúc',
    to_date_enroll: 'Lọc ngày kết thúc',
    from_date_absent: 'Ngày nghỉ học viên',
    to_date_absent: 'Ngày nghỉ học viên',
  },
};

// These screens expose an observed update action, but the reference form has
// no separate generic "Lọc" or "Xóa lọc" submit/reset controls. Keep the
// route-owned action visible while suppressing controls introduced by the
// shared renderer.
export const TRAINING_AUTO_FILTER_ROUTES = Object.freeze([
  '/report/training/test',
  '/report/training/class/v2',
  '/report/training/allocation_student/index',
  '/report/training/homework_ratio/index',
  '/report/training/due_date_student',
]);

function escapeReportHtml(value) {
  return String(value ?? '').replace(/[&<>'"]/g, char => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;' }[char]));
}

function reportCell(value) {
  if (value === null || value === undefined || value === '') return '—';
  if (typeof value === 'number') return Number(value).toLocaleString('vi-VN');
  return escapeReportHtml(value);
}

function trainingFilterLabel(filter, route = '', index = -1) {
  // Repeated date placeholders are observed controls. Distinct field names
  // carry identity; generated numeric suffixes change visible copy.
  const routeLabel = route === '/report/teacher/rest_learning' && index >= 12
    ? (String(filter.name || '') === 'from_date_enroll' || String(filter.name || '') === 'to_date_enroll' ? 'Ngày ghi danh học bù' : TRAINING_ROUTE_PLACEHOLDERS[route]?.[String(filter.name || '')])
    : TRAINING_ROUTE_PLACEHOLDERS[route]?.[String(filter.name || '')];
  return String(routeLabel || filter.label || filter.placeholder || filter.options?.[0] || '');
}

/** Render the observed report contract without the generic table toolbar.
 * The generic renderer adds a client search/page-size control that is absent
 * on several reference screens and therefore creates duplicate filters.
 */
export function createTrainingReportRenderer() {
  return async (screen, ctx) => {
    screen.replaceChildren();
    const loading = document.createElement('p');
    loading.className = 'report-route-status'; loading.setAttribute('role', 'status');
    loading.textContent = 'Đang tải dữ liệu báo cáo…'; screen.append(loading);
    let response;
    try {
      response = await ctx.api(`/api/reports/run?route=${encodeURIComponent(ctx.route)}`);
    } catch (error) {
      loading.className = 'report-route-status error'; loading.setAttribute('role', 'alert');
      loading.textContent = error?.message || 'Không thể tải dữ liệu báo cáo.';
      return true;
    }
    const payload = response?.data || response || {};
    const filters = Array.isArray(payload.filters) ? payload.filters : [];
    const fields = filters.map((filter, index) => {
      const name = String(filter.name || `filter_${index + 1}`).replace(/[^A-Za-z0-9_-]/g, '_');
      const options = Array.isArray(filter.options) ? filter.options.map(value => String(value)) : [];
      const label = trainingFilterLabel(filter, ctx.route, index);
      if (String(filter.type || '').toLowerCase().startsWith('select') || options.length) {
        const aria = escapeReportHtml(label);
        return `<label>${escapeReportHtml(label)}<select name="${escapeReportHtml(name)}" aria-label="${aria}">${options.map(value => `<option value="${escapeReportHtml(value)}">${escapeReportHtml(value)}</option>`).join('')}</select></label>`;
      }
      const placeholder = String(filter.placeholder || label);
      return `<label><input name="${escapeReportHtml(name)}" type="text" placeholder="${escapeReportHtml(placeholder)}" aria-label="${escapeReportHtml(placeholder)}"></label>`;
    }).join('');
    const columns = Array.isArray(payload.columns) ? payload.columns : [];
    const rows = Array.isArray(payload.rows) ? payload.rows : [];
    const pageConfig = reportPageSizes(filters);
    const pagination = TRAINING_REPORT_PAGINATION[ctx.route] || null;
    const table = columns.length
      ? createReportTable({ columns, rows, cell: (row, column) => reportCell(row[column.key]), pageSizes: pageConfig.values, pagination })
      : '<div class="empty">Không có dữ liệu.</div>';
    const title = escapeReportHtml(payload.title || trainingReportMetadata[ctx.route]?.title || 'Báo cáo');
    const routeActions = TRAINING_ROUTE_ACTIONS[ctx.route] || [];
    const actions = `${routeActions.map(label => `<button class="ghost report-action" type="button">${escapeReportHtml(label)}</button>`).join('')}${ctx.route === '/report/training/class/v2' ? '' : `<a class="btn ghost report-action" href="/api/reports/export?route=${encodeURIComponent(ctx.route)}">Excel</a>`}`;
    const tabLabels = TRAINING_ROUTE_TABS[ctx.route] || [title];
    const tabs = tabLabels.map((label, index) => `<button class="ref-tab${index === 0 ? ' active' : ''}" role="tab" type="button" aria-selected="${index === 0 ? 'true' : 'false'}">${escapeReportHtml(label)}</button>`).join('');
    const runLabel = routeActions.includes('Cập nhật dữ liệu') ? 'Cập nhật dữ liệu' : 'Lọc';
    const observedAutoFilters = TRAINING_AUTO_FILTER_ROUTES.includes(ctx.route);
    screen.innerHTML = `<section class="card"><div class="page-head"><div><h1>${title}</h1></div><div class="page-actions">${actions}</div></div><div class="ref-tabs" role="tablist">${tabs}</div><form class="filter-strip" data-report-form>${fields}${observedAutoFilters ? '' : `<button class="primary" type="submit">${escapeReportHtml(runLabel)}</button><button class="ghost" type="reset">Xóa lọc</button>`}</form>${table}</section>`;
    const form = screen.querySelector('[data-report-form]');
    const tableRoot = screen.querySelector('[data-report-table]');
    const pageSizeControl = pageConfig.observed ? { name: pageConfig.name } : null;
    const tableController = tableRoot ? mountReportTable(tableRoot, { columns, rows, cell: (row, column) => reportCell(row[column.key]), pageSizes: pageConfig.values, pageSizeControl, pagination }) : null;
    const run = async () => {
      const query = new URLSearchParams({ route: ctx.route });
      for (const [key, value] of new FormData(form).entries()) if (String(value)) query.set(key, String(value));
      const submit = form.querySelector('button[type="submit"]');
      if (submit) submit.disabled = true;
      try {
        const next = await ctx.api(`/api/reports/run?${query.toString()}`);
        const data = next?.data || next || {};
        if (Array.isArray(data.rows)) tableController?.setRows(data.rows);
      } catch (error) {
        const body = screen.querySelector('tbody');
        if (body) body.innerHTML = `<tr><td colspan="${Math.max(columns.length, 1)}" class="empty error" role="alert">${escapeReportHtml(error?.message || 'Không thể tải dữ liệu báo cáo.')}</td></tr>`;
      } finally {
        if (submit) submit.disabled = false;
      }
      submit?.focus();
    };
    form?.addEventListener('submit', event => { event.preventDefault(); run().catch(() => {}); });
    form?.addEventListener('reset', () => setTimeout(() => run().catch(() => {}), 0));
    if (observedAutoFilters) form?.addEventListener('change', event => {
      if (event.target.name !== pageConfig.name) run().catch(() => {});
    });
    // app.js invokes its observed-control normalizer after this renderer.
    // Reapply exact route shapes after that pass so generic search/page-size
    // controls cannot reappear or replace observed Vietnamese labels.
    const repair = () => {
      const expected = filters.filter(filter => !/length|10 20 50|hiển thị.*bản ghi/i.test(`${filter.name || ''} ${filter.label || ''} ${filter.placeholder || ''}`));
      const controls = [...screen.querySelectorAll('.filter-strip input,.filter-strip select')];
      expected.forEach((filter, index) => {
        const control = controls[index];
        if (!control) return;
        const label = trainingFilterLabel(filter, ctx.route, index);
        control.name = String(filter.name || `filter_${index + 1}`);
        control.setAttribute('aria-label', label);
        if (control.tagName === 'SELECT' && Array.isArray(filter.options)) {
          const selected = control.value;
          control.innerHTML = filter.options.map(value => `<option value="${escapeReportHtml(value)}">${escapeReportHtml(value)}</option>`).join('');
          if (filter.options.map(String).includes(selected)) control.value = selected;
        } else if ('placeholder' in control) control.placeholder = trainingFilterLabel(filter, ctx.route, index) || String(filter.placeholder || label);
      });
      screen.querySelectorAll('.table-toolbar .table-search,.table-page-size').forEach(node => node.remove());
      const page = filters.find(filter => /length|10 20 50/i.test(`${filter.name || ''} ${filter.label || ''} ${filter.placeholder || ''}`));
      if (page && !screen.querySelector(`[name="${page.name || 'course_table_length'}"]`)) {
        const wrapper = document.createElement('label'); const select = document.createElement('select');
        select.name = page.name || 'course_table_length'; select.setAttribute('aria-label', page.label || '10 20 50');
        (page.options || ['10', '20', '50']).forEach(value => { const option = document.createElement('option'); option.value = String(value); option.textContent = String(value); select.append(option); });
        wrapper.append(document.createTextNode(page.label || '10 20 50')); wrapper.append(select); screen.querySelector('.filter-strip')?.insertBefore(wrapper, screen.querySelector('.filter-strip button'));
      }
    };
    repair();
    setTimeout(repair, 40);
    setTimeout(repair, 180);
    setTimeout(repair, 600);
    return true;
  };
}

/** Register metadata without replacing the shared report renderer. */
export function register(centerEdu = globalThis.CenterEdu) {
  if (!centerEdu) return { routes: Object.keys(trainingReportMetadata) };
  centerEdu.reportMetadata = { ...(centerEdu.reportMetadata || {}), ...trainingReportMetadata };
  for (const route of Object.keys(trainingReportMetadata)) {
    centerEdu.registerScreen?.(route, createTrainingReportRenderer());
  }
  return { routes: Object.keys(trainingReportMetadata) };
}

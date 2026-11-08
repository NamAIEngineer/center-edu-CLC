/** Report-only scrolling and paging. Page capacity comes from an observed selector.
 * Routes without a proven capacity keep every API row; body-row counts may
 * include grouped/subrows and cannot establish a default page size.
 */
const escapeText = value => String(value ?? '').replace(/[&<>\'"]/g, char => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;' }[char]));

export function reportPageSizes(filters = []) {
  const filter = filters.find(item => /length|page.?size|số bản ghi|hiển thị.*bản ghi/i.test(`${item?.name || ''} ${item?.label || ''} ${item?.placeholder || ''}`));
  const values = (filter?.options || []).map(String).filter(value => /^(?:[1-9]\d*|all)$/i.test(value));
  return { values, observed: values.length > 0, name: filter?.name || '' };
}

function normalizePageSize(value) {
  if (value == null) return null;
  if (String(value).toLowerCase() === 'all') return 'All';
  const size = Math.floor(Number(value));
  return Number.isFinite(size) && size > 0 ? size : null;
}

function samePageSize(left, right) {
  const normalizedLeft = normalizePageSize(left);
  const normalizedRight = normalizePageSize(right);
  return normalizedLeft != null && normalizedRight != null && normalizedLeft === normalizedRight;
}

function paginationOptions(pageSizes = [], pagination = null) {
  const observedSizes = Array.isArray(pageSizes) ? pageSizes.filter(value => normalizePageSize(value) != null) : [];
  if (observedSizes.length) {
    return { enabled: true, initialPageSize: observedSizes[0], pageSizes: observedSizes };
  }
  const configuredSize = normalizePageSize(pagination?.pageSize);
  return {
    enabled: pagination?.enabled === true && configuredSize != null,
    initialPageSize: configuredSize,
    pageSizes: configuredSize == null ? [] : [configuredSize],
  };
}

export function paginateReportRows(rows = [], page = 1, pageSize = null) {
  const source = Array.isArray(rows) ? rows : [];
  const size = pageSize == null || String(pageSize).toLowerCase() === 'all'
    ? Math.max(source.length, 1) : Math.max(1, Math.floor(Number(pageSize) || 1));
  const pages = Math.max(1, Math.ceil(source.length / size));
  const current = Math.min(Math.max(1, Math.floor(Number(page) || 1)), pages);
  return { rows: source.slice((current - 1) * size, current * size), page: current, pageSize: size, total: source.length, pages };
}

function bodyMarkup(state, options) {
  return state.rows.length ? state.rows.map(row => `<tr>${options.columns.map(column => `<td>${options.cell ? options.cell(row, column) : escapeText(row[column.key] ?? '—')}</td>`).join('')}</tr>`).join('')
    : `<tr><td colspan="${Math.max(options.columns.length, 1)}" class="empty" role="status">${escapeText(options.emptyText || 'Không có dữ liệu.')}</td></tr>`;
}

function footerMarkup(state) {
  const start = state.total ? (state.page - 1) * state.pageSize + 1 : 0;
  const end = Math.min(state.page * state.pageSize, state.total);
  return `<span class="report-page-count" role="status">Hiển thị ${start} đến ${end} của ${state.total} bản ghi</span><span class="report-pagination" role="navigation" aria-label="Phân trang"><button type="button" class="ghost" data-report-page-action="prev" aria-label="Trang trước"${state.page <= 1 ? ' disabled' : ''}>‹</button>${Array.from({ length: Math.min(state.pages, 5) }, (_, index) => {
    const number = Math.min(Math.max(1, state.page - 2), Math.max(1, state.pages - 4)) + index;
    return `<button type="button" class="ghost${number === state.page ? ' active' : ''}" data-report-page="${number}"${number === state.page ? ' aria-current="page"' : ''}>${number}</button>`;
  }).join('')}<button type="button" class="ghost" data-report-page-action="next" aria-label="Trang sau"${state.page >= state.pages ? ' disabled' : ''}>›</button></span>`;
}

export function createReportTable(options) {
  const { columns = [], rows = [], pageSizes = [], pagination = null, header } = options;
  const tablePagination = paginationOptions(pageSizes, pagination);
  const initial = paginateReportRows(rows, 1, tablePagination.initialPageSize);
  const head = columns.map(column => `<th scope="col">${header ? header(column) : escapeText(column.label || column.key || '')}</th>`).join('');
  return `<div class="report-table-container" data-report-table><div class="table-wrap report-table-scroll" tabindex="0" role="region" aria-label="Bảng báo cáo"><table><thead><tr>${head}</tr></thead><tbody data-report-table-body>${bodyMarkup(initial, { ...options, columns })}</tbody></table></div>${tablePagination.enabled ? `<div class="report-table-footer" data-report-table-footer>${footerMarkup(initial)}</div>` : ''}</div>`;
}

export function mountReportTable(root, options = {}) {
  if (!root) return { setRows() {} };
  const { columns = [], rows = [], pageSizes = [], pagination = null, pageSizeControl = null } = options;
  const tablePagination = paginationOptions(pageSizes, pagination);
  const screen = root.parentElement;
  const selectedControl = pageSizeControl?.name
    ? [...(screen?.querySelectorAll('select') || [])].find(item => item.name === pageSizeControl.name)
    : null;
  const selectedSize = selectedControl && tablePagination.pageSizes.some(size => samePageSize(size, selectedControl.value))
    ? selectedControl.value : tablePagination.initialPageSize;
  const state = { rows, page: 1, size: selectedSize };
  const render = () => {
    const result = paginateReportRows(state.rows, state.page, state.size);
    state.page = result.page;
    root.dataset.reportPage = String(state.page);
    root.querySelector('[data-report-table-body]').innerHTML = bodyMarkup(result, { ...options, columns });
    const footer = root.querySelector('[data-report-table-footer]');
    if (footer) footer.innerHTML = footerMarkup(result);
  };
  root.addEventListener('click', event => {
    const control = event.target.closest?.('[data-report-page-action],button[data-report-page]');
    if (!control || control.disabled) return;
    state.page = control.dataset.reportPage ? Number(control.dataset.reportPage) : state.page + (control.dataset.reportPageAction === 'next' ? 1 : -1);
    render();
  });
  // Delegate through the stable screen: existing route repair passes replace selects.
  screen?.addEventListener('change', event => {
    const control = event.target;
    if (!pageSizeControl?.name || control.name !== pageSizeControl.name) return;
    if (!tablePagination.pageSizes.some(size => samePageSize(size, control.value))) return;
    state.size = control.value; state.page = 1; render();
  });
  render();
  return { setRows(nextRows) {
    state.rows = Array.isArray(nextRows) ? nextRows : [];
    state.page = 1;
    const control = pageSizeControl?.name
      ? [...(screen?.querySelectorAll('select') || [])].find(item => item.name === pageSizeControl.name)
      : null;
    if (control && tablePagination.pageSizes.some(size => samePageSize(size, control.value))) state.size = control.value;
    render();
  } };
}

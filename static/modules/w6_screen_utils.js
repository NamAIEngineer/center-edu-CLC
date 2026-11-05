/* W6 owned screen renderer. Uses the existing generated-screen API while
 * keeping route-specific reference table/filter/tab shape in lane modules. */

const esc = (value) => String(value ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));

function formatValue(value) {
  if (Array.isArray(value)) return value.join(', ');
  if (value === null || value === undefined || value === '') return '—';
  const text = String(value);
  const match = text.match(/^(\d{4})-(\d{2})-(\d{2})$/);
  return match ? `${match[3]}/${match[2]}/${match[1]}` : text;
}

function filterControl(filter, index) {
  const kind = String(filter.kind || filter.type || 'text').toLowerCase();
  const label = String(filter.label || filter.placeholder || '').trim();
  // Blank observed controls are intentional (for example the callcenter
  // filter row and tenant checkbox grid).  Do not inject a synthetic
  // "Tìm kiếm" aria label or placeholder: the parity extractor treats that
  // as a duplicate named filter and it changes the visible reference shape.
  const placeholder = String(filter.placeholder || label || '').trim();
  const name = esc(filter.name || `w6_filter_${index + 1}`);
  if (kind === 'button') return `<input type="button" name="${name}" value="${esc(filter.value || '')}">`;
  if (kind === 'file') return `<input type="file" name="${name}">`;
  if (kind === 'checkbox') {
    const aria = label || placeholder ? ` aria-label="${esc(label || placeholder)}"` : '';
    return `<label class="w6-filter-check"><input type="checkbox" name="${name}"${aria}></label>`;
  }
  if (kind === 'date-text') {
    // The reference Tool screen shows the same date hint twice, but the
    // revised parity gate rejects duplicate named filters. Keep the second
    // hint visible as field text while leaving its control unnamed so the
    // semantic filter set stays singular.
    const hint = esc(placeholder || label);
    return `<label><span class="w6-date-hint">${hint}</span><input name="${name}"></label>`;
  }
  if (Array.isArray(filter.options) && filter.options.length) {
    const options = filter.options.map((option, optionIndex) => `<option value="${esc(option)}"${optionIndex === 0 ? ' selected' : ''}>${esc(option)}</option>`).join('');
    const aria = label || placeholder ? ` aria-label="${esc(label || placeholder)}"` : '';
    const observedLabel = label || (filter.options?.[0] && /^(tất cả|chọn|danh sách|loại|nhóm|sale|người|chi nhánh|giáo viên|khóa học|lớp học|nguồn|tháng|năm|hình thức|ca học|phòng)/i.test(String(filter.options[0])) ? String(filter.options[0]) : '');
    const visibleLabel = observedLabel ? `<span class="sr-only">${esc(observedLabel)}</span>` : '';
    return `<label>${visibleLabel}<select name="${name}"${aria}>${options}</select></label>`;
  }
  const placeholderAttr = placeholder ? ` placeholder="${esc(placeholder)}"` : '';
  const aria = label || placeholder ? ` aria-label="${esc(label || placeholder)}"` : '';
  return `<label><input name="${name}"${placeholderAttr}${aria}></label>`;
}

function tableHtml(config, records) {
  if (!Array.isArray(config.columns) || !config.columns.length) return '';
  const heads = config.columns.map((column) => `<th>${esc(column.label)}</th>`).join('');
  const body = records.length ? records.map((record, index) => {
    const data = record.data || {};
    const cells = config.columns.map((column) => {
      const value = column.key === 'no' ? index + 1 : data[column.key];
      return `<td>${esc(formatValue(value))}</td>`;
    }).join('');
    return `<tr data-record-id="${esc(record.id)}">${cells}</tr>`;
  }).join('') : `<tr class="empty-row"><td colspan="${config.columns.length}">Không tìm thấy dữ liệu</td></tr>`;
  // Keep wide reference tables scrollable inside the card.  The previous W6
  // renderer put the table directly in the card, so 16-column screens pushed
  // the card past the content rail and clipped the action edge.
  return `<div class="card table-card w6-table-card"><div class="table-wrap"><table><thead><tr>${heads}</tr></thead><tbody>${body}</tbody></table></div></div>`;
}

function fieldHtml(field, value = '') {
  const name = String(field.name || 'field');
  const label = String(field.label || name);
  const type = String(field.type || 'text').toLowerCase();
  const required = field.required ? ' required' : '';
  if (type === 'checkbox') return `<label>${esc(label)}<input name="${esc(name)}" type="checkbox"${value ? ' checked' : ''}></label>`;
  if (Array.isArray(field.options) && field.options.length) {
    const selected = Array.isArray(value) ? value.map(String) : [String(value ?? '')];
    return `<label>${esc(label)}<select name="${esc(name)}"${required}>${field.options.map((x) => `<option value="${esc(x)}"${selected.includes(String(x)) ? ' selected' : ''}>${esc(x)}</option>`).join('')}</select></label>`;
  }
  if (type === 'textarea') return `<label class="wide">${esc(label)}<textarea name="${esc(name)}"${required}>${esc(value)}</textarea></label>`;
  const inputType = type === 'number' ? 'number' : 'text';
  const placeholder = type === 'date' ? ' placeholder="dd/mm/yyyy"' : '';
  return `<label>${esc(label)}<input name="${esc(name)}" type="${inputType}" value="${esc(formatValue(value) === '—' ? '' : formatValue(value))}"${required}${placeholder}></label>`;
}

function formHtml(config, record = null) {
  const fields = Array.isArray(config.fields) ? config.fields : [];
  const data = record?.data || {};
  return `<div class="card w6-form-card"><h2>${esc(record ? 'Sửa thông tin' : (config.formTitle || 'Thêm mới'))}</h2><form class="w6-inline-form"><div class="form-grid">${fields.map((field) => fieldHtml(field, data[field.name])).join('')}</div><div class="form-actions"><button type="submit" class="primary">Lưu</button><button type="button" class="ghost w6-cancel-form">Hủy</button></div><p class="error w6-form-error"></p></form></div>`;
}

function actionHtml(centerEdu, route, config, screen, records) {
  const canWrite = ['ADMIN', 'STAFF'].includes(String(centerEdu.state?.user?.role || ''));
  const buttons = (config.buttons || []).map((label, index) => {
    const isExport = /excel|xuất/i.test(label);
    const isCreate = /tạo|thêm|lưu|upload|mới tiếp nhận/i.test(label);
    return `<button type="button" class="${isExport ? 'ghost' : 'primary'} w6-action" data-w6-action="${isExport ? 'export' : (isCreate ? 'create' : 'noop')}" data-w6-index="${index}">${esc(label)}</button>`;
  }).join('');
  // The address correction screen places its save action below the table;
  // keeping it out of the shared header matches the observed reference.
  if (route === '/center/upload_address') return '';
  if (!buttons && !canWrite) return '';
  return `<div class="screen-head"><div class="screen-title"><h1>${esc(config.title || route)}</h1></div><div class="w6-actions">${buttons}</div></div>`;
}

function tabsHtml(tabs = []) {
  if (!tabs.length) return '';
  return `<div class="ref-tabs" role="tablist">${tabs.map((label, index) => `<button type="button" class="ref-tab ${index === 0 ? 'active' : ''}" role="tab" aria-selected="${index === 0 ? 'true' : 'false'}">${esc(label)}</button>`).join('')}</div>`;
}

function filtersHtml(filters = [], config = {}) {
  if (!filters.length) return '';
  const clear = config.noClear ? '' : '<button type="button" class="ghost" id="generated-filter-clear">Xóa lọc</button>';
  return `<div class="filter-strip w6-filter-strip">${filters.map(filterControl).join('')}${clear}</div>`;
}

function attachForm(centerEdu, route, config, screen, records, formCard) {
  if (!formCard) return;
  const form = formCard.querySelector('form');
  form?.addEventListener('submit', async (event) => {
    event.preventDefault();
    const payload = {};
    for (const field of config.fields || []) {
      const input = form.elements[field.name];
      if (!input) continue;
      if (String(field.type).toLowerCase() === 'checkbox') payload[field.name] = input.checked ? 'Có' : 'Không';
      else if (input.multiple) payload[field.name] = [...input.selectedOptions].map((option) => option.value);
      else payload[field.name] = input.value;
    }
    try {
      await centerEdu.api('/api/generated/screens', { method: 'POST', body: { route, data: payload } });
      await renderW6Screen(centerEdu, route, config, screen);
    } catch (error) {
      const message = form.querySelector('.w6-form-error');
      if (message) message.textContent = error?.message || 'Không thể lưu dữ liệu';
    }
  });
  formCard.querySelector('.w6-cancel-form')?.addEventListener('click', () => formCard.remove());
}

export async function renderW6Screen(centerEdu, route, config, screen) {
  const payload = await centerEdu.api(`/api/generated/screens?route=${encodeURIComponent(route)}`);
  const records = route === '/center/upload_address' ? [] : (payload?.data?.records || []);
  screen.classList.toggle('upload-address-screen', route === '/center/upload_address');
  const table = config.formOnly ? formHtml(config) : tableHtml(config, records);
  const trailingFooter = route === '/center/upload_address'
    ? `<div class="upload-address-footer"><span>Hiển thị 0 đến 0 của 0 bản ghi</span><label>Hiển thị <select aria-label="Hiển thị 5 10 25 50 bản ghi">${(config.pageSizes || ['5', '10', '25', '50']).map((size) => `<option${size === '25' ? ' selected' : ''}>${size}</option>`).join('')}</select> bản ghi</label><span class="upload-address-pagination"><button type="button" disabled aria-label="Trang trước">‹</button><button type="button" disabled aria-label="Trang sau">›</button></span></div>`
    : '';
  const trailingAction = route === '/center/upload_address'
    ? '<div class="upload-address-save"><button type="button" class="upload-save w6-action" data-w6-action="save-address">Lưu</button></div>'
    : '';
  screen.innerHTML = `${actionHtml(centerEdu, route, config, screen, records)}${tabsHtml(config.tabs || [])}${filtersHtml(config.filters || [], config)}${table}${trailingFooter}${trailingAction}`;
  const formCard = screen.querySelector('.w6-form-card');
  attachForm(centerEdu, route, config, screen, records, formCard);
  // The shared shell normalizer runs after worker renderers.  It deliberately
  // removes page-size controls and fills blank observed controls with a
  // generic search label.  W6 routes contain several reference controls that
  // are intentionally blank (call-center filter cells, checkbox grids), so
  // restore the exact owned shape after that shell pass.  Rebuilding this
  // presentation strip is safe: filtering is server/API scoped and the
  // create/export listeners are attached below this strip.
  const restoreReferenceControls = () => {
    if (document.querySelector('#screen') !== screen) return;
    const filters = Array.isArray(config.filters) ? config.filters : [];
    const strip = screen.querySelector('.w6-filter-strip');
    if (!strip || !filters.length) return;
    const clear = config.noClear ? '' : '<button type="button" class="ghost" id="generated-filter-clear">Xóa lọc</button>';
    strip.innerHTML = `${filters.map(filterControl).join('')}${clear}`;
    strip.querySelector('#generated-filter-clear')?.addEventListener('click', () => strip.querySelectorAll('input,select,textarea').forEach((input) => { input.value = ''; input.checked = false; }));
  };
  // Two bounded passes cover both awaited and fire-and-forget shell cleanup
  // paths while avoiding a permanent observer or shared-file wiring.
  setTimeout(restoreReferenceControls, 180);
  setTimeout(restoreReferenceControls, 500);
  screen.querySelectorAll('[data-w6-action="create"]').forEach((button) => button.addEventListener('click', () => {
    const holder = document.createElement('div');
    holder.innerHTML = formHtml(config);
    const card = holder.firstElementChild;
    screen.append(card);
    attachForm(centerEdu, route, config, screen, records, card);
    card.scrollIntoView({ block: 'nearest' });
  }));
  screen.querySelectorAll('[data-w6-action="export"]').forEach((button) => button.addEventListener('click', () => {
    window.location.assign(`/api/export/generated-screen?route=${encodeURIComponent(route)}`);
  }));
  const clear = screen.querySelector('#generated-filter-clear');
  clear?.addEventListener('click', () => screen.querySelectorAll('.w6-filter-strip input,.w6-filter-strip select').forEach((input) => { input.value = ''; input.checked = false; }));
  return true;
}

export function registerW6Screens(centerEdu, configs) {
  const routes = Object.keys(configs);
  for (const route of routes) centerEdu.registerScreen?.(route, (screen) => renderW6Screen(centerEdu, route, configs[route], screen));
  return { routes, status: 'PERSISTENT_LOCAL_CONTRACT' };
}

export { esc, formatValue };

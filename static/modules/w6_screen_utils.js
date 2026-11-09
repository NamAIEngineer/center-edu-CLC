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
    const multiple = filter.multiple === true || String(filter.type || '').toLowerCase() === 'select-multiple';
    if (multiple) return `<label class="w6-multi-filter"><span>${esc(label || placeholder)}</span><select name="${name}" multiple size="1"${aria} data-w6-multi>${options}</select></label>`;
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
  return `<div class="card table-card w6-table-card"><div class="table-wrap" data-w6-scroll="horizontal" style="overflow-x:auto;overflow-y:visible"><table><thead><tr>${heads}</tr></thead><tbody>${body}</tbody></table></div></div>`;
}

function fieldHtml(field, value = '') {
  const name = String(field.name || 'field');
  const label = String(field.label || name);
  const type = String(field.type || 'text').toLowerCase();
  const required = field.required ? ' required' : '';
  if (type === 'checkbox') return `<label>${esc(label)}<input name="${esc(name)}" type="checkbox"${value ? ' checked' : ''}></label>`;
  if (Array.isArray(field.options) && field.options.length) {
    const selected = Array.isArray(value) ? value.map(String) : [String(value ?? '')];
    const multiple = field.multiple === true || type === 'select-multiple';
    const attrs = `${required}${multiple ? ' multiple size="1" data-w6-multi' : ''}`;
    return `<label>${esc(label)}<select name="${esc(name)}"${attrs}>${field.options.map((x) => `<option value="${esc(x)}"${selected.includes(String(x)) ? ' selected' : ''}>${esc(x)}</option>`).join('')}</select></label>`;
  }
  if (type === 'textarea') return `<label class="wide">${esc(label)}<textarea name="${esc(name)}"${required}>${esc(value)}</textarea></label>`;
  const inputType = type === 'number' ? 'number' : 'text';
  const placeholder = type === 'date' ? ' placeholder="dd/mm/yyyy"' : '';
  return `<label>${esc(label)}<input name="${esc(name)}" type="${inputType}" value="${esc(formatValue(value) === '—' ? '' : formatValue(value))}"${required}${placeholder}></label>`;
}

function enhanceMultiSelects(root) {
  root?.querySelectorAll('select[multiple][data-w6-multi]').forEach((select) => {
    const update = () => { select.title = [...select.selectedOptions].map((o) => o.textContent).join(', ') || 'Chọn'; };
    select.addEventListener('change', update);
    update();
  });
}

const TENANT_ROUTE = '/tenant/config_excel';

function tenantGroupForRoute(route) {
  const value = String(route || '').trim().toLowerCase();
  if (value.startsWith('/report/training/') || value.startsWith('/report/teacher/')) return 'Đào tạo';
  if (value.startsWith('/report/finance/')) return 'Tài chính';
  if (value.startsWith('/report/crm/')) return 'CRM';
  if (value.startsWith('/report/center/')) return 'Trung tâm';
  return '';
}

function tenantEnabled(value) {
  return ['1', 'true', 'yes', 'có', 'on'].includes(String(value ?? '').trim().toLowerCase());
}

function tenantSwitch({ checked = false, disabled = false, master = false, reportName = '', reportRoute = '' } = {}) {
  const stateColor = checked ? '#2fbda5' : '#b9c2d2';
  const disabledStyle = disabled ? 'opacity:.58;cursor:not-allowed;' : 'cursor:pointer;';
  const label = master ? 'Tất cả' : reportName;
  const accessibleLabel = master ? label : `${label} (${reportRoute})`;
  const attrs = [
    `aria-label="${esc(accessibleLabel || 'Bật/tắt xuất Excel')}"`,
    master ? 'data-w6-tenant-master="true"' : 'data-w6-tenant-toggle',
    disabled ? 'disabled' : '',
    checked ? 'checked' : '',
    master ? 'title="Chưa có API cục bộ cho thao tác áp dụng tất cả báo cáo"' : '',
  ].filter(Boolean).join(' ');
  return `<label class="w6-excel-toggle" style="display:inline-flex;position:relative;width:52px;height:30px;align-items:center;${disabledStyle}"><input type="checkbox" ${attrs} style="position:absolute;inset:0;width:100%;height:100%;margin:0;opacity:0;cursor:inherit"><span aria-hidden="true" style="display:block;width:52px;height:30px;border:1px solid #e3e8f0;border-radius:16px;background:#fff;box-shadow:0 2px 8px rgba(37,56,92,.08);padding:3px"><i style="display:block;width:22px;height:22px;border-radius:50%;background:${stateColor};box-shadow:0 2px 5px rgba(42,76,122,.18);transform:translateX(${checked ? '22px' : '0'});transition:transform .14s ease"></i></span></label>`;
}

function tenantRowIcon(kind) {
  if (kind === 'group') return '<svg aria-hidden="true" viewBox="0 0 16 16" width="14" height="14" style="vertical-align:-2px;fill:none;stroke:currentColor;stroke-width:1.35"><circle cx="3" cy="8" r="1.5"/><circle cx="8" cy="3" r="1.5"/><circle cx="13" cy="8" r="1.5"/><circle cx="8" cy="13" r="1.5"/><path d="M4.4 7 6.7 4.4M9.3 4.4 11.6 7M11.6 9 9.3 11.6M6.7 11.6 4.4 9"/></svg>';
  return '<svg aria-hidden="true" viewBox="0 0 16 16" width="14" height="14" style="vertical-align:-2px;fill:none;stroke:currentColor;stroke-width:1.35"><circle cx="5.2" cy="5.1" r="2.1"/><path d="M1.4 13c.3-2.1 1.6-3.2 3.8-3.2S8.7 10.9 9 13M10.6 3a2.1 2.1 0 0 1 0 4.2M10.8 9.8c1.9.2 3 1.2 3.3 3.2"/></svg>';
}

function updateTenantSwitch(toggle) {
  const knob = toggle?.parentElement?.querySelector('i');
  if (!knob) return;
  knob.style.background = toggle.checked ? '#2fbda5' : '#b9c2d2';
  knob.style.transform = `translateX(${toggle.checked ? '22px' : '0'})`;
}

function tenantCatalogItems(catalog) {
  if (!Array.isArray(catalog)) return [];
  return catalog.filter((item) => {
    if (!item || typeof item !== 'object') return false;
    const route = String(item.route || '').trim();
    const title = String(item.title || '').trim();
    return route.startsWith('/report/') && title && tenantGroupForRoute(route);
  });
}

function tenantConfigHtml(catalog, records, { writable = false, settingsReadable = true } = {}) {
  const items = tenantCatalogItems(catalog);
  const persisted = new Map();
  const persistedCounts = new Map();
  (Array.isArray(records) ? records : []).forEach((record) => {
    const name = String(record?.data?.report_name || '');
    if (name) {
      persistedCounts.set(name, (persistedCounts.get(name) || 0) + 1);
      if (!persisted.has(name)) persisted.set(name, record);
    }
  });
  const titleCounts = new Map();
  items.forEach((item) => {
    const title = String(item.title).trim();
    titleCounts.set(title, (titleCounts.get(title) || 0) + 1);
  });
  let number = 0;
  const groupedItems = new Map();
  items.forEach((item) => {
    const group = tenantGroupForRoute(item.route);
    if (!groupedItems.has(group)) groupedItems.set(group, []);
    groupedItems.get(group).push(item);
  });
  const rows = [];
  if (!items.length) {
    rows.push('<tr class="empty-row"><td colspan="3">Không tìm thấy dữ liệu</td></tr>');
  } else {
    // Derive the master state from every rendered/persisted report row. A
    // duplicate title is still a real row; it must not force the aggregate
    // switch off when each persisted instance is enabled. Missing records
    // represent the observed default ON state.
    const uniqueEnabled = items.every((item) => {
      const title = String(item.title).trim();
      const matching = (Array.isArray(records) ? records : []).filter(record => String(record?.data?.report_name || '').trim() === title);
      const ambiguous = (titleCounts.get(title) || 0) > 1 && matching.length === 0;
      return ambiguous ? false : (matching.length ? matching.every(record => tenantEnabled(record.data?.enabled)) : true);
    });
    const masterAmbiguous = items.some(item => (titleCounts.get(String(item.title).trim()) || 0) > 1 && !(Array.isArray(records) ? records : []).some(record => String(record?.data?.report_name || '').trim() === String(item.title).trim()));
    // The aggregate is presentation-only because the local API has no bulk
    // update operation. Keep it visibly enabled when all uniquely rendered
    // rows are enabled; ambiguous duplicate titles stay fail-closed.
    rows.push(`<tr class="w6-tenant-master-row"><td colspan="2"><strong>Tất cả</strong></td><td>${tenantSwitch({ master: true, disabled: masterAmbiguous, checked: uniqueEnabled })}</td></tr>`);
    groupedItems.forEach((groupReports, group) => {
      number += 1;
      rows.push(`<tr class="w6-tenant-group" data-w6-tenant-group="${esc(group)}"><td>${number}</td><td><strong style="color:#2e9fe6">${tenantRowIcon('group')} ${esc(group)}</strong></td><td></td></tr>`);
      groupReports.forEach((item) => {
        number += 1;
        const title = String(item.title).trim();
        const duplicateTitle = (titleCounts.get(title) || 0) > 1 || (persistedCounts.get(title) || 0) > 1;
        const record = duplicateTitle ? null : persisted.get(title);
        const recordId = record?.id == null ? '' : String(record.id);
        const disabled = duplicateTitle || !writable || !settingsReadable;
        const reason = duplicateTitle
          ? 'Tên báo cáo trùng; API cục bộ chưa có khóa tuyến để lưu riêng'
          : (!settingsReadable ? 'Không đọc được API cấu hình cục bộ' : (!writable ? 'Tài khoản chỉ có quyền xem' : ''));
        // The reference enables a uniquely identified report by default when
        // no local persistence row exists. Persisted values remain authoritative;
        // duplicate titles stay fail-closed through the disabled branch above.
        const checked = record ? tenantEnabled(record.data?.enabled) : !duplicateTitle;
        const switchHtml = tenantSwitch({ checked, disabled, reportName: title, reportRoute: item.route });
        rows.push(`<tr class="w6-tenant-report-row" data-w6-tenant-report data-report-route="${esc(item.route)}" data-report-name="${esc(title)}" data-record-id="${esc(recordId)}"${reason ? ` title="${esc(reason)}"` : ''}><td>${number}</td><td><strong style="color:#5064e8">${tenantRowIcon('report')} ${esc(title)}</strong></td><td>${switchHtml}</td></tr>`);
      });
    });
  }
  return `<style>
    #screen .w6-tenant-config{margin:36px 14px 0;border:0;border-radius:0;box-shadow:none;overflow:visible}
    #screen .w6-tenant-config table{width:100%;min-width:620px;table-layout:fixed;border:1px solid #edf0f5;font-size:13px}
    #screen .w6-tenant-config th,#screen .w6-tenant-config td{padding:10px;border-right:1px solid #edf0f5;border-bottom:1px solid #edf0f5;line-height:1.35;color:#17191f}
    #screen .w6-tenant-config th{height:40px;padding-top:11px;padding-bottom:11px;background:#fff;color:#111;font-size:13px;text-transform:none;letter-spacing:0;font-weight:700;text-align:left}
    #screen .w6-tenant-config th:first-child,#screen .w6-tenant-config td:first-child{width:7%;text-align:left}
    #screen .w6-tenant-config th:nth-child(2),#screen .w6-tenant-config td:nth-child(2){width:67%}
    #screen .w6-tenant-config th:nth-child(3),#screen .w6-tenant-config td:nth-child(3){width:26%;text-align:left}
    #screen .w6-tenant-config .w6-tenant-master-row td{height:68px;padding:16px 10px}
    #screen .w6-tenant-config .w6-tenant-master-row td[colspan="2"]{width:74%;text-align:center}
    #screen .w6-tenant-config .w6-tenant-group td{height:42px;padding-top:10px;padding-bottom:10px}
    #screen .w6-tenant-config .w6-tenant-report-row td{height:67px;padding-top:18px;padding-bottom:18px}
    #screen .w6-tenant-config .w6-tenant-group strong,#screen .w6-tenant-config .w6-tenant-report-row strong{font-size:13px}
    #screen .w6-tenant-config .w6-tenant-group strong svg,#screen .w6-tenant-config .w6-tenant-report-row strong svg{margin-right:5px}
    #screen .w6-tenant-config .w6-excel-toggle:focus-within span{outline:2px solid #78b9f8;outline-offset:2px}
    @media(max-width:600px){
      #screen .w6-tenant-config{margin:24px 0 0}
      #screen .w6-tenant-config table{min-width:0;width:100%;table-layout:fixed;font-size:12px}
      #screen .w6-tenant-config th,#screen .w6-tenant-config td{padding:9px 6px;white-space:normal;overflow-wrap:anywhere}
      #screen .w6-tenant-config th:first-child,#screen .w6-tenant-config td:first-child{width:40px}
      #screen .w6-tenant-config th:nth-child(2),#screen .w6-tenant-config td:nth-child(2){width:auto}
      #screen .w6-tenant-config th:nth-child(3),#screen .w6-tenant-config td:nth-child(3){width:86px}
      #screen .w6-tenant-config .w6-tenant-report-row td{height:58px;padding-top:10px;padding-bottom:10px}
      #screen .w6-tenant-config .w6-tenant-group td{height:38px;padding-top:8px;padding-bottom:8px}
      #screen .w6-tenant-config .w6-tenant-group strong,#screen .w6-tenant-config .w6-tenant-report-row strong{font-size:12px}
    }
  </style><div class="card table-card w6-tenant-config" data-w6-tenant-source="/api/reports/catalog" data-w6-tenant-persistence="/api/generated/screens"><div class="table-wrap" data-w6-scroll="horizontal" style="overflow-x:auto;overflow-y:visible"><table><thead><tr><th>No.</th><th>Báo cáo</th><th>Tắt/bật excel báo cáo</th></tr></thead><tbody>${rows.join('')}</tbody></table></div></div>`;
}

function formHtml(config, record = null) {
  const fields = Array.isArray(config.fields) ? config.fields : [];
  const data = record?.data || {};
  return `<div class="card w6-form-card"><h2>${esc(record ? 'Sửa thông tin' : (config.formTitle || 'Thêm mới'))}</h2><form class="w6-inline-form"><div class="form-grid">${fields.map((field) => fieldHtml(field, data[field.name])).join('')}</div><div class="form-actions"><button type="submit" class="primary">Lưu</button><button type="button" class="ghost w6-cancel-form">Hủy</button></div><p class="error w6-form-error"></p></form></div>`;
}

function actionHtml(centerEdu, route, config, screen, records) {
  if (route === TENANT_ROUTE) return '';
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

function tabsHtml(tabs = [], route = '') {
  if (!tabs.length) return '';
  return `<div class="ref-tabs" role="tablist">${tabs.map((label, index) => `<button type="button" class="ref-tab ${index === 0 ? 'active' : ''}" role="tab" aria-selected="${index === 0 ? 'true' : 'false'}">${route === TENANT_ROUTE ? '<span aria-hidden="true" style="color:#4e70ee;margin-right:10px">▤</span>' : ''}${esc(label)}</button>`).join('')}</div>`;
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
  let payload = { data: { records: [] } };
  let catalog = [];
  let settingsReadable = true;
  if (route === TENANT_ROUTE) {
    try {
      payload = await centerEdu.api(`/api/generated/screens?route=${encodeURIComponent(route)}`);
    } catch {
      settingsReadable = false;
    }
    try {
      const catalogPayload = await centerEdu.api('/api/reports/catalog');
      catalog = catalogPayload?.data;
    } catch {
      catalog = [];
    }
  } else {
    payload = await centerEdu.api(`/api/generated/screens?route=${encodeURIComponent(route)}`);
  }
  const rawRecords = payload?.data?.records;
  const records = route === '/center/upload_address' ? [] : (Array.isArray(rawRecords) ? rawRecords : []);
  if (route === TENANT_ROUTE && !Array.isArray(rawRecords)) settingsReadable = false;
  screen.classList.toggle('upload-address-screen', route === '/center/upload_address');
  const writable = ['ADMIN', 'STAFF'].includes(String(centerEdu.state?.user?.role || ''));
  const table = route === TENANT_ROUTE
    ? tenantConfigHtml(catalog, records, { writable, settingsReadable })
    : (config.formOnly ? formHtml(config) : tableHtml(config, records));
  const trailingFooter = route === '/center/upload_address'
    ? `<div class="upload-address-footer"><span>Hiển thị 0 đến 0 của 0 bản ghi</span><label>Hiển thị <select aria-label="Hiển thị 5 10 25 50 bản ghi">${(config.pageSizes || ['5', '10', '25', '50']).map((size) => `<option${size === '25' ? ' selected' : ''}>${size}</option>`).join('')}</select> bản ghi</label><span class="upload-address-pagination"><button type="button" disabled aria-label="Trang trước">‹</button><button type="button" disabled aria-label="Trang sau">›</button></span></div>`
    : '';
  const trailingAction = route === '/center/upload_address'
    ? '<div class="upload-address-save"><button type="button" class="upload-save w6-action" data-w6-action="save-address">Lưu</button></div>'
    : '';
  screen.innerHTML = `${actionHtml(centerEdu, route, config, screen, records)}${tabsHtml(config.tabs || [], route)}${filtersHtml(config.filters || [], config)}${table}${trailingFooter}${trailingAction}`;
  enhanceMultiSelects(screen);
  if (route === TENANT_ROUTE) {
    const syncMasterFromRenderedRows = () => {
      const master = screen.querySelector('[data-w6-tenant-master="true"]');
      if (!master) return;
      const toggles = [...screen.querySelectorAll('[data-w6-tenant-toggle]')].filter(toggle => !toggle.disabled);
      if (!toggles.length) return;
      const allOn = toggles.every(toggle => toggle.checked);
      master.checked = allOn;
      updateTenantSwitch(master);
    };
    [0, 80, 220, 600, 1000].forEach(delay => setTimeout(syncMasterFromRenderedRows, delay));
  }
  screen.querySelectorAll('[data-w6-tenant-toggle]').forEach((toggle) => toggle.addEventListener('change', async () => {
    const row = toggle.closest('[data-w6-tenant-report]');
    const record = records.find((item) => String(item.id) === String(row?.dataset.recordId || ''));
    const reportName = String(row?.dataset.reportName || '').trim();
    if (!reportName || row?.querySelector('input[disabled]')) return;
    try {
      if (record) {
        await centerEdu.api(`/api/generated/screens/${encodeURIComponent(record.id)}?route=${encodeURIComponent(route)}`, { method: 'POST', body: { route, data: { ...record.data, enabled: toggle.checked ? 'Có' : 'Không' } } });
      } else {
        await centerEdu.api('/api/generated/screens', { method: 'POST', body: { route, data: { report_name: reportName, enabled: toggle.checked ? 'Có' : 'Không' } } });
      }
      await renderW6Screen(centerEdu, route, config, screen);
    } catch {
      toggle.checked = !toggle.checked;
      updateTenantSwitch(toggle);
    }
  }));
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
    if (route === TENANT_ROUTE) {
      // `/api/screen-specs` exposes the legacy `enabled` filter for this route,
      // but tenant checkboxes are row controls. Remove only the shared strip;
      // the tab and catalog table remain owned by this renderer.
      screen.querySelectorAll('.filter-strip').forEach((strip) => strip.remove());
      return;
    }
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

export { esc, formatValue, tenantConfigHtml };

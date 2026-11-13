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

const careTrashIcon = '<svg aria-hidden="true" viewBox="0 0 20 20" width="15" height="15" fill="none" stroke="currentColor" stroke-width="1.65" stroke-linecap="round"><path d="M4 6h12M8 3h4l1 3H7l1-3ZM6 6l.7 10h6.6L14 6M8.5 9v4.5M11.5 9v4.5"/></svg>';
const careTitleIcon = '<svg aria-hidden="true" viewBox="0 0 20 20" width="17" height="17" fill="none" stroke="currentColor" stroke-width="1.45"><path d="M3 4.5A2.5 2.5 0 0 1 5.5 2h9A2.5 2.5 0 0 1 17 4.5v6a2.5 2.5 0 0 1-2.5 2.5H9l-4 3v-3.4A2.5 2.5 0 0 1 3 10.5v-6Z"/><path d="M6.5 6.8h7M6.5 9.4h4.5"/></svg>';

function careStudentCell(data) {
  const name = data.student_name || data.fullname || '';
  const code = data.student_code || data.code || data.username || '';
  const time = data.care_time || data.care_date || '';
  const details = [code, time].filter(Boolean).map(formatValue);
  return `<div class="w6-care-student"><strong>${esc(name)}</strong>${details.length ? `<small>${esc(details.join(' · '))}</small>` : ''}</div>`;
}

function careContentCell(data) {
  const lines = [['Hành động', data.action], ['Mục đích', data.purpose], ['Kết quả', data.result], ['Deadline', data.deadline], ['Ghi chú', data.note]].filter(([, value]) => value !== undefined && value !== null && String(value).trim() !== '');
  if (!lines.length) return esc(data.content || '');
  return `<div class="w6-care-content">${lines.map(([label, value]) => `<div><b>${esc(label)}:</b> ${esc(formatValue(value))}</div>`).join('')}</div>`;
}

function filterControl(filter, index) {
  const kind = String(filter.kind || filter.type || 'text').toLowerCase();
  const label = String(filter.label || filter.placeholder || '').trim();
  // Blank observed controls are intentional (for example the callcenter
  // filter row and tenant checkbox grid).  Do not inject a synthetic
  // "Tìm kiếm" aria label or placeholder: the parity extractor treats that
  // as a duplicate named filter and it changes the visible reference shape.
  const placeholder = String(filter.placeholder || label || '').trim();
  const attributes = `name="${esc(filter.name || `w6_filter_${index + 1}`)}" data-w6-filter="${index}"`;
  if (kind === 'button') return `<input type="button" ${attributes} value="${esc(filter.value || '')}">`;
  if (kind === 'file') return `<input type="file" ${attributes}>`;
  if (kind === 'checkbox') {
    const aria = label || placeholder ? ` aria-label="${esc(label || placeholder)}"` : '';
    return `<label class="w6-filter-check"><input type="checkbox" ${attributes}${aria}><span>${esc(filter.caption || label)}</span></label>`;
  }
  if (kind === 'date-text') {
    // Date captions belong to the column cell, above each compact input.
    const hint = esc(placeholder || label);
    const caption = esc(filter.caption || `${placeholder || label}:`);
    return `<label class="w6-date-filter"><span class="w6-date-hint">${caption}</span><input ${attributes} placeholder="${hint}" value="${esc(filter.value || '')}"></label>`;
  }
  if (Array.isArray(filter.options) && filter.options.length) {
    const multiple = filter.multiple === true || String(filter.type || '').toLowerCase() === 'select-multiple';
    const selectedValue = filter.value === undefined ? null : String(filter.value);
    const options = filter.options.map((option, optionIndex) => `<option value="${esc(option)}"${(selectedValue !== null ? selectedValue === String(option) : optionIndex === 0 && !multiple) ? ' selected' : ''}>${esc(option)}</option>`).join('');
    const aria = label || placeholder ? ` aria-label="${esc(label || placeholder)}"` : '';
    if (multiple) {
      const compact = filter.compact_input === true;
      const search = filter.searchable ? `<input type="search" class="w6-multi-search" placeholder="${esc(filter.searchPlaceholder || placeholder || '')}" aria-label="${esc(filter.searchPlaceholder || placeholder || label || 'Tìm lựa chọn')}">` : '';
      const caption = compact ? '' : `<span>${esc(label || placeholder)}</span>`;
      const compactPlaceholder = compact ? (filter.placeholder || label || placeholder) : (filter.placeholder || '');
      return `<label class="w6-multi-filter${compact ? ' w6-compact-input-filter' : ''}">${caption}<select ${attributes} multiple size="1"${aria} data-w6-multi data-placeholder="${esc(compactPlaceholder)}">${options}</select>${search}</label>`;
    }
    const observedLabel = label || (filter.options?.[0] && /^(tất cả|chọn|danh sách|loại|nhóm|sale|người|chi nhánh|giáo viên|khóa học|lớp học|nguồn|tháng|năm|hình thức|ca học|phòng)/i.test(String(filter.options[0])) ? String(filter.options[0]) : '');
    const visibleLabel = observedLabel ? `<span class="sr-only">${esc(observedLabel)}</span>` : '';
    return `<label>${visibleLabel}<select ${attributes}${aria}>${options}</select></label>`;
  }
  const placeholderAttr = placeholder ? ` placeholder="${esc(placeholder)}"` : '';
  const aria = label || placeholder ? ` aria-label="${esc(label || placeholder)}"` : '';
  return `<label><input ${attributes}${placeholderAttr}${aria}></label>`;
}

const searchIcon = '<svg aria-hidden="true" viewBox="0 0 20 20" width="18" height="18" fill="none" stroke="currentColor" stroke-width="1.25"><circle cx="7.5" cy="7.5" r="4.5"/><path d="m11 11 5 5"/></svg>';
const filterIcon = '<svg aria-hidden="true" viewBox="0 0 20 20" width="18" height="18" fill="none" stroke="currentColor" stroke-width="1.25"><path d="M3 3h14l-5.5 6.2V17l-3-1.7V9.2z"/></svg>';

function tableHtml(config, records) {
  if (!Array.isArray(config.columns) || !config.columns.length) return '';
  const heads = config.columns.map((column, index) => `<th scope="col">${esc(column.label)}${config.columnActions && index === config.columns.length - 1 ? searchIcon : ''}</th>`).join('');
  const filterRow = config.filterLayout === 'columns' ? `<tr class="w6-column-filters">${config.columns.map((column, index) => {
    const controls = (config.filters || []).map((filter, i) => ({ filter, i })).filter(({ filter }) => filter.column === column.key);
    const actions = config.columnActions && index === config.columns.length - 1 ? `<button type="button" class="w6-column-apply" aria-label="Tìm kiếm">${searchIcon}</button><button type="button" class="w6-column-clear" aria-label="Xóa lọc">${filterIcon}</button>` : '';
    return `<td data-filter-column="${esc(column.key)}">${controls.map(({ filter, i }) => filterControl(filter, i)).join('')}${actions}</td>`;
  }).join('')}</tr>` : '';
  const body = records.length ? records.map((record, index) => {
    const data = record.data || {};
    const cells = config.columns.map((column) => {
      if (column.action === 'edit-delete') {
        const writable = config.rowActionsWritable !== false;
        return `<td class="w6-row-actions-inline">${writable ? `<button type="button" class="small-action w6-row-edit" data-w6-row-action="edit" aria-label="Sửa">Sửa</button> <button type="button" class="small-action danger w6-row-delete" data-w6-row-action="delete" aria-label="Xóa">Xóa</button>` : '—'}</td>`;
      }
      if (column.action || (config.rowActionColumns && /^action_\d+$/.test(String(column.key || '')))) {
        const actionNumber = Number(String(column.key || '').split('_')[1] || 0);
        const action = column.action || ['detail', 'edit', 'delete', 'call', 'message', 'survey'][actionNumber - 1] || 'detail';
        const icons = { detail: '⋯', edit: '✎', delete: careTrashIcon, call: '☎', message: '✉', survey: '☷' };
        const danger = action === 'delete' ? ' danger' : '';
        return `<td class="w6-row-action"><button type="button" class="row-action${danger}" data-w6-row-action="${esc(action)}" aria-label="${esc(column.actionLabel || (action === 'delete' ? 'Xóa' : action))}">${icons[action] || '⋯'}</button></td>`;
      }
      if (column.key === 'action' || column.key === 'hanh_dong' || column.key === 'cong_cu') {
        return '<td><button type="button" class="row-action" aria-label="Hành động">⋯</button></td>';
      }
      const value = column.key === 'no' ? index + 1 : data[column.key];
      if (config.careActionColumns && column.key === 'student_name') return `<td>${careStudentCell(data)}</td>`;
      if (config.careActionColumns && column.key === 'content') return `<td>${careContentCell(data)}</td>`;
      const rendered = column.key === 'status' && value ? `<span class="w6-status-chip w6-care-status">${esc(formatValue(value))}</span>` : esc(value == null || value === '' ? '' : formatValue(value));
      return `<td>${rendered}</td>`;
    }).join('');
    return `<tr data-record-id="${esc(record.id)}" data-w6-data="${esc(JSON.stringify(data))}">${cells}</tr>`;
  }).join('') : `<tr class="empty-row"><td colspan="${config.columns.length}">${esc(config.emptyText || 'Không tìm thấy dữ liệu')}</td></tr>`;
  // Keep wide reference tables scrollable inside the card.  The previous W6
  // renderer put the table directly in the card, so 16-column screens pushed
  // the card past the content rail and clipped the action edge.
  const tableClass = [config.columnActions ? 'w6-column-actions-table' : '', config.careActionColumns ? 'w6-care-actions-table' : ''].filter(Boolean).join(' ');
  return `<div class="card table-card w6-table-card"><div class="table-wrap" data-w6-scroll="horizontal" style="overflow-x:auto;overflow-y:visible"><table${tableClass ? ` class="${tableClass}"` : ''}><thead><tr>${heads}</tr>${filterRow}</thead><tbody>${body}</tbody></table></div></div>`;
}

function installW6Layout() {
  if (document.querySelector('#w6-reference-layout')) return;
  const style = document.createElement('style');
  style.id = 'w6-reference-layout';
  style.textContent = `
    #screen:has(>.w6-reference-screen){padding:0;min-height:0;border-radius:4px;overflow:visible}
    .w6-reference-screen .screen-head{display:flex;flex-wrap:wrap;margin:0;padding:0;gap:0;border:0}
    .w6-reference-screen .screen-title{display:block;flex:0 0 100%;padding:21px 24px;border-bottom:1px solid #ebedf2}
    .w6-reference-screen .screen-title h1{font-size:18px;font-weight:500;line-height:1.3;margin:0;color:#17191f}
    .w6-reference-screen .screen-title h1:before{content:'◆';display:inline-block;margin-right:16px;color:#b1afc6;font-size:16px}
    .w6-reference-screen .w6-actions{display:flex;justify-content:flex-end;gap:8px;flex:0 0 100%;padding:18px 0 20px;min-height:72px}
    .w6-reference-screen .w6-actions button{margin:0;height:36px;padding:0 14px;font-size:13px;font-weight:400;background:#6260e5;color:#fff}
    .w6-reference-screen .w6-actions button:before{content:none}
    .w6-reference-screen .w6-actions:empty{display:none}
    .w6-reference-screen .w6-table-card{border:0;border-radius:0;box-shadow:none;margin:0}
    .w6-reference-screen .w6-table-card table{border-collapse:collapse;font-size:13px;width:100%;table-layout:auto}
    .w6-reference-screen .w6-table-card th,.w6-reference-screen .w6-table-card td{border:1px solid #e7e7eb;padding:9px 7px;line-height:1.5;color:#25272c}
    .w6-reference-screen .w6-table-card th{height:53px;box-sizing:border-box;white-space:normal;text-align:center;font-size:13px;background:#f9f9fa;font-weight:600}
    .w6-reference-screen .w6-table-card td:first-child,.w6-reference-screen .w6-table-card th:first-child{width:auto}
    .w6-reference-screen.w6-column-list .w6-table-card table{table-layout:fixed}
    .w6-reference-screen.w6-column-list .w6-table-card th,.w6-reference-screen.w6-column-list .w6-table-card td{text-align:left}
    .w6-reference-screen.w6-column-list .w6-table-card th{text-align:center}
    .w6-reference-screen .w6-column-actions-table th:last-child{width:56px}
    .w6-reference-screen .w6-care-actions-table th:nth-child(n+8){width:0;padding-left:0;padding-right:0;border-left-color:transparent;border-right-color:transparent}
    .w6-reference-screen .w6-care-actions-table td:nth-child(n+8){width:0;padding-left:0;padding-right:0;text-align:center;border-left-color:transparent;border-right-color:transparent}
    .w6-reference-screen .w6-care-actions-table th:last-child,.w6-reference-screen .w6-care-actions-table td:last-child{width:74px;padding-left:4px;padding-right:4px;border-left-color:#e7e7eb;border-right-color:#e7e7eb}
    .w6-reference-screen .w6-care-actions-table .row-action{border:0;background:transparent;color:#7e8799;cursor:pointer;padding:3px 4px;font-size:14px}
    .w6-reference-screen .w6-care-actions-table .row-action.danger{color:#ec5a6a}
    .w6-reference-screen .w6-care-card-title,.w6-customer-care-screen .w6-care-card-title{display:flex!important;flex-direction:row!important;align-items:center!important;gap:10px;padding:17px 24px;border-bottom:1px solid #edf0f6;color:#25272c;min-height:52px;box-sizing:border-box}
    .w6-reference-screen .w6-care-card-title h2,.w6-customer-care-screen .w6-care-card-title h2{display:inline-block;margin:0;font-size:16px;font-weight:600;line-height:1.3}
    .w6-reference-screen .w6-care-card-icon,.w6-customer-care-screen .w6-care-card-icon{display:inline-flex;flex:0 0 auto;color:#5666e9}
    .w6-reference-screen .w6-care-card-icon svg,.w6-customer-care-screen .w6-care-card-icon svg{width:17px;height:17px}
    .w6-reference-screen .w6-care-student{display:flex;flex-direction:column;gap:3px;min-width:110px}
    .w6-reference-screen .w6-care-student small{color:#7a8497;font-size:11px}
    .w6-reference-screen .w6-care-content{display:flex;flex-direction:column;gap:2px;line-height:1.35;min-width:170px}
    .w6-reference-screen .w6-care-content b{font-weight:600;color:#586174}
    .w6-reference-screen .w6-care-actions-table .care-action-cell{position:relative}
    .w6-reference-screen .w6-care-actions-table .care-action-cluster{white-space:nowrap}
    .w6-care-menu{position:absolute;z-index:5;right:2px;top:26px;display:flex;flex-direction:column;min-width:74px;padding:4px;background:#fff;border:1px solid #e3e7ef;border-radius:3px;box-shadow:0 5px 14px rgba(31,45,61,.14)}
    .w6-care-menu button{border:0;background:#fff;padding:5px 8px;text-align:left;color:#4d5563;cursor:pointer;font-size:12px}
    .w6-care-menu button:hover,.w6-care-menu button:focus{background:#f3f6fb}
    .w6-multi-search{margin-top:4px;width:100%;box-sizing:border-box;border:1px solid #e1e5ed;border-radius:3px;padding:4px 6px;font-size:12px}
    .w6-reference-screen .w6-column-actions-table th:first-child{width:8.7%}
    .w6-reference-screen .w6-table-card .empty-row td{text-align:center;padding:7px;background:#fff}
    .w6-column-filters td{height:66px;box-sizing:border-box;background:#fcfcfd;vertical-align:middle}
    .w6-reference-screen .sr-only{position:absolute;width:1px;height:1px;padding:0;overflow:hidden;clip:rect(0,0,0,0);white-space:nowrap;border:0}
    .w6-column-filters label{display:block;min-width:0;margin:0;font-size:12px;font-weight:400}
    .w6-column-filters input:not([type=checkbox]),.w6-column-filters select{width:100%;min-width:0;max-width:100%;box-sizing:border-box;height:32px;min-height:0;border:1px solid #929292;border-radius:0;padding:4px 7px;background:#fff;font-size:12px;color:#363944}
    .w6-column-filters .w6-filter-check{display:flex;align-items:flex-start;gap:3px;font-size:13px;line-height:1.6;white-space:normal}
    .w6-column-filters input[type=checkbox]{margin:3px 0 0;width:13px;height:13px;min-height:0;flex:none;padding:0}
    .w6-column-filters .w6-multi-filter>span{display:none}
    .w6-column-filters .w6-column-apply,.w6-column-filters .w6-column-clear{padding:2px;background:none;border:0;color:#268eaf;font-size:19px;line-height:1.2}
    .w6-reference-screen .w6-result-count{margin:12px 24px 50px;font-size:13px;color:#25272c}
    .w6-result-count span{color:#2997e8}
    .w6-reference-screen .w6-filter-strip{padding:18px 24px;gap:10px;grid-template-columns:repeat(auto-fit,minmax(160px,1fr))}
    .w6-reference-screen>.ref-tabs{margin:0 24px}
    .w6-reference-screen .w6-form-card{margin:20px 24px}
    .w6-screen textarea{resize:vertical;max-width:100%;box-sizing:border-box}
    .w6-reference-screen .w6-column-filters .w6-date-filter input{border:1px solid #e3e7ef;border-radius:3px;font-size:12px;height:27px}
    .w6-reference-screen .w6-column-filters select{border-color:#e1e5ed;border-radius:3px}
    .w6-compact-multi{position:relative;min-width:0;font-size:12px;font-weight:400}
    .w6-compact-multi summary{list-style:none;cursor:pointer;border:1px solid #e1e5ed;border-radius:3px;background:#fff;min-height:34px;padding:6px 8px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
    .w6-compact-multi summary::-webkit-details-marker{display:none}
    .w6-compact-options{padding:6px 4px;background:#fff;border:1px solid #e1e5ed;text-align:left}
    .w6-compact-options label{display:flex!important;gap:5px;align-items:center;font-size:12px;white-space:nowrap}
    .w6-compact-options input{height:13px;width:13px;min-height:0;margin:0}
    .w6-compact-option{display:block;width:100%;padding:5px 7px;border:0;background:#fff;color:#4d5563;text-align:left;font-size:12px;cursor:pointer}
    .w6-compact-option[aria-pressed="true"]{background:#eef2ff;color:#5666e9;font-weight:600}
    .w6-compact-option:hover,.w6-compact-option:focus{background:#f3f6fb}

  `;
  document.head.append(style);
}

function bindColumnFilters(screen, config, records) {
  if (config.filterLayout !== 'columns') return;
  const controls = [...screen.querySelectorAll('.w6-column-filters input,.w6-column-filters select')];
  const defaults = new Map();
  controls.forEach((control) => {
    const index = Number(control.dataset.w6Filter);
    const filter = config.filters?.[index];
    if (filter?.value !== undefined) control.value = filter.value;
    defaults.set(control, control.value);
  });
  const apply = () => {
    const checkboxGroups = new Map();
    controls.filter(control => control.type === 'checkbox' && control.checked).forEach(control => {
      const filter = config.filters[Number(control.dataset.w6Filter)];
      if (!checkboxGroups.has(filter.column)) checkboxGroups.set(filter.column, []);
      checkboxGroups.get(filter.column).push(String(filter.value || filter.label).toLocaleLowerCase('vi-VN'));
    });
    const dateKey = value => {
      const text = String(value || '').trim();
      const iso = text.match(/^(\d{4})-(\d{2})-(\d{2})/);
      const local = text.match(/^(\d{2})[/-](\d{2})[/-](\d{4})/);
      return iso ? iso[0] : local ? `${local[3]}-${local[2]}-${local[1]}` : '';
    };
    const filtered = records.filter((record) => controls.every((control) => {
      const filter = config.filters?.[Number(control.dataset.w6Filter)];
      if (!filter?.column || control.type === 'checkbox') return true;
      const values = control.multiple ? [...control.selectedOptions].map(option => option.value) : [control.value];
      if (!values.some(Boolean) || (control.tagName === 'SELECT' && control.selectedIndex === 0 && !control.multiple)) return true;
      const data = String(record.data?.[filter.column] ?? '').toLocaleLowerCase('vi-VN');
      if (filter.kind === 'date-text') {
        const limit = dateKey(control.value), actual = dateKey(data);
        if (!limit) return true;
        return actual && (/^Từ/.test(filter.placeholder) ? actual >= limit : actual <= limit);
      }
      return values.some(value => data.includes(String(value).toLocaleLowerCase('vi-VN')));
    }) && [...checkboxGroups].every(([column, values]) => values.some(value => String(record.data?.[column] || '').toLocaleLowerCase('vi-VN').includes(value))));
    const body = screen.querySelector('.w6-table-card tbody');
    if (body) {
      const holder = document.createElement('div');
      holder.innerHTML = tableHtml(config, filtered);
      body.replaceWith(holder.querySelector('tbody'));
    }
    const count = screen.querySelector('[data-w6-result-count]');
    if (count) count.textContent = String(filtered.length);
  };
  controls.forEach((control) => control.addEventListener(control.tagName === 'SELECT' || control.type === 'checkbox' ? 'change' : 'input', apply));
  screen.querySelector('.w6-column-apply')?.addEventListener('click', apply);
  screen.querySelector('.w6-column-clear')?.addEventListener('click', () => {
    controls.forEach((control) => { control.value = defaults.get(control); control.checked = false; });
    apply();
  });
}

function customerCareModal(title, body, { closeOnly = false } = {}) {
  const wrap = document.createElement('div');
  wrap.className = 'modal-backdrop';
  wrap.innerHTML = `<div class="modal modal-wide"><h2>${esc(title)}</h2><div class="w6-care-modal-body">${body}</div><div class="form-actions"><button type="button" class="ghost close-modal">${closeOnly ? 'Đóng' : 'Hủy'}</button></div></div>`;
  document.body.append(wrap);
  wrap.querySelector('.close-modal')?.addEventListener('click', () => wrap.remove());
  return wrap;
}

function customerCareFilters(screen) {
  const values = {};
  screen.querySelectorAll('.w6-filter-strip input,.w6-filter-strip select').forEach((control) => {
    const name = control.name || '';
    if (!name) return;
    if (control.multiple) values[name] = [...control.selectedOptions].map((option) => option.value).filter(Boolean);
    else values[name] = control.value || '';
  });
  return values;
}

function customerCareRecordMatches(data, filters) {
  const sentinel = new Set(['', 'tất cả', 'chọn lớp học', 'chọn nhân viên', 'chọn số lần chăm sóc', 'all']);
  const equal = (key, value) => {
    const expected = String(value || '').trim().toLocaleLowerCase('vi');
    if (sentinel.has(expected)) return true;
    return String(data[key] ?? '').trim().toLocaleLowerCase('vi') === expected;
  };
  if (filters.q && !JSON.stringify(data).toLocaleLowerCase('vi').includes(String(filters.q).toLocaleLowerCase('vi'))) return false;
  if (!equal('status', filters.status)) return false;
  if (!equal('class_name', filters.class_name)) return false;
  if (!equal('staff_name', filters.staff_name)) return false;
  if (!equal('care_round', filters.care_round)) return false;
  const date = String(data.care_date || '').slice(0, 10);
  if (filters.date_from && (!date || date < String(filters.date_from))) return false;
  if (filters.date_to && (!date || date > String(filters.date_to))) return false;
  for (const key of ['action', 'result', 'purpose']) {
    const selected = Array.isArray(filters[key]) ? filters[key].filter((value) => value) : [];
    if (selected.length && !selected.some((value) => equal(key, value))) return false;
    const search = String(filters[`${key}_search`] || '').trim().toLocaleLowerCase('vi');
    if (search && !String(data[key] || '').toLocaleLowerCase('vi').includes(search)) return false;
  }
  return true;
}

function bindCustomerCareRows(centerEdu, route, config, screen, records) {
  screen.querySelectorAll('[data-w6-row-action]').forEach((button) => {
    if (button.dataset.w6CareBound) return;
    button.dataset.w6CareBound = 'true';
    button.addEventListener('click', async () => {
      const row = button.closest('tr[data-record-id]');
      const record = records.find((item) => String(item.id) === String(row?.dataset.recordId));
      if (!record) return;
      const data = record.data || {};
      const action = button.dataset.w6RowAction;
      if (action === 'detail' || action === 'survey') {
        customerCareModal(action === 'survey' ? 'Khảo sát chăm sóc' : 'Chi tiết chăm sóc', `<dl class="w6-care-detail">${Object.entries(data).map(([key, value]) => `<dt>${esc(key)}</dt><dd>${esc(Array.isArray(value) ? value.join(', ') : value || '—')}</dd>`).join('')}</dl>`, { closeOnly: true });
        return;
      }
      if (action === 'call' || action === 'message') {
        customerCareModal(action === 'call' ? 'Gọi điện' : 'Nhắn tin', `<p>Hành động outbound bị chặn trong QA. Bản ghi vẫn giữ nguyên.</p><p><b>${esc(data.student_name || 'Học viên')}</b></p>`, { closeOnly: true });
        return;
      }
      if (action === 'delete') {
        if (!window.confirm('Xóa bản ghi chăm sóc này?')) return;
        const query = new URLSearchParams({ route,
          ...(record.version != null ? { version: record.version } : {}),
          ...(record.updated_at ? { updated_at: record.updated_at } : {}),
        });
        await centerEdu.api(`/api/generated/screens/${encodeURIComponent(record.id)}?${query}`, { method: 'DELETE' });
        await renderW6Screen(centerEdu, route, config, screen);
        return;
      }
      if (action === 'edit') {
        const holder = document.createElement('div');
        holder.innerHTML = formHtml(config, record);
        const card = holder.firstElementChild;
        screen.append(card);
        attachForm(centerEdu, route, config, screen, records, card, record);
        card.scrollIntoView({ block: 'nearest' });
      }
    });
  });
}

function bindCustomerCareScreen(centerEdu, route, config, screen, records) {
  if (route !== '/cso/customer-care' || !screen) return;
  const tableCard = screen.querySelector('.w6-table-card');
  if (tableCard && !screen.querySelector('.w6-care-result-count')) {
    tableCard.insertAdjacentHTML('afterend', '<div class="w6-care-result-count" aria-live="polite"></div>');
  }
  const apply = () => {
    const filters = customerCareFilters(screen);
    const filtered = records.filter((record) => customerCareRecordMatches(record.data || {}, filters));
    const body = screen.querySelector('.w6-table-card tbody');
    if (body) {
      const holder = document.createElement('div');
      holder.innerHTML = tableHtml(config, filtered.slice(0, Math.max(1, Number(filters.page_size || 10))));
      body.replaceWith(holder.querySelector('tbody'));
    }
    bindCustomerCareRows(centerEdu, route, config, screen, records);
    const footer = screen.querySelector('.w6-care-result-count');
    if (footer) footer.textContent = `Hiển thị ${filtered.length ? 1 : 0} đến ${Math.min(filtered.length, Number(filters.page_size || 10))} của ${filtered.length} bản ghi`;
  };
  if (!screen.dataset.w6CareFiltersBound) {
    screen.dataset.w6CareFiltersBound = 'true';
    screen.querySelectorAll('.w6-filter-strip input,.w6-filter-strip select').forEach((control) => control.addEventListener(control.multiple || control.tagName === 'SELECT' ? 'change' : 'input', apply));
  }
  bindCustomerCareRows(centerEdu, route, config, screen, records);
  apply();
}

function bindHolidayRows(centerEdu, route, config, screen, records) {
  if (route !== '/center/holiday/index' || !screen) return;
  screen.querySelectorAll('[data-w6-row-action]').forEach((button) => {
    if (button.dataset.w6HolidayBound) return;
    button.dataset.w6HolidayBound = 'true';
    button.addEventListener('click', async () => {
      const row = button.closest('tr[data-record-id]');
      const record = records.find((item) => String(item.id) === String(row?.dataset.recordId));
      if (!record) return;
      if (button.dataset.w6RowAction === 'delete') {
        if (!window.confirm('Xóa lịch nghỉ này?')) return;
        const query = new URLSearchParams({
          route,
          ...(record.version != null ? { version: record.version } : {}),
          ...(record.updated_at ? { updated_at: record.updated_at } : {}),
        });
        await centerEdu.api(`/api/generated/screens/${encodeURIComponent(record.id)}?${query}`, { method: 'DELETE' });
        await renderW6Screen(centerEdu, route, config, screen);
        return;
      }
      if (button.dataset.w6RowAction === 'edit') {
        openHolidayForm(centerEdu, route, config, screen, records, record);
      }
    });
  });
}

function openHolidayForm(centerEdu, route, config, screen, records, record = null) {
  const holder = document.createElement('div');
  holder.innerHTML = formHtml({ ...config, formTitle: record ? 'Sửa lịch nghỉ' : 'Tạo mới lịch nghỉ' }, record);
  const card = holder.firstElementChild;
  const backdrop = document.createElement('div');
  backdrop.className = 'modal-backdrop w6-holiday-modal';
  backdrop.setAttribute('role', 'dialog');
  backdrop.setAttribute('aria-modal', 'true');
  backdrop.setAttribute('aria-label', record ? 'Sửa lịch nghỉ' : 'Tạo mới lịch nghỉ');
  const panel = document.createElement('div');
  panel.className = 'modal modal-wide';
  panel.append(...Array.from(card.children));
  backdrop.append(panel);
  document.body.append(backdrop);
  attachForm(centerEdu, route, config, screen, records, panel, record);
  panel.querySelector('.w6-cancel-form')?.addEventListener('click', () => backdrop.remove());
  backdrop.addEventListener('click', (event) => { if (event.target === backdrop) backdrop.remove(); });
  panel.querySelector('input,select,textarea,button')?.focus();
}

function fieldHtml(field, value = '') {
  const name = String(field.name || 'field');
  const label = String(field.label || name);
  const type = String(field.type || 'text').toLowerCase();
  const required = field.required ? ' required' : '';
  if (type === 'repeater') {
    let pairs = [];
    try { pairs = value ? (Array.isArray(value) ? value : JSON.parse(value)) : []; } catch { pairs = []; }
    if (!Array.isArray(pairs)) pairs = [];
    const rows = (pairs.length ? pairs : [{ key: '', value: '' }]).map((pair) => `<div class="w6-repeater-row"><input name="${esc(name)}_key[]" placeholder="Ký tự" value="${esc(pair?.key ?? '')}"><input name="${esc(name)}_value[]" placeholder="Giá trị" value="${esc(pair?.value ?? '')}"><button type="button" class="ghost w6-repeater-add" aria-label="Thêm dòng">＋</button></div>`).join('');
    return `<fieldset class="w6-repeater-field"><legend>${esc(label)}</legend><div data-w6-repeater="${esc(name)}">${rows}</div></fieldset>`;
  }
  if (type === 'checkbox') return `<label>${esc(label)}<input name="${esc(name)}" type="checkbox"${value ? ' checked' : ''}></label>`;
  if (Array.isArray(field.options) && field.options.length) {
    const selected = Array.isArray(value) ? value.map(String) : [String(value ?? '')];
    const multiple = field.multiple === true || type === 'select-multiple';
    const attrs = `${required}${multiple ? ' multiple size="1" data-w6-multi' : ''}`;
    const options = field.options.map((item) => {
      const optionValue = item && typeof item === 'object' ? item.value : item;
      const optionLabel = item && typeof item === 'object' ? item.label : item;
      return `<option value="${esc(optionValue)}"${selected.includes(String(optionValue)) ? ' selected' : ''}>${esc(optionLabel)}</option>`;
    }).join('');
    if (type === 'radio') return `<fieldset class="w6-radio-field"><legend>${esc(label)}</legend>${field.options.map((item) => { const optionValue = item && typeof item === 'object' ? item.value : item; const optionLabel = item && typeof item === 'object' ? item.label : item; return `<label><input type="radio" name="${esc(name)}" value="${esc(optionValue)}"${selected.includes(String(optionValue)) ? ' checked' : ''}${required}>${esc(optionLabel)}</label>`; }).join('')}</fieldset>`;
    return `<label>${esc(label)}<select name="${esc(name)}"${attrs}>${options}</select></label>`;
  }
  if (type === 'textarea') return `<label class="wide">${esc(label)}<textarea name="${esc(name)}"${required}>${esc(value)}</textarea></label>`;
  const inputType = type === 'number' ? 'number' : type === 'datetime-local' ? 'datetime-local' : type === 'password' ? 'password' : 'text';
  const placeholder = field.placeholder ? ` placeholder="${esc(field.placeholder)}"` : (type === 'date' ? ' placeholder="dd/mm/yyyy"' : '');
  return `<label>${esc(label)}<input name="${esc(name)}" type="${inputType}" value="${esc(formatValue(value) === '—' ? '' : formatValue(value))}"${required}${placeholder}></label>`;
}

function dailyCriteria(record) {
  let value = record?.data?.criteria;
  if (typeof value === 'string') { try { value = JSON.parse(value); } catch { value = []; } }
  return Array.isArray(value) ? value.filter((item) => item && typeof item === 'object') : [];
}

function dailyCourseIds(record) {
  let value = record?.data?.course_ids;
  if (typeof value === 'string') { try { value = JSON.parse(value); } catch { value = value.split(','); } }
  return Array.isArray(value) ? value.map(String).filter(Boolean) : [];
}

function dailyPersistedData(record) {
  const data = { ...(record?.data || {}) };
  delete data.criteria_count; delete data.course_count;
  return data;
}

function dailyEvaluationFormFields(courseOptions = []) {
  const fields = [
    { name: 'name', label: 'Tên bài đánh giá', required: true },
    { name: 'description', label: 'Mô tả', type: 'textarea' },
    { name: 'status', label: 'Trạng thái', type: 'radio', options: ['Hoạt động', 'Đã khóa'] },
  ];
  if (courseOptions.length) fields.push({ name: 'course_ids', label: 'Khóa học', type: 'select-multiple', multiple: true, options: courseOptions });
  return fields;
}

export function dailyEvaluationDetailHtml(record, courseOptions = [], writable = true) {
  if (!record) return '<p>Vui lòng chọn bài đánh giá</p>';
  const data = record.data || {};
  const criteria = dailyCriteria(record);
  const courseIds = dailyCourseIds(record);
  const courses = new Map((Array.isArray(courseOptions) ? courseOptions : []).map((course) => [String(course.value ?? course.id), course]));
  const courseRows = courseIds.map((id) => courses.get(id)).filter(Boolean).map((course) => `<li>${esc(course.label || course.name || course.code || course.value)}</li>`).join('');
  const value = (criterion) => criterion.value || (criterion.max_value !== undefined && criterion.max_value !== '' ? `Điểm tối đa: ${criterion.max_value}` : '—');
  const rows = criteria.map((criterion, index) => `<tr data-criterion-index="${index}"><td>${index + 1}</td><td>${esc(criterion.name || '—')}</td><td>${esc(criterion.assessment_type || '—')}</td><td>${esc(value(criterion))}</td><td><span class="w6-daily-status">${esc(criterion.status || 'Hoạt động')}</span></td><td>${writable ? `<button type="button" class="small-action w6-daily-criterion-edit" data-criterion-index="${index}">Sửa</button> <button type="button" class="small-action danger w6-daily-criterion-delete" data-criterion-index="${index}">Xóa</button>` : '—'}</td></tr>`).join('');
  const courseLabel = courseIds.length ? `${courseIds.length} khóa học` : '0 khóa học';
  return `<div class="w6-evaluation-detail" data-daily-evaluation-id="${esc(record.id)}"><div class="w6-daily-detail-head"><div><h3>${esc(data.name || 'Bài đánh giá')}</h3><p>${esc(data.description || '—')}</p></div>${writable ? '<div class="w6-daily-detail-actions"><button type="button" class="small-action w6-daily-evaluation-edit">Sửa</button><button type="button" class="small-action danger w6-daily-evaluation-delete">Xóa</button></div>' : ''}</div><div class="w6-daily-meta"><span class="w6-daily-course-popover"><details><summary>${esc(courseLabel)}</summary><ul>${courseRows || '<li>Chưa có dữ liệu khóa học</li>'}</ul></details></span><span>Trạng thái: ${esc(data.status || '—')}</span><span>${criteria.length} Tiêu chí</span></div>${writable ? '<div class="w6-panel-actions"><button type="button" class="primary w6-daily-criterion-create">＋ Tạo</button></div>' : ''}<div class="table-wrap"><table class="w6-daily-criteria-table"><thead><tr><th>No.</th><th>Tiêu chí</th><th>Hình thức đánh giá</th><th>Giá trị</th><th>Trạng thái</th><th>Hành động</th></tr></thead><tbody>${rows || '<tr class="empty-row"><td colspan="6">Chưa có tiêu chí</td></tr>'}</tbody></table></div></div>`;
}

function dailyEvaluationFormRecord(record) {
  if (!record) return null;
  const data = { ...(record.data || {}) }; data.course_ids = dailyCourseIds(record);
  return { ...record, data };
}

function bindRepeater(card) {
  card?.querySelectorAll('.w6-repeater-add').forEach((button) => {
    if (button.dataset.bound) return;
    button.dataset.bound = 'true';
    button.addEventListener('click', () => { const row = button.closest('.w6-repeater-row'); const clone = row?.cloneNode(true); if (!clone) return; clone.querySelectorAll('input').forEach((input) => { input.value = ''; }); row.parentElement.append(clone); bindRepeater(row.parentElement); });
  });
}

function openSetupModal(centerEdu, route, config, screen, records = [], record = null) {
  const holder = document.createElement('div'); holder.innerHTML = formHtml({ ...config, formTitle: config.formTitle || (record ? 'Sửa thông tin' : 'Tạo mới') }, record);
  const card = holder.firstElementChild; const backdrop = document.createElement('div'); backdrop.className = 'modal-backdrop w6-setup-modal'; backdrop.setAttribute('role', 'dialog'); backdrop.setAttribute('aria-modal', 'true');
  const panel = document.createElement('div'); panel.className = 'modal modal-wide'; panel.append(...Array.from(card.children)); backdrop.append(panel); document.body.append(backdrop);
  attachForm(centerEdu, route, config, screen, records, panel, record); bindRepeater(panel);
  panel.querySelector('.w6-cancel-form')?.addEventListener('click', () => backdrop.remove()); backdrop.addEventListener('click', (event) => { if (event.target === backdrop) backdrop.remove(); });
  panel.querySelector('input,select,textarea,button')?.focus();
}

function openDailyCriterionModal(centerEdu, route, screen, record, criteria, criterionIndex = null) {
  const criterion = criterionIndex == null ? null : criteria[criterionIndex];
  const fields = [{ name: 'name', label: 'Tiêu chí', required: true }, { name: 'assessment_type', label: 'Hình thức đánh giá', options: ['Nhập điểm', 'Bằng số', 'Bằng phần trăm', 'Bằng ký tự', 'Bằng văn bản'] }, { name: 'value', label: 'Giá trị' }, { name: 'max_value', label: 'Điểm tối đa', type: 'number' }, { name: 'status', label: 'Trạng thái', type: 'radio', options: ['Hoạt động', 'Đã khóa'] }];
  const holder = document.createElement('div'); holder.innerHTML = formHtml({ formTitle: criterion ? 'Sửa tiêu chí' : 'Tạo tiêu chí', fields }, { data: criterion || {} }); const card = holder.firstElementChild;
  const backdrop = document.createElement('div'); backdrop.className = 'modal-backdrop w6-setup-modal'; backdrop.setAttribute('role', 'dialog'); backdrop.setAttribute('aria-modal', 'true'); const panel = document.createElement('div'); panel.className = 'modal modal-wide'; panel.append(...Array.from(card.children)); backdrop.append(panel); document.body.append(backdrop);
  const form = panel.querySelector('form'); const error = panel.querySelector('.w6-form-error'); const close = () => backdrop.remove(); panel.querySelector('.w6-cancel-form')?.addEventListener('click', close); backdrop.addEventListener('click', (event) => { if (event.target === backdrop) close(); });
  form?.addEventListener('submit', async (event) => { event.preventDefault(); const next = criteria.map((item) => ({ ...item })); const nextItem = { ...(criterion || {}), ...Object.fromEntries(new FormData(form)), id: criterion?.id || `criterion-${Date.now()}` }; if (!nextItem.status) nextItem.status = 'Hoạt động'; if (criterionIndex == null) next.push(nextItem); else next[criterionIndex] = nextItem; const data = dailyPersistedData(record); data.criteria = JSON.stringify(next); try { await centerEdu.api(`/api/generated/screens/${encodeURIComponent(record.id)}`, { method: 'POST', body: { route, data, version: record.version, updated_at: record.updated_at, full_body: true } }); close(); await renderW6Screen(centerEdu, route, {}, screen); } catch (reason) { error.textContent = reason?.message || 'Không thể lưu tiêu chí.'; } });
}

async function renderDailyEvaluationDetail(centerEdu, route, config, screen, record, courseOptions, writable) {
  screen.dataset.dailySelectedId = String(record.id); const detail = screen.querySelector('.w6-evaluation-detail'); if (!detail) return; detail.outerHTML = dailyEvaluationDetailHtml(record, courseOptions, writable); const currentDetail = screen.querySelector('.w6-evaluation-detail'); const criteria = dailyCriteria(record);
  currentDetail.querySelector('.w6-daily-evaluation-edit')?.addEventListener('click', () => openSetupModal(centerEdu, route, { formTitle: 'Sửa bài đánh giá', fields: dailyEvaluationFormFields(courseOptions) }, screen, [], dailyEvaluationFormRecord(record)));
  currentDetail.querySelector('.w6-daily-evaluation-delete')?.addEventListener('click', async () => { if (!window.confirm('Xóa bài đánh giá này?')) return; const query = new URLSearchParams({ route, version: record.version, updated_at: record.updated_at }); try { await centerEdu.api(`/api/generated/screens/${encodeURIComponent(record.id)}?${query}`, { method: 'DELETE' }); await renderW6Screen(centerEdu, route, config, screen); } catch (reason) { const error = document.createElement('p'); error.className = 'error'; error.textContent = reason?.message || 'Không thể xóa bài đánh giá.'; currentDetail.prepend(error); } });
  currentDetail.querySelector('.w6-daily-criterion-create')?.addEventListener('click', () => openDailyCriterionModal(centerEdu, route, screen, record, criteria)); currentDetail.querySelectorAll('.w6-daily-criterion-edit').forEach((button) => button.addEventListener('click', () => openDailyCriterionModal(centerEdu, route, screen, record, criteria, Number(button.dataset.criterionIndex)))); currentDetail.querySelectorAll('.w6-daily-criterion-delete').forEach((button) => button.addEventListener('click', async () => { if (!window.confirm('Xóa tiêu chí này?')) return; const next = criteria.filter((_item, index) => index !== Number(button.dataset.criterionIndex)); const data = dailyPersistedData(record); data.criteria = JSON.stringify(next); try { await centerEdu.api(`/api/generated/screens/${encodeURIComponent(record.id)}`, { method: 'POST', body: { route, data, version: record.version, updated_at: record.updated_at, full_body: true } }); await renderW6Screen(centerEdu, route, config, screen); } catch (reason) { const error = document.createElement('p'); error.className = 'error'; error.textContent = reason?.message || 'Không thể xóa tiêu chí.'; currentDetail.prepend(error); } }));
}

const PEOPLE_ROUTES = {
  '/center/parent/index': '/api/parents',
  '/center/staff': '/api/staff',
};

function currentPeopleBranchId() {
  return document.querySelector('#branch-manager-scope select')?.value || '';
}

function peopleFields(route, record = null, students = [], branchState = {}) {
  const branchOptions = Array.isArray(branchState.options) ? branchState.options : [];
  const branchField = {
    name: 'branch_id', label: 'Chi nhánh', required: branchOptions.length > 1,
    value: record?.branch_id ?? branchState.selected ?? '',
    options: [{ value: '', label: 'Chọn chi nhánh' }, ...branchOptions],
  };
  const base = route === '/center/parent/index' ? [
    { name: 'image_data', label: 'Ảnh đại diện', type: 'file' },
    { name: 'fullname', label: 'Họ và tên', required: true },
    { name: 'dob', label: 'Ngày sinh', type: 'date' },
    { name: 'gender', label: 'Giới tính', options: ['Nam', 'Nữ'] },
    { name: 'phone', label: 'Số điện thoại' }, { name: 'email', label: 'Email' },
    { name: 'username', label: 'Tên đăng nhập', required: true },
    { name: 'password', label: 'Mật khẩu', type: 'password', required: !record },
    { name: 'code', label: 'Mã phụ huynh', required: true }, branchField,
    { name: 'status', label: 'Trạng thái', options: ['Hoạt động', 'Đang khóa'] },
    { name: 'job', label: 'Nghề nghiệp' }, { name: 'organization', label: 'Tổ chức' },
    { name: 'position', label: 'Chức vụ' }, { name: 'zalo', label: 'Zalo' },
    { name: 'facebook', label: 'Facebook' }, { name: 'address', label: 'Địa chỉ', type: 'textarea' },
    { name: 'student_ids', label: 'Học viên', type: 'select-multiple', multiple: true, required: true, options: students },
    { name: 'source_type', label: 'Nguồn giới thiệu' }, { name: 'source_id', label: 'Mã nguồn' },
  ] : [
    { name: 'fullname', label: 'Họ và tên', required: true }, { name: 'dob', label: 'Ngày sinh', type: 'date' },
    { name: 'gender', label: 'Giới tính', options: ['Nam', 'Nữ'] }, { name: 'phone', label: 'Số điện thoại' },
    { name: 'email', label: 'Email' }, { name: 'username', label: 'Tên đăng nhập', required: true },
    { name: 'password', label: 'Mật khẩu', type: 'password', required: !record },
    { name: 'code', label: 'Mã nhân viên', required: true }, branchField,
    { name: 'roles', label: 'Phân quyền', type: 'select-multiple', multiple: true, options: ['Nhân viên sale', 'Hỗ trợ khách hàng', 'Quản lý tài chính', 'Nhân viên chăm sóc khách hàng', 'BRANCH_MANAGER'] },
    { name: 'department', label: 'Phòng ban', options: ['Quản lý trung tâm', 'Phòng sale-CSKH', 'Teacher', 'Tài chính', 'CM'] },
    { name: 'position', label: 'Chức vụ', options: ['Quản lý trung tâm', 'Quản lý đào tạo'] },
    { name: 'status', label: 'Trạng thái', options: ['Hoạt động', 'Đang khóa'] },
  ];
  return base;
}

async function peopleBranchState(centerEdu, record = null) {
  try {
    const scope = (await centerEdu.api('/api/branch-manager/scope'))?.data || {};
    const options = (Array.isArray(scope.branches) ? scope.branches : []).map((branch) => ({
      value: String(branch.id), label: String(branch.name || branch.code || branch.id),
    }));
    const selected = record?.branch_id != null ? String(record.branch_id)
      : (currentPeopleBranchId() || (options.length === 1 ? options[0].value : ''));
    return { options, selected };
  } catch (_) {
    return { options: [], selected: record?.branch_id == null ? '' : String(record.branch_id) };
  }
}

async function fileDataUrl(file) {
  if (!file) return '';
  return await new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result || ''));
    reader.onerror = reject;
    reader.readAsDataURL(file);
  });
}

async function renderPeopleScreen(centerEdu, route, config, screen) {
  const endpoint = PEOPLE_ROUTES[route];
  if (!endpoint) return false;
  const branchState = await peopleBranchState(centerEdu);
  const query = new URLSearchParams();
  const oldControls = [...screen.querySelectorAll('.w6-filter-strip input,.w6-filter-strip select')];
  oldControls.forEach((control) => { if (control.value && control.name && control.name !== 'student_table_length' && control.name !== 'staff_table_length') query.set(control.name, control.value); });
  const payload = await centerEdu.api(`${endpoint}${query.toString() ? `?${query}` : ''}`);
  const rows = Array.isArray(payload?.data) ? payload.data : [];
  let students = [];
  if (route === '/center/parent/index') {
    try {
      const studentPayload = await centerEdu.api('/api/students');
      students = (Array.isArray(studentPayload?.data) ? studentPayload.data : []).map((item) => ({ value: String(item.id), label: `${item.full_name || item.fullname || ''} (${item.student_code || item.code || item.id})` }));
    } catch { students = []; }
  }
  const records = rows.map((data) => ({ id: data.id, data }));
  const routeConfig = { ...config, fields: peopleFields(route, null, students, branchState) };
  screen.className = `${screen.className || ''} w6-people-screen`.trim();
  screen.innerHTML = `<section class="w6-screen w6-reference-screen">${actionHtml(centerEdu, route, routeConfig, screen, records)}${filtersHtml(config.filters || [], config)}${tableHtml(routeConfig, records)}</section>`;
  installW6Layout();
  enhanceMultiSelects(screen);
  const openForm = (record = null) => {
    const holder = document.createElement('div');
    const formConfig = { ...routeConfig, fields: peopleFields(route, record, students, record ? { ...branchState, selected: String(record.data?.branch_id ?? branchState.selected) } : branchState) };
    holder.innerHTML = formHtml(formConfig, record ? { data: record.data } : null);
    const card = holder.firstElementChild;
    screen.querySelector('.w6-screen')?.append(card);
    attachForm(centerEdu, route, formConfig, screen, records, card, record);
    enhanceMultiSelects(card);
    card.scrollIntoView({ block: 'nearest' });
  };
  screen.querySelectorAll('[data-w6-action="create"]').forEach((button) => button.addEventListener('click', () => openForm()));
  screen.querySelectorAll('tr[data-record-id] .row-action').forEach((button) => button.addEventListener('click', () => {
    const row = button.closest('tr');
    const record = records.find((item) => String(item.id) === String(row?.dataset.recordId));
    if (record) openForm(record);
  }));
  screen.querySelectorAll('.w6-filter-strip input,.w6-filter-strip select').forEach((control) => control.addEventListener(control.tagName === 'SELECT' ? 'change' : 'input', () => renderPeopleScreen(centerEdu, route, config, screen)));
  screen.querySelectorAll('[data-w6-action="export"]').forEach((button) => button.addEventListener('click', () => window.location.assign(`${endpoint}/export`)));
  return true;
}


function enhanceMultiSelects(root) {
  root?.querySelectorAll('select[multiple][data-w6-multi]').forEach((select) => {
    if (select.dataset.compactBound) return;
    select.dataset.compactBound = 'true';
    const widget = document.createElement('details');
    widget.className = 'w6-compact-multi';
    const summary = document.createElement('summary');
    summary.setAttribute('aria-label', select.getAttribute('aria-label') || 'Trạng thái');
    const menu = document.createElement('div');
    menu.className = 'w6-compact-options';
    const update = () => {
      summary.textContent = [...select.selectedOptions].map(option => option.textContent).join(', ') || select.dataset.placeholder || '\u00a0';
      menu.querySelectorAll('input').forEach((input, i) => { input.checked = select.options[i].selected; });
      select._compactRefresh = update;
    };
    const careScreen = Boolean(select.closest('.w6-customer-care-screen'));
    [...select.options].forEach((option) => {
      if (careScreen) {
        const choice = document.createElement('button');
        choice.type = 'button'; choice.className = 'w6-compact-option'; choice.textContent = option.textContent;
        choice.setAttribute('aria-pressed', option.selected ? 'true' : 'false');
        choice.addEventListener('click', () => { option.selected = !option.selected; choice.setAttribute('aria-pressed', option.selected ? 'true' : 'false'); select.dispatchEvent(new Event('change', { bubbles: true })); update(); });
        menu.append(choice);
      } else {
        const label = document.createElement('label');
        const check = document.createElement('input');
        check.type = 'checkbox'; check.checked = option.selected;
        label.append(check, document.createTextNode(option.textContent));
        check.addEventListener('change', () => { option.selected = check.checked; select.dispatchEvent(new Event('change', { bubbles: true })); update(); });
        menu.append(label);
      }
    });
    widget.append(summary, menu);
    select.style.display = 'none';
    select.after(widget);
    select.addEventListener('change', update);
    const search = select.closest('label')?.querySelector('.w6-multi-search');
    search?.addEventListener('input', () => {
      const term = String(search.value || '').toLocaleLowerCase('vi-VN');
      menu.querySelectorAll('label').forEach((item) => { item.hidden = Boolean(term) && !item.textContent.toLocaleLowerCase('vi-VN').includes(term); });
    });
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
    // The reference exposes the aggregate label as a header cell, not a
    // plain data cell. Keep the visible row and switch layout unchanged while
    // preserving the observable column-header contract.
    rows.push(`<tr class="w6-tenant-master-row"><th scope="rowgroup" colspan="2"><strong>Tất cả</strong></th><th scope="rowgroup">${tenantSwitch({ master: true, disabled: masterAmbiguous, checked: uniqueEnabled })}</th></tr>`);
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
    #screen .w6-reference-screen:has(.w6-tenant-config)>.ref-tabs{margin:0;padding:0 24px;min-height:66px;display:flex;align-items:stretch;border-bottom:1px solid #edf0f5}
    #screen .w6-reference-screen:has(.w6-tenant-config)>.ref-tabs .ref-tab{padding:0 0;margin-right:24px;border-radius:0;color:#17191f;font-size:13px;font-weight:400;background:none;border-bottom:1px solid #716aca}
    #screen .w6-tenant-config{margin:36px 36px 0;border:0;border-radius:0;box-shadow:none;overflow:visible}
    #screen .w6-tenant-config table{width:100%;min-width:620px;table-layout:fixed;border:1px solid #edf0f5;font-size:13px}
    #screen .w6-tenant-config th,#screen .w6-tenant-config td{padding:10px;border-right:1px solid #edf0f5;border-bottom:1px solid #edf0f5;line-height:1.35;color:#17191f}
    #screen .w6-tenant-config th{height:40px;padding-top:11px;padding-bottom:11px;background:#fff;color:#111;font-size:13px;text-transform:none;letter-spacing:0;font-weight:700;text-align:left}
    #screen .w6-tenant-config th:first-child,#screen .w6-tenant-config td:first-child{width:7%;text-align:left}
    #screen .w6-tenant-config th:nth-child(2),#screen .w6-tenant-config td:nth-child(2){width:67%}
    #screen .w6-tenant-config th:nth-child(3),#screen .w6-tenant-config td:nth-child(3){width:26%;text-align:left}
    #screen .w6-tenant-config .w6-tenant-master-row td{height:68px;padding:16px 10px}
    #screen .w6-tenant-config .w6-tenant-master-row td[colspan="2"]{width:74%;text-align:center}
    #screen .w6-tenant-config .w6-tenant-group td{height:42px;padding-top:10px;padding-bottom:10px}
    #screen .w6-tenant-config .w6-tenant-report-row td{height:67px;padding-top:14px;padding-bottom:14px;box-sizing:border-box}
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
  return `<div class="card w6-form-card"><h2>${esc(record ? 'Sửa thông tin' : (config.formTitle || 'Thêm mới'))}</h2><form class="w6-inline-form"><div class="form-grid">${fields.map((field) => fieldHtml(field, data[field.name] ?? field.value)).join('')}</div><div class="form-actions"><button type="submit" class="primary">Lưu</button><button type="button" class="ghost w6-cancel-form">Hủy</button></div><p class="error w6-form-error"></p></form></div>`;
}

// Setup screens use a two-panel reference layout rather than the generic
// list shell. Keep the panels source-backed: records come from the route API;
// empty panels stay empty instead of fabricating demo rows.
export function setupDailyEvaluationHtml(records, config) {
  const rows = Array.isArray(records) ? records : [];
  const items = rows.map((record) => {
    const data = record?.data || {};
    const name = esc(data.name || '');
    const count = data.criteria_count == null ? '—' : esc(data.criteria_count);
    return `<button type="button" class="w6-evaluation-item" data-record-id="${esc(record.id)}"><span>${name}</span><b>${count} Tiêu chí</b></button>`;
  }).join('');
  return `<div class="w6-setup-panels w6-daily-evaluation"><section class="card"><div class="w6-panel-title"><span aria-hidden="true">◆</span><h2>Bài đánh giá</h2></div><div class="w6-panel-actions"><button type="button" class="primary w6-action" data-w6-action="create">＋ Tạo</button></div><div class="w6-evaluation-list">${items || '<p class="empty">Chưa có bài đánh giá</p>'}</div></section><section class="card"><div class="w6-panel-title"><h2>Tiêu chí đánh giá</h2></div><div class="w6-evaluation-detail"><p>Vui lòng chọn bài đánh giá</p></div></section></div>`;
}

export function setupCriteriaHtml(records, testRecords = []) {
  const rows = Array.isArray(records) ? records : [];
  const body = rows.map((record, index) => {
    const data = record?.data || {};
    return `<tr data-record-id="${esc(record.id)}"><td>${index + 1}</td><td>${esc(data.skill || data.name)}</td><td><span class="w6-criteria-link">• ${esc(data.assessment_type)}</span></td><td>${esc(data.value ?? data.max_value)}</td><td><button type="button" class="small-action w6-criteria-edit" data-record-id="${esc(record.id)}" aria-label="Sửa">♢</button><button type="button" class="small-action w6-criteria-delete" data-record-id="${esc(record.id)}" aria-label="Xóa">♧</button></td></tr>`;
  }).join('');
  const testItems = (Array.isArray(testRecords) ? testRecords : []).map((record) => `<button type="button" class="w6-evaluation-item" data-test-id="${esc(record.id)}"><span>${esc(record.data?.name || '')}</span><b>${esc(record.data?.criteria_count ?? '—')} tiêu chí</b></button>`).join('');
  return `<div class="w6-setup-criteria card"><div class="w6-panel-title"><span aria-hidden="true">◆</span><h1>Thiết lập tiêu chí test</h1></div><div class="w6-setup-panels"><section class="card"><div class="w6-panel-title"><h2>Bài test</h2></div><div class="w6-panel-actions"><button type="button" class="primary w6-action" data-w6-action="create-test">＋ Bài test</button></div><div class="w6-evaluation-list">${testItems || '<p class="empty">Chưa có bài test</p>'}</div></section><section class="card"><div class="w6-panel-title"><h2>Tiêu chí</h2></div><div class="w6-panel-actions"><button type="button" class="primary w6-action" data-w6-action="create">＋ Tạo tiêu chí</button></div><div class="table-wrap"><table><thead><tr><th>STT</th><th>Kỹ năng</th><th>Hình thức đánh giá</th><th>Giá trị</th><th>Hành động</th></tr></thead><tbody>${body || `<tr class="empty-row"><td colspan="5">Không tìm thấy dữ liệu</td></tr>`}</tbody></table></div></section></div></div>`;
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
  if (route === '/center/upload_address' || route === '/center/upload_address/index_customer') return '';
  if (!buttons && !canWrite) return '';
  const heading = route === '/cso/customer-care' ? '' : `<div class="screen-title"><h1>${esc(config.title || route)}</h1></div>`;
  return `<div class="screen-head${route === '/cso/customer-care' ? ' w6-care-actions-head' : ''}">${heading}<div class="w6-actions">${buttons}</div></div>`;
}

function tabsHtml(tabs = [], route = '') {
  if (!tabs.length) return '';
  return `<div class="ref-tabs" role="tablist">${tabs.map((label, index) => `<button type="button" class="ref-tab ${index === 0 ? 'active' : ''}" role="tab" aria-selected="${index === 0 ? 'true' : 'false'}">${route === TENANT_ROUTE ? '<span aria-hidden="true" style="color:#4e70ee;margin-right:10px">▤</span>' : ''}${esc(label)}</button>`).join('')}</div>`;
}


function filtersHtml(filters = [], config = {}) {
  if (!filters.length || config.filterLayout === 'columns') return '';
  const clear = config.noClear ? '' : '<button type="button" class="ghost" id="generated-filter-clear">Xóa lọc</button>';
  return `<div class="filter-strip w6-filter-strip">${filters.map(filterControl).join('')}${clear}</div>`;
}

function attachForm(centerEdu, route, config, screen, records, formCard, record = null) {
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
    if (record && record.data?.version != null) payload.version = record.data.version;
    if (route === '/center/parent/index' && record && !payload.password) delete payload.password;
    if (route === '/center/staff' && record && !payload.password) delete payload.password;
    try {
      const dedicated = PEOPLE_ROUTES[route];
      const url = dedicated ? (record ? `${dedicated}/${encodeURIComponent(record.id)}` : dedicated) : (record ? `/api/generated/screens/${encodeURIComponent(record.id)}` : '/api/generated/screens');
      const body = dedicated ? payload : (record ? { route, data: payload, version: record.version, updated_at: record.updated_at, full_body: true } : { route, data: payload });
      await centerEdu.api(url, { method: 'POST', body });
      formCard.closest('.w6-holiday-modal,.w6-setup-modal')?.remove();
      await (dedicated ? renderPeopleScreen(centerEdu, route, config, screen) : renderW6Screen(centerEdu, route, config, screen));
    } catch (error) {
      const message = form.querySelector('.w6-form-error');
      if (!message) return;
      message.textContent = error?.message || 'Không thể lưu dữ liệu';
      if (record && (error?.status === 409 || error?.status === 428)) {
        const reload = document.createElement('button');
        reload.type = 'button'; reload.className = 'ghost conflict-reload'; reload.textContent = 'Tải lại';
        reload.addEventListener('click', () => renderW6Screen(centerEdu, route, config, screen));
        message.append(' ', reload);
      }
    }
  });
  formCard.querySelector('.w6-cancel-form')?.addEventListener('click', () => formCard.remove());
}

export async function renderW6Screen(centerEdu, route, config, screen) {
  if (PEOPLE_ROUTES[route]) return renderPeopleScreen(centerEdu, route, config, screen);
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
  const records = Array.isArray(rawRecords) ? rawRecords : [];
  const uploadAddressRoute = route === '/center/upload_address' || route === '/center/upload_address/index_customer';
  if (route === TENANT_ROUTE && !Array.isArray(rawRecords)) settingsReadable = false;
  screen.classList.toggle('upload-address-screen', uploadAddressRoute);
  screen.classList.toggle('upload-address-customer-screen', route === '/center/upload_address/index_customer');
  const writable = ['ADMIN', 'STAFF'].includes(String(centerEdu.state?.user?.role || ''));
  if (route === '/setup/daily-evaluation' || route === '/setup/criteria') {
    if (!document.querySelector('#w6-setup-layout-style')) {
      const style = document.createElement('style');
      style.id = 'w6-setup-layout-style';
      style.textContent = '.w6-setup-panels{display:grid;grid-template-columns:minmax(300px,.8fr) minmax(420px,1.5fr);gap:30px}.w6-setup-panels>.card,.w6-setup-criteria{background:#fff;border-radius:4px;box-shadow:0 5px 20px rgba(31,45,61,.06);overflow:hidden}.w6-panel-title{display:flex;align-items:center;gap:12px;padding:18px 24px;border-bottom:1px solid #edf0f6}.w6-panel-title h1,.w6-panel-title h2{margin:0;font-size:18px;font-weight:500}.w6-panel-actions{display:flex;justify-content:flex-end;padding:24px 30px 10px}.w6-evaluation-list{padding:8px 28px 24px}.w6-evaluation-item{display:flex;justify-content:space-between;align-items:center;width:100%;padding:13px 2px;border:0;background:transparent;color:#6d7384;text-align:left;cursor:pointer}.w6-evaluation-item.active{color:#5666e9;background:#f6f7ff}.w6-evaluation-item b{border-radius:16px;background:#2fbda5;color:#fff;padding:5px 12px;font-size:11px}.w6-evaluation-detail{padding:24px;color:#20212a}.w6-daily-detail-head{display:flex;align-items:flex-start;justify-content:space-between;gap:16px;padding-bottom:18px;border-bottom:1px solid #edf0f6}.w6-daily-detail-head h3{margin:0 0 6px;font-size:18px;font-weight:500}.w6-daily-detail-head p{margin:0;color:#697184;font-size:13px}.w6-daily-detail-actions{display:flex;gap:8px;flex:0 0 auto}.w6-daily-meta{display:flex;align-items:center;gap:18px;padding:16px 0;color:#697184;font-size:13px}.w6-daily-course-popover details{position:relative}.w6-daily-course-popover summary{color:#5666e9;cursor:pointer;list-style:none}.w6-daily-course-popover summary::-webkit-details-marker{display:none}.w6-daily-course-popover ul{position:absolute;z-index:2;min-width:190px;margin:8px 0 0;padding:10px 16px;background:#fff;border:1px solid #e4e8f0;border-radius:3px;box-shadow:0 5px 18px rgba(31,45,61,.12);list-style:none}.w6-daily-course-popover li{padding:4px 0;white-space:nowrap}.w6-daily-status{display:inline-block;padding:4px 9px;border-radius:12px;background:#e8f7f3;color:#279a87;font-size:11px}.w6-daily-criteria-table{width:100%;border-collapse:collapse}.w6-daily-criteria-table th,.w6-daily-criteria-table td{padding:12px 10px;border:1px solid #edf0f6;text-align:left}.w6-daily-criteria-table th{text-align:center;background:#fafbfe;font-weight:500}.w6-daily-criteria-table .small-action{margin-right:6px}.w6-setup-unavailable{padding:0 24px 24px;margin:0;color:#697184;font-size:12px}.w6-setup-criteria>.w6-panel-title{margin-bottom:22px}.w6-setup-criteria>.w6-setup-panels{padding:0 22px 22px}.w6-criteria-link{color:#5666e9}.w6-setup-criteria table{width:100%;border-collapse:collapse}.w6-setup-criteria th,.w6-setup-criteria td{padding:14px 10px;border:1px solid #edf0f6;text-align:left}.w6-setup-criteria th{text-align:center}@media(max-width:800px){.w6-setup-panels{grid-template-columns:1fr}.w6-daily-detail-head,.w6-daily-meta{align-items:flex-start;flex-direction:column}.w6-daily-detail-actions{width:100%}}';
      document.head.append(style);
      const referenceSetupStyle = document.createElement('style');
      referenceSetupStyle.id = 'w6-setup-reference-tokens';
      referenceSetupStyle.textContent = '.w6-setup-panels{grid-template-columns:minmax(420px,.7fr) minmax(600px,1fr)}@media(max-width:800px){.w6-setup-panels{grid-template-columns:minmax(0,1fr)}}.w6-setup-panels .primary{background:#36bea5}.w6-setup-panels .primary:hover{background:#2cae95}';
      document.head.append(referenceSetupStyle);
    }
    let testRecords = [];
    let testCourseOptions = [];
    let dailyCourseOptions = [];
    if (route === '/setup/criteria' || route === '/setup/daily-evaluation') {
      if (route === '/setup/criteria') {
        try {
          const testPayload = await centerEdu.api('/api/generated/screens?route=%2Fsetup%2Ftest');
          testRecords = Array.isArray(testPayload?.data?.records) ? testPayload.data.records : [];
        } catch { testRecords = []; }
      }
      try {
        const coursePayload = await centerEdu.api('/api/courses');
        const options = (Array.isArray(coursePayload?.data) ? coursePayload.data : []).map((course) => ({ value: String(course.id), label: course.name || course.title || course.code || String(course.id) }));
        testCourseOptions = options;
        dailyCourseOptions = options;
      } catch { testCourseOptions = []; }
    }
    screen.innerHTML = route === '/setup/daily-evaluation'
      ? setupDailyEvaluationHtml(records, config)
      : setupCriteriaHtml(records, testRecords);
    const selectDailyEvaluation = (item) => {
      const record = records.find((entry) => String(entry.id) === String(item.dataset.recordId));
      if (!record) return;
      screen.querySelectorAll('.w6-evaluation-item').forEach((button) => button.classList.toggle('active', button === item));
      if (route === '/setup/daily-evaluation') renderDailyEvaluationDetail(centerEdu, route, config, screen, record, dailyCourseOptions, writable);
    };
    screen.querySelectorAll('.w6-evaluation-item').forEach((item) => item.addEventListener('click', () => selectDailyEvaluation(item)));
    if (route === '/setup/daily-evaluation' && screen.dataset.dailySelectedId) {
      const selected = screen.querySelector(`.w6-evaluation-item[data-record-id="${CSS.escape(screen.dataset.dailySelectedId)}"]`);
      if (selected) selectDailyEvaluation(selected);
    }
    screen.querySelectorAll('[data-w6-action="create"]').forEach((button) => button.addEventListener('click', () => {
      const holder = document.createElement('div');
      const createConfig = route === '/setup/daily-evaluation'
        ? { ...config, formTitle: 'Tạo bài đánh giá', fields: dailyEvaluationFormFields(dailyCourseOptions) }
        : config;
      if (route === '/setup/daily-evaluation') { openSetupModal(centerEdu, route, createConfig, screen); return; }
      holder.innerHTML = formHtml(createConfig); const card = holder.firstElementChild; screen.append(card); attachForm(centerEdu, route, createConfig, screen, records, card); card.scrollIntoView({ block: 'nearest' });
    }));
    screen.querySelector('[data-w6-action="create-test"]')?.addEventListener('click', () => {
      const testConfig = { formTitle: 'Tạo bài test', fields: [
        { name: 'name', label: 'Tên bài test', required: true },
        { name: 'skills', label: 'Kỹ năng', type: 'select-multiple', multiple: true, required: true, options: ['Nghe', 'Nói', 'Đọc', 'Viết'] },
        { name: 'course_ids', label: 'Khóa học', type: 'select-multiple', multiple: true, options: testCourseOptions },
        { name: 'center', label: 'Trung tâm', required: true },
      ] };
      const holder = document.createElement('div'); holder.innerHTML = formHtml(testConfig);
      const card = holder.firstElementChild; screen.append(card);
      attachForm(centerEdu, '/setup/test', testConfig, screen, testRecords, card);
      card.scrollIntoView({ block: 'nearest' });
    });
    if (route === '/setup/criteria') {
      screen.querySelectorAll('.w6-criteria-edit').forEach((button) => button.addEventListener('click', () => {
        const record = records.find((item) => String(item.id) === String(button.dataset.recordId));
        if (!record) return;
        const holder = document.createElement('div');
        holder.innerHTML = formHtml(config, record);
        const card = holder.firstElementChild;
        screen.append(card);
        attachForm(centerEdu, route, config, screen, records, card, record);
        card.scrollIntoView({ block: 'nearest' });
      }));
      screen.querySelectorAll('.w6-criteria-delete').forEach((button) => button.addEventListener('click', async () => {
        const record = records.find((item) => String(item.id) === String(button.dataset.recordId));
        if (!record) return;
        if (!window.confirm('Xóa tiêu chí này?')) return;
        const query = new URLSearchParams({ route,
          ...(record.version != null ? { version: record.version } : {}),
          ...(record.updated_at ? { updated_at: record.updated_at } : {}),
        });
        await centerEdu.api(`/api/generated/screens/${encodeURIComponent(record.id)}?${query}`, { method: 'DELETE' });
        await renderW6Screen(centerEdu, route, config, screen);
      }));
    }
    return true;
  }
  // The class tool is a two-workflow form in the reference.  It has no table
  // or generic toolbar; keep both date inputs and their action beside the
  // explanatory label so the route remains usable when the API has no rows.
  if (route === '/center/tool/center/index') {
    screen.classList.add('w6-center-tool-screen');
    if (!document.querySelector('#w6-center-tool-style')) {
      const style = document.createElement('style');
      style.id = 'w6-center-tool-style';
      style.textContent = `
        .w6-center-tool-screen{padding:0 24px 32px}.w6-center-tool-screen .w6-tool-title{display:flex;align-items:center;gap:12px;padding:20px 0 16px;border-bottom:1px solid #edf0f6}.w6-center-tool-screen .w6-tool-title h1{margin:0;font-size:18px;font-weight:500}.w6-center-tool-screen .w6-tool-form{padding:22px 0 0}.w6-center-tool-screen .w6-tool-row{display:grid;grid-template-columns:220px minmax(260px,1fr) 280px;column-gap:24px;align-items:start;margin:0 0 24px}.w6-center-tool-screen .w6-tool-label{padding-top:8px;font-size:13px;color:#4d5563}.w6-center-tool-screen .w6-tool-field{min-width:0}.w6-center-tool-screen .w6-tool-field input{display:block;width:100%;height:36px;box-sizing:border-box;border:1px solid #dfe4ee;border-radius:3px;padding:7px 10px;background:#fff;color:#4d5563}.w6-center-tool-screen .w6-tool-field p{margin:6px 0 0;color:#697184;font-size:13px}.w6-center-tool-screen .w6-tool-action{display:flex;align-items:flex-start}.w6-center-tool-screen .w6-tool-action button{width:100%;height:36px;padding:0 14px;background:#34bfa3;color:#fff;border:0;border-radius:3px;font-size:13px;cursor:pointer;white-space:nowrap}.w6-center-tool-screen .w6-tool-action button:disabled{opacity:.65;cursor:wait}.w6-center-tool-screen .w6-tool-message{min-height:18px;margin:6px 0 0;color:#268eaf;font-size:12px}.w6-center-tool-screen .w6-tool-message.error{color:#c53d54}@media(max-width:800px){.w6-center-tool-screen .w6-tool-row{grid-template-columns:1fr;row-gap:8px}.w6-center-tool-screen .w6-tool-label{padding-top:0}.w6-center-tool-screen .w6-tool-action button{width:auto}}
      `;
      document.head.append(style);
    }
    screen.innerHTML = `<section class="w6-screen w6-center-tool-screen"><div class="w6-tool-title"><span aria-hidden="true">⚙</span><h1>Công cụ cho lớp học</h1></div><div class="w6-tool-form"><div class="w6-tool-row w6-tool-row-url"><label class="w6-tool-label" for="w6-tool-class-url">Nhập đường link của lớp</label><div class="w6-tool-field"><input id="w6-tool-class-url" name="ClassUrl" data-tool-field="class_url" placeholder="Nhập đường link của lớp" aria-label="Nhập đường link của lớp" required></div><div></div></div><div class="w6-tool-row"><label class="w6-tool-label" for="w6-tool-cancelled-date">Ngày cần khôi phục hủy buổi</label><div class="w6-tool-field"><input id="w6-tool-cancelled-date" name="TimeTableDate" data-tool-field="cancelled_session_date" type="date" aria-label="Ngày buổi hủy"><p>Hãy chọn ngày mà cần khôi phục hủy buổi</p><p class="w6-tool-message" data-w6-tool-message="restore" role="status"></p></div><div class="w6-tool-action"><button type="button" data-w6-tool-action="restore">Nhấn vào đây để khôi phục buổi hủy</button></div></div><div class="w6-tool-row"><label class="w6-tool-label" for="w6-tool-start-date">Ngày cần bắt đầu đúng</label><div class="w6-tool-field"><input id="w6-tool-start-date" name="TimeTableDate" data-tool-field="new_start_date" type="date" aria-label="Ngày bắt đầu mới"><p>Hãy chọn ngày bắt đầu đúng</p><p class="w6-tool-message" data-w6-tool-message="start" role="status"></p></div><div class="w6-tool-action"><button type="button" data-w6-tool-action="start">Nhấn vào đây để đổi ngày bắt đầu</button></div></div></div></section>`;
    const classUrl = screen.querySelector('[data-tool-field="class_url"]');
    const setMessage = (kind, message, error = false) => { const target = screen.querySelector(`[data-w6-tool-message="${kind}"]`); if (target) { target.textContent = message; target.classList.toggle('error', error); } };
    const runTool = async (kind, endpoint, dateField, confirmText) => {
      const button = screen.querySelector(`[data-w6-tool-action="${kind}"]`); const date = screen.querySelector(`[data-tool-field="${dateField}"]`)?.value || '';
      if (!classUrl?.value.trim()) { setMessage(kind, 'Nhập đường link của lớp.', true); classUrl?.focus(); return; }
      if (!date) { setMessage(kind, 'Chọn ngày trước khi thực hiện.', true); screen.querySelector(`[data-tool-field="${dateField}"]`)?.focus(); return; }
      if (typeof window.confirm === 'function' && !window.confirm(confirmText)) return;
      button.disabled = true; setMessage(kind, 'Đang xử lý…');
      try { const result = await centerEdu.api(endpoint, { method: 'POST', body: { class_url: classUrl.value.trim(), [dateField]: date } }); const item = result?.data || {}; setMessage(kind, kind === 'restore' ? `Đã khôi phục buổi ${item.session_date || date}.` : `Đã đổi ngày bắt đầu sang ${item.start_date || date}.`); }
      catch (error) { setMessage(kind, error?.message || 'Không thể thực hiện thao tác.', true); }
      finally { button.disabled = false; }
    };
    screen.querySelector('[data-w6-tool-action="restore"]')?.addEventListener('click', () => runTool('restore', '/api/center-tool/restore-cancelled', 'cancelled_session_date', 'Khôi phục buổi học đã hủy?'));
    screen.querySelector('[data-w6-tool-action="start"]')?.addEventListener('click', () => runTool('start', '/api/center-tool/change-start-date', 'new_start_date', 'Đổi ngày bắt đầu và dời lịch học?'));
    const removeUnownedStrip = () => {
      if (document.querySelector('#screen') !== screen) return;
      screen.querySelectorAll('.filter-strip').forEach(strip => strip.remove());
    };
    setTimeout(removeUnownedStrip, 180);
    setTimeout(removeUnownedStrip, 500);
    return true;
  }
  const renderConfig = route === '/center/holiday/index' ? { ...config, rowActionsWritable: writable } : config;
  const table = route === TENANT_ROUTE
    ? tenantConfigHtml(catalog, records, { writable, settingsReadable })
    : (config.formOnly ? formHtml(config) : tableHtml(renderConfig, records));
  const trailingFooter = uploadAddressRoute
    ? `<div class="upload-address-footer"><span>Hiển thị ${records.length ? 1 : 0} đến ${records.length} của ${records.length} bản ghi</span><label>Hiển thị <select aria-label="Hiển thị 5 10 25 50 bản ghi">${(config.pageSizes || ['5', '10', '25', '50']).map((size) => `<option${size === '25' ? ' selected' : ''}>${size}</option>`).join('')}</select> bản ghi</label><span class="upload-address-pagination"><button type="button" disabled aria-label="Trang trước">‹</button><button type="button" disabled aria-label="Trang sau">›</button></span></div>`
    : '';
  const trailingAction = uploadAddressRoute
    ? '<div class="upload-address-save"><button type="button" class="upload-save w6-action" data-w6-action="save-address">Lưu</button></div>'
    : '';
  const headings = Array.isArray(config.headings) && config.headings.length
    ? `<div class="w6-section-headings">${config.headings.map((heading) => `<h2>${esc(heading)}</h2>`).join('')}</div>`
    : '';
  const resultCount = config.resultCount ? `<p class="w6-result-count">Kết quả: <span data-w6-result-count>${records.length}</span></p>` : '';
  const careTitle = route === '/cso/customer-care' ? `<div class="w6-care-card-title"><span class="w6-care-card-icon" aria-hidden="true">${careTitleIcon}</span><h2>Chăm sóc khách hàng</h2></div>` : '';
  const referenceRoute = /^\/(callcenter|center|tenant)\//.test(route) || route === '/cso/customer-care';
  screen.innerHTML = `<section class="w6-screen${referenceRoute ? ' w6-reference-screen' : ''}${route === '/cso/customer-care' ? ' w6-customer-care-screen' : ''}${config.filterLayout === 'columns' ? ' w6-column-list' : ''}">${careTitle}${actionHtml(centerEdu, route, config, screen, records)}${resultCount}${headings}${tabsHtml(config.tabs || [], route)}${filtersHtml(config.filters || [], config)}${table}${trailingFooter}${trailingAction}</section>`;
  installW6Layout();
  bindColumnFilters(screen, config, records);
  enhanceMultiSelects(screen);
  bindCustomerCareScreen(centerEdu, route, config, screen, records);
  bindHolidayRows(centerEdu, route, renderConfig, screen, records);
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
    if (route === '/callcenter/get-statistic') return;
    if (document.querySelector('#screen') !== screen || !screen.querySelector('.w6-screen')) return;
    if (route === TENANT_ROUTE || config.filterLayout === 'columns') {
      // Column filters already belong to their table cells. The optional shared
      // screen-spec reconciliation may add a legacy strip; remove only that strip.
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
    enhanceMultiSelects(strip);
    if (route === '/cso/customer-care') {
      delete screen.dataset.w6CareFiltersBound;
      bindCustomerCareScreen(centerEdu, route, config, screen, records);
    }
    strip.querySelector('#generated-filter-clear')?.addEventListener('click', () => strip.querySelectorAll('input,select,textarea').forEach((input) => { input.value = ''; input.checked = false; }));
  };
  // Two bounded passes cover both awaited and fire-and-forget shell cleanup
  // paths while avoiding a permanent observer or shared-file wiring.
  setTimeout(restoreReferenceControls, 180);
  setTimeout(restoreReferenceControls, 500);
  screen.querySelectorAll('[data-w6-action="create"]').forEach((button) => button.addEventListener('click', () => {
    if (route === '/center/holiday/index') {
      openHolidayForm(centerEdu, route, config, screen, records);
      return;
    }
    const holder = document.createElement('div');
    holder.innerHTML = formHtml(config);
    const card = holder.firstElementChild;
    screen.append(card);
    attachForm(centerEdu, route, config, screen, records, card);
    card.scrollIntoView({ block: 'nearest' });
  }));
  if (route === '/cso/customer-care') {
    screen.querySelectorAll('[data-w6-action="noop"]').forEach((button) => button.addEventListener('click', () => {
      const label = button.textContent.trim();
      const status = label === 'Chưa xử lý' ? 'Chưa xử lý' : label === 'Đã xong' ? 'Đã xong' : '';
      const control = screen.querySelector('select[name="status"]');
      if (status && control) { control.value = status; control.dispatchEvent(new Event('change', { bubbles: true })); }
    }));
  }
  screen.querySelectorAll('[data-w6-action="export"]').forEach((button) => button.addEventListener('click', () => {
    const params = new URLSearchParams({ route });
    if (route === '/cso/customer-care') {
      screen.querySelectorAll('.w6-filter-strip input,.w6-filter-strip select').forEach((control) => {
        const name = control.name || '';
        if (!name || name === 'page_size') return;
        const value = control.multiple ? [...control.selectedOptions].map((option) => option.value).filter(Boolean).join(',') : control.value;
        if (value && !/^(tất cả|chọn)/i.test(value)) params.set(name, value);
      });
    }
    window.location.assign(`/api/export/generated-screen?${params.toString()}`);
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

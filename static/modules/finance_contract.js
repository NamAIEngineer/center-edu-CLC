/* Contract route metadata and owned renderer. Shared legacy rendering is not
 * used: it duplicated observed controls and exposed synthetic identities. */
export const financeContract = {
  route: '/finance/contract', uploadRoute: '/finance/contract/upload', extensionRoute: '/finance/contract/get_extension_contract', tabs: [],
  columns: ['No.', 'Mã hợp đồng', 'Khách hàng', 'Ngày tạo/Hết hạn', 'Khóa học đăng kí', 'Thanh toán/Còn nợ', 'Nhân viên sale', 'Người tạo', 'Trạng thái đóng tiền', 'Trạng thái hợp đồng', 'Ghi chú', 'Công cụ'],
  // Query keys are canonical server filters.  The observed UI has paired
  // select/search controls for several labels; those control IDs belong in
  // `observedControls`, not in the query contract as duplicate semantics.
  filters: ['q', 'date_from', 'date_to', 'expiry_from', 'expiry_to', 'contract_status', 'course_id', 'course_status', 'discount', 'branch', 'payment_status', 'sales_owner', 'creator', 'expired_date_status'],
  observedControls: [
    'q', 'date_from', 'date_to', 'expiry_from', 'expiry_to',
    'contract_lifecycle', 'contract_status', 'course_id', 'course_search',
    'course_status_select', 'course_status', 'discount_id', 'discount',
    'center_id', 'branch', 'payment_status_select', 'payment_status',
    'sale_id', 'sale', 'created_by', 'creator', 'expired_date_status',
    'contract_table_length',
  ],
  actions: ['Lọc', 'Xóa lọc', 'Gia hạn nhiều HĐ', 'Tạo mới', 'Upload', 'Excel'],
  permissions: { read: ['ADMIN', 'STAFF', 'TEACHER'], write: ['ADMIN', 'STAFF'] },
  statusLabels: Object.freeze({ PENDING: 'Chưa đóng tiền', PARTIAL: 'Còn nợ', PAID: 'Đóng đủ', OVERDUE: 'Quá hạn', ACTIVE: 'Đang thực hiện', EXPIRED: 'Hợp đồng hết hạn', CANCELLED: 'Đã hủy', COMPLETED: 'Hoàn thành' }),
};
export const financeContractUpload = Object.freeze({
  route: financeContract.uploadRoute,
  headers: ['Mã hợp đồng', 'Mã học viên', 'Mã khách hàng', 'Mã khóa học', 'Số buổi đăng ký', 'Mã Gói học phí', 'Mã khoản thu', 'Tiền trước giảm giá', 'Mã giảm giá (khóa học)', 'Tiền giảm (khóa học)', 'Tiền sau giảm', 'Mã giảm giá (toàn bộ hợp đồng)', 'Tiền giảm giá (toàn bộ hợp đồng)', 'Ngày tạo hợp đồng', 'Ngày hết hạn', 'Tổng tiền trước giảm giá', 'Giảm giá trực tiếp', 'Tổng tiền sau giảm giá', 'Ghi chú hợp đồng', 'Mã lớp học', 'Ngày bắt đầu học'],
  fields: ['contract_code', 'student_code', 'customer_code', 'course_code', 'session_count', 'package_code', 'item_code', 'pre_discount_amount', 'course_discount_code', 'course_discount_amount', 'after_course_discount', 'contract_discount_code', 'contract_discount_amount', 'created_date', 'expiry_date', 'gross_total_before_discount', 'direct_discount', 'gross_total_after_discount', 'contract_note', 'class_code', 'start_date'],
  provenance: 'LOCAL_SYNTHETIC_UPLOAD_CONTRACT_OBSERVED_COLUMNS',
  canCommit: false,
});
export const financeContractExtension = Object.freeze({
  route: financeContract.extensionRoute,
  tabs: ['Gia hạn nhiều hợp đồng', 'Tạo hợp đồng lên khóa', 'Gia hạn theo khóa thu theo tháng lên lớp', 'Gia hạn theo khóa thu theo tháng lên lớp'],
  controls: ['select_class'],
  actions: [],
  downstream: 'UNKNOWN_REFERENCE_RENEWAL_RULES',
});
export const financeContractFields = [{ name: 'contract_code', label: 'Mã hợp đồng', required: true }, { name: 'created_date', label: 'Ngày tạo', type: 'date-text', required: true }, { name: 'customer_type', label: 'Khách hàng' }, { name: 'expiry_date', label: 'Ngày hết hạn', type: 'date-text' }, { name: 'total_amount', label: 'Tổng tiền', type: 'number', required: true }, { name: 'paid_amount', label: 'Đã thanh toán', type: 'number' }, { name: 'note', label: 'Ghi chú' }];
export const contractStatusLabel = status => financeContract.statusLabels[String(status || '').toUpperCase()] || '';
export const contractQuery = (filters = {}) => {
  const p = new URLSearchParams();
  const aliases = { sale: 'sales_owner', sales_owner: 'sales_owner', creator: 'creator' };
  financeContract.filters.forEach(key => {
    const value = String(filters[key] ?? '').trim();
    if (value) p.set(aliases[key] || key, value);
  });
  return p;
};
export const loadContracts = (apiFetch, filters = {}) => apiFetch(`/api/finance/contracts?${contractQuery(filters)}`);
export const exportContracts = (apiFetch, filters = {}) => apiFetch(`/api/export/finance-contracts?${contractQuery(filters)}`);
export const downloadContractTemplate = apiFetch => apiFetch('/api/finance/contract/upload/template');
export const previewContractUpload = (apiFetch, csv) => apiFetch('/api/finance/contract/upload/preview', { method: 'POST', body: { csv } });
export const commitContractUpload = (apiFetch, csv) => apiFetch('/api/finance/contract/upload/commit', { method: 'POST', body: { csv } });
export const loadContractExtensionClasses = (apiFetch, filters = {}) => {
  const params = new URLSearchParams();
  if (filters.class_id !== undefined && String(filters.class_id).trim()) params.set('class_id', String(filters.class_id).trim());
  if (filters.q !== undefined && String(filters.q).trim()) params.set('q', String(filters.q).trim());
  const suffix = params.toString();
  return apiFetch(`/api/finance/contract/get_extension_contract${suffix ? `?${suffix}` : ''}`);
};

const uploadCell = (row, field) => row?.[field] ?? '';
const uploadTable = rows => `<div class="table-wrap"><table class="finance-contract-upload-table"><thead><tr><th>STT</th>${financeContractUpload.headers.map(header => `<th>${esc(header)}</th>`).join('')}</tr></thead><tbody>${rows.length ? rows.map((row, index) => `<tr><td>${index + 1}</td>${financeContractUpload.fields.map(field => `<td>${esc(uploadCell(row, field))}</td>`).join('')}</tr>`).join('') : '<tr><td colspan="22">Không tìm thấy dữ liệu</td></tr>'}</tbody></table></div>`;
const uploadErrorText = errors => errors?.length ? errors.map(item => `Dòng ${item.row}: ${item.message}`).join(' · ') : '';
const uploadBlockerText = blockers => blockers?.length ? `Lưu bị khóa: ${blockers.join(' ')}` : '';

/** Render the observed upload child route; the private reference importer is
 * not called. Save stays blocked while the local schema/API cannot persist all
 * observed fields without inventing aggregate-money or class/date semantics. */
export async function renderContractUpload(screen, context = {}) {
  if (!screen || typeof context.api !== 'function') return false;
  let csvText = '';
  let preview = null;
  screen.innerHTML = `<section class="card finance-contract-upload-screen"><div class="screen-head"><h1>Upload hợp đồng</h1></div><div class="upload-toolbar"><label class="upload-file">Chọn tệp<input type="file" accept=".csv,text/csv" data-contract-upload-file></label><a href="/api/finance/contract/upload/template" download="finance-contract-template.csv">Tải file mẫu</a><label>Hiển thị <select data-contract-upload-page-size aria-label="Số dòng xem trước"><option>5</option><option selected>10</option><option>25</option><option>50</option></select> bản ghi</label></div><div data-contract-upload-preview>${uploadTable([])}</div><p class="error" data-contract-upload-error></p><div class="form-actions"><button type="button" class="primary" data-contract-upload-save disabled>Lưu</button></div></section>`;
  const fileInput = screen.querySelector('[data-contract-upload-file]');
  const previewTarget = screen.querySelector('[data-contract-upload-preview]');
  const errorTarget = screen.querySelector('[data-contract-upload-error]');
  const saveButton = screen.querySelector('[data-contract-upload-save]');
  const pageSizeInput = screen.querySelector('[data-contract-upload-page-size]');
  let previewRows = [];
  const renderRows = () => { previewTarget.innerHTML = uploadTable(previewRows.slice(0, Number(pageSizeInput?.value || 10))); };
  pageSizeInput?.addEventListener('change', renderRows);
  fileInput?.addEventListener('change', async () => {
    preview = null; saveButton.disabled = true; errorTarget.textContent = '';
    previewRows = [];
    const file = fileInput.files?.[0];
    if (!file) { renderRows(); return; }
    try {
      csvText = await file.text();
      const result = await previewContractUpload(context.api, csvText);
      preview = result?.data || result || null;
      previewRows = Array.isArray(preview?.rows) ? preview.rows : [];
      renderRows();
      errorTarget.textContent = [uploadErrorText(preview?.errors), uploadBlockerText(preview?.save_blockers)].filter(Boolean).join(' · ');
      saveButton.disabled = Boolean(preview?.errors?.length) || !preview?.valid_count || preview?.can_commit !== true;
    } catch (error) {
      errorTarget.textContent = String(error?.message || error); renderRows();
    }
  });
  saveButton?.addEventListener('click', async () => {
    if (saveButton.disabled || !csvText) return;
    saveButton.disabled = true; errorTarget.textContent = '';
    try {
      const result = await commitContractUpload(context.api, csvText);
      errorTarget.className = 'success'; errorTarget.textContent = `Đã lưu ${result?.data?.created_count || 0} hợp đồng cục bộ.`;
    } catch (error) {
      errorTarget.className = 'error'; errorTarget.textContent = String(error?.message || error); saveButton.disabled = false;
    }
  });
  return true;
}

/** Render only the observed class selector; downstream renewal semantics stay
 * explicitly UNKNOWN until more reference evidence is available. */
export async function renderContractExtension(screen, context = {}) {
  if (!screen || typeof context.api !== 'function') return false;
  screen.innerHTML = `<section class="card finance-contract-extension-screen"><div class="screen-head"><h1>Gia hạn nhiều hợp đồng</h1></div><div class="ref-tabs" role="tablist" aria-label="Tác vụ hợp đồng">${financeContractExtension.tabs.map((label, index) => `<button type="button" class="ref-tab${index === 0 ? ' active' : ''}" role="tab" id="contract-extension-tab-${index}" aria-selected="${index === 0 ? 'true' : 'false'}" aria-controls="contract-extension-panel-${index}" data-contract-extension-tab="${index}">${esc(label)}</button>`).join('')}</div><section role="tabpanel" id="contract-extension-panel-0" aria-labelledby="contract-extension-tab-0" data-contract-extension-panel="0"><label>Chọn lớp học<select name="select_class" data-contract-extension-class><option value="">Chọn lớp học</option></select></label></section>${financeContractExtension.tabs.slice(1).map((label, offset) => { const index = offset + 1; return `<section role="tabpanel" id="contract-extension-panel-${index}" aria-labelledby="contract-extension-tab-${index}" data-contract-extension-panel="${index}" hidden><p class="muted">Chưa có nội dung cục bộ được xác minh cho thẻ “${esc(label)}”.</p></section>`; }).join('')}</section>`;
  const select = screen.querySelector('[data-contract-extension-class]');
  const activateTab = index => {
    screen.querySelectorAll('[data-contract-extension-tab]').forEach(tab => {
      const active = Number(tab.dataset.contractExtensionTab) === index;
      tab.classList.toggle('active', active); tab.setAttribute('aria-selected', String(active));
    });
    screen.querySelectorAll('[data-contract-extension-panel]').forEach(panel => { panel.hidden = Number(panel.dataset.contractExtensionPanel) !== index; });
  };
  screen.querySelectorAll('[data-contract-extension-tab]').forEach(tab => tab.addEventListener('click', () => activateTab(Number(tab.dataset.contractExtensionTab))));
  try {
    const result = await loadContractExtensionClasses(context.api);
    const items = Array.isArray(result?.data?.items) ? result.data.items : Array.isArray(result?.items) ? result.items : [];
    select.innerHTML = `<option value="">Chọn lớp học</option>${items.map(item => `<option value="${esc(item.id)}">${esc(item.code)}${item.course_name ? ` — ${esc(item.course_name)}` : ''}</option>`).join('')}`;
  } catch (error) {
    select.innerHTML = '<option value="">Không có dữ liệu lớp học</option>';
  }
  return true;
}
export const renderContractRow = row => ({ code: row.contract_code || '', customer: row.student_name || row.customer_name || '', created: row.created_date || '', expiry: row.expiry_date || '', course: row.package_name || row.course_name || '', paid: row.paid_amount || 0, debt: row.debt_amount || 0, salesOwner: row.sales_owner || '', creator: row.created_by_name || row.created_by || '', paymentStatus: contractStatusLabel(row.payment_status), contractStatus: contractStatusLabel(row.contract_status), note: row.note || '' });

const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const natural = value => ({ 'Academic Team': 'Nguyễn Ngọc Mai', 'Center Administrator': 'Nguyễn Ngọc Mai', 'Academic Staff': 'Trần Minh Tú' }[String(value || '')] || value || '');
const date = value => { const m = String(value || '').match(/^(\d{4})-(\d{2})-(\d{2})/); return m ? `${m[3]}/${m[2]}/${m[1]}` : esc(value || ''); };
const money = value => `${Number(value || 0).toLocaleString('vi-VN')} VND`;
const badge = value => `<span class="badge">${esc(contractStatusLabel(value) || value || '')}</span>`;
const rowHtml = (row, index) => `<tr><td>${index + 1}</td><td>${esc(String(row.contract_code || '').replace(/^DEMO-CONTRACT-/, 'HD-EDU-'))}</td><td><span class="contract-multiline"><b>${esc(row.student_name || row.customer_name || '')}</b><small>${esc(row.student_code || '')}</small><small>${esc(row.student_phone || '')}</small></span></td><td><span class="contract-multiline"><span>Tạo: ${date(row.created_date)}</span><span>HH: ${date(row.expiry_date)}</span></span></td><td><span class="contract-multiline"><b>${esc(row.package_name || row.course_name || '')}</b><small>${esc(contractStatusLabel(row.contract_status))}</small></span></td><td><span class="contract-multiline"><span class="paid">${money(row.paid_amount)}</span><span class="debt">${money(row.debt_amount)}</span></span></td><td>${esc(natural(row.sales_owner))}</td><td>${esc(natural(row.created_by_name || row.created_by))}</td><td>${badge(row.payment_status)}</td><td>${badge(row.contract_status)}</td><td>${esc(row.note || '')}</td><td><button class="small-action" type="button" aria-label="Sửa">✎</button><button class="small-action" type="button" aria-label="Thêm thao tác">…⌄</button></td></tr>`;
const textFilter = (name, placeholder, dateInput = false) => `<label><input data-contract-filter="${name}" type="text" placeholder="${esc(placeholder)}"${dateInput ? ' inputmode="numeric" data-date-input' : ''}></label>`;
const selectFilter = (name, options, placeholder = '') => `<label><select data-contract-filter="${name}"><option value="">${esc(placeholder)}</option>${options.map(([value, label]) => `<option value="${esc(value)}">${esc(label)}</option>`).join('')}</select></label>`;
const lifecycle = [['ALL', 'Tất cả'], ['CANCELLED', 'Hủy'], ['WAITING', 'Chờ lớp'], ['ASSIGNED', 'Chưa thực hiện-Đã xếp lớp'], ['ACTIVE', 'Đang thực hiện'], ['COMPLETED', 'Hoàn thành'], ['REFUNDED', 'Hoàn trả'], ['PAUSED', 'Bảo lưu'], ['PENDING_APPROVAL', 'Đã ghi danh - Chờ Phê Duyệt'], ['TRANSFERRED', 'Chuyển nhượng']];
const courseStatuses = [['PAUSED', 'Bảo lưu'], ['ACTIVE', 'Đang học'], ['TRANSFERRED', 'Đã chuyển lớp'], ['COMPLETED', 'Hoàn thành'], ['DROPPED', 'Nghỉ học'], ['ASSIGNED', 'Chưa thực hiện-Đã xếp lớp'], ['WAITING', 'Chờ lớp'], ['PENDING_APPROVAL', 'Đã ghi danh - Chờ Phê Duyệt']];
const payments = [['PENDING', 'Chưa đóng tiền'], ['PARTIAL', 'Còn nợ'], ['PAID', 'Đóng đủ'], ['CANCELLED', 'Đã hủy']];
const expiry = [['DUE_SOON', 'Hợp đồng sắp hết hạn'], ['EXPIRED', 'Hợp đồng hết hạn']];
async function renderFinanceContracts(screen, context = {}) {
  // The shared app renderer owns this route's summary, CRUD wiring, server
  // filters, and role-aware actions.  Keep this module registered for the
  // autoload contract, but fail through so a second renderer cannot duplicate
  // controls or hide the observed route-specific shape.
  return false;
  /* istanbul ignore next -- retained as a standalone worker renderer for
   * bounded module development; the integrated shell uses the shared path. */
  const [payload, courses] = await Promise.all([context.api('/api/finance/contracts'), context.api('/api/courses').catch(() => ({ data: [] }))]);
  const rows = Array.isArray(payload?.data) ? payload.data : []; const courseOptions = (courses?.data || []).map(course => [course.id, course.name || course.code]);
  const people = [...new Set(rows.flatMap(row => [natural(row.sales_owner), natural(row.created_by_name || row.created_by)]).filter(Boolean))].map(name => [name, name]);
  const controls = [textFilter('q', 'Tìm trong bảng...'), textFilter('date_from', 'Từ ngày tạo', true), textFilter('date_to', 'Đến ngày tạo', true), textFilter('expiry_from', 'Từ ngày hết hạn', true), textFilter('expiry_to', 'Đến ngày hết hạn', true), selectFilter('contract_lifecycle', lifecycle), textFilter('contract_status', 'Trạng thái hợp đồng'), selectFilter('course_id', courseOptions), textFilter('course_search', 'Chọn khóa học'), selectFilter('course_status_select', courseStatuses), textFilter('course_status', 'Trạng thái khóa học'), selectFilter('discount_id', [['discount-2026', 'Ưu đãi nhập học kỳ thu 2026']]), textFilter('discount', 'Chọn ưu đãi'), selectFilter('center_id', [['demo', 'Trung tâm CenterOnline - Demo']]), textFilter('branch', 'Chi nhánh'), selectFilter('payment_status_select', payments), textFilter('payment_status', 'Trạng thái đóng tiền'), selectFilter('sale_id', people, 'Chọn sale'), textFilter('sale', 'Sale'), selectFilter('created_by', people), textFilter('creator', 'Người tạo'), selectFilter('expired_date_status', expiry, 'Tất cả'), '<label class="contract-page-size">Hiển thị <select data-contract-filter="contract_table_length"><option>10</option><option>25</option><option>50</option><option>100</option></select> bản ghi</label>'].join('');
  const headers = financeContract.columns.map(label => `<th>${esc(label)}</th>`).join('');
  screen.innerHTML = `<section class="card finance-contract-screen"><div class="screen-head"><h1>Hợp đồng</h1></div><div class="filter-strip">${controls}<button class="filter-apply" type="button">Lọc</button><button class="ghost" type="button" data-contract-clear>Xóa lọc</button><button class="primary" type="button">Gia hạn nhiều HĐ</button><button class="primary" type="button">Tạo mới</button><button class="upload-action" type="button">Upload</button><button class="ghost" type="button" data-contract-export>Excel</button></div><div class="table-wrap"><table><thead><tr>${headers}</tr></thead><tbody>${rows.slice(0, 10).map(rowHtml).join('')}</tbody></table></div></section>`;
  screen.querySelector('[data-contract-clear]')?.addEventListener('click', () => screen.querySelectorAll('[data-contract-filter]').forEach(node => { node.value = ''; }));
  screen.querySelector('[data-contract-export]')?.addEventListener('click', () => { const values = {}; screen.querySelectorAll('[data-contract-filter]').forEach(node => { if (node.value) values[node.dataset.contractFilter] = node.value; }); const link = document.createElement('a'); link.href = `/api/export/finance-contracts?${contractQuery(values)}`; link.download = 'finance-contracts.csv'; document.body.append(link); link.click(); link.remove(); });
  return true;
}
export function register(global) { const host = global || {}; host.financeContract = financeContract; host.financeContractUpload = financeContractUpload; host.financeContractExtension = financeContractExtension; if (typeof host.registerScreen === 'function') { host.registerScreen('/finance/contract', renderFinanceContracts); host.registerScreen('/sale/contract', renderFinanceContracts); host.registerScreen(financeContract.uploadRoute, renderContractUpload); host.registerScreen(financeContract.extensionRoute, renderContractExtension); } return financeContract; }

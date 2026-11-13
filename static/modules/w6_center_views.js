/* Route-owned Center layouts whose reference is not a generic table. */
import { esc } from './w6_screen_utils.js';

async function generatedRecords(centerEdu, route) {
  try {
    const payload = await centerEdu.api(`/api/generated/screens?route=${encodeURIComponent(route)}`);
    return Array.isArray(payload?.data?.records) ? payload.data.records : [];
  } catch { return []; }
}

async function courseOptions(centerEdu) {
  try {
    const payload = await centerEdu.api('/api/courses');
    const rows = Array.isArray(payload?.data) ? payload.data : [];
    const names = rows.map(row => String(row?.name || row?.course_name || row?.title || '').trim()).filter(Boolean);
    return [...new Set(names)];
  } catch { return []; }
}

function centerOptionsMarkup(records) {
  const rows = records.map((record, index) => {
    const d = record?.data || {};
    return `<tr data-record-id="${esc(record.id)}"><td>${index + 1}</td><td><strong>${esc(d.name || '')}</strong></td><td>${esc(d.center || '')}</td><td>${esc(d.effective_date || '')}</td><td><button type="button" class="small-action w6-center-options-edit" data-record-id="${esc(record.id)}" aria-label="Sửa">♢</button><button type="button" class="small-action w6-center-options-delete" data-record-id="${esc(record.id)}" aria-label="Xóa">♧</button></td></tr>`;
  }).join('');
  return `<section class="w6-center-options"><div class="w6-center-options-groups"><h2>⚙ Nhóm trường</h2><select class="w6-center-options-center" aria-label="Trung tâm"><option>Trung tâm CenterOnline - Demo</option></select><p class="active">Trường học</p><p>Nguồn dữ liệu</p><p>Phân loại hành động</p><p>Phân loại khách hàng</p><p>Kết quả</p><p>Đánh giá mức độ hài lòng</p><p>Đơn vị</p><p>Mục đích</p><p>Lý do xuất vật phẩm</p><p>Lý do nhập vật phẩm</p><p>Cấu hình trường thông tin bắt buộc</p><p>Cấu hình lịch sử chăm sóc</p></div><div class="w6-center-options-values"><header><h2>⚙ Giá trị tùy chọn</h2><button type="button" class="primary" data-w6-action="create">＋ Thêm mới</button></header><div class="table-wrap"><table><thead><tr><th>No.</th><th>Tên giá trị</th><th>Trung tâm áp dụng</th><th>Thời gian</th><th>Công cụ</th></tr></thead><tbody>${rows || '<tr class="empty-row"><td colspan="5">Không tìm thấy dữ liệu</td></tr>'}</tbody></table></div></div></section>`;
}

function centerOptionsModal(centerEdu, route, screen, record = null) {
  const data = record?.data || {};
  const wrap = document.createElement('div');
  wrap.className = 'modal-backdrop';
  wrap.innerHTML = `<div class="modal modal-wide" role="dialog" aria-modal="true" aria-labelledby="w6-center-options-dialog-title"><h2 id="w6-center-options-dialog-title">${record ? 'Sửa giá trị tùy chọn' : 'Thêm giá trị tùy chọn'}</h2><form class="w6-center-options-form"><div class="form-grid"><label>Nhập tên giá trị<input name="name" required value="${esc(data.name || '')}"></label><label>Trung tâm áp dụng<select name="center" required><option value="Trung tâm CenterOnline - Demo"${data.center === 'Trung tâm CenterOnline - Demo' || !data.center ? ' selected' : ''}>Trung tâm CenterOnline - Demo</option></select></label><label>Thời gian<input name="effective_date" type="date" value="${esc(data.effective_date || '')}"></label></div><div class="form-actions"><button type="button" class="ghost w6-center-options-cancel">Hủy</button><button type="submit" class="primary">Lưu</button></div><p class="error w6-center-options-error" role="alert"></p></form></div>`;
  document.body.append(wrap);
  const close = () => wrap.remove();
  wrap.querySelector('.w6-center-options-cancel')?.addEventListener('click', close);
  wrap.addEventListener('click', event => { if (event.target === wrap) close(); });
  wrap.querySelector('form')?.addEventListener('submit', async event => {
    event.preventDefault();
    const form = event.currentTarget;
    const body = { name: form.elements.name.value.trim(), center: form.elements.center.value, effective_date: form.elements.effective_date.value };
    const error = wrap.querySelector('.w6-center-options-error');
    error.textContent = '';
    try {
      const endpoint = record ? `/api/generated/screens/${encodeURIComponent(record.id)}` : '/api/generated/screens';
      const payload = record ? { route, data: body } : { route, data: body };
      await centerEdu.api(endpoint, { method: 'POST', body: payload });
      close();
      await renderCenterSpecial(centerEdu, route, screen);
    } catch (err) {
      error.textContent = err?.message || 'Không thể lưu giá trị tùy chọn.';
    }
  });
  wrap.querySelector('input[name="name"]')?.focus();
}

function centerOptionsDeleteModal(centerEdu, route, screen, record) {
  const wrap = document.createElement('div');
  wrap.className = 'modal-backdrop';
  wrap.innerHTML = `<div class="modal" role="dialog" aria-modal="true" aria-labelledby="w6-center-options-delete-title"><h2 id="w6-center-options-delete-title">Xóa giá trị tùy chọn?</h2><p>Bản ghi “${esc(record?.data?.name || '')}” sẽ được ẩn khỏi màn hình hiện tại.</p><div class="form-actions"><button type="button" class="ghost w6-center-options-cancel">Hủy</button><button type="button" class="primary danger w6-center-options-confirm-delete">Xóa</button></div><p class="error w6-center-options-error" role="alert"></p></div>`;
  document.body.append(wrap);
  const close = () => wrap.remove();
  wrap.querySelector('.w6-center-options-cancel')?.addEventListener('click', close);
  wrap.addEventListener('click', event => { if (event.target === wrap) close(); });
  wrap.querySelector('.w6-center-options-confirm-delete')?.addEventListener('click', async event => {
    const button = event.currentTarget;
    const error = wrap.querySelector('.w6-center-options-error');
    button.disabled = true;
    error.textContent = '';
    try {
      await centerEdu.api(`/api/generated/screens/${encodeURIComponent(record.id)}?route=${encodeURIComponent(route)}`, { method: 'DELETE' });
      close();
      await renderCenterSpecial(centerEdu, route, screen);
    } catch (err) {
      button.disabled = false;
      error.textContent = err?.message || 'Không thể xóa giá trị tùy chọn.';
    }
  });
  wrap.querySelector('.w6-center-options-cancel')?.focus();
}

function bindCenterOptionsActions(centerEdu, route, screen, records) {
  screen.querySelector('[data-w6-action="create"]')?.addEventListener('click', () => centerOptionsModal(centerEdu, route, screen));
  screen.querySelectorAll('.w6-center-options-edit').forEach(button => button.addEventListener('click', () => {
    const record = records.find(item => String(item.id) === String(button.dataset.recordId));
    if (record) centerOptionsModal(centerEdu, route, screen, record);
  }));
  screen.querySelectorAll('.w6-center-options-delete').forEach(button => button.addEventListener('click', () => {
    const record = records.find(item => String(item.id) === String(button.dataset.recordId));
    if (record) centerOptionsDeleteModal(centerEdu, route, screen, record);
  }));
}

function centerManagerMarkup(branches = []) {
  const rows = (branches || []).map(branch => `<tr data-branch-id="${esc(branch.id)}"><td>${esc(branch.code)}</td><td><input class="w6-branch-name" value="${esc(branch.name)}" aria-label="Tên chi nhánh ${esc(branch.code)}"></td><td><span class="w6-branch-status">${branch.status === 'active' ? 'Hoạt động' : 'Đã khóa'}</span></td><td><button type="button" class="small-action w6-branch-save" data-branch-id="${esc(branch.id)}">Lưu</button><button type="button" class="small-action w6-branch-toggle" data-branch-id="${esc(branch.id)}">${branch.status === 'active' ? 'Khóa' : 'Mở khóa'}</button><button type="button" class="small-action danger w6-branch-delete" data-branch-id="${esc(branch.id)}">Xóa</button></td></tr>`).join('');
  return `<section class="w6-center-manager"><header class="w6-center-manager-head"><div><h1>⚙ Cơ cấu tổ chức trung tâm</h1><p class="muted">Chi nhánh trực thuộc tenant hiện tại</p></div><button type="button" class="primary" data-w6-branch-create>＋ Thêm chi nhánh</button></header><div class="table-wrap"><table><thead><tr><th>Mã</th><th>Tên chi nhánh</th><th>Trạng thái</th><th>Hành động</th></tr></thead><tbody>${rows || '<tr class="empty-row"><td colspan="4">Chưa có chi nhánh. Tạo chi nhánh đầu tiên.</td></tr>'}</tbody></table></div><p class="error w6-branch-error" role="alert"></p></section>`;
}

function centerBranchModal(centerEdu, route, screen, record = null) {
  const wrap = document.createElement('div');
  wrap.className = 'modal-backdrop';
  wrap.innerHTML = `<div class="modal" role="dialog" aria-modal="true"><h2>${record ? 'Sửa chi nhánh' : 'Thêm chi nhánh'}</h2><form><label>Mã chi nhánh<input name="code" required maxlength="64" value="${esc(record?.code || '')}" ${record ? 'readonly' : ''}></label><label>Tên chi nhánh<input name="name" required maxlength="160" value="${esc(record?.name || '')}"></label><div class="form-actions"><button type="button" class="ghost close-modal">Hủy</button><button type="submit" class="primary">Lưu</button></div><p class="error modal-error" role="alert"></p></form></div>`;
  document.body.append(wrap);
  const close = () => wrap.remove();
  wrap.querySelector('.close-modal').onclick = close;
  wrap.addEventListener('click', event => { if (event.target === wrap) close(); });
  wrap.querySelector('form').onsubmit = async event => {
    event.preventDefault();
    const form = event.currentTarget, error = wrap.querySelector('.modal-error');
    error.textContent = '';
    try {
      const body = { code: form.elements.code.value.trim(), name: form.elements.name.value.trim() };
      await centerEdu.api(record ? `/api/branch-manager/branches/${encodeURIComponent(record.id)}` : '/api/branch-manager/branches', { method: 'POST', body });
      close();
      await renderCenterSpecial(centerEdu, route, screen);
    } catch (err) { error.textContent = err?.message || 'Không thể lưu chi nhánh.'; }
  };
  wrap.querySelector('input[name="name"]')?.focus();
}

async function renderCenterManager(centerEdu, route, screen) {
  let branches = [];
  try { branches = (await centerEdu.api('/api/branch-manager/branches')).data || []; }
  catch (err) { screen.innerHTML = `<section class="w6-center-manager"><h1>⚙ Cơ cấu tổ chức trung tâm</h1><p class="error" role="alert">${esc(err?.message || 'Bạn không có quyền quản lý chi nhánh.')}</p></section>`; return; }
  screen.innerHTML = centerManagerMarkup(branches);
  screen.querySelector('[data-w6-branch-create]')?.addEventListener('click', () => centerBranchModal(centerEdu, route, screen));
  const error = screen.querySelector('.w6-branch-error');
  screen.querySelectorAll('.w6-branch-save').forEach(button => button.addEventListener('click', async () => {
    const row = button.closest('tr'), id = button.dataset.branchId;
    try { await centerEdu.api(`/api/branch-manager/branches/${encodeURIComponent(id)}`, { method: 'POST', body: { name: row.querySelector('.w6-branch-name').value.trim() } }); await renderCenterManager(centerEdu, route, screen); }
    catch (err) { error.textContent = err?.message || 'Không thể cập nhật chi nhánh.'; }
  }));
  screen.querySelectorAll('.w6-branch-toggle').forEach(button => button.addEventListener('click', async () => {
    const branch = branches.find(item => String(item.id) === String(button.dataset.branchId));
    try { await centerEdu.api(`/api/branch-manager/branches/${encodeURIComponent(branch.id)}`, { method: 'POST', body: { status: branch.status === 'active' ? 'inactive' : 'active' } }); await renderCenterManager(centerEdu, route, screen); }
    catch (err) { error.textContent = err?.message || 'Không thể đổi trạng thái chi nhánh.'; }
  }));
  screen.querySelectorAll('.w6-branch-delete').forEach(button => button.addEventListener('click', async () => {
    const branch = branches.find(item => String(item.id) === String(button.dataset.branchId));
    if (!branch || !window.confirm(`Xóa chi nhánh ${branch.name}?`)) return;
    try { await centerEdu.api(`/api/branch-manager/branches/${encodeURIComponent(branch.id)}`, { method: 'DELETE' }); await renderCenterManager(centerEdu, route, screen); }
    catch (err) { error.textContent = err?.message || 'Không thể xóa chi nhánh.'; }
  }));
}

function centerDocumentPermissionMarkup(courses) {
  const options = (courses || []).map(course => `<option value="${esc(course)}">${esc(course)}</option>`).join('');
  return `<section class="w6-document-permission"><header><h1>Phân quyền tài liệu</h1></header><div class="w6-document-controls"><select aria-label="Chọn khóa học"><option value="">Chọn khóa học</option>${options}</select><input placeholder="Tìm kiếm ..." aria-label="Tìm kiếm ..."><button type="button" class="primary">Cập nhật</button></div></section>`;
}

function installCenterSpecialStyles() {
  if (document.querySelector('#w6-center-special-styles')) return;
  const style = document.createElement('style'); style.id = 'w6-center-special-styles'; style.textContent = `
    #screen:has(.w6-center-options) + .filter-strip,#screen:has(.w6-document-permission) + .filter-strip,#screen:has(.w6-center-manager) + .filter-strip{display:none}.w6-center-options-values header{display:flex;align-items:center;justify-content:space-between}.w6-center-options-values header h2{padding:0;border:0}.w6-center-options-values table{width:100%;border-collapse:collapse}.w6-center-options-values th,.w6-center-options-values td{padding:12px 10px;border:1px solid #edf0f6}.w6-center-options-values th{text-align:left}
    .w6-center-manager{width:100%}.w6-center-manager-head{display:flex;align-items:center;justify-content:space-between;gap:16px;margin-bottom:16px}.w6-center-manager-head h1{margin:0}.w6-center-manager table{width:100%;border-collapse:collapse}.w6-center-manager th,.w6-center-manager td{padding:10px;border:1px solid #edf0f6;text-align:left}.w6-center-manager td input{height:32px;border:1px solid #dfe5ee;border-radius:3px;padding:4px 8px}.w6-center-manager td button{margin-right:6px}
    .w6-document-permission header h1{margin:0;font-size:18px;font-weight:500}.w6-document-controls{display:grid;grid-template-columns:1fr 1fr auto;gap:30px;padding:24px}.w6-document-controls input,.w6-document-controls select{height:36px;border:1px solid #e1e5ed;border-radius:3px;padding:0 12px}.w6-document-controls button{height:36px}
    @media(max-width:800px){.w6-center-options{grid-template-columns:1fr}.w6-document-controls{grid-template-columns:1fr}}
  `; document.head.append(style);
}

export async function renderCenterSpecial(centerEdu, route, screen) {
  installCenterSpecialStyles();
  const records = await generatedRecords(centerEdu, route);
  if (route === '/center/options') screen.innerHTML = centerOptionsMarkup(records);
  else if (route === '/center/manager/index') { await renderCenterManager(centerEdu, route, screen); return true; }
  else if (route === '/center/document-permission') screen.innerHTML = centerDocumentPermissionMarkup(await courseOptions(centerEdu));
  if (route === '/center/options') bindCenterOptionsActions(centerEdu, route, screen, records);
  // The shared shell appends legacy spec filters beside #screen after route render.
  // These three reference layouts own their controls, so remove that adjacent duplicate.
  const legacyFilters = screen.nextElementSibling;
  if (legacyFilters?.classList.contains('filter-strip')) legacyFilters.remove();
  return true;
}

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
    return `<tr><td>${index + 1}</td><td><strong>${esc(d.name || '')}</strong></td><td>${esc(d.center || '')}</td><td>${esc(d.effective_date || '')}</td><td><button type="button" class="small-action" aria-label="Sửa">♢</button><button type="button" class="small-action" aria-label="Xóa">♧</button></td></tr>`;
  }).join('');
  return `<section class="w6-center-options"><div class="w6-center-options-groups"><h2>⚙ Nhóm trường</h2><select class="w6-center-options-center" aria-label="Trung tâm"><option>Trung tâm CenterOnline - Demo</option></select><p class="active">Trường học</p><p>Nguồn dữ liệu</p><p>Phân loại hành động</p><p>Phân loại khách hàng</p><p>Kết quả</p><p>Đánh giá mức độ hài lòng</p><p>Đơn vị</p><p>Mục đích</p><p>Lý do xuất vật phẩm</p><p>Lý do nhập vật phẩm</p><p>Cấu hình trường thông tin bắt buộc</p><p>Cấu hình lịch sử chăm sóc</p></div><div class="w6-center-options-values"><header><h2>⚙ Giá trị tùy chọn</h2><button type="button" class="primary" data-w6-action="create">＋ Thêm mới</button></header><div class="table-wrap"><table><thead><tr><th>No.</th><th>Tên giá trị</th><th>Trung tâm áp dụng</th><th>Thời gian</th><th>Công cụ</th></tr></thead><tbody>${rows || '<tr class="empty-row"><td colspan="5">Không tìm thấy dữ liệu</td></tr>'}</tbody></table></div></div></section>`;
}

function centerManagerMarkup(records) {
  const rows = records.map(record => record?.data || {}).filter(Boolean);
  const center = rows[0]?.center || '';
  const items = rows.map(d => `<li>▦ ${esc(d.fullname || '')}${d.department ? ` <em>(${esc(d.department)})</em>` : ''}</li>`).join('');
  return `<section class="w6-center-manager"><h1>⚙ Cơ cấu tổ chức trung tâm</h1>${center || items ? `<ul><li>⊟ 🏢 ${esc(center)}${center ? ' <em>(center)</em>' : ''}${items ? `<ul>${items}</ul>` : ''}</li></ul>` : '<p class="empty">Không tìm thấy dữ liệu</p>'}</section>`;
}

function centerDocumentPermissionMarkup(courses) {
  return `<section class="w6-document-permission"><header><h1>Phân quyền tài liệu</h1></header><div class="w6-document-controls"><select aria-label="Chọn khóa học"><option selected>Chọn khóa học</option>${courses.map(course => `<option>${esc(course)}</option>`).join('')}</select><input placeholder="Tìm kiếm ..." aria-label="Tìm kiếm ..."><button type="button" class="primary">▣ Cập nhật</button></div></section>`;
}

function installCenterSpecialStyles() {
  if (document.querySelector('#w6-center-special-styles')) return;
  const style = document.createElement('style'); style.id = 'w6-center-special-styles'; style.textContent = `
    #screen:has(.w6-center-options) + .filter-strip,#screen:has(.w6-document-permission) + .filter-strip,#screen:has(.w6-center-manager) + .filter-strip{display:none}.w6-center-options-values header{display:flex;align-items:center;justify-content:space-between}.w6-center-options-values header h2{padding:0;border:0}.w6-center-options-values table{width:100%;border-collapse:collapse}.w6-center-options-values th,.w6-center-options-values td{padding:12px 10px;border:1px solid #edf0f6}.w6-center-options-values th{text-align:left}
    .w6-center-manager{width:410px}.w6-center-manager ul{list-style:none;margin:0;padding:18px 28px;color:#565d6c}.w6-center-manager li{padding:6px 0}.w6-center-manager li ul{padding:0 22px}.w6-center-manager em{color:#aaa}
    .w6-document-permission header h1{margin:0;font-size:18px;font-weight:500}.w6-document-controls{display:grid;grid-template-columns:1fr 1fr auto;gap:30px;padding:24px}.w6-document-controls input,.w6-document-controls select{height:36px;border:1px solid #e1e5ed;border-radius:3px;padding:0 12px}.w6-document-controls button{height:36px}
    @media(max-width:800px){.w6-center-options{grid-template-columns:1fr}.w6-document-controls{grid-template-columns:1fr}}
  `; document.head.append(style);
}

export async function renderCenterSpecial(centerEdu, route, screen) {
  installCenterSpecialStyles();
  const records = await generatedRecords(centerEdu, route);
  if (route === '/center/options') screen.innerHTML = centerOptionsMarkup(records);
  else if (route === '/center/manager/index') screen.innerHTML = centerManagerMarkup(records);
  else if (route === '/center/document-permission') screen.innerHTML = centerDocumentPermissionMarkup(await courseOptions(centerEdu));
  // The shared shell appends legacy spec filters beside #screen after route render.
  // These three reference layouts own their controls, so remove that adjacent duplicate.
  const legacyFilters = screen.nextElementSibling;
  if (legacyFilters?.classList.contains('filter-strip')) legacyFilters.remove();
  return true;
}

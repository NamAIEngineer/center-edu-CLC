/* W6 route-owned dual-view tabs. No shell/app ownership. */
const VIEW_RULES = Object.freeze({
  '/callcenter/get-statistic': { field: 'direction', values: ['inbound', 'outbound'], labels: ['Thống kê cuộc gọi vào', 'Thống kê cuộc gọi ra'] },
  '/cso/support': { field: 'scope', values: ['external', 'internal'], labels: ['Tiếp nhận từ người dùng', 'Hỗ trợ nội bộ'] },
  '/center/upload_address': { field: 'target', values: ['student', 'potential'], labels: ['Công cụ chỉnh sửa địa chỉ học sinh', 'Công cụ chỉnh sửa địa chỉ khách hàng tiềm năng'] },
});

export function bindW6Tabs(route, screen, records = []) {
  const rule = VIEW_RULES[route];
  if (!rule || !screen || screen.dataset.w6TabsBound === route) return false;
  const tabs = [...screen.querySelectorAll('.ref-tab')];
  if (tabs.length < 2) return false;
  screen.dataset.w6TabsBound = route;
  const source = Array.isArray(records) ? records : [];
  const apply = (index) => {
    tabs.forEach((tab, i) => { tab.classList.toggle('active', i === index); tab.setAttribute('aria-selected', i === index ? 'true' : 'false'); });
    const title = screen.querySelector('.screen-title h1');
    if (title) title.textContent = rule.labels[index];
    const rows = [...screen.querySelectorAll('tbody tr[data-record-id]')];
    const hasDiscriminatedSource = source.some(item => String(item.data?.[rule.field] || '').trim());
    let visibleNo = 1;
    rows.forEach((row) => {
      const record = source.find(item => String(item.id) === String(row.dataset.recordId));
      const marker = String(record?.data?.[rule.field] || '').trim();
      // Once the route has persisted view-specific rows, unmarked legacy rows
      // must not leak into either tab. This keeps each tab a true projection.
      row.hidden = hasDiscriminatedSource ? marker !== rule.values[index] : false;
      if (!row.hidden) {
        const noCell = row.querySelector('td:first-child');
        if (noCell) noCell.textContent = String(visibleNo++);
      }
    });
    if (route === '/callcenter/get-statistic') {
      const staffHead = screen.querySelector('thead th:nth-child(2)');
      if (staffHead) staffHead.textContent = index === 0 ? 'Nhân viên nghe' : 'Nhân viên gọi';
    }
    if (route === '/center/upload_address') {
      const file = screen.querySelector('input[type=file]');
      if (file) file.setAttribute('aria-label', index === 0 ? 'Tệp địa chỉ học sinh' : 'Tệp địa chỉ khách hàng tiềm năng');
      screen.dataset.w6UploadTarget = rule.values[index];
      screen.dataset.w6UploadIndex = String(index);
      if (file) file.value = '';
      const body = screen.querySelector('tbody');
      if (body) body.innerHTML = '<tr class="empty-row"><td colspan="16">Không tìm thấy dữ liệu</td></tr>';
      const count = screen.querySelector('.upload-address-footer > span');
      if (count) count.textContent = 'Hiển thị 0 đến 0 của 0 bản ghi';
    }
    screen.dispatchEvent(new CustomEvent('w6:view-change', { detail: { route, index, value: rule.values[index] } }));
  };
  tabs.forEach((tab, index) => tab.addEventListener('click', () => apply(index)));
  if (route === '/center/upload_address') {
    const handleFile = async (event) => {
      const file = event.target.closest?.('input[type=file]');
      if (!file || !screen.contains(file)) return;
      // The generic generated-screen filter listener also observes file
      // controls and can replace the preview tbody. Own the event in capture
      // phase so the import preview remains visible and target-specific.
      event.stopImmediatePropagation();
      const selected = file.files?.[0];
      if (!selected) return;
      const text = await readFileText(selected);
      const parsed = parseCsv(text);
      const columns = ['Chi nhánh','Mã học viên','Học viên','Mã định danh','Tên tiếng anh','Giới tính','Ngày sinh','Tài khoản','SĐT','Email','Tỉnh cũ','Huyện cũ','Xã phường','Tỉnh mới','Phường xã mới'];
      const headers = parsed[0] || [];
      const hasHeader = headers.some(value => columns.includes(value.trim()));
      const dataRows = hasHeader ? parsed.slice(1) : parsed;
      const body = screen.querySelector('tbody');
      if (body) body.innerHTML = dataRows.filter(row => row.some(value => value.trim())).map((row, index) => `<tr data-import-target="${rule.values[Number(screen.dataset.w6UploadIndex || 0)]}"><td>${index + 1}</td>${columns.map((_, col) => `<td>${escapeHtml(row[col] || '')}</td>`).join('')}</tr>`).join('') || '<tr class="empty-row"><td colspan="16">Không tìm thấy dữ liệu</td></tr>';
      const count = dataRows.filter(row => row.some(value => value.trim())).length;
      const summary = screen.querySelector('.upload-address-footer > span');
      if (summary) summary.textContent = `Hiển thị ${count ? 1 : 0} đến ${count} của ${count} bản ghi`;
      screen.dataset.w6UploadTarget = rule.values[Number(screen.dataset.w6UploadIndex || 0)];
    };
    // Delegate from the screen root so a generated-screen rerender cannot
    // orphan the preview listener or replace the input before it runs.
    screen.addEventListener('change', handleFile, true);
  }
  apply(0);
  return true;
}

function readFileText(file) {
  if (typeof file.text === 'function') return file.text();
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result || ''));
    reader.onerror = () => reject(reader.error || new Error('Không đọc được tệp CSV'));
    reader.readAsText(file);
  });
}

function parseCsv(text) {
  const rows = []; let row = []; let value = ''; let quoted = false;
  for (let i = 0; i < text.length; i++) {
    const ch = text[i];
    if (ch === '"' && quoted && text[i + 1] === '"') { value += '"'; i++; }
    else if (ch === '"') quoted = !quoted;
    else if (ch === ',' && !quoted) { row.push(value); value = ''; }
    else if ((ch === '\n' || ch === '\r') && !quoted) { if (ch === '\r' && text[i + 1] === '\n') i++; row.push(value); if (row.some(cell => cell.trim())) rows.push(row); row = []; value = ''; }
    else value += ch;
  }
  row.push(value); if (row.some(cell => cell.trim())) rows.push(row);
  return rows;
}
function escapeHtml(value) { return String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c])); }
export { VIEW_RULES, parseCsv, readFileText };

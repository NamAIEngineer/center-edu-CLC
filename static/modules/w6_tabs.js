/* W6 route-owned dual-view tabs. No shell/app ownership. */
const VIEW_RULES = Object.freeze({
  '/callcenter/get-statistic': { field: 'direction', values: ['inbound', 'outbound'], labels: ['Thống kê cuộc gọi vào', 'Thống kê cuộc gọi ra'] },
  '/cso/support': { field: 'scope', values: ['external', 'internal'], labels: ['Tiếp nhận từ người dùng', 'Hỗ trợ nội bộ'] },
  // The current observed screen exposes import history and an instructions
  // panel. Keep the target discriminator for imported preview rows, but do
  // not present the archived student/potential labels as the live contract.
  '/center/upload_address': { field: 'target', values: ['history', 'guide'], labels: ['Lịch sử import', 'Hướng dẫn'] },
});

export function bindW6Tabs(route, screen, records = []) {
  const rule = VIEW_RULES[route];
  if (!rule || !screen || screen.dataset.w6TabsBound === route) return false;
  const tabs = [...screen.querySelectorAll('.ref-tab')];
  if (tabs.length < 2) return false;
  screen.dataset.w6TabsBound = route;
  const source = Array.isArray(records) ? records : [];
  const apply = (index) => {
    const activeTabs = [...screen.querySelectorAll('.ref-tabs .ref-tab')];
    activeTabs.forEach((tab, i) => { tab.classList.toggle('active', i === index); tab.setAttribute('aria-selected', i === index ? 'true' : 'false'); });
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
      if (file) file.setAttribute('aria-label', index === 0 ? 'Tệp import địa chỉ' : 'Tệp hướng dẫn import');
      screen.dataset.w6UploadTarget = rule.values[index];
      screen.dataset.w6UploadIndex = String(index);
      if (file) file.value = '';
      const body = screen.querySelector('tbody');
      if (body) body.innerHTML = index === 0
        ? '<tr class="empty-row"><td colspan="16">Không tìm thấy dữ liệu</td></tr>'
        : '<tr class="empty-row"><td colspan="16">Chọn tệp CSV để xem hướng dẫn import</td></tr>';
      screen.querySelector('[data-w6-upload-guide]')?.remove();
      if (index === 1) {
        const guide = document.createElement('div');
        guide.dataset.w6UploadGuide = 'true';
        guide.className = 'w6-upload-guide';
        guide.innerHTML = '<h3>Hướng dẫn import</h3><p>Tệp CSV cần có hàng tiêu đề theo đúng thứ tự cột. Kiểm tra bản xem trước trước khi bấm Lưu.</p><a class="w6-upload-template" download="mau_import_dia_chi.csv" href="data:text/csv;charset=utf-8,%EF%BB%BFChi%20nh%C3%A1nh%2CM%C3%A3%20h%E1%BB%8Dc%20vi%C3%AAn%2CH%E1%BB%8Dc%20vi%C3%AAn%2CM%C3%A3%20%C4%91%E1%BB%8Bnh%20danh%2CT%C3%AAn%20ti%E1%BA%BFng%20anh%2CGi%E1%BB%9Bi%20t%C3%ADnh%2CNg%C3%A0y%20sinh%2CT%C3%A0i%20kho%E1%BA%A3n%2CS%C4%90T%2CEmail%2CT%E1%BB%89nh%20c%C5%A9%2CHuy%E1%BB%87n%20c%C5%A9%2CX%C3%A3%20ph%C6%B0%E1%BB%9Dng%2CT%E1%BB%89nh%20m%E1%BB%9Bi%2CPh%C6%B0%E1%BB%9Dng%20x%C3%A3%20m%E1%BB%9Bi%0A">Tải mẫu CSV</a>';
        screen.querySelector('.w6-table-card')?.after(guide);
      }
      const count = screen.querySelector('.upload-address-footer > span');
      if (count) count.textContent = 'Hiển thị 0 đến 0 của 0 bản ghi';
    }
    screen.dispatchEvent(new CustomEvent('w6:view-change', { detail: { route, index, value: rule.values[index] } }));
  };
  tabs.forEach((tab, index) => {
    tab.addEventListener('click', () => apply(index));
    if (route === '/center/upload_address') tab.dataset.w6UploadBound = 'true';
  });
  if (route === '/center/upload_address') {
    // app.js may reconcile tabs from its archived screen-spec after this
    // renderer runs. Re-label and rebind replacement nodes at this owner seam
    // without changing the protected shell or its metadata source.
    const reconcile = () => {
      if (typeof window !== 'undefined' && window.location.pathname.split('?')[0] !== route) {
        screen._w6UploadTabObserver?.disconnect();
        screen._w6UploadTabObserver = null;
        return;
      }
      const current = [...screen.querySelectorAll('.ref-tabs .ref-tab')];
      if (current.length < rule.labels.length) return;
      current.slice(0, rule.labels.length).forEach((tab, index) => {
        if (tab.textContent.trim() !== rule.labels[index]) tab.textContent = rule.labels[index];
        if (tab.dataset.w6UploadBound === 'true') return;
        tab.dataset.w6UploadBound = 'true';
        tab.addEventListener('click', () => apply(index));
      });
    };
    reconcile();
    screen._w6UploadTabObserver?.disconnect();
    screen._w6UploadTabObserver = new MutationObserver(reconcile);
    screen._w6UploadTabObserver.observe(screen, { childList: true, subtree: true });
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

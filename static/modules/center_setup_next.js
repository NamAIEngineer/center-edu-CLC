/* Center teacher directory contract UI. Registry integration is intentionally
 * separate from app.js so this module can be mounted without global changes. */
export const CENTER_TEACHER_CONTRACT = Object.freeze({
  route: "/center/teacher",
  columns: ["No.", "Giáo viên", "Tài khoản", "Liên hệ", "Quốc tịch", "Phân quyền", "Trạng thái", "Hành động"],
  filters: [
    { name: "q", placeholder: "Tìm kiếm", type: "search" },
    { name: "nationality", placeholder: "Chọn quốc tịch", type: "select" },
    { name: "status", placeholder: "Chọn trạng thái", type: "select", options: ["Kích hoạt", "Đang khóa"] },
  ],
  pageSizes: [10, 25, 50, 100],
  actions: ["create", "update", "delete", "export"],
});

// Route-local copy used by setup/utility screens. Keep labels in Vietnamese
// and spell the address utility consistently with the navigation contract.
export const CENTER_SETUP_COPY = Object.freeze({
  addressToolTitle: "Công cụ chỉnh sửa địa chỉ",
  addressStudentTab: "Công cụ chỉnh sửa địa chỉ học sinh",
  addressProspectTab: "Công cụ chỉnh sửa địa chỉ khách hàng tiềm năng",
  exportConfigTitle: "Cấu hình xuất Excel báo cáo",
});

export function bindClassroomTabs(root = document) {
  const screen = root.querySelector?.('#screen') || root;
  if (!screen || screen.dataset.classroomTabsBound === '/setup/classroom' || String(window.location.pathname || '').split('?')[0] !== '/setup/classroom') return;
  const tabs = [...screen.querySelectorAll('.ref-tabs .ref-tab')]; if (tabs.length < 2) return;
  screen.dataset.classroomTabsBound = '/setup/classroom';
  const payloadRows = payload => {
    if (Array.isArray(payload)) return payload;
    if (Array.isArray(payload?.data)) return payload.data;
    if (Array.isArray(payload?.data?.items)) return payload.data.items;
    if (Array.isArray(payload?.items)) return payload.items;
    return [];
  };
  const cell = (row, value) => { const td = document.createElement('td'); td.textContent = value == null ? '' : String(value); return td; };
  const refreshRows = async index => {
    const tbody = screen.querySelector('table tbody'); if (!tbody || typeof fetch !== 'function') return;
    const endpoint = index === 1 ? '/api/session-slots' : '/api/classrooms';
    try {
      const response = await fetch(endpoint, { credentials: 'same-origin' });
      if (!response.ok) throw new Error(`classroom tab request failed: ${response.status}`);
      const rows = payloadRows(await response.json());
      tbody.replaceChildren();
      rows.forEach((row, rowIndex) => {
        const tr = document.createElement('tr');
        tr.dataset.view = index === 1 ? 'slots' : 'rooms';
        const values = index === 1
          ? [rowIndex + 1, row.code, row.name, `${row.start_time || ''}${row.end_time ? `–${row.end_time}` : ''}`, row.status]
          : [rowIndex + 1, row.code, row.name, row.capacity, row.description || '—', row.status];
        values.forEach(value => tr.append(cell(row, value)));
        const action = cell(row, '');
        const button = document.createElement('button'); button.type = 'button'; button.className = 'small-action'; button.textContent = 'Sửa';
        if (row.id != null) button.dataset.id = row.id;
        action.append(button); tr.append(action); tbody.append(tr);
      });
      screen.dataset.classroomRowsSource = endpoint;
      screen.dispatchEvent(new CustomEvent('classroom-tab-data-change', { detail: { index, endpoint, count: rows.length } }));
    } catch (error) {
      screen.dataset.classroomTabError = String(error?.message || error);
      screen.dispatchEvent(new CustomEvent('classroom-tab-data-error', { detail: { index, endpoint, error } }));
    }
  };
  tabs.forEach((tab, index) => tab.addEventListener('click', () => {
    tabs.forEach((item, i) => { const active = i === index; item.classList.toggle('active', active); item.setAttribute('aria-selected', active ? 'true' : 'false'); });
    screen.dataset.classroomView = index === 1 ? 'slots' : 'rooms';
    refreshRows(index);
  }));
  // The renderer starts on rooms.  Keep the initial table intact, while a
  // subsequent click loads the authoritative persisted table for that view.
  screen.dataset.classroomView = 'rooms';
}
if (typeof document !== 'undefined' && typeof MutationObserver === 'function') { const root = document.querySelector('#screen') || document.body; new MutationObserver(() => bindClassroomTabs(document)).observe(root, { childList: true, subtree: true }); [0,120,500].forEach(delay => setTimeout(() => bindClassroomTabs(document), delay)); }

export function teacherQuery(filters = {}) {
  const params = new URLSearchParams();
  for (const [key, value] of Object.entries(filters)) {
    if (value !== undefined && value !== null && String(value).trim() !== "") params.set(key, value);
  }
  return params.toString();
}

export async function loadTeachers(filters = {}, fetcher = fetch) {
  const query = teacherQuery(filters);
  const response = await fetcher(`/api/center/teachers${query ? `?${query}` : ""}`, { credentials: "same-origin" });
  if (!response.ok) throw new Error(`teacher list failed: ${response.status}`);
  return response.json();
}

export function renderTeacherRows(tbody, rows, { canEdit = false } = {}) {
  tbody.replaceChildren();
  for (const [index, row] of rows.entries()) {
    const tr = document.createElement("tr");
    const cells = [index + 1, row.full_name, row.username,
      [row.phone, row.email].filter(Boolean).join(" / "), row.nationality,
      row.role || "Giáo viên", row.status];
    for (const value of cells) {
      const td = document.createElement("td"); td.textContent = value || ""; tr.append(td);
    }
    const action = document.createElement("td");
    if (canEdit) { const button = document.createElement("button"); button.type = "button"; button.dataset.teacherId = row.id; button.textContent = "⋯"; action.append(button); }
    tr.append(action); tbody.append(tr);
  }
}

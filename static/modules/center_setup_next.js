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

const classroomTabButtons = new WeakSet();
const classroomViews = new WeakMap();

function classroomPresentation(screen, index) {
  screen.classList.add('classroom-setup-screen');
  screen.querySelector('.screen-head')?.remove();
  screen.querySelector('#export-classrooms, #export-session-slots')?.remove();
  screen.querySelector('.table-toolbar')?.remove();
  screen.querySelector('#classroom-filter-clear, #session-slot-clear')?.remove();
  let tabs = screen.querySelector('.ref-tabs');
  if (!tabs) {
    tabs = document.createElement('div'); tabs.className = 'ref-tabs'; tabs.setAttribute('role', 'tablist');
    tabs.innerHTML = ['Phòng học', 'Ca học'].map(label => `<button type="button" class="ref-tab" role="tab">${label}</button>`).join('');
    screen.prepend(tabs);
  }
  const filter = screen.querySelector('.filter-strip');
  if (filter) {
    filter.querySelectorAll('label').forEach(label => [...label.childNodes].filter(node => node.nodeType === 3).forEach(node => node.remove()));
    const input = filter.querySelector('input'); if (input) input.placeholder = 'Tìm...';
    if (!filter.querySelector('.classroom-create')) {
      const create = document.createElement('button'); create.type = 'button'; create.className = 'primary classroom-create'; create.textContent = '+ Thêm mới';
      create.addEventListener('click', () => (index === 1 ? globalThis.sessionSlotModal : globalThis.classroomModal)?.());
      filter.append(create);
    }
  }
  tabs.querySelectorAll('.ref-tab').forEach((tab, i) => {
    tab.classList.toggle('active', i === index); tab.setAttribute('aria-selected', String(i === index));
  });
  if (!document.querySelector('#classroom-setup-presentation')) {
    const style = document.createElement('style'); style.id = 'classroom-setup-presentation';
    style.textContent = '#screen.classroom-setup-screen{padding:0!important;min-height:0}.classroom-setup-screen{padding:0!important}.classroom-setup-screen>.ref-tabs{margin:0;padding:0 24px;height:66px;border-bottom:1px solid #edf0f5;gap:24px}.classroom-setup-screen>.filter-strip{display:flex;padding:24px;margin:0;gap:30px}.classroom-setup-screen>.filter-strip label{flex:0 0 253px;width:253px;min-width:0}.classroom-setup-screen>.filter-strip input,.classroom-setup-screen>.filter-strip select{width:100%;height:35px;min-width:0}.classroom-setup-screen .classroom-create{margin-left:auto;background:#2bbf9a;border:0;height:35px;padding:0 14px}.classroom-setup-screen>.table-card{box-shadow:none;border:0;margin:0;padding:0 24px 24px}.classroom-setup-screen table{border-collapse:collapse;width:100%}.classroom-setup-screen td,.classroom-setup-screen th{border:1px solid #eef0f5;padding:14px 10px;font-size:13px}.classroom-setup-screen .table-footer{display:flex;align-items:center;padding-top:18px}.classroom-setup-screen .table-page-size{display:flex;align-items:center;gap:5px;white-space:nowrap}.classroom-setup-screen .table-page-size select{height:30px;border:1px solid #e7eaf2;border-radius:4px;padding:4px 10px}.classroom-setup-screen .classroom-page-count{margin-right:auto;font-size:13px}.classroom-setup-screen .badge.green{background:#32a7f6;color:white}';
    document.head.append(style);
  }
  const card = screen.querySelector('[data-table-card]');
  const updateCount = () => {
    const footer = card?.querySelector('.table-footer'); if (!footer) return;
    let count = footer.querySelector('.classroom-page-count');
    if (!count) { count = document.createElement('span'); count.className = 'classroom-page-count'; footer.prepend(count); }
    const table = globalThis.CenterEdu?.state?.tableRegistry?.[card.dataset.tableCard];
    const total = table?.rows?.length || 0, size = Number(card.dataset.pageSize || 10), page = Number(card.dataset.page || 0);
    const value = `Hiển thị ${total ? page * size + 1 : 0} đến ${Math.min((page + 1) * size, total)} của ${total} bản ghi`;
    if (count.textContent !== value) count.textContent = value;
  };
  updateCount();
  if (card && !card.dataset.classroomFooterBound) {
    card.dataset.classroomFooterBound = 'true';
    new MutationObserver(updateCount).observe(card, { childList: true, subtree: true });
  }
}

export function bindClassroomTabs(root = document) {
  const screen = root.querySelector?.('#screen') || root;
  const route = String(window.location.pathname || '').split('?')[0];
  if (!screen || !['/setup/classroom', '/setup/session'].includes(route)) {
    if (screen) { classroomViews.delete(screen); screen.classList?.remove('classroom-setup-screen'); }
    return;
  }
  const tabs = [...screen.querySelectorAll('.ref-tabs .ref-tab')]; if (tabs.length < 2) return;
  const index = classroomViews.get(screen) ?? (route === '/setup/session' ? 1 : 0);
  classroomViews.set(screen, index);
  classroomPresentation(screen, index);
  tabs.forEach((tab, tabIndex) => {
    if (classroomTabButtons.has(tab)) return;
    classroomTabButtons.add(tab);
    tab.addEventListener('click', async event => {
      event.preventDefault(); event.stopImmediatePropagation();
      if (classroomViews.get(screen) === tabIndex) return;
      const target = tabIndex === 1 ? '/setup/session' : '/setup/classroom';
      if (typeof (tabIndex === 1 ? globalThis.sessionSlots : globalThis.classrooms) !== 'function') return;
      window.history.pushState({}, '', target);
      window.dispatchEvent(new PopStateEvent('popstate'));
    }, true);
  });
}
export function register(host = globalThis.CenterEdu) {
  const renderClassroomRoute = async (screen, index) => {
    classroomViews.set(screen, index);
    const renderer = index === 1 ? globalThis.sessionSlots : globalThis.classrooms;
    if (typeof renderer !== 'function') return false;
    await renderer(screen);
    classroomPresentation(screen, index);
    bindClassroomTabs(screen);
    return true;
  };
  host?.registerScreen?.('/setup/classroom', screen => renderClassroomRoute(screen, 0));
  host?.registerScreen?.('/setup/session', screen => renderClassroomRoute(screen, 1));
  return CENTER_TEACHER_CONTRACT;
}
if (typeof document !== 'undefined' && typeof MutationObserver === 'function') {
  const root = document.querySelector('#screen') || document.body;
  new MutationObserver(() => bindClassroomTabs(document)).observe(root, { childList: true, subtree: true });
  [0, 120, 500].forEach(delay => setTimeout(() => bindClassroomTabs(document), delay));
}

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

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

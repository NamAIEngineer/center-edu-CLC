/* W6 survey route contract.  app.js owns the shell and HTTP session; this
 * adapter keeps observed labels, form normalization and table semantics local
 * to the survey module until the coordinator wires the registry import. */
export const SURVEY_CONTRACT = Object.freeze({
  route: "/survey",
  createRoute: "/survey/create_survey",
  columns: [
    "No.", "Tên khảo sát", "Hạn làm",
    "Đã làm / Đã gửi / Người nhận", "Người tạo",
    "Thống kê / Kết quả", "Hành động",
  ],
  filters: [
    { name: "q", label: "Tìm kiếm...", type: "search" },
    { name: "status", label: "Trạng thái", type: "select", options: ["Bản nháp", "Đã phát hành", "Đã đóng"] },
    { name: "page_size", label: "Hiển thị bản ghi", type: "select", options: [5, 10, 25, 50] },
  ],
  form: [
    { name: "name", label: "Tên khảo sát", type: "text", required: true },
    { name: "due_date", label: "Hạn làm", type: "text", placeholder: "dd/mm/yyyy" },
    { name: "status", label: "Trạng thái", type: "select", options: ["Bản nháp", "Đã phát hành", "Đã đóng"] },
    { name: "description", label: "Mô tả", type: "textarea" },
  ],
  actions: ["read", "create", "update", "archive", "respond", "export"],
});

const STATUS_TO_API = Object.freeze({ "Bản nháp": "DRAFT", "Đã phát hành": "PUBLISHED", "Đã đóng": "CLOSED" });
const STATUS_FROM_API = Object.freeze(Object.fromEntries(Object.entries(STATUS_TO_API).map(([label, value]) => [value, label])));

export function surveyQuery(filters = {}) {
  const params = new URLSearchParams();
  if (String(filters.q ?? "").trim()) params.set("q", String(filters.q).trim());
  const status = STATUS_TO_API[filters.status] || filters.status;
  if (status) params.set("status", status);
  if (filters.page_size) params.set("page_size", String(filters.page_size));
  return params.toString();
}

export function normalizeSurveyForm(values = {}) {
  const output = { ...values };
  const date = String(output.due_date ?? "").trim();
  const match = date.match(/^(\d{1,2})[\/-](\d{1,2})[\/-](\d{4})$/);
  if (match) output.due_date = `${match[3]}-${match[2].padStart(2, "0")}-${match[1].padStart(2, "0")}`;
  if (output.status) output.status = STATUS_TO_API[output.status] || output.status;
  return output;
}

export function displaySurveyStatus(status) {
  return STATUS_FROM_API[String(status ?? "").toUpperCase()] || String(status ?? "");
}

export function displaySurveyDate(value) {
  const match = String(value ?? "").trim().match(/^(\d{4})-(\d{2})-(\d{2})$/);
  return match ? `${match[3]}/${match[2]}/${match[1]}` : String(value ?? "");
}

export function validateSurveyForm(values = {}) {
  const errors = {};
  if (!String(values.name ?? "").trim()) errors.name = "Tên khảo sát là bắt buộc";
  const normalized = normalizeSurveyForm(values);
  if (normalized.due_date && !/^\d{4}-\d{2}-\d{2}$/.test(normalized.due_date)) errors.due_date = "Hạn làm phải theo định dạng dd/mm/yyyy";
  return errors;
}

export function renderSurveyRows(tbody, rows = [], { canEdit = false } = {}) {
  tbody.replaceChildren();
  for (const [index, row] of rows.entries()) {
    const tr = document.createElement("tr");
    const values = [
      index + 1,
      row.name || "",
      displaySurveyDate(row.due_date),
      `${row.completed_count ?? 0} / ${row.sent_count ?? 0} / ${row.recipient_count ?? 0}`,
      row.created_by_name || "",
      row.response_count ?? row.completed_count ?? 0,
    ];
    for (const value of values) {
      const td = document.createElement("td");
      td.textContent = String(value ?? "");
      tr.append(td);
    }
    const action = document.createElement("td");
    if (canEdit) {
      const button = document.createElement("button");
      button.type = "button";
      button.dataset.surveyId = row.id;
      button.textContent = "Mở";
      action.append(button);
    }
    tr.append(action);
    tbody.append(tr);
  }
}

export function exportSurveyUrl(filters = {}) {
  const query = surveyQuery(filters);
  return `/api/export/surveys${query ? `?${query}` : ""}`;
}

export function register(centerEdu = globalThis.CenterEdu) {
  const routes = [SURVEY_CONTRACT.route, SURVEY_CONTRACT.createRoute];
  if (!centerEdu) return { routes };
  centerEdu.w6LaneMetadata = {
    ...(centerEdu.w6LaneMetadata || {}),
    survey: { routes, status: "PERSISTENT_LOCAL_CONTRACT" },
  };
  centerEdu.registerScreen?.(SURVEY_CONTRACT.route, async (screen, ctx) => {
    // Registration is exercised independently of the browser shell. Defer
    // rendering until the coordinator supplies its authenticated API context.
    if (!screen || !ctx || typeof ctx.api !== 'function') return false;
    const canEdit = ['ADMIN', 'STAFF'].includes(String(ctx.state?.user?.role || '').toUpperCase());
    const esc = centerEdu.helpers?.esc || (value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c])));
    const date = value => { const m = String(value || '').match(/^(\d{4})-(\d{2})-(\d{2})/); return m ? `${m[3]}/${m[2]}/${m[1]}` : ''; };
    const cells = row => [row.id, row.name || '', date(row.due_date), `${row.completed_count ?? 0} / ${row.sent_count ?? 0} / ${row.recipient_count ?? 0}`, row.created_by_name || '', row.response_count ?? row.completed_count ?? 0];
    screen.innerHTML = `<div class="screen-head"><div class="screen-title"><h1>Danh sách khảo sát</h1></div><div class="page-actions">${canEdit ? '<button class="primary" id="survey-create" type="button">Tạo khảo sát</button><button class="ghost" id="survey-statistics" type="button">Thống kê</button><button class="ghost" id="survey-results" type="button">Kết quả</button><button class="ghost" id="survey-export" type="button">Xuất CSV</button>' : ''}</div></div><div class="ref-tabs" role="tablist"><button class="ref-tab active" role="tab" aria-selected="true">Danh sách khảo sát</button></div><div class="filter-strip"><label><input name="q" type="search" placeholder="Tìm kiếm..." aria-label="Tìm kiếm..."></label><label><select name="status" aria-label="Trạng thái"><option value="">Tất cả</option><option value="DRAFT">Bản nháp</option><option value="PUBLISHED">Đã phát hành</option><option value="CLOSED">Đã đóng</option></select></label><button class="ghost" id="survey-filter-clear" type="button">Xóa lọc</button></div><label class="table-page-size"><span>Hiển thị bản ghi</span><select name="page_size" aria-label="Hiển thị bản ghi"><option>5</option><option>10</option><option>25</option><option>50</option></select></label><div class="card table-card"><table><thead><tr>${SURVEY_CONTRACT.columns.map(label => `<th>${esc(label)}</th>`).join('')}</tr></thead><tbody></tbody></table></div>`;
    // Keep references before the shared normalizer can rename controls (for
    // example, q -> tim_kiem). Selector lookups after normalization would
    // detach query, listeners, export and clear from the actual controls.
    const qControl = screen.querySelector('input[name="q"]');
    const statusControl = screen.querySelector('select[name="status"]');
    const pageSizeControl = screen.querySelector('select[name="page_size"]');
    const body = screen.querySelector('tbody');
    let refreshVersion = 0;
    const query = () => {
      const p = new URLSearchParams();
      const q = String(qControl?.value || '').trim();
      const status = String(statusControl?.value || '');
      const pageSize = String(pageSizeControl?.value || '');
      if (q) p.set('q', q);
      if (status) p.set('status', status);
      if (pageSize) p.set('page_size', pageSize);
      return p;
    };
    const refresh = async () => {
      const version = ++refreshVersion;
      const p = query();
      const response = await ctx.api(`/api/surveys${p.toString() ? `?${p}` : ''}`);
      if (version !== refreshVersion) return;
      const rows = (Array.isArray(response?.data) ? response.data : []).slice(0, Number(pageSizeControl?.value || 5));
      body.replaceChildren();
      if (!rows.length) { const tr = document.createElement('tr'); const td = document.createElement('td'); td.colSpan = SURVEY_CONTRACT.columns.length; td.className = 'empty'; td.textContent = 'Không có dữ liệu.'; tr.append(td); body.append(tr); return; }
      rows.forEach((row) => { const tr = document.createElement('tr'); cells(row).forEach((value) => { const td = document.createElement('td'); td.textContent = String(value ?? ''); tr.append(td); }); const td = document.createElement('td'); if (canEdit) { const button = document.createElement('button'); button.type = 'button'; button.className = 'small-action survey-open'; button.dataset.surveyId = row.id; button.textContent = 'Mở'; td.append(button); } else td.textContent = '—'; tr.append(td); body.append(tr); });
    };
    const go = route => { window.history.pushState({}, '', route); window.dispatchEvent(new PopStateEvent('popstate')); };
    screen.querySelector('#survey-create')?.addEventListener('click', () => go(SURVEY_CONTRACT.createRoute));
    screen.querySelector('#survey-statistics')?.addEventListener('click', () => go('/survey/statistics'));
    screen.querySelector('#survey-results')?.addEventListener('click', () => go('/survey/results'));
    screen.querySelector('#survey-export')?.addEventListener('click', () => { window.location.assign(exportSurveyUrl(Object.fromEntries(query()))); });
    screen.querySelector('#survey-filter-clear')?.addEventListener('click', () => { if (qControl) qControl.value = ''; if (statusControl) statusControl.value = ''; refresh(); });
    qControl?.addEventListener('input', refresh);
    statusControl?.addEventListener('change', refresh);
    pageSizeControl?.addEventListener('change', refresh);
    screen.addEventListener('click', event => { const button = event.target.closest('.survey-open'); if (button) globalThis.surveyBuilderModal?.(button.dataset.surveyId); });
    await refresh();
    return true;
  });
  centerEdu.registerScreen?.(SURVEY_CONTRACT.createRoute, async () => false);
  return { routes, status: "PERSISTENT_LOCAL_CONTRACT" };
}


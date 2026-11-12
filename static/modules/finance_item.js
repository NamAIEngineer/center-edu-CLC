import { bindFinanceViews } from './finance_tab_views.js';

export function parseFinanceItemCsv(text) {
  const rows = []; let row = [], cell = '', quoted = false;
  for (let i = 0; i < text.length; i += 1) {
    const char = text[i];
    if (quoted) {
      if (char === '"' && text[i + 1] === '"') { cell += '"'; i += 1; }
      else if (char === '"') quoted = false;
      else cell += char;
    } else if (char === '"') quoted = true;
    else if (char === ',') { row.push(cell); cell = ''; }
    else if (char === '\n' || char === '\r') {
      if (char === '\r' && text[i + 1] === '\n') i += 1;
      row.push(cell); cell = '';
      if (row.some(value => value !== '')) rows.push(row);
      row = [];
    } else cell += char;
  }
  row.push(cell);
  if (row.some(value => value !== '')) rows.push(row);
  return rows;
}
/* Finance item screen contract. Mounted by the app registry when wired. */
export const FINANCE_ITEM_CONTRACT = Object.freeze({
  route: "/finance/item",
  tabs: ["Danh mục vật phẩm", "Vật phẩm", "Phiếu nhập kho", "Phiếu xuất kho"],
  columns: ["No.", "Mã vật phẩm", "Danh mục", "Tên vật phẩm", "Khóa học áp dụng", "Đơn vị tính", "Trung tâm áp dụng", "Số lượng còn", "Giá bán", "Điều chỉnh giá", "Trạng thái", "Công cụ"],
  filters: [
    { name: "q", placeholder: "Tìm trong bảng...", type: "search" },
    { name: "status", placeholder: "Chọn trạng thái", type: "select", options: ["Hoạt động", "Tạm khóa"] },
  ],
  pageSizes: [5, 10, 25, 50],
  actions: ["Định giá", "Upload", "Excel", "Thêm vật phẩm"],
  form: [
    { name: "image_logo", type: "file", label: "Ảnh" },
    { name: "code", type: "text", label: "Mã vật phẩm" },
    { name: "fullname", type: "text", label: "Tên vật phẩm" },
    { name: "description", type: "textarea", label: "Màu sắc, kích cỡ, mô tả" },
    { name: "unit", type: "select", label: "Đơn vị tính" },
    { name: "category", type: "select", label: "Danh mục" },
    { name: "course_ids", type: "multi-select", label: "Khóa học áp dụng" },
    { name: "start_date", type: "text", label: "Ngày bắt đầu" },
  ],
});

export function itemQuery(filters = {}) {
  const params = new URLSearchParams();
  Object.entries(filters).forEach(([k, v]) => { if (v !== null && v !== undefined && String(v).trim()) params.set(k, v); });
  return params.toString();
}

export async function loadItems(filters = {}, fetcher = fetch) {
  const query = itemQuery(filters);
  const response = await fetcher(`/api/finance/items${query ? `?${query}` : ""}`, { credentials: "same-origin" });
  if (!response.ok) throw new Error(`finance item list failed: ${response.status}`);
  return response.json();
}

export function renderItemRows(tbody, rows, { canEdit = false } = {}) {
  tbody.replaceChildren();
  rows.forEach((row, index) => {
    const tr = document.createElement("tr");
    [index + 1, row.code, row.category, row.fullname, row.course_ids || "", row.unit, row.branch, row.quantity, row.sale_price, row.price_adjustment, row.status].forEach(value => { const td = document.createElement("td"); td.textContent = value ?? ""; tr.append(td); });
    const action = document.createElement("td");
    if (canEdit) { const button = document.createElement("button"); button.type = "button"; button.dataset.itemId = row.id; button.textContent = "⋯"; action.append(button); }
    tr.append(action); tbody.append(tr);
  });
}

function bindFinanceTabState(screen, context) { bindFinanceViews(screen, 'item', context); }

export function register(global) {
  const host = global || {};
  host.financeItem = FINANCE_ITEM_CONTRACT;
  host.financeItemCsvParser = parseFinanceItemCsv;
  const render = async (screen, context) => {
    const fn = globalThis.financeItems;
    if (typeof fn !== 'function') return false;
    await fn(screen, context);
    bindFinanceTabState(screen, context);
    return true;
  };
  if (typeof host.registerScreen === 'function') host.registerScreen(FINANCE_ITEM_CONTRACT.route, render);
  return FINANCE_ITEM_CONTRACT;
}

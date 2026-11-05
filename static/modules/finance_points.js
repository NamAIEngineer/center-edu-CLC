/* Finance accumulate-points local screen contract. */
export const pointsScreen = {
  route: '/finance/accumulate_points', entity: 'finance_point_rules',
  tabs: ['Thiết lập tích điểm', 'Thống kê tích điểm'],
  filters: [{name:'q', type:'text', placeholder:'Tìm trong bảng...'},{name:'page_size', type:'select', options:[5,10,25,50]}],
  columns: ['No.','Mã tích điểm','Tên','Trạng thái','Số tiền tích 1 điểm','Tỉ lệ quy đổi','Trung tâm áp dụng','Công cụ'],
  actions: ['Tạo mã tích điểm','Excel'],
  form: [
    {name:'code', label:'Mã tích điểm', required:true}, {name:'name', label:'Tên', required:true},
    {name:'status', label:'Trạng thái', type:'select', options:[['active','Hoạt động'],['inactive','Ngừng hoạt động']], required:true},
    {name:'amount_per_point', label:'Số tiền tích 1 điểm', required:true},
    {name:'conversion_rate', label:'Tỉ lệ quy đổi', required:true},
    {name:'center_id', label:'Trung tâm áp dụng', required:true}
  ], permissions: {read:['ADMIN','STAFF','TEACHER'], write:['ADMIN','STAFF']}
};
export const statusLabel = s => s === 'active' ? 'Hoạt động' : 'Ngừng hoạt động';
export const formatVnd = v => `${Number(v || 0).toLocaleString('vi-VN')} VND`;
export function renderPointRows(items = []) { return items.map((r,i) => ({no:i+1, code:r.code, name:r.name, status:statusLabel(r.status), amountPerPoint:formatVnd(r.amount_per_point), conversionRate:formatVnd(r.conversion_rate), center:r.center_name, action:'…'})); }
export async function loadPointRules(apiFetch, filters = {}) { const p = new URLSearchParams(filters); return apiFetch(`/api/finance/point-rules?${p}`); }
export async function exportPointRules(apiFetch, filters = {}) { const p = new URLSearchParams(filters); return apiFetch(`/api/export/finance-point-rules?${p}`); }

export function register(global) {
  const host = global || {};
  host.financePoints = pointsScreen;
  const render = async (screen, context) => {
    const fn = globalThis.financePoints;
    if (typeof fn !== 'function') return false;
    await fn(screen, context);
    return true;
  };
  if (typeof host.registerScreen === 'function') host.registerScreen(pointsScreen.route, render);
  return pointsScreen;
}

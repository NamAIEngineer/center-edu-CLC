/* W6 call-center route contract. */
export const CALLCENTER_LANE_ROUTES = Object.freeze(["/callcenter/extension", "/callcenter/staff", "/callcenter/get-statistic", "/callcenter/history"]);
export const CALL_RESULT_LABELS = Object.freeze(["Thất bại", "Gọi nhỡ", "Thành công"]);
export function callcenterQuery(filters = {}) { const q = new URLSearchParams(); for (const [k, v] of Object.entries(filters)) if (v) q.set(k, v); return q.toString(); }

export function bindCallStatisticTabs(root = document) {
  const screen = root.querySelector?.('#screen') || root;
  if (!screen || screen.dataset.callStatisticTabsBound === '/callcenter/get-statistic' || String(window.location.pathname || '').split('?')[0] !== '/callcenter/get-statistic') return;
  const tabs = [...screen.querySelectorAll('.ref-tabs .ref-tab')]; if (tabs.length < 2) return;
  screen.dataset.callStatisticTabsBound = '/callcenter/get-statistic';
  tabs.forEach((tab, index) => tab.addEventListener('click', () => {
    tabs.forEach((item, i) => { const active = i === index; item.classList.toggle('active', active); item.setAttribute('aria-selected', active ? 'true' : 'false'); });
    screen.dataset.callStatisticView = index === 1 ? 'outgoing' : 'incoming';
    screen.querySelectorAll('tbody tr').forEach(row => { const direction = String(row.dataset.direction || '').toLowerCase(); row.hidden = Boolean(direction) && ((index === 1 && !/out|ra/.test(direction)) || (index === 0 && /out|ra/.test(direction))); });
  }));
}
if (typeof document !== 'undefined' && typeof MutationObserver === 'function') { const root = document.querySelector('#screen') || document.body; new MutationObserver(() => bindCallStatisticTabs(document)).observe(root, { childList: true, subtree: true }); [0,120,500].forEach(delay => setTimeout(() => bindCallStatisticTabs(document), delay)); }

export function register(centerEdu = globalThis.CenterEdu) {
  if (!centerEdu) return { routes: CALLCENTER_LANE_ROUTES };
  centerEdu.w6LaneMetadata = {
    ...(centerEdu.w6LaneMetadata || {}),
    callcenter: { routes: CALLCENTER_LANE_ROUTES, status: "PERSISTENT_LOCAL_CONTRACT" },
  };
  const configs = {
    "/callcenter/extension": { title:"Danh sách số máy lẻ", columns:[], filters:[], buttons:["Thêm mới","Excel"], formOnly:true, fields:[{name:"extension",label:"Số máy nhánh",required:true},{name:"staff_name",label:"Nhân viên",options:["Nguyễn Ngọc Mai","Lê Hoàng Anh","Trần Minh Tú"]},{name:"status",label:"Trạng thái",options:["Đang hoạt động","Đã khóa"]}] },
    "/callcenter/staff": { title:"Danh sách nhân viên trực", columns:[{key:"no",label:"No."},{key:"nhan_vien",label:"Nhân viên"},{key:"so_may",label:"Số máy"},{key:"trang_thai",label:"Trạng thái"},{key:"cong_cu",label:"Công cụ"}], filters:[{name:"q",placeholder:"Tìm kiếm",type:"text"}], buttons:["Thêm số máy"], fields:[{name:"staff_name",label:"Nhân viên",required:true,options:["Nguyễn Ngọc Mai","Lê Hoàng Anh","Trần Minh Tú"]},{name:"extension",label:"Số máy nhánh",required:true},{name:"active",label:"Đang trực",type:"checkbox"},{name:"note",label:"Ghi chú",type:"textarea"}] },
    "/callcenter/get-statistic": { title:"Thống kê cuộc gọi vào", columns:[{key:"no",label:"No."},{key:"staff_name",label:"Nhân viên nghe"},{key:"sale_group",label:"Nhóm sale"},{key:"center",label:"Trung tâm"},{key:"total_calls",label:"Tổng cuộc gọi"},{key:"answered_calls",label:"Cuộc gọi thành công"},{key:"missed_calls",label:"Cuộc gọi nhỡ"},{key:"failed_calls",label:"Thất bại"}], filters:[{name:"from_date",placeholder:"Từ ngày",type:"date"},{name:"to_date",placeholder:"Đến ngày",type:"date"}], tabs:["Thống kê cuộc gọi vào","Thống kê cuộc gọi ra"], buttons:["Xuất Excel"], fields:[{name:"from_date",label:"Từ ngày",type:"date",required:true},{name:"to_date",label:"Đến ngày",type:"date",required:true},{name:"total_calls",label:"Tổng số cuộc gọi",type:"number"},{name:"answered_calls",label:"Cuộc gọi đã nghe",type:"number"},{name:"missed_calls",label:"Cuộc gọi nhỡ",type:"number"}] },
    "/callcenter/history": { title:"Lịch sử cuộc gọi", columns:[{key:"no",label:"No."},{key:"called_at",label:"Thời gian"},{key:"caller",label:"Người gọi"},{key:"party",label:"Đối tượng"},{key:"staff_name",label:"Nhân viên"},{key:"result",label:"Kết quả"}], filters:[{placeholder:"Tìm kiếm"},{placeholder:"Tìm kiếm"},{options:["Tất cả","Học viên","Phụ huynh","Giáo viên","Nhân viên","Tiềm năng"]},{kind:"checkbox",placeholder:"Đã nghe"},{kind:"checkbox",placeholder:"Gọi nhỡ"},{options:["Tất cả","Nguyễn Ngọc Mai","Lê Hoàng Anh","Trần Minh Tú"]},{options:["Thất bại","Gọi nhỡ","Thành công"]},{kind:"text",placeholder:"Tìm kiếm"},{placeholder:"Từ ngày"},{placeholder:"Đến ngày"}], buttons:["Thêm mới","Excel"], fields:[{name:"called_at",label:"Thời gian",type:"date",required:true},{name:"caller",label:"Người gọi",required:true},{name:"party",label:"Đối tượng",options:["Học viên","Phụ huynh","Giáo viên","Nhân viên","Tiềm năng"]},{name:"staff_name",label:"Nhân viên",options:["Nguyễn Ngọc Mai","Lê Hoàng Anh","Trần Minh Tú"]},{name:"result",label:"Kết quả",options:["Thất bại","Gọi nhỡ","Thành công"]},{name:"duration",label:"Thời lượng",type:"number"},{name:"note",label:"Ghi chú",type:"textarea"}] },
  };
  for (const route of CALLCENTER_LANE_ROUTES) centerEdu.registerScreen?.(route, async () => false);
  return { routes: CALLCENTER_LANE_ROUTES, status: "PERSISTENT_LOCAL_CONTRACT" };
}


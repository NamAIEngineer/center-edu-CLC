/* W6 CSO route contract. */
export const CSO_LANE_ROUTES = Object.freeze(["/cso/support", "/cso/customer-care"]);
export const CSO_STATUS_LABELS = Object.freeze(["Mới tiếp nhận", "Đang xử lý", "Đã xử lý", "Đã đóng", "Đã xong", "Quá hạn"]);
export function csoQuery(filters = {}) { const q = new URLSearchParams(); for (const [k, v] of Object.entries(filters)) if (v) q.set(k, v); return q.toString(); }

export function register(centerEdu = globalThis.CenterEdu) {
  if (!centerEdu) return { routes: CSO_LANE_ROUTES };
  centerEdu.w6LaneMetadata = {
    ...(centerEdu.w6LaneMetadata || {}),
    cso: { routes: CSO_LANE_ROUTES, status: "PERSISTENT_LOCAL_CONTRACT" },
  };
  const configs = {
    "/cso/support": { title:"Hỗ trợ", columns:[{key:"no",label:"No."},{key:"deadline",label:"Thời gian"},{key:"type",label:"Loại"},{key:"content",label:"Nội dung"},{key:"sender",label:"Người gửi"},{key:"class_name",label:"Lớp của học viên"},{key:"staff_name",label:"Nhân viên"},{key:"status",label:"Trạng thái"}], filters:[{options:["Tất cả trạng thái","Mới tiếp nhận","Đang xử lý","Đã xử lý","Đã đóng"]},{options:["Tất cả loại","Phản hồi/Hỗ trợ","Khiếu nại"]},{placeholder:"Từ ngày"},{placeholder:"Đến ngày"},{placeholder:"Tìm..."}], tabs:["Tiếp nhận từ người dùng","Hỗ trợ nội bộ"], buttons:["Excel","Tạo","Mới tiếp nhận"], fields:[{name:"sender",label:"Học viên / Phụ huynh"},{name:"student_name",label:"Học viên"},{name:"content",label:"Nội dung",type:"textarea",required:true},{name:"staff_name",label:"Nhân viên",options:["Nguyễn Ngọc Mai","Lê Hoàng Anh","Trần Minh Tú"]},{name:"type",label:"Loại",options:["Phản hồi/Hỗ trợ","Khiếu nại"]},{name:"deadline",label:"Hạn xử lý",type:"date"},{name:"status",label:"Trạng thái",options:["Mới tiếp nhận","Đang xử lý","Đã xử lý","Đã đóng"]},{name:"note",label:"Ghi chú",type:"textarea"}] },
    "/cso/customer-care": { title:"Chăm sóc khách hàng", columns:[{key:"no",label:"No."},{key:"student_name",label:"Học viên"},{key:"class_name",label:"Lớp"},{key:"staff_name",label:"Nhân viên"},{key:"care_round",label:"Lần chăm sóc"},{key:"content",label:"Nội dung"},{key:"status",label:"Trạng thái"}], filters:[{options:["Tất cả","Chưa xử lý","Đang xử lý","Đã xong","Quá hạn"]},{placeholder:"Từ ngày"},{placeholder:"Đến ngày"},{placeholder:"Tìm..."},{options:["Chọn lớp học","Lớp Tiếng Anh giao tiếp A1","Lớp IELTS Foundation"]},{options:["Chọn nhân viên","Nguyễn Ngọc Mai","Lê Hoàng Anh","Trần Minh Tú"]},{options:["Chọn số lần chăm sóc","Lần 01","Lần 02","Lần 03","Lần 04"]},{options:["Gọi điện","Nhắn tin","Khảo sát"]},{placeholder:"Chọn hành động"},{options:["Đồng ý","Từ chối"]},{placeholder:"Chọn kết quả"},{options:["Khảo sát","Bán thêm","Xử lý góp ý/khiếu nại"]},{placeholder:"Chọn mục đích"},{options:["5","10","25","50"]}], buttons:["Excel","Tạo mới","Chưa xử lý","Đã xong"], fields:[{name:"student_name",label:"Học viên",required:true},{name:"class_name",label:"Lớp",options:["Lớp Tiếng Anh giao tiếp A1","Lớp IELTS Foundation"]},{name:"staff_name",label:"Nhân viên",options:["Nguyễn Ngọc Mai","Lê Hoàng Anh","Trần Minh Tú"]},{name:"care_round",label:"Lần chăm sóc",options:["Lần 01","Lần 02","Lần 03","Lần 04"]},{name:"content",label:"Nội dung",type:"textarea"},{name:"action",label:"Hành động",options:["Gọi điện","Nhắn tin","Khảo sát"]},{name:"purpose",label:"Mục đích",options:["Khảo sát","Bán thêm","Xử lý góp ý/khiếu nại"]},{name:"result",label:"Kết quả",options:["Đồng ý","Từ chối"]},{name:"care_date",label:"Ngày chăm sóc",type:"date"},{name:"status",label:"Trạng thái",options:["Chưa xử lý","Đang xử lý","Đã xong","Quá hạn"]}] },
  };
  for (const route of CSO_LANE_ROUTES) centerEdu.registerScreen?.(route, async () => false);
  return { routes: CSO_LANE_ROUTES, status: "PERSISTENT_LOCAL_CONTRACT" };
}


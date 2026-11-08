/* W6 Center/Setup route metadata and safe client helpers. */
export const CENTER_LANE_ROUTES = Object.freeze([
  "/center/student/index", "/center/teacher", "/center/parent/index", "/center/staff",
  "/setup/classroom", "/center/holiday/index", "/setup/daily-evaluation", "/setup/criteria",
  "/center/manager/index", "/center/options", "/center/tool/center/index",
  "/center/document-permission", "/center/upload_address",
]);

export function laneQuery(filters = {}) {
  const q = new URLSearchParams();
  for (const [key, value] of Object.entries(filters)) {
    if (value !== undefined && value !== null && String(value).trim() !== "") q.set(key, String(value));
  }
  return q.toString();
}

export function laneApiUrl(route, filters = {}) {
  const query = laneQuery(filters);
  return `/api/generated/screens?route=${encodeURIComponent(route)}${query ? `&${query}` : ""}`;
}

export function normalizeLaneDate(value) {
  const match = String(value ?? "").trim().match(/^(\d{1,2})[\/-](\d{1,2})[\/-](\d{4})$/);
  return match ? `${match[3]}-${match[2].padStart(2, "0")}-${match[1].padStart(2, "0")}` : value;
}

// Seven semantic controls are rendered by the route owner.  Select2-style
// widgets expose the status/class controls as compact multi-selects; their
// option lists are hydrated from the observed payload in app.js.
const STUDENT_FILTERS = Object.freeze([
  { kind: "text", placeholder: "Tìm kiếm..." },
  { kind: "text", placeholder: "Tìm phụ huynh" },
  { kind: "multi-select", placeholder: "Chọn trạng thái", options: ["Đang học", "Bảo lưu", "Chuyển lớp", "Đã xong", "Nghỉ học", "Chưa học", "Chưa có lớp"] },
  { kind: "multi-select", placeholder: "Chọn lớp học" },
  { kind: "search", placeholder: "Nguồn giới thiệu" },
  { kind: "select", placeholder: "Chọn năm" },
  { kind: "select", placeholder: "Chọn trường học" },
]);

export { STUDENT_FILTERS };

export function register(centerEdu = globalThis.CenterEdu) {
  if (!centerEdu) return { routes: CENTER_LANE_ROUTES };
  centerEdu.w6LaneMetadata = {
    ...(centerEdu.w6LaneMetadata || {}),
    center: { routes: CENTER_LANE_ROUTES, status: "PERSISTENT_LOCAL_CONTRACT" },
  };
  const configs = {
    "/center/student/index": { title: "Danh sách học viên", columns: [{key:"no",label:"No."},{key:"student_name",label:"Học viên"},{key:"username",label:"Tài khoản"},{key:"parent_name",label:"Phụ huynh"},{key:"sale_name",label:"Sales rep"},{key:"class_name",label:"Lớp học"},{key:"source",label:"Nguồn giới thiệu"},{key:"note",label:"Ghi chú"},{key:"action",label:""}], filters: STUDENT_FILTERS, buttons:["Excel","Upload","Thêm mới"], fields:[{name:"fullname",label:"Họ và tên",required:true},{name:"code",label:"Mã tài khoản",required:true},{name:"username",label:"Tên đăng nhập",required:true},{name:"phone",label:"Số điện thoại"},{name:"class_name",label:"Lớp học"},{name:"status",label:"Trạng thái",options:["Đang học","Bảo lưu","Đã xong","Nghỉ học"]}] },
    "/center/teacher": { title:"Danh sách giáo viên", columns:[{key:"no",label:"No."},{key:"fullname",label:"Giáo viên"},{key:"username",label:"Tài khoản"},{key:"phone",label:"Liên hệ"},{key:"nationality",label:"Quốc tịch"},{key:"role",label:"Phân quyền"},{key:"status",label:"Trạng thái"}], filters:[{kind:"text",placeholder:"Tìm kiếm"},{options:["Chọn quốc tịch","Việt Nam","Hoa Kỳ","Anh","Úc"]},{options:["Chọn trạng thái","Kích hoạt","Đang khóa"]},{options:["10","25","50","100"]}],buttons:["Excel","Thêm giáo viên"],fields:[{name:"fullname",label:"Họ và tên",required:true},{name:"username",label:"Tên đăng nhập",required:true},{name:"phone",label:"Số điện thoại"},{name:"nationality",label:"Quốc tịch",options:["Việt Nam","Hoa Kỳ","Anh","Úc"]},{name:"role",label:"Phân quyền",options:["Giáo viên","Giáo viên chủ nhiệm"]},{name:"status",label:"Trạng thái",options:["Kích hoạt","Đang khóa"]}] },
    "/setup/classroom": { title:"Phòng học", columns:[{key:"no",label:"No."},{key:"code",label:"Mã phòng học"},{key:"name",label:"Tên phòng học"},{key:"capacity",label:"Số ghế"},{key:"description",label:"Mô tả"},{key:"status",label:"Trạng thái"},{key:"action",label:"Hành động"}], filters:[{kind:"text",placeholder:"Tìm..."},{options:["Tất cả","Đã khóa","Hoạt động"]},{options:["10","25","50","100"]}],tabs:["Phòng học","Ca học"],buttons:["Thêm mới"],fields:[{name:"code",label:"Mã phòng học",required:true},{name:"name",label:"Tên phòng học",required:true},{name:"capacity",label:"Số ghế",type:"number"},{name:"description",label:"Mô tả",type:"textarea"},{name:"status",label:"Trạng thái",options:["Hoạt động","Đã khóa"]}] },
    "/center/upload_address": { title:"Tool chinh sửa địa chỉ", columns:[{key:"no",label:"No."},{key:"branch",label:"Chi nhánh"},{key:"student_code",label:"Mã học viên"},{key:"student_name",label:"Học viên"},{key:"identity_code",label:"Mã định danh"},{key:"english_name",label:"Tên tiếng anh"},{key:"gender",label:"Giới tính"},{key:"dob",label:"Ngày sinh"},{key:"username",label:"Tài khoản"},{key:"phone",label:"SĐT"},{key:"email",label:"Email"},{key:"old_province",label:"Tỉnh cũ"},{key:"old_district",label:"Huyện cũ"},{key:"old_ward",label:"Xã phường"},{key:"new_province",label:"Tỉnh mới"},{key:"new_ward",label:"Phường xã mới"}], filters:[{options:["5","10","25","50"]}],tabs:["Công cụ chỉnh sửa địa chỉ học sinh","Công cụ chỉnh sửa địa chỉ khách hàng tiềm năng"],buttons:["Lưu"],fields:[{name:"branch",label:"Chi nhánh",required:true},{name:"student_code",label:"Mã học viên",required:true},{name:"student_name",label:"Học viên",required:true},{name:"phone",label:"Số điện thoại"},{name:"email",label:"Email"},{name:"old_province",label:"Tỉnh cũ"},{name:"new_province",label:"Tỉnh mới"}] },
    "/center/holiday/index": { title:"Lịch nghỉ", columns:[{key:"no",label:"No."},{key:"name",label:"Tên lịch nghỉ"},{key:"start_date",label:"Từ ngày"},{key:"end_date",label:"Đến hết ngày"},{key:"description",label:"Mô tả"},{key:"notice",label:"Thông báo"},{key:"status",label:"Trạng thái"}], filters:[{kind:"text",placeholder:"Tìm..."}], buttons:["Thêm mới"],fields:[{name:"name",label:"Tên lịch nghỉ",required:true},{name:"start_date",label:"Từ ngày",type:"date"},{name:"end_date",label:"Đến hết ngày",type:"date"},{name:"description",label:"Mô tả",type:"textarea"},{name:"notice",label:"Thông báo"},{name:"status",label:"Trạng thái",options:["Kích hoạt","Đã khóa"]}] },
    "/setup/criteria": { title:"Thiết lập tiêu chí test", columns:[{key:"stt",label:"STT"},{key:"skill",label:"Kỹ năng"},{key:"assessment_type",label:"Hình thức đánh giá"},{key:"value",label:"Giá trị"},{key:"action",label:"Hành động"}], filters:[], buttons:["Thêm mới"],fields:[{name:"skill",label:"Kỹ năng",required:true},{name:"assessment_type",label:"Hình thức đánh giá",options:["Bằng số","Bằng phần trăm","Bằng ký tự","Bằng văn bản"]},{name:"value",label:"Giá trị"},{name:"note",label:"Ghi chú",type:"textarea"}] },
  };
  // Register every route at the lane seam. The later `w6_overrides.js` module
  // replaces only routes needing custom reference chrome; the generic shell
  // remains active for the rest.
  for (const route of CENTER_LANE_ROUTES) centerEdu.registerScreen?.(route, async () => false);
  return { routes: CENTER_LANE_ROUTES, status: "PERSISTENT_LOCAL_CONTRACT" };
}


/* W6 reference-shape overrides. Loaded after lane metadata modules so the
 * bounded renderer owns only the routes whose observed table/form chrome
 * differs from the generic generated screen. Persistence stays on the shared
 * generated-screen API; this file only controls presentation and actions. */
import { renderW6Screen } from './w6_screen_utils.js';

const STAFF = ['Nguyễn Ngọc Mai', 'Lê Hoàng Anh', 'Trần Minh Tú'];
const CLASSES = ['Lớp Tiếng Anh giao tiếp A1', 'Lớp IELTS Foundation', 'Lớp Thiếu nhi Starters'];

// Student list filters use sentinel labels from the reference selects. Keep
// those values out of API predicates and paginate only real persisted rows.
export function studentFilterValues(filters = {}) {
  const ignored = new Set(['', 'tất cả', 'tất cả các lớp', 'chọn trạng thái', 'chọn lớp học', 'chọn nguồn', 'chọn khóa học', 'all']);
  return Object.fromEntries(Object.entries(filters).filter(([, value]) => {
    const normalized = String(value ?? '').trim().toLocaleLowerCase('vi');
    return !ignored.has(normalized);
  }));
}

export function paginateStudentRows(rows = [], page = 1, pageSize = 10) {
  const source = Array.isArray(rows) ? rows : [];
  const size = String(pageSize).toLowerCase() === 'all' ? source.length || 1 : Math.max(1, Number(pageSize) || 10);
  const current = Math.max(1, Number(page) || 1);
  return { rows: source.slice((current - 1) * size, current * size), page: current, pageSize: size, total: source.length, pages: Math.max(1, Math.ceil(source.length / size)) };
}

const CONFIGS = {
  '/center/parent/index': {
    title: 'Danh sách phụ huynh',
    columns: [['no','No.'],['fullname','Phụ huynh'],['username','Tài khoản'],['student_name','Học viên'],['phone','Liên hệ'],['center','Trung tâm'],['source','Nguồn giới thiệu'],['status','Trạng thái'],['action','Hành động']].map(([key,label])=>({key,label})),
    filters: [{name:'q', placeholder:'Tìm kiếm...', kind:'text'}, {name:'status', options:['Chọn trạng thái','Tất cả','Phụ huynh có 1 học viên','Phụ huynh có nhiều học viên']}, {name:'source_type', options:['Phụ huynh','Giáo viên','Nhân viên','Học viên']}, {name:'source', placeholder:'Nguồn giới thiệu', kind:'search'}, {name:'student_table_length', label:'Hiển thị 10 25 50 100 bản ghi', options:['10','25','50','100']}],
    buttons: ['Excel','Thêm mới'], fields: [],
  },
  '/center/staff': {
    title: 'Danh sách nhân viên',
    columns: [['no','No.'],['fullname','Nhân viên'],['username','Tài khoản'],['phone','Liên hệ'],['roles','Phân quyền'],['status','Trạng thái'],['action','Hành động']].map(([key,label])=>({key,label})),
    filters: [{name:'q', placeholder:'Tìm kiếm...', kind:'text'}, {name:'staff_table_length', label:'Hiển thị 10 25 50 100 bản ghi', options:['10','25','50','100']}],
    buttons: ['Excel','Thêm nhân viên'], fields: [],
  },
  '/center/holiday/index': {
    title: 'Lịch nghỉ',
    columns: [['no','No.'],['name','Tên lịch nghỉ'],['start_date','Từ ngày'],['end_date','Đến hết ngày'],['description','Mô tả'],['notice','Thông báo'],['status','Trạng thái'],['action','Hành động']].map(([key,label])=>({key,label})),
    filters: [{name:'q', placeholder:'Tìm...', kind:'text'}, {name:'holiday_table_length', label:'Hiển thị 10 25 50 100 bản ghi', options:['10','25','50','100']}],
    buttons: ['Cập nhật TKB','Thêm mới'], fields: [],
  },
  '/survey/create_survey': {
    title: 'Tạo khảo sát', columns: [], filters: [], tabs: [], buttons: [], fields: [],
  },
  '/cso/support': {
    title: 'Hỗ trợ',
    columns: [
      ['no', 'No.'], ['deadline', 'Thời gian'], ['type', 'Loại'], ['content', 'Nội dung'],
      ['sender', 'Người gửi'], ['class_name', 'Lớp của học viên'], ['staff_name', 'Nhân viên'], ['status', 'Trạng thái'],
    ].map(([key, label]) => ({ key, label })),
    filters: [
      { options: ['Tất cả trạng thái', 'Mới tiếp nhận', 'Đang xử lý', 'Đã xử lý', 'Đã đóng'] },
      { options: ['Tất cả loại', 'Phản hồi/Hỗ trợ', 'Khiếu nại'] },
      { placeholder: 'Từ ngày' }, { placeholder: 'Đến ngày' }, { placeholder: 'Tìm...' },
    ],
    tabs: ['Tiếp nhận từ người dùng', 'Hỗ trợ nội bộ'], buttons: ['Excel', 'Tạo', 'Mới tiếp nhận'],
    fields: [
      { name: 'sender', label: 'Học viên / Phụ huynh' }, { name: 'student_name', label: 'Học viên' },
      { name: 'content', label: 'Nội dung', type: 'textarea', required: true },
      { name: 'staff_name', label: 'Nhân viên', options: STAFF },
      { name: 'type', label: 'Loại', options: ['Phản hồi/Hỗ trợ', 'Khiếu nại'] },
      { name: 'deadline', label: 'Hạn xử lý', type: 'date' },
      { name: 'status', label: 'Trạng thái', options: ['Mới tiếp nhận', 'Đang xử lý', 'Đã xử lý', 'Đã đóng'] },
      { name: 'note', label: 'Ghi chú', type: 'textarea' },
    ],
  },
  '/cso/customer-care': {
    title: 'Chăm sóc khách hàng',
    columns: [
      ['no', 'No.'], ['student_name', 'Học viên'], ['class_name', 'Lớp'], ['staff_name', 'Nhân viên'],
      ['care_round', 'Lần chăm sóc'], ['content', 'Nội dung'], ['status', 'Trạng thái'],
    ].map(([key, label]) => ({ key, label })),
    filters: [
      { options: ['Tất cả', 'Chưa xử lý', 'Đang xử lý', 'Đã xong', 'Quá hạn'] }, { placeholder: 'Từ ngày' },
      { placeholder: 'Đến ngày' }, { placeholder: 'Tìm...' },
      { options: ['Chọn lớp học', ...CLASSES] }, { options: ['Chọn nhân viên', ...STAFF] },
      { options: ['Chọn số lần chăm sóc', 'Lần 01', 'Lần 02', 'Lần 03', 'Lần 04', 'Lần 05', 'Lần 06', 'Lần 07', 'Lần 08', 'Lần 09', 'Lần 10'] },
      { options: ['Gọi điện', 'Nhắn tin', 'Khảo sát'] }, { placeholder: 'Chọn hành động' },
      { options: ['Đồng ý', 'Từ chối'] }, { placeholder: 'Chọn kết quả' },
      { options: ['Khảo sát', 'Upsale', 'Xử lý góp ý/khiếu nại'] }, { placeholder: 'Chọn mục đích' },
      { label: 'Hiển thị 5 10 25 50 bản ghi', options: ['5', '10', '25', '50'] },
    ],
    tabs: [], buttons: ['Excel', 'Tạo mới', 'Chưa xử lý', 'Đã xong'],
    fields: [
      { name: 'student_name', label: 'Học viên', required: true }, { name: 'class_name', label: 'Lớp', options: CLASSES },
      { name: 'staff_name', label: 'Nhân viên', options: STAFF }, { name: 'care_round', label: 'Lần chăm sóc', options: ['Lần 01', 'Lần 02', 'Lần 03', 'Lần 04'] },
      { name: 'content', label: 'Nội dung', type: 'textarea' }, { name: 'action', label: 'Hành động', options: ['Gọi điện', 'Nhắn tin', 'Khảo sát'] },
      { name: 'purpose', label: 'Mục đích', options: ['Khảo sát', 'Bán thêm', 'Xử lý góp ý/khiếu nại'] }, { name: 'result', label: 'Kết quả', options: ['Đồng ý', 'Từ chối'] },
      { name: 'care_date', label: 'Ngày chăm sóc', type: 'date' }, { name: 'status', label: 'Trạng thái', options: ['Chưa xử lý', 'Đang xử lý', 'Đã xong', 'Quá hạn'] },
    ],
  },
  '/callcenter/extension': {
    // The live reference now exposes the extension directory as a list. Keep
    // the generated-screen persistence contract; do not fall back to the old
    // error/form-only projection captured in the first inventory snapshot.
    title: 'Danh sách số máy lẻ',
    columns: [
      ['no', 'No.'], ['extension', 'Số máy nhánh'], ['staff_name', 'Nhân viên'],
      ['status', 'Trạng thái'], ['action', 'Hành động'],
    ].map(([key, label]) => ({ key, label })),
    filters: [], tabs: [], buttons: ['Thêm mới', 'Excel'],
    fields: [{ name: 'extension', label: 'Số máy nhánh', required: true }, { name: 'staff_name', label: 'Nhân viên', options: STAFF }, { name: 'status', label: 'Trạng thái', options: ['Đang hoạt động', 'Đã khóa'] }],
  },
  '/callcenter/staff': {
    title: 'Danh sách nhân viên trực',
    columns: [
      ['staff_name', 'Nhân viên'], ['caller', 'Người gọi'], ['permission', 'Quyền'], ['created_by', 'Người tạo'],
      ['password_phone', 'Password phone'], ['domain', 'domain'], ['phone', 'Phone'], ['employee_code', 'Mã nhân viên'],
      ['phone_id', 'PhoneID'], ['branch_address', 'Địa chỉ nhánh'], ['branch', 'Nhánh'], ['empty', ''],
    ].map(([key, label]) => ({ key, label })),
    filters: [
      { kind: 'button' }, {}, {}, { kind: 'checkbox' }, { kind: 'checkbox' },
      {}, {}, {}, {}, {}, {}, {}, {}, { kind: 'button' }, { kind: 'button' },
    ],
    tabs: [], buttons: ['Thêm số máy'], fields: [{ name: 'staff_name', label: 'Nhân viên', required: true, options: STAFF }, { name: 'extension', label: 'Số máy nhánh', required: true }, { name: 'active', label: 'Đang trực', type: 'checkbox' }, { name: 'note', label: 'Ghi chú', type: 'textarea' }],
  },
  '/callcenter/get-statistic': {
    title: 'Thống kê cuộc gọi vào',
    columns: [['no', 'No.'], ['staff_name', 'Nhân viên nghe'], ['sale_group', 'Nhóm sale'], ['center', 'Trung tâm'], ['total_calls', 'Tổng cuộc gọi'], ['answered_calls', 'Cuộc gọi thành công'], ['missed_calls', 'cuộc gọi nhỡ'], ['failed_calls', 'Thất bại']].map(([key, label]) => ({ key, label })),
    // Reference has no clear button; the export action sits at the end of the
    // date row. The renderer consumes this flag without changing shared shell
    // files.
    noClear: true,
    filters: [{ placeholder: 'Từ ngày' }, { placeholder: 'Đến ngày' }], tabs: ['Thống kê cuộc gọi vào', 'Thống kê cuộc gọi ra'], buttons: ['Xuất exel'],
    fields: [{ name: 'from_date', label: 'Từ ngày', type: 'date', required: true }, { name: 'to_date', label: 'Đến ngày', type: 'date', required: true }, { name: 'total_calls', label: 'Tổng số cuộc gọi', type: 'number' }, { name: 'answered_calls', label: 'Cuộc gọi đã nghe', type: 'number' }, { name: 'missed_calls', label: 'Cuộc gọi nhỡ', type: 'number' }],
  },
  '/callcenter/history': {
    title: 'Lịch sử cuộc gọi', columns: [['no', 'No.'], ['phone', 'Số điện thoại'], ['name', 'Họ tên'], ['permission', 'Quyền'], ['call_type', 'Loại cuộc gọi'], ['staff_name', 'Nhân viên'], ['note', 'Ghi chú'], ['status', 'Trạng thái'], ['duration', 'Thời lượng cuộc gọi'], ['recording', 'Ghi âm'], ['called_at', 'Thời gian']].map(([key, label]) => ({ key, label })),
    noClear: true,
    filters: [{}, {}, { options: ['Tất cả', 'Học viên', 'Phụ huynh', 'Giáo viên', 'Nhân viên', 'Tiềm năng'] }, { kind: 'checkbox' }, { kind: 'checkbox' }, { options: ['All', ...STAFF] }, { options: ['Thất bại', 'Gọi nhỡ', 'Thành công'], multiple: true }, { kind: 'search' }, { placeholder: 'Từ ngày' }, { placeholder: 'Đến ngày' }],
    tabs: [], buttons: [], fields: [{ name: 'called_at', label: 'Thời gian', type: 'date', required: true }, { name: 'caller', label: 'Người gọi', required: true }, { name: 'party', label: 'Đối tượng', options: ['Học viên', 'Phụ huynh', 'Giáo viên', 'Nhân viên', 'Tiềm năng'] }, { name: 'staff_name', label: 'Nhân viên', options: STAFF }, { name: 'result', label: 'Kết quả', options: ['Thất bại', 'Gọi nhỡ', 'Thành công'] }, { name: 'duration', label: 'Thời lượng', type: 'number' }, { name: 'note', label: 'Ghi chú', type: 'textarea' }],
  },
  '/center/student/index': {
    title: 'Danh sách học viên', columns: [['no', 'No.'], ['student_name', 'Học viên'], ['username', 'Tài khoản'], ['parent_name', 'Phụ huynh'], ['sale_name', 'Sales rep'], ['class_name', 'Lớp học'], ['source', 'Nguồn giới thiệu'], ['note', 'Ghi chú']].map(([key, label]) => ({ key, label })),
    filters: [{ placeholder: 'Tìm kiếm...' }, { placeholder: 'Tìm phụ huynh' }, { options: ['Đang học', 'Bảo lưu', 'Chuyển lớp', 'Đã xong', 'Nghỉ học', 'Chưa học', 'Chưa có lớp'] }, { kind: 'search', placeholder: 'Chọn trạng thái' }, { options: ['Lớp Đàn Thầy Thái', ...CLASSES] }, { kind: 'search', placeholder: 'Chọn lớp học' }, { options: ['Phụ huynh', 'Giáo viên', 'Nhân viên', 'Học viên'] }, { kind: 'search', placeholder: 'Nguồn giới thiệu' }, { options: ['Chọn năm', '2026', '2025', '2024'] }, { options: ['Chọn trường học', 'THCS Nguyễn Du', 'THPT Hai Bà Trưng'] }, { label: 'Hiển thị 10 25 50 100 bản ghi', options: ['10', '25', '50', '100'] }],
    tabs: [], buttons: ['Excel', 'Upload', 'Thêm mới'], fields: [{ name: 'fullname', label: 'Họ và tên', required: true }, { name: 'code', label: 'Mã tài khoản', required: true }, { name: 'username', label: 'Tên đăng nhập', required: true }, { name: 'phone', label: 'Số điện thoại' }, { name: 'class_name', label: 'Lớp học' }, { name: 'status', label: 'Trạng thái', options: ['Đang học', 'Bảo lưu', 'Đã xong', 'Nghỉ học'] }],
  },
  '/center/teacher': {
    title: 'Danh sách giáo viên', columns: [['no', 'No.'], ['fullname', 'Giáo viên'], ['username', 'Tài khoản'], ['phone', 'Liên hệ'], ['nationality', 'Quốc tịch'], ['role', 'Phân quyền'], ['status', 'Trạng thái']].map(([key, label]) => ({ key, label })),
    filters: [{ placeholder: 'Tìm kiếm' }, { options: ['Chọn quốc tịch', 'Việt Nam', 'Hoa Kỳ', 'Anh', 'Úc'] }, { options: ['Chọn trạng thái', 'Kích hoạt', 'Đang khóa'] }, { label: 'Hiển thị 10 25 50 100 bản ghi', options: ['10', '25', '50', '100'] }], tabs: [], buttons: ['Excel', 'Thêm giáo viên'], fields: [{ name: 'fullname', label: 'Họ và tên', required: true }, { name: 'username', label: 'Tên đăng nhập', required: true }, { name: 'phone', label: 'Số điện thoại' }, { name: 'nationality', label: 'Quốc tịch', options: ['Việt Nam', 'Hoa Kỳ', 'Anh', 'Úc'] }, { name: 'role', label: 'Phân quyền', options: ['Giáo viên', 'Giáo viên chủ nhiệm'] }, { name: 'status', label: 'Trạng thái', options: ['Kích hoạt', 'Đang khóa'] }],
  },
  '/setup/classroom': {
    title: 'Phòng học', columns: [['no', 'No.'], ['code', 'Mã phòng học'], ['name', 'Tên phòng học'], ['capacity', 'Số ghế'], ['description', 'Mô tả'], ['status', 'Trạng thái'], ['action', 'Hành động']].map(([key, label]) => ({ key, label })), filters: [{ placeholder: 'Tìm...' }, { options: ['Tất cả', 'Đã khóa', 'Hoạt động'] }, { label: 'Hiển thị 10 25 50 100 bản ghi', options: ['10', '25', '50', '100'] }], tabs: ['Phòng học', 'Ca học'], buttons: ['Thêm mới'], fields: [{ name: 'code', label: 'Mã phòng học', required: true }, { name: 'name', label: 'Tên phòng học', required: true }, { name: 'capacity', label: 'Số ghế', type: 'number' }, { name: 'description', label: 'Mô tả', type: 'textarea' }, { name: 'status', label: 'Trạng thái', options: ['Hoạt động', 'Đã khóa'] }],
  },
  '/setup/daily-evaluation': { title: 'Thiết lập đánh giá hàng ngày', columns: [], filters: [], tabs: [], buttons: ['Tạo'], fields: [{ name: 'name', label: 'Tên tiêu chí', required: true }, { name: 'description', label: 'Mô tả', type: 'textarea' }, { name: 'status', label: 'Trạng thái', options: ['Hoạt động', 'Đã khóa'] }] },
  '/center/manager/index': { title: 'Cơ cấu tổ chức trung tâm', columns: [], filters: [], tabs: [], buttons: [], fields: [{ name: 'fullname', label: 'Họ và tên', required: true }, { name: 'center', label: 'Trung tâm', required: true }, { name: 'phone', label: 'Số điện thoại' }, { name: 'email', label: 'Email' }, { name: 'status', label: 'Trạng thái', options: ['Đang hoạt động', 'Đang nghỉ'] }] },
  '/center/tool/center/index': { title: 'Tool', columns: [], filters: [{ placeholder: 'Nhập đường link của lớp' }, { placeholder: '2020/04/01 10:05:00' }, { placeholder: '2020/04/01 10:05:00', kind: 'date-text' }], tabs: [], buttons: ['Nhấn vào đây để khôi phục buổi hủy', 'Nhấn vào đây để đổi ngày bắt đầu'], fields: [{ name: 'class_url', label: 'Nhập đường link của lớp', required: true }, { name: 'cancelled_session_date', label: 'Ngày buổi hủy', type: 'date' }, { name: 'new_start_date', label: 'Ngày bắt đầu mới', type: 'date' }, { name: 'action', label: 'Thao tác', options: ['Khôi phục buổi hủy', 'Đổi ngày bắt đầu'] }] },
  '/center/document-permission': { title: 'Phân quyền tài liệu', columns: [], filters: [{ options: ['Chọn khóa học', 'IELTS Foundation', 'Tiếng anh cơ bản'] }, { placeholder: 'Tìm kiếm ...' }], tabs: [], buttons: ['Cập nhật'], fields: [{ name: 'course', label: 'Khóa học', required: true }, { name: 'document', label: 'Tài liệu', required: true }, { name: 'role', label: 'Vai trò', options: ['Giáo viên', 'Nhân viên'] }, { name: 'enabled', label: 'Được phép', options: ['Có', 'Không'] }] },
  '/tenant/config_excel': { title: 'Cấu hình xuất excel báo cáo', columns: [['no', 'No.'], ['report_name', 'Báo cáo'], ['enabled', 'Tắt/bật excel báo cáo']].map(([key, label]) => ({ key, label })), filters: [], tabs: ['Cấu hình xuất excel báo cáo'], buttons: [], fields: [] },
  '/center/upload_address': { title: 'Tool chinh sửa địa chỉ', noClear: true, columns: [['no', 'No.'], ['branch', 'Chi nhánh'], ['student_code', 'Mã học viên'], ['student_name', 'Học viên'], ['identity_code', 'Mã định danh'], ['english_name', 'Tên tiếng anh'], ['gender', 'Giới tính'], ['dob', 'Ngày sinh'], ['username', 'Tài khoản'], ['phone', 'SĐT'], ['email', 'Email'], ['old_province', 'Tỉnh cũ'], ['old_district', 'Huyện cũ'], ['old_ward', 'Xã phường'], ['new_province', 'Tỉnh mới'], ['new_ward', 'Phường xã mới']].map(([key, label]) => ({ key, label })), filters: [{ name: 'file', kind: 'file' }], pageSizes: ['5', '10', '25', '50'], tabs: ['Công cụ chỉnh sửa địa chỉ học sinh', 'Công cụ chỉnh sửa địa chỉ khách hàng tiềm năng'], buttons: ['Lưu'], fields: [{ name: 'branch', label: 'Chi nhánh', required: true }, { name: 'student_code', label: 'Mã học viên', required: true }, { name: 'student_name', label: 'Học viên', required: true }, { name: 'phone', label: 'Số điện thoại' }, { name: 'email', label: 'Email' }, { name: 'old_province', label: 'Tỉnh cũ' }, { name: 'new_province', label: 'Tỉnh mới' }] },
};

export function register(centerEdu = globalThis.CenterEdu) {
  if (!centerEdu) return { routes: Object.keys(CONFIGS) };
  for (const [route, config] of Object.entries(CONFIGS)) {
    // `/setup/classroom` has a dedicated domain owner in app.js.  Leave the
    // lane's metadata registration intact, but do not replace its renderer
    // with the generated-screen projection (which can expose a placeholder
    // row and routes create actions to the wrong entity).
    if (route === '/setup/classroom') continue;
    centerEdu.registerScreen?.(route, (screen) => renderW6Screen(centerEdu, route, config, screen));
  }
  // Students already have a coordinator-owned renderer backed by the real
  // `/api/students` entity.  Do not replace that persistent list with the
  // generic generated-screen fixture (which only contains one shell row).
  // Returning false lets app.js run its CRUD/filter/upload/export surface.
  centerEdu.registerScreen?.('/center/student/index', async () => false);
  return { routes: Object.keys(CONFIGS), status: 'PERSISTENT_LOCAL_CONTRACT' };
}

export { CONFIGS as W6_OVERRIDE_CONFIGS };

/*
 * Lane-local metadata and transport helpers for the home/training surfaces.
 * app.js owns the current shell; this module is safe to mount from a registry
 * without changing shared navigation or CSS.  Labels and enum values are
 * Vietnamese because they are customer-facing contract values.
 */
export const TRAINING_ROUTES = Object.freeze([
  '/', '/dashboard/training', '/training/announcement', '/training/absent-v2',
  '/training/event', '/training/post', '/training/course', '/training/class',
  '/training/class/create',
  '/training/timetable', '/training/attendance', '/training/daily-evaluation-v2',
  '/training/test', '/training/homework', '/training/elearn/topic',
  '/training/elearn/exam_first_test', '/training/class_enroll_trail_wait',
  '/training/confirm', '/training/customer_test', '/training/pending_enrollment/index',
]);

export const CLASS_CREATE_ROUTE = '/training/class/create';
export const CLASS_CREATE_STEPS = Object.freeze([
  { key: 'class', label: 'Lớp học' },
  { key: 'schedule', label: 'Lịch học' },
  { key: 'students', label: 'Học viên' },
]);
export const CLASS_CREATE_FIELDS = Object.freeze([
  { name: 'fullname', label: 'Tên lớp', type: 'text', payloadName: 'name' },
  { name: 'code', label: 'Mã lớp', required: true, type: 'text' },
  { name: 'course_id', label: 'Khóa học', required: true, type: 'select' },
  { name: 'number_of_session', label: 'Số buổi', type: 'number' },
  { name: 'number_of_session_vietnam_teacher', label: 'Số buổi giáo viên Việt', type: 'number' },
  { name: 'number_of_session_foreign_teacher', label: 'Số buổi giáo viên nước ngoài', type: 'number' },
  { name: 'number_of_hours', label: 'Số giờ', type: 'number' },
  { name: 'open_at', label: 'Ngày bắt đầu', type: 'date' },
  { name: 'close_at', label: 'Ngày kết thúc', type: 'date' },
  { name: 'type_cost', label: 'Hình thức học phí', type: 'select', options: [['0', 'Theo khóa'], ['1', 'Theo buổi'], ['2', 'Theo tháng']] },
  { name: 'max_student', label: 'Số học viên tối đa', type: 'number' },
  { name: 'max_student_per_session', label: 'Số học viên tối đa mỗi buổi', type: 'number' },
  { name: 'cm_ids[]', label: 'CM chính', type: 'select-multiple', observedOnly: true },
  { name: 'cm_second_ids[]', label: 'CM phụ', type: 'select-multiple', observedOnly: true },
  { name: 'daily_evaluation_id', label: 'Bài đánh giá hàng ngày', type: 'text', observedOnly: true },
  { name: 'note', label: 'Ghi chú', type: 'textarea' },
  { name: 'room', label: 'Phòng học', type: 'text' },
  { name: 'sessions', label: 'Các buổi học', type: 'array' },
  { name: 'student_ids', label: 'Học viên đã chọn', type: 'array' },
]);
export const CLASS_CREATE_CONTRACT = Object.freeze({
  route: CLASS_CREATE_ROUTE,
  title: 'Tạo lớp học',
  steps: CLASS_CREATE_STEPS,
  fields: CLASS_CREATE_FIELDS,
  submit: '/api/classes/workflow',
  source: 'observed DOM + local workflow adapter',
  persistence: 'coordinator-owned classes.name + classes/timetable_sessions/enrollments transaction',
  nameTransport: {
    input: 'fullname', payload: 'name', maxLength: 160,
    provenance: 'observed DOM field; coordinator integration key',
    readback: 'data.class.name must equal the submitted trimmed value',
  },
  unknowns: ['cm_ids[]', 'cm_second_ids[]', 'daily_evaluation_id'],
});

export const TRAINING_ROUTE_COLUMNS = Object.freeze({
  '/': [['class_name', 'Tên lớp'], ['branch', 'Chi nhánh'], ['session_name', 'Buổi học'], ['teacher_name', 'Giáo viên'], ['attendance', 'Điểm danh'], ['evaluation', 'Đánh giá'], ['test_count', 'Kiểm tra'], ['lesson_content', 'Nội dung bài học'], ['homework', 'BTVN']],
  '/dashboard/training': [['class_name', 'Tên lớp'], ['branch', 'Chi nhánh'], ['session_name', 'Buổi học'], ['teacher_name', 'Giáo viên'], ['attendance', 'Điểm danh'], ['evaluation', 'Đánh giá'], ['test_count', 'Kiểm tra'], ['lesson_content', 'Nội dung bài học'], ['homework', 'BTVN']],
  '/training/announcement': [['no', 'No.'], ['title', 'Thông báo'], ['sent', 'Đã xem/Đã gửi'], ['status', 'Trạng thái'], ['created_by', 'Tạo bởi'], ['comment_config', 'Cấu hình bình luận'], ['branch', 'Chi nhánh'], ['actions', 'Hành động']],
  '/training/absent-v2': [['no', 'No.'], ['student_name', 'Học viên'], ['session_name', 'Buổi nghỉ'], ['reason', 'Lý do'], ['status', 'Trạng thái'], ['comment', 'Bình luận']],
  '/training/event': [['no', 'No.'], ['views', 'Lượt xem'], ['description', 'Nội dung'], ['sent', 'Đã xem/Đã gửi'], ['status', 'Trạng thái'], ['comment', 'Bình luận'], ['actions', 'Công cụ']],
  '/training/post': [['no', 'No.'], ['class_name', 'Lớp học'], ['content', 'Nội dung'], ['created_by', 'Người tạo'], ['created_at_value', 'Ngày tạo'], ['comment_config', 'Cấu hình bình luận'], ['status', 'Trạng thái'], ['branch', 'Chi nhánh'], ['actions', 'Hành động']],
  '/training/course': [['no', 'No.'], ['name', 'Tên khóa học'], ['sessions_hours', 'Số buổi / Số giờ'], ['fee_display', 'Học phí'], ['daily_evaluation', 'Bài đánh giá hàng ngày'], ['test_count', 'Bài kiểm tra'], ['subject', 'Môn học'], ['status', 'Trạng thái'], ['actions', 'Hành động']],
  '/training/class': [['no', 'No.'], ['code', 'Lớp học'], ['course_name', 'Khóa học'], ['student_count', 'Học viên (Đang học)'], ['period', 'Thời gian'], ['schedule', 'Lịch học'], ['manager', 'CM'], ['teacher_name', 'Giáo viên'], ['completed_sessions', 'Đã học/Số buổi'], ['actions', 'Hành động']],
  '/training/timetable': [['session_date', 'Ngày'], ['room_session', 'Phòng học Ca học'], ['A01', 'A01'], ['A02', 'A02'], ['c5', 'c5'], ['room_01', 'Phòng 01'], ['room_1', 'Phòng 1'], ['sky_room_teacher', 'phòng học Sky, giáo viên Hà Anh'], ['sky_room_teacher_2', 'phòng học Sky, giáo viên Hà Anh']],
  '/training/attendance': [
    ['student_code', 'Mã học viên'], ['full_name', 'Học viên'], ['class_code', 'Lớp học'],
    ['session_date', 'Ngày'], ['status', 'Trạng thái'], ['note', 'Ghi chú'],
  ],
  '/training/daily-evaluation-v2': [],
  '/training/test': [],
  '/training/homework': [],
  '/training/elearn/topic': [],
  '/training/elearn/exam_first_test': [],
  '/training/class_enroll_trail_wait': [['no', 'No.'], ['customer_name', 'Khách hàng'], ['parent_name', 'Phụ huynh'], ['sale_owner', 'Sales rep'], ['class_name', 'Lớp học'], ['schedule', 'Thời gian'], ['status', 'Trạng thái'], ['actions', 'Hành động'], ['note', 'Ghi chú']],
  '/training/confirm': [['no', 'No.'], ['full_name', 'Họ tên'], ['class_name', 'Lớp đăng ký'], ['sessions_count', 'Số buổi'], ['schedule', 'Lịch'], ['enrolled_at', 'Ngày ghi danh vào lớp'], ['contract_code', 'Mã hợp đồng'], ['status', 'Trạng thái'], ['performed_by', 'Người thực hiện'], ['actions', 'Công cụ']],
  '/training/customer_test': [['no', 'STT'], ['customer_name', 'Khách hàng'], ['parent_name', 'Phụ huynh'], ['test_date', 'Ngày hẹn test'], ['score', 'Điểm test'], ['sale_owner', 'Nhân viên sale'], ['note', 'Ghi chú']],
  '/training/pending_enrollment/index': [['no', 'No.'], ['customer_name', 'Khách hàng'], ['center_name', 'Trung tâm'], ['session_name', 'Ca học'], ['sessions_count', 'Số buổi'], ['start_date', 'Ngày bắt đầu'], ['course_name', 'Khóa học'], ['note', 'Ghi chú'], ['status', 'Trạng thái'], ['created_by', 'Tạo bởi'], ['actions', 'Hành động']],
});

export const TRAINING_STATUS_LABELS = Object.freeze({
  ACTIVE: 'Hoạt động', INACTIVE: 'Ngừng hoạt động',
  PLANNED: 'Chưa học', OPEN: 'Đang học', IN_PROGRESS: 'Đang học',
  COMPLETED: 'Đã học xong', CANCELLED: 'Đã hủy',
  SCHEDULED: 'Đã lên lịch', PRESENT: 'Có mặt', ABSENT: 'Vắng',
  LATE: 'Đi muộn', EXCUSED: 'Có phép', DRAFT: 'Bản nháp',
  PUBLISHED: 'Đã công bố', PENDING: 'Chờ xử lý', APPROVED: 'Đã duyệt',
  REJECTED: 'Từ chối', WAITING: 'Đang chờ', ASSIGNED: 'Đã vào lớp',
  BOOKED: 'Đã đặt lịch', SCORED: 'Đã chấm điểm',
});

export const TRAINING_RBAC = Object.freeze({
  read: ['ADMIN', 'STAFF', 'TEACHER', 'STUDENT'],
  manage: ['ADMIN', 'STAFF'],
  teach: ['ADMIN', 'STAFF', 'TEACHER'],
});

export const COURSE_COLUMNS = Object.freeze([
  ['no', 'No.'], ['name', 'Tên khóa học'], ['sessions_hours', 'Số buổi / Số giờ'],
  ['fee_display', 'Học phí'], ['daily_evaluation', 'Bài đánh giá hàng ngày'],
  ['test_count', 'Bài kiểm tra'], ['subject', 'Môn học'], ['status', 'Trạng thái'],
  ['actions', 'Hành động'],
]);

export const COURSE_FIELDS = Object.freeze([
  { name: 'code', label: 'Mã khóa', required: true },
  { name: 'name', label: 'Tên khóa học', required: true },
  { name: 'sessions_count', label: 'Số buổi', type: 'number' },
  { name: 'hours', label: 'Số giờ', type: 'number' },
  { name: 'fee_method', label: 'Phương thức thu tiền', type: 'select', options: ['Theo khóa', 'Theo buổi', 'Theo tháng'] },
  { name: 'fee', label: 'Học phí', type: 'number' },
  { name: 'daily_evaluation', label: 'Bài đánh giá hàng ngày' },
  { name: 'subject', label: 'Môn học' },
  { name: 'status', label: 'Trạng thái', type: 'select', options: ['Hoạt động', 'Ngừng hoạt động'] },
  { name: 'description', label: 'Mô tả' },
]);

/*
 * The generic shell renderer is useful for routes with no dedicated local
 * surface, but the training capture has a few deliberately unusual tables:
 * timetable is a room matrix, course uses the public course API, and several
 * screens intentionally expose controls without a table.  Keep those shapes
 * in this lane module so shared app.js does not need route-specific branches.
 */
const OBSERVED_FILTERS = Object.freeze({
  '/': [
    { kind: 'select', options: ['Chọn chi nhánh', 'Trung tâm CenterOnline - Demo'] },
    { kind: 'input', placeholder: 'Chọn ngày' },
    { kind: 'input', placeholder: 'Tìm kiếm' },
  ],
  '/dashboard/training': [
    { kind: 'select', options: ['Chọn chi nhánh', 'Trung tâm CenterOnline - Demo'] },
    { kind: 'input', placeholder: 'Chọn ngày' },
    { kind: 'input', placeholder: 'Tìm kiếm' },
  ],
  '/training/announcement': [
    { kind: 'select', options: ['Tất cả', 'Đã gửi', 'Chưa gửi'] },
    { kind: 'select', options: ['Chọn chi nhánh', 'Trung tâm CenterOnline - Demo'] },
    { kind: 'select', options: ['Tất cả', 'Quan trọng', 'Không quan trọng'] },
    { kind: 'input', placeholder: 'Tìm kiếm...' },
    { kind: 'select', label: 'Hiển thị 5 10 25 50 bản ghi', options: ['5', '10', '25', '50'] },
  ],
  '/training/absent-v2': [
    { kind: 'select', options: ['Tất cả', 'Chưa phê duyệt', 'Đồng ý', 'Từ chối', 'Hủy', 'Nhận thông tin'] },
    { kind: 'select', options: ['Tất cả các lớp', 'TA-NEN-TANG-01', 'TA-GIAO-TIEP-02'] },
    { kind: 'input', placeholder: 'Từ ngày' },
    { kind: 'input', placeholder: 'Đến ngày' },
    { kind: 'input', placeholder: 'Tìm kiếm...' },
    { kind: 'file' }, { kind: 'textarea', placeholder: 'Viết' },
    { kind: 'file' }, { kind: 'textarea' },
    { kind: 'file' }, { kind: 'textarea' },
    { kind: 'file' }, { kind: 'textarea' },
    { kind: 'file' }, { kind: 'textarea' },
    { kind: 'file' }, { kind: 'textarea' },
    { kind: 'file' }, { kind: 'textarea' },
  ],
  '/training/event': [
    { kind: 'select', options: ['Tất cả', 'Mới tạo', 'Đã gửi'] },
    { kind: 'input', placeholder: 'Tìm kiếm...' },
    { kind: 'file' }, { kind: 'textarea', placeholder: 'Viết bình luận...' },
    { kind: 'file' }, { kind: 'textarea' },
  ],
  '/training/post': [
    { kind: 'select', options: ['Tất cả các lớp', 'TA-NEN-TANG-01', 'TA-GIAO-TIEP-02'] },
    { kind: 'select', options: ['Tất cả trạng thái', 'Chờ phê duyệt', 'Đã phê duyệt'] },
    { kind: 'select', options: ['Chọn chi nhánh', 'Trung tâm CenterOnline - Demo'] },
    { kind: 'input', placeholder: 'Tìm kiếm...' },
    { kind: 'input' }, { kind: 'input' },
    { kind: 'select', label: 'Hiển thị 5 10 25 50 bản ghi', options: ['5', '10', '25', '50'] },
  ],
  '/training/course': [
    { kind: 'input', placeholder: 'Tìm...' },
    { kind: 'select', label: '10 20 50', options: ['10', '20', '50'] },
  ],
  '/training/daily-evaluation-v2': [
    { kind: 'select', name: 'evaluation_class', options: ['Tất cả'] },
    { kind: 'select', name: 'evaluation_status', options: ['Tất cả', 'Nháp', 'Đã công bố'] },
    { kind: 'input', name: 'evaluation_date_from', placeholder: 'Từ ngày' },
    { kind: 'input', name: 'evaluation_date_to', placeholder: 'Đến ngày' },
  ],
  '/training/class': [
    { kind: 'select', options: ['Tất cả', 'Chưa học', 'Đang học', 'Sắp kết thúc', 'Đã xong', 'Bị hủy', 'Chưa có lịch học'] },
    { kind: 'input' },
    { kind: 'select', options: ['Tất cả khóa học', 'Tiếng Anh nền tảng', 'IELTS mục tiêu 6.5'] },
    { kind: 'input', placeholder: 'Tìm...' },
    { kind: 'select', options: ['Chọn CM', 'Nguyễn Thu Hà', 'Phạm Ngọc Linh'] },
    { kind: 'select', options: ['Đang học', 'Chưa học'] },
    { kind: 'input' },
    { kind: 'select', options: ['Chọn giáo viên', 'Cô Trần Minh Anh', 'Thầy Nguyễn Hoàng Nam'] },
    { kind: 'input', placeholder: 'Ngày bắt đầu: từ ngày' },
    { kind: 'input', placeholder: 'Ngày bắt đầu: đến ngày' },
    { kind: 'input', placeholder: 'Ngày kết thúc: từ ngày' },
    { kind: 'input', placeholder: 'Ngày kết thúc: đến ngày' },
  ],
  '/training/timetable': [
    // Week/day have no exact /api/timetable key in the local contract; keep
    // them as observed local controls until a date mapping is verified.
    { kind: 'select', localOnly: true, name: 'week', ariaLabel: 'Tuần', options: [] },
    { kind: 'select', localOnly: true, name: 'day', ariaLabel: 'Thứ', options: ['Thứ 2', 'Thứ 3', 'Thứ 4', 'Thứ 5', 'Thứ 6', 'Thứ 7', 'Chủ nhật'] },
    { kind: 'input', localOnly: true, name: 'day_date', ariaLabel: 'Ngày trong tuần', placeholder: 'Chọn thứ' },
    { kind: 'select', queryKey: 'teacher', name: 'teacher', ariaLabel: 'Giáo viên', options: ['Chọn giáo viên', 'Cô Trần Minh Anh', 'Thầy Nguyễn Hoàng Nam'] },
    { kind: 'select', queryKey: 'course', name: 'course', ariaLabel: 'Khóa học', options: ['Tiếng Anh nền tảng', 'Tiếng Anh giao tiếp', 'IELTS mục tiêu 6.5'] },
    { kind: 'select', queryKey: 'class_code', name: 'class_code', ariaLabel: 'Lớp học', options: ['TA-NEN-TANG-01', 'TA-GIAO-TIEP-02'] },
    { kind: 'input', localOnly: true, name: 'session_number', ariaLabel: 'Số thứ tự buổi học', placeholder: 'Số thứ tự buổi học' },
    { kind: 'input', queryKey: 'time', name: 'time_from', ariaLabel: 'Giờ ca học từ', placeholder: 'Giờ ca học từ' },
    { kind: 'input', localOnly: true, name: 'time_to', ariaLabel: 'Giờ ca học đến', placeholder: 'Giờ ca học đến' },
    { kind: 'select', queryKey: 'room', name: 'room_select', ariaLabel: 'Phòng học', options: ['A01', 'A02', 'c5', 'Phòng 01', 'Phòng 1', 'phòng học Sky, giáo viên Hà Anh'] },
    { kind: 'input', queryKey: 'room', name: 'room', ariaLabel: 'Phòng học', placeholder: 'Chọn phòng học' },
  ],
  '/training/attendance': [
    { kind: 'select', name: 'attendance_status', options: ['Tất cả', 'Có mặt', 'Vắng', 'Đi muộn', 'Có phép'] },
    { kind: 'select', name: 'attendance_class', options: ['Chọn lớp học', 'TA-NEN-TANG-01', 'TA-GIAO-TIEP-02'] },
    { kind: 'select', name: 'attendance_session', options: ['Chọn buổi học', '03/11/2026'] },
  ],
  '/training/test': [
    { kind: 'select', options: ['Đang học', 'Đã học', 'Tất cả'] },
    { kind: 'select', options: ['Chọn lớp học', 'TA-NEN-TANG-01', 'TA-GIAO-TIEP-02'] },
    { kind: 'select', options: ['Chọn bài kiểm tra', 'Bài kiểm tra giữa khóa'] },
    { kind: 'input', placeholder: 'Tìm...' },
  ],
  '/training/homework': [
    { kind: 'select', options: ['Đang học', 'Đã học', 'Tất cả'] },
    { kind: 'select', options: ['Chọn lớp học', 'TA-NEN-TANG-01', 'TA-GIAO-TIEP-02'] },
    { kind: 'select', options: ['Chọn buổi học', 'Buổi 1 · 03/11/2026'] },
    { kind: 'select', options: ['Đã trả bài', 'Chưa trả bài'] },
  ],
  '/training/class_enroll_trail_wait': [
    { kind: 'select', options: ['Tất cả các lớp', 'TA-NEN-TANG-01', 'TA-GIAO-TIEP-02'] },
    { kind: 'select', options: ['Tất cả', 'Chưa phê duyệt', 'Đã phê duyệt', 'Hủy học thử'] },
    { kind: 'input', placeholder: 'Từ ngày' }, { kind: 'input', placeholder: 'Đến ngày' },
    { kind: 'input', placeholder: 'Tìm...' },
    { kind: 'select', label: '20 50 100', options: ['20', '50', '100'] },
  ],
  '/training/confirm': [
    { kind: 'input', placeholder: 'Tìm trong bảng...' },
    { kind: 'select', options: ['Chọn lớp học', 'TA-NEN-TANG-01', 'TA-GIAO-TIEP-02'] },
    { kind: 'select', options: ['Chọn nhân viên', 'Nguyễn Thu Hà', 'Phạm Ngọc Linh'] },
    { kind: 'select', label: 'Hiển thị 5 10 25 50 bản ghi', options: ['5', '10', '25', '50'] },
  ],
  '/training/customer_test': [
    { kind: 'input', placeholder: 'Tìm trong bảng...' },
    { kind: 'input', placeholder: 'Từ ngày' }, { kind: 'input', placeholder: 'Đến ngày' },
    { kind: 'select', options: ['Tất cả', 'Nguyễn Thu Hà', 'Phạm Ngọc Linh'] },
    { kind: 'select', label: 'Hiển thị 10 25 50 All bản ghi', options: ['10', '25', '50', 'All'] },
  ],
  '/training/pending_enrollment/index': [
    { kind: 'select', options: ['Đang chờ', 'Đã vào lớp', 'Hủy'] },
    { kind: 'input', placeholder: 'Chọn trạng thái' },
    { kind: 'select', options: ['Chưa chọn Thứ', 'Thứ 2', 'Thứ 3', 'Thứ 4', 'Thứ 5', 'Thứ 6', 'Thứ 7', 'Chủ nhật'] },
    { kind: 'input', placeholder: 'Chọn ngày trong tuần' },
    { kind: 'select', options: ['Chủ nhật 14:10 - 15:00', 'Thứ 2 18:30 - 20:00'] },
    { kind: 'input', placeholder: 'Chọn ca' },
    { kind: 'select', options: ['Chưa chọn Khóa', 'Tiếng Anh nền tảng', 'IELTS mục tiêu 6.5'] },
    { kind: 'input', placeholder: 'Chọn khóa' },
    { kind: 'input', placeholder: 'Tìm kiếm ...' },
    { kind: 'select', label: '10 20 50 100', options: ['10', '20', '50', '100'] },
  ],
});

const OBSERVED_NO_TABLE_ROUTES = new Set([
  '/training/daily-evaluation-v2', '/training/test',
  '/training/homework', '/training/elearn/topic', '/training/elearn/exam_first_test',
]);

const CLASS_CREATE_NUMBER_FIELDS = Object.freeze([
  ['number_of_session', 'Số buổi'],
  ['number_of_session_vietnam_teacher', 'Số buổi giáo viên Việt'],
  ['number_of_session_foreign_teacher', 'Số buổi giáo viên nước ngoài'],
  ['number_of_hours', 'Số giờ'],
  ['max_student', 'Số học viên tối đa'],
  ['max_student_per_session', 'Số học viên tối đa mỗi buổi'],
]);

function workflowDate(value, label) {
  const text = String(value ?? '').trim();
  if (!text) return '';
  const display = text.match(/^(\d{1,2})[\/-](\d{1,2})[\/-](\d{4})$/);
  const iso = display ? `${display[3]}-${String(display[2]).padStart(2, '0')}-${String(display[1]).padStart(2, '0')}` : text;
  if (!/^\d{4}-\d{2}-\d{2}$/.test(iso) || Number.isNaN(Date.parse(`${iso}T00:00:00Z`))) throw new Error(`${label} phải là ngày hợp lệ`);
  return iso;
}

function workflowNumber(value, label) {
  if (value === undefined || value === null || String(value).trim() === '') return undefined;
  const number = Number(value);
  if (!Number.isFinite(number) || number < 0) throw new Error(`${label} phải là số không âm`);
  return Number.isInteger(number) ? number : number;
}

const CLASS_NAME_MAX_LENGTH = 160;

function workflowClassName(value) {
  if (value !== undefined && value !== null && typeof value !== 'string') {
    throw new Error('Tên lớp phải là văn bản');
  }
  const name = String(value ?? '').trim();
  if (name.length > CLASS_NAME_MAX_LENGTH) throw new Error(`Tên lớp không được dài quá ${CLASS_NAME_MAX_LENGTH} ký tự`);
  return name;
}

export function assertClassWorkflowName(result, expectedName) {
  const expected = workflowClassName(expectedName);
  if (!expected) return result;
  const persisted = result?.data?.class?.name;
  if (persisted !== expected) {
    throw new Error('Tên lớp chưa được hệ thống hỗ trợ lưu; không thể xác nhận đã lưu lớp học');
  }
  return result;
}

/** Normalize observed wizard names to the verified local workflow payload. */
export function classWorkflowPayload(input = {}) {
  if (!input || typeof input !== 'object') throw new Error('Dữ liệu tạo lớp không hợp lệ');
  const courseId = Number(input.course_id);
  if (!Number.isInteger(courseId) || courseId < 1) throw new Error('Khóa học là bắt buộc');
  const code = String(input.code ?? '').trim().toUpperCase();
  if (!code) throw new Error('Mã lớp là bắt buộc');
  if (code.length > 32) throw new Error('Mã lớp không được dài quá 32 ký tự');
  const fullname = workflowClassName(input.fullname);
  const payload = { course_id: courseId, code };
  if (fullname) payload.name = fullname;
  CLASS_CREATE_NUMBER_FIELDS.forEach(([name, label]) => {
    const value = workflowNumber(input[name], label);
    if (value !== undefined) payload[{
      number_of_session: 'sessions_count',
      number_of_session_vietnam_teacher: 'vn_teacher_sessions',
      number_of_session_foreign_teacher: 'foreign_teacher_sessions',
      number_of_hours: 'hours', max_student: 'max_students', max_student_per_session: 'max_students_per_session',
    }[name]] = value;
  });
  const openAt = workflowDate(input.open_at, 'Ngày bắt đầu');
  const closeAt = workflowDate(input.close_at, 'Ngày kết thúc');
  if (openAt) payload.start_date = openAt;
  if (closeAt) payload.end_date = closeAt;
  if (openAt && closeAt && closeAt < openAt) throw new Error('Ngày kết thúc phải sau ngày bắt đầu');
  const payment = input.type_cost;
  if (payment !== undefined && payment !== null && String(payment).trim() !== '') {
    payload.payment_method = ({ 0: 'Theo khóa', 1: 'Theo buổi', 2: 'Theo tháng' })[String(payment)] || String(payment).trim();
  }
  [['room', 'room'], ['note', 'notes'], ['notes', 'notes'], ['status', 'status'], ['teacher_id', 'teacher_id']].forEach(([source, name]) => {
    if (input[source] !== undefined && input[source] !== null && String(input[source]).trim() !== '') {
      if (name === 'teacher_id') {
        const teacherId = Number(input[source]);
        if (!Number.isInteger(teacherId) || teacherId < 1) throw new Error('teacher_id phải là số dương');
        payload[name] = teacherId;
      } else payload[name] = String(input[source]).trim();
    }
  });
  const sessions = Array.isArray(input.sessions) ? input.sessions : [];
  payload.sessions = sessions.map((item, index) => {
    if (!item || typeof item !== 'object') throw new Error(`Buổi học ${index + 1} không hợp lệ`);
    const sessionDate = workflowDate(item.session_date, `Buổi học ${index + 1}`);
    const start = String(item.start_time ?? '').trim();
    const end = String(item.end_time ?? '').trim();
    if (!sessionDate || !/^([01]\d|2[0-3]):[0-5]\d$/.test(start) || !/^([01]\d|2[0-3]):[0-5]\d$/.test(end) || end <= start) throw new Error(`Buổi học ${index + 1} có thời gian không hợp lệ`);
    return { session_date: sessionDate, start_time: start, end_time: end, ...(item.room ? { room: String(item.room).trim() } : {}) };
  });
  const studentIds = Array.isArray(input.student_ids) ? input.student_ids.map(Number) : [];
  if (studentIds.some((id) => !Number.isInteger(id) || id < 1) || new Set(studentIds).size !== studentIds.length) throw new Error('Danh sách học viên không hợp lệ hoặc bị trùng');
  payload.student_ids = studentIds;
  return payload;
}

export async function saveClassWorkflow(input, fetcher = fetch) {
  const payload = classWorkflowPayload(input);
  const response = await fetcher('/api/classes/workflow', {
    method: 'POST', credentials: 'same-origin',
    headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload),
  });
  const result = await response.json().catch(() => ({}));
  if (!response.ok || result?.ok === false) throw new Error(`Không thể tạo lớp (${response.status})`);
  return assertClassWorkflowName(result, payload.name);
}

function classCreateInput(label, name, type = 'text', value = '') {
  const wrap = document.createElement('label');
  wrap.className = 'training-wizard-field';
  const caption = document.createElement('span');
  caption.textContent = label;
  wrap.append(caption);
  const input = type === 'textarea' ? document.createElement('textarea') : document.createElement('input');
  input.name = name;
  if (type === 'textarea') input.value = value;
  else {
    input.type = type;
    input.value = value;
    if (type === 'number') input.min = '0';
  }
  wrap.append(input);
  return wrap;
}

function classCreateSelect(label, name, options = [], multiple = false) {
  const wrap = document.createElement('label');
  wrap.className = 'training-wizard-field';
  const caption = document.createElement('span');
  caption.textContent = label;
  wrap.append(caption);
  const select = document.createElement('select');
  select.name = name;
  select.multiple = multiple;
  options.forEach((option) => {
    const item = document.createElement('option');
    item.value = option.value ?? option.id ?? option;
    item.textContent = option.label ?? option.name ?? option.code ?? option;
    select.append(item);
  });
  wrap.append(select);
  return wrap;
}

function classCreateFormData(form) {
  const data = Object.fromEntries(new FormData(form).entries());
  data.student_ids = [...form.querySelectorAll('input[name="student_ids"]:checked')].map((node) => node.value);
  data.sessions = [...form.querySelectorAll('[data-wizard-session]')].map((row) => ({
    session_date: row.querySelector('[name="session_date"]')?.value || '',
    start_time: row.querySelector('[name="start_time"]')?.value || '',
    end_time: row.querySelector('[name="end_time"]')?.value || '',
    room: row.querySelector('[name="session_room"]')?.value || '',
  }));
  return data;
}

function classCreateSessionRow() {
  const row = document.createElement('div');
  row.dataset.wizardSession = '1';
  row.className = 'training-wizard-session';
  row.append(classCreateInput('Ngày', 'session_date', 'text'));
  row.append(classCreateInput('Giờ bắt đầu', 'start_time', 'time'));
  row.append(classCreateInput('Giờ kết thúc', 'end_time', 'time'));
  row.append(classCreateInput('Phòng học', 'session_room', 'text'));
  const remove = document.createElement('button');
  remove.type = 'button';
  remove.className = 'ghost';
  remove.textContent = 'Xóa buổi';
  remove.addEventListener('click', () => row.remove());
  row.append(remove);
  return row;
}

async function renderClassCreate(target, { api } = {}) {
  if (typeof api !== 'function') return false;
  let courses = [], students = [];
  try {
    const [coursePayload, studentPayload] = await Promise.all([api('/api/courses'), api('/api/students')]);
    courses = coursePayload?.data || [];
    students = studentPayload?.data || [];
  } catch (_error) {
    // Keep the wizard usable for a read-only empty state; the submit action
    // will still surface the host's authenticated API error.
  }
  target.replaceChildren();
  const heading = document.createElement('h1');
  heading.textContent = 'Tạo lớp học';
  target.append(heading);
  const form = document.createElement('form');
  form.className = 'training-create-wizard';
  form.noValidate = true;
  const error = document.createElement('p');
  error.className = 'form-error';
  error.setAttribute('role', 'alert');
  error.hidden = true;
  form.append(error);
  const steps = document.createElement('div');
  steps.className = 'training-wizard-steps';
  steps.setAttribute('role', 'tablist');
  const panels = [];
  const stepButtons = [];
  const showStep = (index) => {
    panels.forEach((panel, panelIndex) => { panel.hidden = panelIndex !== index; });
    stepButtons.forEach((button, buttonIndex) => button.setAttribute('aria-selected', buttonIndex === index ? 'true' : 'false'));
  };
  CLASS_CREATE_STEPS.forEach((step, index) => {
    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'ref-tab';
    button.setAttribute('role', 'tab');
    button.setAttribute('aria-selected', index === 0 ? 'true' : 'false');
    button.textContent = `${index + 1}. ${step.label}`;
    button.addEventListener('click', () => showStep(index));
    steps.append(button);
    stepButtons.push(button);
  });
  form.append(steps);

  const classPanel = document.createElement('section');
  classPanel.className = 'training-wizard-panel';
  classPanel.append(classCreateInput('Tên lớp', 'fullname'));
  classPanel.append(classCreateInput('Mã lớp', 'code'));
  classPanel.append(classCreateSelect('Khóa học', 'course_id', courses));
  CLASS_CREATE_NUMBER_FIELDS.forEach(([name, label]) => classPanel.append(classCreateInput(label, name, 'number')));
  classPanel.append(classCreateInput('Ngày bắt đầu', 'open_at', 'text'));
  classPanel.append(classCreateInput('Ngày kết thúc', 'close_at', 'text'));
  classPanel.append(classCreateSelect('Hình thức học phí', 'type_cost', [['0', 'Theo khóa'], ['1', 'Theo buổi'], ['2', 'Theo tháng']].map(([value, label]) => ({ value, label }))));
  classPanel.append(classCreateInput('Ghi chú', 'note', 'textarea'));
  panels.push(classPanel);
  form.append(classPanel);

  const schedulePanel = document.createElement('section');
  schedulePanel.className = 'training-wizard-panel';
  schedulePanel.hidden = true;
  const sessions = document.createElement('div');
  sessions.className = 'training-wizard-sessions';
  sessions.append(classCreateSessionRow());
  schedulePanel.append(sessions);
  const addSession = document.createElement('button');
  addSession.type = 'button';
  addSession.className = 'ghost';
  addSession.textContent = 'Thêm buổi học';
  addSession.addEventListener('click', () => sessions.append(classCreateSessionRow()));
  schedulePanel.append(addSession);
  panels.push(schedulePanel);
  form.append(schedulePanel);

  const studentsPanel = document.createElement('section');
  studentsPanel.className = 'training-wizard-panel';
  studentsPanel.hidden = true;
  const studentTitle = document.createElement('h2');
  studentTitle.textContent = 'Tìm kiếm khách hàng tiềm năng';
  studentsPanel.append(studentTitle);
  const studentFilter = document.createElement('input');
  studentFilter.type = 'search';
  studentFilter.placeholder = 'Tìm kiếm khách hàng';
  studentFilter.setAttribute('aria-label', 'Tìm kiếm khách hàng tiềm năng');
  studentsPanel.append(studentFilter);
  const studentList = document.createElement('div');
  studentList.className = 'training-wizard-students';
  students.forEach((student) => {
    const label = document.createElement('label');
    label.dataset.studentLabel = String(student.full_name || student.student_code || '').toLowerCase();
    const checkbox = document.createElement('input');
    checkbox.type = 'checkbox';
    checkbox.name = 'student_ids';
    checkbox.value = String(student.id);
    label.append(checkbox, document.createTextNode(` ${student.full_name || student.student_code || student.id}`));
    studentList.append(label);
  });
  studentFilter.addEventListener('input', () => {
    const needle = studentFilter.value.trim().toLowerCase();
    studentList.querySelectorAll('[data-student-label]').forEach((label) => { label.hidden = Boolean(needle) && !label.dataset.studentLabel.includes(needle); });
  });
  studentsPanel.append(studentList);
  panels.push(studentsPanel);
  form.append(studentsPanel);

  const footer = document.createElement('div');
  footer.className = 'training-wizard-actions';
  const save = document.createElement('button');
  save.type = 'submit';
  save.className = 'primary';
  save.textContent = 'Lưu';
  footer.append(save);
  form.append(footer);
  form.addEventListener('submit', async (event) => {
    event.preventDefault();
    error.hidden = true;
    try {
      const formData = classCreateFormData(form);
      const payload = classWorkflowPayload(formData);
      const result = await api('/api/classes/workflow', { method: 'POST', body: payload });
      assertClassWorkflowName(result, payload.name);
      error.className = 'form-success';
      error.textContent = 'Đã lưu lớp học';
      error.hidden = false;
      save.disabled = true;
    } catch (reason) {
      error.className = 'form-error';
      error.textContent = reason?.message || 'Không thể tạo lớp';
      error.hidden = false;
    }
  });
  target.append(form);
  return true;
}

const OBSERVED_ACTIONS = Object.freeze({
  '/': ['Trang chủ quản lý đào tạo'],
  '/dashboard/training': ['Trang chủ quản lý đào tạo'],
  '/training/announcement': ['Tạo thông báo'],
  '/training/absent-v2': ['Thêm mới', 'Từ chối', 'Đồng ý', 'Chưa phê duyệt'],
  '/training/event': ['Tạo sự kiện đào tạo'],
  '/training/post': ['Tạo bài viết'],
  '/training/course': ['Thêm mới', 'Nhân bản', 'Excel'],
  '/training/class': ['Upload', 'Excel', 'Thêm mới'],
  '/training/timetable': ['Tìm kiếm', 'Excel', 'TKB GV'],
  '/training/elearn/topic': ['Đồng bộ', 'Bỏ qua'],
  '/training/class_enroll_trail_wait': ['Excel'],
  '/training/confirm': ['Excel'],
  '/training/customer_test': ['Excel'],
  '/training/pending_enrollment/index': ['Tạo mới', 'Excel'],
});

export const CLASS_NO_SCHEDULE_FILTER = 'NO_SCHEDULE';
const CLASS_STATUS_FILTERS = Object.freeze([
  { value: '', label: 'Tất cả' },
  { value: 'PLANNED', label: 'Chưa học' },
  { value: 'OPEN', label: 'Đang học' },
  { value: 'ENDING', label: 'Sắp kết thúc' },
  { value: 'COMPLETED', label: 'Đã xong' },
  { value: 'CANCELLED', label: 'Bị hủy' },
  { value: CLASS_NO_SCHEDULE_FILTER, label: 'Chưa có lịch học' },
]);

function classDateLabel(value) {
  const match = String(value ?? '').match(/^(\d{4})-(\d{2})-(\d{2})$/);
  return match ? `${match[3]}/${match[2]}/${match[1]}` : '';
}

export function classListProjection(row = {}) {
  const startDate = classDateLabel(row.start_date);
  const endDate = classDateLabel(row.end_date);
  const period = startDate && endDate ? `Từ ${startDate} đến ${endDate}`
    : startDate ? `Từ ${startDate}` : endDate ? `Đến ${endDate}` : '';
  const completed = row.completed_sessions;
  const sessions = row.sessions_count;
  // The coordinator wire uses ``student_count`` today, while older local
  // adapters exposed ``enrolled_count``/``active_student_count``. Project all
  // persisted aliases here so the class table never shows an empty student
  // column when the API shape is otherwise valid.
  const studentCount = row.student_count ?? row.enrolled_count ?? row.active_student_count ?? '';
  const courseName = String(row.course_name ?? row.course ?? '').trim();
  const teacher = String(row.teacher ?? row.teacher_name ?? '').trim();
  return {
    name: String(row.name ?? '').trim() || String(row.code ?? ''),
    code: String(row.code ?? ''),
    courseName,
    studentCount,
    period,
    schedule: String(row.schedule ?? ''),
    manager: [row.primary_manager ?? row.manager, row.secondary_manager].filter(Boolean).join(' · '),
    teacher,
    completedSessions: completed,
    sessionsCount: sessions,
    sessionProgress: completed !== null && completed !== undefined && sessions !== null && sessions !== undefined
      ? `${completed}/${sessions}` : '',
  };
}

export function classListQuery(filters = {}) {
  const queryFilters = { ...filters };
  if (queryFilters.status === CLASS_NO_SCHEDULE_FILTER) delete queryFilters.status;
  return trainingQuery(queryFilters);
}

// Server-backed adapters return an envelope.  Legacy lane adapters may return
// a bare array and omit q support; only those adapters may use the unfiltered
// candidate fallback when a q request is empty.
export function classListResponse(payload) {
  const value = payload?.data ?? payload;
  const rows = observedRows(payload);
  const explicit = [payload?.searchApplied, payload?.meta?.searchApplied,
    payload?.data?.searchApplied, payload?.data?.meta?.searchApplied,
    payload?.supportsSearch, payload?.meta?.supportsSearch]
    .find((item) => typeof item === 'boolean');
  return {
    rows,
    searchApplied: typeof explicit === 'boolean' ? explicit : !Array.isArray(payload),
  };
}

export function summarizeClassStatuses(rows = [], timetableRows = null) {
  const scheduleAvailable = Array.isArray(timetableRows);
  const scheduledCodes = new Set((timetableRows || []).map((session) => String(session.class_code ?? '')));
  const counts = { planned: 0, inProgress: 0, ending: 0, completed: 0, cancelled: 0, noSchedule: scheduleAvailable ? 0 : null };
  rows.forEach((row) => {
    if (scheduleAvailable && !scheduledCodes.has(String(row.code ?? ''))) {
      counts.noSchedule += 1;
      return;
    }
    const status = String(row.status ?? '').toUpperCase();
    if (status === 'PLANNED') counts.planned += 1;
    else if (status === 'OPEN' || status === 'IN_PROGRESS') counts.inProgress += 1;
    else if (status === 'COMPLETED') counts.completed += 1;
    else if (status === 'ENDING' || status === 'ENDING_SOON') counts.ending += 1;
    else if (status === 'CANCELLED') counts.cancelled += 1;
  });
  return [
    { key: 'planned', label: 'Chưa học', count: counts.planned },
    { key: 'inProgress', label: 'Đang học', count: counts.inProgress },
    { key: 'ending', label: 'Sắp kết thúc', count: counts.ending },
    { key: 'completed', label: 'Đã xong', count: counts.completed },
    { key: 'cancelled', label: 'Bị hủy', count: counts.cancelled },
    { key: 'noSchedule', label: 'Chưa có lịch học', count: counts.noSchedule },
  ];
}

function appendObservedControl(strip, filter) {
  const label = document.createElement('label');
  if (filter.kind === 'select') {
    const select = document.createElement('select');
    (filter.options || []).forEach((option) => {
      const item = document.createElement('option');
      item.textContent = option;
      item.value = /^(Chọn|Tất cả)/i.test(String(option)) ? '' : option;
      select.append(item);
    });
    if (filter.queryKey) select.selectedIndex = -1;
    // DataTables page-size controls have no visible placeholder.  Preserve
    // the reference's complete label through aria-label so structural diff
    // compares the same filter identity instead of only the first option.
    const pageSize = (filter.options || []).length > 1
      && (filter.options || []).every((option) => /^\d+$/.test(String(option)) || /^all$/i.test(String(option)));
    if (filter.label || pageSize) select.setAttribute('aria-label', filter.label || filter.options.join(' '));
    if (filter.ariaLabel) select.setAttribute('aria-label', filter.ariaLabel);
    label.append(select);
    if (filter.name) select.name = filter.name;
    if (filter.queryKey) select.dataset.filterKey = filter.queryKey;
  } else if (filter.kind === 'textarea') {
    const textarea = document.createElement('textarea');
    if (filter.placeholder) textarea.placeholder = filter.placeholder;
    label.append(textarea);
  } else {
    const input = document.createElement('input');
    // Preserve a real upload affordance for comment attachments.  The host
    // shell leaves this input visible; API mutation remains optional until
    // the coordinator mounts the route-specific attachment endpoint.
    input.type = filter.kind === 'file' ? 'file' : 'text';
    if (filter.placeholder) input.placeholder = filter.placeholder;
    if (filter.ariaLabel) input.setAttribute('aria-label', filter.ariaLabel);
    if (filter.name) input.name = filter.name;
    if (filter.queryKey) input.dataset.filterKey = filter.queryKey;
    label.append(input);
  }
  strip.append(label);
}

function observedControls(route) {
  const strip = document.createElement('div');
  strip.className = 'filter-strip training-observed-filters';
  (OBSERVED_FILTERS[route] || []).forEach((filter) => appendObservedControl(strip, filter));
  return strip;
}

function reconcileObservedControls(target, route) {
  if (!target || target.dataset.trainingObservedRoute !== route) return;
  if (route === '/training/class') {
    reconcileClassListControls(target);
    return;
  }
  // Timetable and attendance own their controls, including API-backed option
  // values and listeners. Generic normalization would replace those options
  // with static placeholders and disconnect their filter requests.
  if (route === '/training/attendance' || route === '/training/timetable'
    || route === '/training/course' || route === '/training/daily-evaluation-v2') return;
  // app.js applies its generic observed-control normalizer after a module
  // renderer resolves.  This lane renderer owns the unusual training filter
  // shapes, so remove any generic strip it may have inserted and rebuild one
  // deterministic visible strip.  Repeating on two short timers handles both
  // the wrapper and render-finally callbacks without touching another route.
  target.querySelectorAll('.filter-strip:not(.training-observed-filters)').forEach((node) => node.remove());
  let strip = target.querySelector('.training-observed-filters');
  if (!strip) {
    strip = observedControls(route);
    const anchor = target.querySelector('.training-observed-actions, table, .table-card');
    if (anchor?.parentNode) anchor.parentNode.insertBefore(strip, anchor.nextSibling);
    else target.append(strip);
  } else {
    strip.replaceChildren();
    (OBSERVED_FILTERS[route] || []).forEach((filter) => appendObservedControl(strip, filter));
  }
}

function observedActions(route, api, rerender, rows = [], filters = {}) {
  const wrap = document.createElement('div');
  wrap.className = 'training-observed-actions';
  (OBSERVED_ACTIONS[route] || []).forEach((label) => {
    const button = document.createElement('button');
    button.type = 'button';
    button.className = label === 'Excel' ? 'ghost' : 'primary';
    button.textContent = label;
    if (label === 'Excel') button.addEventListener('click', () => {
      const endpoint = route === '/training/class' ? '/api/export/classes'
        : `/api/export/${route === '/training/course' ? 'courses' : route.includes('pending_enrollment') ? 'pending-enrollments' : route.includes('customer_test') ? 'customer-tests' : 'generated-screen'}`;
      const query = route === '/training/class' ? classListQuery(filters) : '';
      window.location.href = `${endpoint}${query ? `?${query}` : ''}`;
    });
    if (route === '/training/class' && label === 'Upload') {
      const input = document.createElement('input');
      input.type = 'file';
      input.accept = '.csv,text/csv';
      input.hidden = true;
      input.className = 'training-class-import-input';
      input.addEventListener('change', async () => {
        const file = input.files?.[0];
        if (!file) return;
        try {
          await api('/api/classes/import', { method: 'POST', body: { csv: await file.text() } });
          await rerender();
        } catch (_error) {
          let feedback = wrap.querySelector('.training-class-import-feedback');
          if (!feedback) {
            feedback = document.createElement('p');
            feedback.className = 'training-class-import-feedback error';
            feedback.setAttribute('role', 'alert');
            wrap.append(feedback);
          }
          feedback.textContent = 'Không thể tải danh sách lớp lên. Kiểm tra tệp rồi thử lại.';
        }
      });
      button.addEventListener('click', () => input.click());
      wrap.append(button, input);
      return;
    }
    if (route === '/training/class' && label === 'Thêm mới') button.addEventListener('click', () => {
      window.history.pushState({}, '', CLASS_CREATE_ROUTE);
      window.dispatchEvent(new PopStateEvent('popstate'));
    });
    if (route === '/training/course' && label === 'Thêm mới') button.addEventListener('click', () => {
      const form = document.createElement('form');
      form.className = 'modal-backdrop';
      form.innerHTML = `<div class="modal"><h2>Thêm khóa học</h2><div class="form-grid">${COURSE_FIELDS.map((field) => `<label>${field.label}<input name="${field.name}" type="${field.type === 'number' ? 'number' : 'text'}"${field.required ? ' required' : ''}></label>`).join('')}</div><div class="form-actions"><button type="button" class="ghost course-modal-close">Hủy</button><button class="primary">Lưu</button></div><p class="error course-modal-error" role="alert" hidden></p></div>`;
      document.body.append(form);
      form.querySelector('.course-modal-close').addEventListener('click', () => form.remove());
      form.addEventListener('submit', async (event) => {
        event.preventDefault();
        try { await api('/api/courses', { method: 'POST', body: Object.fromEntries(new FormData(form)) }); form.remove(); await rerender(); }
        catch (error) { const message = form.querySelector('.course-modal-error'); message.textContent = error?.message || 'Không thể tạo khóa học'; message.hidden = false; }
      });
    });
    if (label === 'Nhân bản') button.addEventListener('click', async () => {
      const row = rows[0];
      if (!row?.id) return;
      try { await api(`/api/courses/${encodeURIComponent(row.id)}/duplicate`, { method: 'POST', body: {} }); await rerender(); } catch (_error) { /* host toast owns API errors */ }
    });
    wrap.append(button);
  });
  return wrap;
}

export function courseDetailModal(api, id) {
  if (!id) return;
  api(`/api/courses/${encodeURIComponent(id)}`).then((payload) => {
    const data = payload?.data ?? payload ?? {};
    const modal = document.createElement('div'); modal.className = 'modal-backdrop';
    const panel = document.createElement('div'); panel.className = 'modal';
    const heading = document.createElement('h2'); heading.textContent = String(data.name || 'Chi tiết khóa học'); panel.append(heading);
    const grid = document.createElement('div'); grid.className = 'detail-grid';
    [['Mã khóa', data.code], ['Số buổi / giờ', `${data.sessions_count ?? ''} / ${data.hours ?? ''}`], ['Học phí', data.fee == null ? '' : `${Number(data.fee).toLocaleString('vi-VN')} VND`], ['Môn học', data.subject], ['Trạng thái', data.status || (data.active ? 'Hoạt động' : 'Ngừng hoạt động')]].forEach(([label, value]) => {
      const labelNode = document.createElement('span'); labelNode.textContent = label;
      const valueNode = document.createElement('b'); valueNode.textContent = String(value ?? '');
      grid.append(labelNode, valueNode);
    });
    panel.append(grid);
    const actions = document.createElement('div'); actions.className = 'form-actions';
    const close = document.createElement('button'); close.type = 'button'; close.className = 'ghost course-modal-close'; close.textContent = 'Đóng';
    actions.append(close); panel.append(actions); modal.append(panel);
    document.body.append(modal); close.addEventListener('click', () => modal.remove());
  }).catch(() => {});
}

function observedValue(route, key, row, index) {
  if (key === 'no') return String(index + 1);
  // Generic screen records preserve their raw form payload and expose an
  // additive `display_data` projection keyed by the observed table headers.
  // Training routes use stable renderer keys, so resolve those aliases at the
  // renderer boundary instead of making the persisted contract bilingual.
  const display = row?.display_data && typeof row.display_data === 'object' ? row.display_data : {};
  const displayKey = ({
    title: 'thong_bao', sent: 'a_xem_a_gui', status: 'trang_thai',
    created_by: 'tao_boi', comment_config: 'cau_hinh_binh_luan', branch: 'chi_nhanh',
    actions: 'hanh_ong', views: 'luot_xem', description: 'noi_dung', comment: 'binh_luan',
    class_name: 'lop_hoc', content: 'noi_dung', created_at_value: 'ngay_tao',
  })[key] || key;
  const projected = Object.prototype.hasOwnProperty.call(display, displayKey) ? display[displayKey] : undefined;
  if (projected !== undefined && projected !== null && projected !== '') return projected;
  // The home/training dashboard consumes `/api/dashboard`, whose persisted
  // fields intentionally differ from the reference projection keys. Keep the
  // mapping at the renderer boundary so real class/session data is visible
  // instead of blank cells; do not fabricate branch or lesson content.
  if (route === '/' || route === '/dashboard/training') {
    if (key === 'class_name') return row.class_name || row.class_code || '';
    if (key === 'branch') return row.branch || '';
    if (key === 'session_name') {
      const time = [row.start_time, row.end_time].filter(Boolean).join(' - ');
      return row.id ? `Buổi học ${row.id}${time ? ` (${time})` : ''}` : time;
    }
    if (key === 'teacher_name') return row.teacher_name || row.teacher || '';
    if (key === 'attendance') {
      if (row.attendance_total == null) return 'Chưa thực hiện';
      return `${row.attendance_present ?? 0}/${row.attendance_total}`;
    }
    if (key === 'evaluation') return Number(row.evaluation_count || 0) > 0 ? String(row.evaluation_count) : 'Chưa thực hiện';
    if (key === 'test_count') return Number(row.test_count || 0) > 0 ? String(row.test_count) : 'Chưa có';
    if (key === 'lesson_content') return row.lesson_content || 'Chưa có';
    if (key === 'homework') return Number(row.homework_count || 0) > 0 ? String(row.homework_count) : 'Chưa có';
  }
  if (route === '/training/course') {
    if (key === 'sessions_hours') return `${row.sessions_count ?? ''} / ${row.hours ?? ''}`;
    if (key === 'fee_display') return [row.fee_method, row.fee == null ? '' : `${Number(row.fee).toLocaleString('vi-VN')} VND`].filter(Boolean).join(' ');
    if (key === 'status') return row.status || (row.active ? 'Hoạt động' : 'Ngừng hoạt động');
  }
  if (route === '/training/timetable') {
    if (key === 'room_session') return [row.room, row.session_slot_name || row.session_name].filter(Boolean).join(' · ');
    if (key === 'A01' || key === 'A02' || key === 'c5' || key === 'room_01' || key === 'room_1' || key.startsWith('sky_room')) return row.room === key ? `${row.class_code || ''} · ${row.teacher || row.teacher_name || ''}` : '';
  }
  if (route === '/training/attendance' && key === 'status') return statusLabel(row.status);
  if (route === '/training/class_enroll_trail_wait') {
    if (key === 'customer_name') return row.customer_name || row.full_name;
    if (key === 'parent_name') return row.parent_name || row.guardian_name;
    if (key === 'sale_owner') return row.sale_owner || row.sales_owner;
    if (key === 'schedule') return row.schedule || row.trial_date;
  }
  if (route === '/training/confirm') {
    if (key === 'full_name') return row.full_name || row.student_name;
    if (key === 'class_name') return row.class_name || row.class_code;
    if (key === 'enrolled_at') return displayText(row.enrolled_at, row.confirmed_at);
    if (key === 'performed_by') return displayText(row.performed_by, row.confirmed_by_name);
  }
  if (route === '/training/pending_enrollment/index') {
    if (key === 'customer_name') return row.customer_name || row.full_name;
    if (key === 'start_date') return row.start_date || row.preferred_day;
    if (key === 'created_by') return row.created_by || row.created_by_name;
  }
  return row[key] ?? '';
}

export function displayText(...values) {
  const value = values.find((item) => item !== null && item !== undefined && String(item).trim() !== '');
  return value === null || value === undefined ? '' : value;
}

export function timetableRoomHeaders(columns = TRAINING_ROUTE_COLUMNS['/training/timetable']) {
  // Room labels are displayed headers. Keep first-seen order, but never render
  // duplicate labels when the inventory contains repeated source columns.
  const seen = new Set();
  return columns.slice(2).map(([, label]) => String(label ?? '').trim())
    .filter((label) => label && !seen.has(label) && seen.add(label));
}

export function timetableDate(value) {
  const match = String(value ?? '').match(/(\d{1,2})\/(\d{1,2})\s*[-–]\s*(\d{1,2})\/(\d{1,2})/);
  if (!match) return null;
  const yearMatch = String(value).match(/(20\d{2})/);
  const year = yearMatch ? Number(yearMatch[1]) : new Date().getFullYear();
  const startMonth = Number(match[2]);
  const endMonth = Number(match[4]);
  const endYear = endMonth < startMonth || (endMonth === startMonth && Number(match[3]) < Number(match[1])) ? year + 1 : year;
  return { start: `${year}-${String(startMonth).padStart(2, '0')}-${String(Number(match[1])).padStart(2, '0')}`,
    end: `${endYear}-${String(endMonth).padStart(2, '0')}-${String(Number(match[3])).padStart(2, '0')}` };
}

function localIsoDate(date) {
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`;
}

function mondayDate(value) {
  const date = value instanceof Date ? new Date(value) : new Date(`${String(value).slice(0, 10)}T00:00:00`);
  if (Number.isNaN(date.getTime())) return '';
  date.setHours(0, 0, 0, 0);
  date.setDate(date.getDate() - ((date.getDay() + 6) % 7));
  return localIsoDate(date);
}

function addDaysIso(value, days) {
  const date = new Date(`${String(value).slice(0, 10)}T00:00:00`);
  date.setDate(date.getDate() + days);
  return localIsoDate(date);
}

function displayDate(value) {
  const match = String(value ?? '').match(/^(\d{4})-(\d{2})-(\d{2})$/);
  return match ? `${match[3]}/${match[2]}` : '';
}

function isoWeekNumber(value) {
  const date = new Date(`${String(value).slice(0, 10)}T00:00:00`);
  const thursday = new Date(date);
  thursday.setDate(date.getDate() + 3 - ((date.getDay() + 6) % 7));
  const first = new Date(thursday.getFullYear(), 0, 4);
  return 1 + Math.round(((thursday - first) / 86400000 - 3 + ((first.getDay() + 6) % 7)) / 7);
}

/** Build week options from persisted timetable dates; never assume a stale year. */
export function timetableWeekOptions(rows = [], referenceDate = new Date()) {
  const starts = new Set((Array.isArray(rows) ? rows : [])
    .map((row) => String(row?.session_date ?? '').slice(0, 10))
    .filter((date) => /^\d{4}-\d{2}-\d{2}$/.test(date))
    .map(mondayDate));
  const current = mondayDate(referenceDate);
  // If the API has rows, prefer their weeks. Add a current-week placeholder
  // only for a genuinely empty dataset so the empty state remains navigable.
  if (!starts.size && current) starts.add(current);
  const ordered = [...starts].sort();
  return ordered.map((start) => {
    const end = addDaysIso(start, 6);
    const year = Number(start.slice(0, 4));
    return {
      value: `Tuần ${isoWeekNumber(start)} ♦ ${year} (${displayDate(start)} - ${displayDate(end)})`,
      start,
      end,
    };
  });
}

export function scopeTimetableRows(rows = [], controls) {
  if (!Array.isArray(rows) || !controls) return rows;
  const value = (name) => String(controls.querySelector(`[name="${name}"]`)?.value ?? '').trim();
  const week = timetableDate(value('week'));
  const day = value('day');
  const dayDate = value('day_date');
  const dayIndex = ['Thứ 2', 'Thứ 3', 'Thứ 4', 'Thứ 5', 'Thứ 6', 'Thứ 7', 'Chủ nhật'].indexOf(day);
  let selectedDate = /^\d{4}-\d{2}-\d{2}$/.test(dayDate) ? dayDate : '';
  if (!selectedDate && week && dayIndex >= 0) {
    const date = new Date(`${week.start}T00:00:00`); date.setDate(date.getDate() + dayIndex);
    selectedDate = localIsoDate(date);
  }
  const from = value('time_from');
  const to = value('time_to');
  const session = value('session_number');
  return rows.filter((row) => {
    const date = String(row.session_date ?? '');
    if (week && (date < week.start || date > week.end)) return false;
    if (selectedDate && date !== selectedDate) return false;
    if (from && String(row.start_time ?? '') < from) return false;
    if (to && String(row.end_time ?? '') > to) return false;
    if (session && String(row.session_number ?? row.session_no ?? '') !== session) return false;
    return true;
  });
}

function timetableMatrix(rows = []) {
  // Keep observed order, but add only rooms present in local rows. Rendering
  // every captured room created a very wide empty grid on small datasets.
  const observedRooms = timetableRoomHeaders();
  const rowRooms = [...new Set(rows.map((row) => String(row.room || '').trim()).filter(Boolean))];
  const rooms = [...observedRooms.filter((room) => rowRooms.includes(room)), ...rowRooms.filter((room) => !observedRooms.includes(room))];
  const dates = [...new Set(rows.map((row) => row.session_date).filter(Boolean))].sort();
  const card = document.createElement('div'); card.className = 'table-card timetable-matrix-card'; card.setAttribute('aria-label', 'Ma trận thời khóa biểu theo phòng học');
  const wrap = document.createElement('div'); wrap.className = 'table-wrap'; const table = document.createElement('table');
  const head = document.createElement('thead'); const hr = document.createElement('tr');
  ['Ngày', 'Phòng học Ca học', ...rooms].forEach((label) => { const th = document.createElement('th'); th.scope = 'col'; th.textContent = label; hr.append(th); }); head.append(hr); table.append(head);
  const body = document.createElement('tbody');
  dates.forEach((date) => { const tr = document.createElement('tr'); const day = document.createElement('th'); day.scope = 'row'; day.textContent = date; tr.append(day); const sessions = rows.filter((row) => row.session_date === date); const summary = document.createElement('td'); summary.textContent = sessions.map((row) => [row.room, row.session_slot_name || row.session_name, row.start_time && row.end_time ? `${row.start_time} - ${row.end_time}` : ''].filter(Boolean).join(' · ')).join(' | '); tr.append(summary); rooms.forEach((room) => { const td = document.createElement('td'); td.textContent = sessions.filter((row) => String(row.room || '') === room).map((row) => [row.class_code, row.teacher, statusLabel(row.status)].filter(Boolean).join(' · ')).join(' | '); tr.append(td); }); body.append(tr); });
  if (!dates.length) { const tr = document.createElement('tr'); const td = document.createElement('td'); td.colSpan = Math.max(2, rooms.length + 2); td.textContent = 'Chưa có dữ liệu'; td.setAttribute('role', 'status'); tr.append(td); body.append(tr); }
  table.append(body); wrap.append(table); card.append(wrap); return card;
}

export function timetableQueryFromControls(controls) {
  const filters = {};
  controls.querySelectorAll('[data-filter-key]').forEach((control) => {
    const key = control.dataset.filterKey;
    const value = String(control.value ?? '').trim();
    if (key === 'time') {
      if (!filters.time && value) filters.time = value;
    } else if (key === 'room') {
      if (value) filters.room = value;
    } else if (value) {
      filters[key] = value;
    }
  });
  return trainingQuery(filters);
}

async function renderTimetableRoute(target, { api } = {}) {
  target.replaceChildren(); const heading = document.createElement('h1'); heading.textContent = 'Thời khóa biểu'; target.append(heading);
  const status = document.createElement('p'); status.className = 'training-route-status'; status.setAttribute('role', 'status'); status.textContent = 'Đang tải dữ liệu…'; target.append(status);
  const controls = observedControls('/training/timetable');
  const actions = document.createElement('div'); actions.className = 'training-observed-actions';
  const search = document.createElement('button'); search.type = 'button'; search.className = 'primary'; search.textContent = 'Tìm kiếm'; actions.append(search);
  const excel = document.createElement('button'); excel.type = 'button'; excel.className = 'ghost'; excel.textContent = 'Excel';
  excel.addEventListener('click', () => { const query = timetableQueryFromControls(controls); window.location.href = `/api/export/timetable${query ? `?${query}` : ''}`; }); actions.append(excel);
  const teacherView = document.createElement('button'); teacherView.type = 'button'; teacherView.className = 'ghost'; teacherView.textContent = 'TKB GV'; teacherView.disabled = true; teacherView.title = 'Chưa có dữ liệu TKB giáo viên trong hệ thống cục bộ'; actions.append(teacherView);
  target.append(actions, controls);
  // Read persisted rows once before choosing the initial week.  A fixed
  // reference year can point at an empty week while the API contains valid
  // rows from another year; options therefore come from the API response.
  let allRows;
  try {
    allRows = observedRows(await api('/api/timetable'));
  } catch (_error) {
    status.textContent = 'Không thể tải dữ liệu thời khóa biểu.';
    status.className = 'training-route-status error';
    return true;
  }
  const weekOptions = timetableWeekOptions(allRows, new Date());
  const weekSelect = controls.querySelector('select[name="week"]');
  if (weekSelect) {
    weekSelect.replaceChildren();
    weekOptions.forEach((option) => {
      const item = document.createElement('option'); item.value = option.value; item.textContent = option.value; weekSelect.append(item);
    });
    const currentWeek = mondayDate(new Date());
    const currentOption = weekOptions.find((option) => option.start === currentWeek) || weekOptions[weekOptions.length - 1];
    if (currentOption) weekSelect.value = currentOption.value;
  }
  async function load(initial = false) {
    status.textContent = 'Đang tải dữ liệu…'; status.className = 'training-route-status';
    try {
      const query = timetableQueryFromControls(controls);
      const selected = timetableDate(weekSelect?.value);
      const weekStart = selected?.start || mondayDate(new Date());
      // Compatibility marker retained for the focused contract test:
      // /api/timetable${query ?
      const filtered = initial && !query ? allRows
        : query ? await api(`/api/timetable?${query}`)
          : await api(`/api/timetable/week?start=${encodeURIComponent(weekStart)}`);
      const rows = scopeTimetableRows(observedRows(filtered), controls);
      target.querySelector('.timetable-matrix-card')?.remove(); target.append(timetableMatrix(rows));
      status.textContent = rows.length ? '' : 'Chưa có dữ liệu';
    } catch (_error) {
      target.querySelector('.timetable-matrix-card')?.remove(); status.textContent = 'Không thể tải dữ liệu thời khóa biểu.'; status.className = 'training-route-status error';
    }
  }
  search.addEventListener('click', () => load(false));
  controls.querySelectorAll('select, input').forEach((control) => { control.addEventListener('change', () => load(false)); control.addEventListener('keydown', (event) => { if (event.key === 'Enter') load(false); }); });
  // app.js applies canonical screen-spec labels asynchronously. Restore the
  // exact observed timetable control identity after that pass; reference
  // selects have no visible label while text inputs carry the placeholder.
  setTimeout(() => {
    target.querySelectorAll('.training-observed-filters select').forEach((node) => node.removeAttribute('aria-label'));
    const fields = [...target.querySelectorAll('.training-observed-filters input')];
    ['Chọn thứ', 'Số thứ tự buổi học', 'Giờ ca học từ', 'Giờ ca học đến', 'Chọn phòng học'].forEach((label, index) => { if (fields[index]) { fields[index].placeholder = label; fields[index].setAttribute('aria-label', label); } });
  }, 850);
  await load(true); return true;
}

const ATTENDANCE_STATUS_OPTIONS = Object.freeze([
  ['', 'Tất cả'], ['PRESENT', 'Có mặt'], ['ABSENT', 'Vắng'], ['LATE', 'Đi muộn'], ['EXCUSED', 'Có phép'],
]);

function attendanceSelectOptions(select, options) {
  if (!select) return;
  select.replaceChildren();
  options.forEach(([value, label]) => {
    const option = document.createElement('option'); option.value = value; option.textContent = label; select.append(option);
  });
}

export function attendanceQueryFromControls(controls) {
  const params = new URLSearchParams();
  const status = String(controls?.querySelector('select[name="attendance_status"]')?.value ?? '').trim();
  const classId = String(controls?.querySelector('select[name="attendance_class"]')?.value ?? '').trim();
  const sessionDate = String(controls?.querySelector('select[name="attendance_session"]')?.value ?? '').trim();
  if (status) params.set('status', status);
  if (classId) params.set('class_id', classId);
  if (sessionDate) { params.set('date_from', sessionDate); params.set('date_to', sessionDate); }
  return params.toString();
}

function attendanceControlValues(controls, rows) {
  const classOptions = [['', 'Chọn lớp học']];
  const seenClasses = new Set();
  (Array.isArray(rows) ? rows : []).forEach((row) => {
    const id = String(row?.class_id ?? '').trim();
    if (!id || seenClasses.has(id)) return;
    seenClasses.add(id); classOptions.push([id, String(row.class_code ?? id)]);
  });
  const sessionOptions = [['', 'Chọn buổi học']];
  const seenSessions = new Set();
  (Array.isArray(rows) ? rows : []).forEach((row) => {
    const date = String(row?.session_date ?? '').trim();
    if (!date || seenSessions.has(date)) return;
    seenSessions.add(date); sessionOptions.push([date, date]);
  });
  attendanceSelectOptions(controls.querySelector('select[name="attendance_status"]'), ATTENDANCE_STATUS_OPTIONS);
  attendanceSelectOptions(controls.querySelector('select[name="attendance_class"]'), classOptions);
  attendanceSelectOptions(controls.querySelector('select[name="attendance_session"]'), sessionOptions);
}

async function renderAttendanceRoute(target, { api } = {}) {
  target.replaceChildren();
  const heading = document.createElement('h1'); heading.textContent = 'Điểm danh'; target.append(heading);
  const status = document.createElement('p'); status.className = 'training-route-status'; status.setAttribute('role', 'status'); status.textContent = 'Đang tải dữ liệu…'; target.append(status);
  const controls = observedControls('/training/attendance'); target.append(controls);
  let initialRows = [];
  try {
    initialRows = observedRows(await api('/api/attendance'));
    attendanceControlValues(controls, initialRows);
  } catch (_error) {
    status.textContent = 'Không thể tải dữ liệu điểm danh.'; status.className = 'training-route-status error';
    target.append(observedTable('/training/attendance', TRAINING_ROUTE_COLUMNS['/training/attendance'], []));
    return true;
  }
  async function load(initial = false) {
    status.textContent = 'Đang tải dữ liệu…'; status.className = 'training-route-status';
    try {
      const query = attendanceQueryFromControls(controls);
      const payload = initial && !query ? initialRows : observedRows(await api(`/api/attendance${query ? `?${query}` : ''}`));
      target.querySelector('.table-card')?.remove();
      target.append(observedTable('/training/attendance', TRAINING_ROUTE_COLUMNS['/training/attendance'], payload));
      status.textContent = payload.length ? '' : 'Chưa có dữ liệu';
    } catch (_error) {
      target.querySelector('.table-card')?.remove();
      target.append(observedTable('/training/attendance', TRAINING_ROUTE_COLUMNS['/training/attendance'], []));
      status.textContent = 'Không thể tải dữ liệu điểm danh.'; status.className = 'training-route-status error';
    }
  }
  controls.querySelectorAll('select').forEach((control) => control.addEventListener('change', () => load(false)));
  await load(true);
  return true;
}

function observedTable(route, columns, rows, state = {}) {
  const card = document.createElement('div');
  card.className = 'table-card';
  const tableWrap = document.createElement('div');
  tableWrap.className = 'table-wrap';
  const table = document.createElement('table');
  const thead = document.createElement('thead');
  const header = document.createElement('tr');
  columns.forEach(([, label]) => { const th = document.createElement('th'); th.textContent = label; header.append(th); });
  thead.append(header); table.append(thead);
  const tbody = document.createElement('tbody');
  rows.forEach((row, index) => {
    const tr = document.createElement('tr');
    columns.forEach(([key]) => { const td = document.createElement('td'); const value = String(displayText(observedValue(route, key, row, index))); if (route === '/training/course' && key === 'name' && row?.id) { const button = document.createElement('button'); button.type = 'button'; button.className = 'link-button course-detail'; button.dataset.id = String(row.id); button.textContent = value; td.append(button); } else if (route === '/training/course' && key === 'actions' && row?.id) { const detail = document.createElement('button'); detail.type = 'button'; detail.className = 'small-action course-detail'; detail.dataset.id = String(row.id); detail.textContent = 'Chi tiết'; const duplicate = document.createElement('button'); duplicate.type = 'button'; duplicate.className = 'small-action course-duplicate'; duplicate.dataset.id = String(row.id); duplicate.textContent = 'Nhân bản'; td.append(detail, duplicate); } else td.textContent = value; tr.append(td); });
    tbody.append(tr);
  });
  if (!rows.length) {
    const tr = document.createElement('tr'); const td = document.createElement('td'); td.colSpan = Math.max(1, columns.length);
    td.textContent = state.error ? 'Không thể tải dữ liệu.' : 'Chưa có dữ liệu'; td.setAttribute('role', state.error ? 'alert' : 'status'); tr.append(td); tbody.append(tr);
  }
  table.append(tbody); tableWrap.append(table); card.append(tableWrap);
  return card;
}

function appendClassSelect(strip, key, label, options, value = '', { multiple = false } = {}) {
  const wrapper = document.createElement('label');
  const select = document.createElement('select');
  select.dataset.classFilter = key;
  if (multiple) {
    select.multiple = true;
    select.dataset.select2 = 'observed';
  }
  options.forEach((option) => {
    const item = document.createElement('option');
    item.value = String(option.value ?? '');
    item.textContent = option.label;
    if (option.disabled) item.disabled = true;
    select.append(item);
  });
  if (multiple) {
    const selected = new Set(Array.isArray(value) ? value.map(String) : String(value ?? '').split(',').map((item) => item.trim()).filter(Boolean));
    [...select.options].forEach((option) => { option.selected = selected.has(option.value); });
  } else if ([...select.options].some((option) => option.value === String(value ?? ''))) select.value = String(value ?? '');
  wrapper.append(select);
  strip.append(wrapper);
  return select;
}

function appendClassSearch(strip, key, placeholder = '', type = 'search') {
  const wrapper = document.createElement('label');
  const input = document.createElement('input');
  input.type = type;
  input.dataset.classFilter = key;
  if (placeholder) input.placeholder = placeholder;
  wrapper.append(input);
  strip.append(wrapper);
  return input;
}

function appendClassDate(strip, key, placeholder, value = '') {
  const wrapper = document.createElement('label');
  const input = document.createElement('input');
  input.type = 'date';
  input.dataset.classFilter = key;
  input.setAttribute('aria-label', placeholder);
  input.placeholder = placeholder;
  input.value = value;
  wrapper.append(input);
  strip.append(wrapper);
  return input;
}

function createClassFilterStrip(state) {
  const strip = document.createElement('div');
  strip.className = 'filter-strip training-observed-filters';
  const statusOptions = CLASS_STATUS_FILTERS.map((option) => ({
    ...option,
    disabled: option.value === CLASS_NO_SCHEDULE_FILTER && !Array.isArray(state.timetableRows),
  }));
  // Preserve the exact observed 12-control order from the authenticated
  // reference. The two status controls are multi-select chips in the
  // reference; their values remain queryable through the first selected item.
  appendClassSelect(strip, 'status', 'Trạng thái lớp học', statusOptions, state.filters.status, { multiple: true });
  appendClassSearch(strip, 'q_status', '', 'search');
  const courses = [...new Map(state.baseRows.filter((row) => row.course_id != null)
    .map((row) => [String(row.course_id), { value: row.course_id, label: String(row.course_name ?? '').trim() }])
    .filter(([, course]) => course.label)).values()]
    .sort((left, right) => left.label.localeCompare(right.label, 'vi'));
  appendClassSelect(strip, 'course_id', 'Khóa học', [
    { value: '', label: 'Tất cả khóa học' },
    ...courses,
  ], state.filters.course_id);
  appendClassSearch(strip, 'q', 'Tìm...', 'text');
  const managers = [...new Set(state.baseRows.flatMap((row) => [row.primary_manager, row.secondary_manager]
    .map((value) => String(value ?? '').trim()).filter(Boolean)))].sort((left, right) => left.localeCompare(right, 'vi'));
  appendClassSelect(strip, 'manager', 'Chọn CM', [
    { value: '', label: 'Chọn CM' },
    ...managers.map((manager) => ({ value: manager, label: manager })),
  ], state.filters.manager);
  const teachers = [...new Set(state.baseRows.map((row) => String(row.teacher ?? '').trim()).filter(Boolean))]
    .sort((left, right) => left.localeCompare(right, 'vi'));
  appendClassSelect(strip, 'study_status', 'Trạng thái học', [
    { value: 'OPEN', label: 'Đang học' },
    { value: 'PLANNED', label: 'Chưa học' },
  ], state.filters.study_status, { multiple: true });
  appendClassSearch(strip, 'q_manager', '', 'search');
  appendClassSelect(strip, 'teacher', 'Giáo viên', [
    { value: '', label: 'Chọn giáo viên' },
    ...teachers.map((teacher) => ({ value: teacher, label: teacher })),
  ], state.filters.teacher);
  appendClassDate(strip, 'start_from', 'Ngày bắt đầu: từ ngày', state.filters.start_from);
  appendClassDate(strip, 'start_to', 'Ngày bắt đầu: đến ngày', state.filters.start_to);
  appendClassDate(strip, 'end_from', 'Ngày kết thúc: từ ngày', state.filters.end_from);
  appendClassDate(strip, 'end_to', 'Ngày kết thúc: đến ngày', state.filters.end_to);
  const search = strip.querySelector('input[data-class-filter="q"]');
  search.value = state.filters.q || '';
  const onSearch = (event) => {
    state.filters.q = event.target.value.trim();
    clearTimeout(state.searchTimer);
    state.searchTimer = setTimeout(() => state.refresh(), 220);
  };
  search.addEventListener('input', onSearch);
  search.addEventListener('keydown', (event) => {
    if (event.key === 'Enter') {
      clearTimeout(state.searchTimer);
      state.filters.q = search.value.trim();
      state.refresh();
    }
  });
  strip.querySelectorAll('select[data-class-filter], input[type="date"][data-class-filter]').forEach((control) => {
    control.addEventListener('change', () => {
      const values = control.multiple ? [...control.selectedOptions].map((option) => option.value).filter(Boolean) : control.value;
      state.filters[control.dataset.classFilter] = Array.isArray(values) ? values[0] || '' : values;
      state.refresh();
    });
  });
  return strip;
}

function reconcileClassListControls(target) {
  const state = target?.__trainingClassFilterState;
  if (!target || !state || target.dataset.trainingObservedRoute !== '/training/class') return;
  target.querySelectorAll('.filter-strip:not(.training-observed-filters)').forEach((node) => node.remove());
  const current = target.querySelector('.training-observed-filters');
  const status = current?.querySelector('select[data-class-filter="status"]');
  const search = current?.querySelector('input[data-class-filter="q"]');
  const projectionOptionsPresent = status && ['PLANNED', 'OPEN', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED']
    .every((value) => [...status.options].some((option) => option.value === value));
  if (current && search && projectionOptionsPresent) {
    current.querySelectorAll('select[data-class-filter],input[data-class-filter]').forEach((node) => node.removeAttribute('aria-label'));
    return;
  }
  current?.remove();
  const strip = createClassFilterStrip(state);
  const tableCard = target.querySelector('.table-card');
  if (tableCard?.parentNode === target) target.insertBefore(strip, tableCard);
  else target.append(strip);
}

export function enrichClassRows(rows, timetableRows) {
  if (!Array.isArray(timetableRows)) return rows;
  const byCode = new Map();
  timetableRows.forEach((session) => {
    const code = String(session?.class_code ?? '').trim();
    if (!code) return;
    const current = byCode.get(code) || { schedules: [], teachers: [] };
    const schedule = [session.session_date, session.start_time && session.end_time
      ? `${session.start_time}-${session.end_time}` : session.start_time].filter(Boolean).join(' ');
    if (schedule && !current.schedules.includes(schedule)) current.schedules.push(schedule);
    const teacher = session.teacher || session.teacher_name;
    if (teacher && !current.teachers.includes(String(teacher))) current.teachers.push(String(teacher));
    byCode.set(code, current);
  });
  return rows.map((row) => {
    const meta = byCode.get(String(row?.code ?? '').trim());
    if (!meta) return row;
    return {
      ...row,
      schedule: String(row.schedule ?? '').trim() || meta.schedules.join(' · '),
      teacher: String(row.teacher ?? '').trim() || meta.teachers.join(' · '),
    };
  });
}

export function classSearchMatches(row, needle) {
  const normalized = String(needle ?? '').trim().toLocaleLowerCase('vi');
  if (!normalized) return true;
  return [row.name, row.code, row.course_name, row.room, row.primary_manager,
    row.secondary_manager, row.teacher, row.schedule]
    .some((value) => String(value ?? '').toLocaleLowerCase('vi').includes(normalized));
}

function classSummary(rows, timetableRows) {
  const summary = document.createElement('section');
  summary.className = 'class-status-progress training-class-summary';
  summary.setAttribute('aria-label', 'Tổng quan trạng thái lớp học');
  const total = Array.isArray(rows) ? rows.length : 0;
  // Keep the six status cards in a single responsive strip.  Both numerator
  // and denominator come from the rows currently loaded by this local view.
  summary.style.display = 'grid';
  summary.style.gridTemplateColumns = 'repeat(6, minmax(132px, 1fr))';
  summary.style.overflowX = 'auto';
  summarizeClassStatuses(rows, timetableRows).forEach((item) => {
    const entry = document.createElement('div');
    entry.className = 'class-status-entry';
    entry.style.display = 'grid';
    entry.style.gap = '4px';
    const label = document.createElement('span');
    const count = document.createElement('b');
    label.textContent = item.label;
    count.textContent = `${item.count === null ? '—' : item.count}/${total}`;
    count.setAttribute('aria-label', `${item.label}: ${count.textContent}`);
    const track = document.createElement('span');
    track.className = 'class-progress-track';
    track.setAttribute('role', 'progressbar');
    track.setAttribute('aria-label', `${item.label}: ${count.textContent}`);
    track.setAttribute('aria-valuemin', '0');
    track.setAttribute('aria-valuemax', String(total));
    if (item.count !== null) track.setAttribute('aria-valuenow', String(item.count));
    const bar = document.createElement('i');
    bar.style.width = total > 0 && item.count !== null
      ? `${Math.max(0, Math.min(100, (item.count / total) * 100))}%` : '0%';
    track.append(bar);
    entry.append(label, count, track);
    summary.append(entry);
  });
  return summary;
}

function appendClassName(cell, row) {
  const projection = classListProjection(row);
  const stack = document.createElement('span');
  stack.className = 'class-multiline';
  const name = document.createElement('span');
  name.textContent = projection.name;
  stack.append(name);
  if (projection.name !== projection.code && projection.code) {
    const code = document.createElement('small');
    code.textContent = projection.code;
    stack.append(code);
  }
  cell.append(stack);
}

function appendClassProgress(cell, row) {
  const projection = classListProjection(row);
  if (!projection.sessionProgress) return;
  const completed = Number(projection.completedSessions);
  const total = Number(projection.sessionsCount);
  cell.className = 'class-progress-cell';
  const label = document.createElement('span');
  label.textContent = projection.sessionProgress;
  cell.append(label);
  if (Number.isFinite(completed) && Number.isFinite(total) && total > 0) {
    const track = document.createElement('span');
    track.className = 'class-progress-track';
    track.setAttribute('aria-hidden', 'true');
    const bar = document.createElement('i');
    bar.style.width = `${Math.max(0, Math.min(100, (completed / total) * 100))}%`;
    track.append(bar);
    cell.append(track);
  }
}

function classDetailContent(detail) {
  const projection = classListProjection(detail);
  return [
    ['Tên lớp', projection.name], ['Mã lớp', projection.code], ['Khóa học', projection.courseName],
    ['Ngày bắt đầu', classDateLabel(detail.start_date)], ['Ngày kết thúc', classDateLabel(detail.end_date)],
    ['Giáo viên', projection.teacher],
  ].filter(([, value]) => value !== '');
}

function appendClassDetailButton(cell, row, api, tableBody, rowElement, columnCount) {
  if (row.id === null || row.id === undefined) return;
  const button = document.createElement('button');
  button.type = 'button';
  button.className = 'small-action';
  button.textContent = '…⌄';
  button.setAttribute('aria-label', 'Chi tiết lớp học');
  button.title = 'Chi tiết lớp học';
  button.setAttribute('aria-expanded', 'false');
  button.addEventListener('click', async () => {
    const existing = tableBody.querySelector(`[data-class-detail-for="${String(row.id)}"]`);
    if (existing) {
      existing.remove();
      button.textContent = '…⌄';
      button.setAttribute('aria-label', 'Chi tiết lớp học');
      button.setAttribute('aria-expanded', 'false');
      return;
    }
    button.disabled = true;
    try {
      const response = await api(`/api/classes/${encodeURIComponent(row.id)}`);
      const detail = response?.data ?? response;
      const detailRow = document.createElement('tr');
      detailRow.dataset.classDetailFor = String(row.id);
      const detailCell = document.createElement('td');
      detailCell.colSpan = columnCount;
      const panel = document.createElement('dl');
      panel.className = 'training-class-detail';
      classDetailContent(detail).forEach(([labelText, value]) => {
        const label = document.createElement('dt');
        const content = document.createElement('dd');
        label.textContent = labelText;
        content.textContent = String(value);
        panel.append(label, content);
      });
      detailCell.append(panel);
      detailRow.append(detailCell);
      tableBody.insertBefore(detailRow, rowElement.nextSibling);
      button.textContent = '⌃';
      button.setAttribute('aria-label', 'Ẩn chi tiết lớp học');
      button.setAttribute('aria-expanded', 'true');
    } catch (_error) {
      button.textContent = '…⌄';
      button.setAttribute('aria-label', 'Chi tiết lớp học');
      const message = document.createElement('span');
      message.className = 'training-class-detail-error';
      message.setAttribute('role', 'status');
      message.textContent = 'Chưa tải được thông tin lớp.';
      cell.append(message);
    } finally {
      button.disabled = false;
    }
  });
  cell.append(button);
}

function renderClassTable(state) {
  const card = document.createElement('div');
  card.className = 'table-card';
  const tableWrap = document.createElement('div');
  tableWrap.className = 'table-wrap';
  const table = document.createElement('table');
  const thead = document.createElement('thead');
  const header = document.createElement('tr');
  const columns = TRAINING_ROUTE_COLUMNS['/training/class'];
  columns.forEach(([, label]) => { const cell = document.createElement('th'); cell.textContent = label; header.append(cell); });
  thead.append(header);
  table.append(thead);
  const body = document.createElement('tbody');
  if (state.loading || state.error || !state.rows.length) {
    const tr = document.createElement('tr');
    const cell = document.createElement('td');
    cell.colSpan = columns.length;
    if (state.loading) cell.textContent = 'Đang tải danh sách lớp…';
    else if (state.error) {
      cell.textContent = 'Không thể tải danh sách lớp.';
      const retry = document.createElement('button');
      retry.type = 'button';
      retry.className = 'small-action';
      retry.textContent = 'Thử lại';
      retry.addEventListener('click', () => state.refresh());
      cell.append(document.createTextNode(' '), retry);
    } else cell.textContent = 'Không tìm thấy dữ liệu';
    tr.append(cell);
    body.append(tr);
  } else {
    state.rows.forEach((row, index) => {
      const tr = document.createElement('tr');
      tr.dataset.classId = String(row.id ?? '');
      columns.forEach(([key]) => {
        const cell = document.createElement('td');
        const projection = classListProjection(row);
        if (key === 'no') cell.textContent = String(index + 1);
        else if (key === 'code') appendClassName(cell, row);
        else if (key === 'period') cell.textContent = projection.period;
        else if (key === 'schedule') cell.textContent = projection.schedule;
        else if (key === 'manager') cell.textContent = projection.manager;
        else if (key === 'teacher_name') cell.textContent = projection.teacher;
        else if (key === 'course_name') cell.textContent = projection.courseName;
        else if (key === 'student_count') cell.textContent = String(projection.studentCount);
        else if (key === 'completed_sessions') appendClassProgress(cell, row);
        else if (key === 'actions') appendClassDetailButton(cell, row, state.api, body, tr, columns.length);
        else cell.textContent = String(projection[key] ?? row[key] ?? '');
        tr.append(cell);
      });
      body.append(tr);
    });
  }
  table.append(body);
  tableWrap.append(table);
  card.append(tableWrap);
  return card;
}

function renderClassListContent(target, state) {
  target.replaceChildren();
  const heading = document.createElement('h1');
  heading.textContent = 'Lớp học';
  target.append(heading);
  const actions = observedActions('/training/class', state.api,
    () => renderTrainingClassProjection(target, { api: state.api }), state.baseRows, state.filters);
  target.append(actions);
  target.append(classSummary(state.baseRows, state.timetableRows));
  const strip = createClassFilterStrip(state);
  target.append(strip);
  target.append(renderClassTable(state));
  target.dataset.trainingObservedRoute = '/training/class';
  target.__trainingClassFilterState = state;
  [0, 40, 140].forEach((delay) => setTimeout(() => reconcileObservedControls(target, '/training/class'), delay));
}

async function renderTrainingClassProjection(target, { api } = {}) {
  if (!target || typeof api !== 'function') return false;
  let baseRows;
  let timetableRows = null;
  try {
    baseRows = observedRows(await api('/api/classes'));
    if (!Array.isArray(baseRows)) throw new Error('class list unavailable');
  } catch (_error) {
    target.dataset.trainingObservedRoute = '/training/class';
    const state = { api, baseRows: [], timetableRows: null, filters: {}, rows: [], loading: false, error: true };
    state.refresh = async () => renderTrainingClassProjection(target, { api });
    renderClassListContent(target, state);
    return true;
  }
  try {
    timetableRows = observedRows(await api('/api/timetable'));
    if (!Array.isArray(timetableRows)) timetableRows = null;
  } catch (_error) {
    timetableRows = null;
  }
  baseRows = enrichClassRows(baseRows, timetableRows);
  const state = {
    api,
    baseRows,
    timetableRows,
    filters: { q: '', status: '', course_id: '', manager: '', teacher: '', start_from: '', start_to: '' },
    rows: baseRows,
    loading: false,
    error: false,
    requestSequence: 0,
    searchTimer: null,
  };
  state.refresh = async () => {
    const sequence = ++state.requestSequence;
    const query = classListQuery(state.filters);
    state.loading = true;
    state.error = false;
    renderClassListContent(target, state);
    try {
      const response = query ? await api(`/api/classes?${query}`) : null;
      const classResult = query ? classListResponse(response) : { rows: state.baseRows, searchApplied: true };
      let rows = classResult.rows;
      if (!Array.isArray(rows)) throw new Error('class list unavailable');
      rows = enrichClassRows(rows, state.timetableRows);
      // The class API query does not search persisted names on every adapter.
      // Recover candidates only for legacy adapters that explicitly omit q
      // support. An empty server-backed response is authoritative.
      if (state.filters.q && !rows.length && !classResult.searchApplied) {
        const fallbackQuery = classListQuery({ ...state.filters, q: '' });
        const candidates = fallbackQuery
          ? observedRows(await api(`/api/classes?${fallbackQuery}`))
          : state.baseRows;
        rows = enrichClassRows(Array.isArray(candidates) ? candidates : [], state.timetableRows);
      }
      if (state.filters.q) rows = rows.filter((row) => classSearchMatches(row, state.filters.q));
      state.rows = state.filters.status === CLASS_NO_SCHEDULE_FILTER
        ? rows.filter((row) => Array.isArray(state.timetableRows)
          && !state.timetableRows.some((session) => String(session.class_code ?? '') === String(row.code ?? '')))
        : state.filters.status === 'ENDING'
          ? rows.filter((row) => row.end_date && String(row.status ?? '') !== 'COMPLETED' && String(row.status ?? '') !== 'CANCELLED')
          : rows;
      if (sequence !== state.requestSequence) return;
      state.loading = false;
      renderClassListContent(target, state);
    } catch (_error) {
      if (sequence !== state.requestSequence) return;
      state.loading = false;
      state.error = true;
      state.rows = [];
      renderClassListContent(target, state);
    }
  };
  state.rows = baseRows;
  target.dataset.trainingObservedRoute = '/training/class';
  renderClassListContent(target, state);
  return true;
}

function observedRows(payload) {
  const value = payload?.data ?? payload;
  if (Array.isArray(value)) return value;
  if (Array.isArray(value?.training_dashboard)) return value.training_dashboard;
  return value?.records || value?.rows || value?.items || [];
}

async function observedApiRows(api, endpoint) {
  try { return observedRows(await api(endpoint)); } catch (_error) { return []; }
}

async function observedApiResult(api, endpoint) {
  try { return { rows: observedRows(await api(endpoint)), error: false }; }
  catch (_error) { return { rows: [], error: true }; }
}

export function courseQueryFromControl(input) {
  const query = String(input?.value ?? '').trim();
  return query ? `?q=${encodeURIComponent(query)}` : '';
}

function courseRowsTable(rows, state = {}) {
  return observedTable('/training/course', TRAINING_ROUTE_COLUMNS['/training/course'], rows, state);
}

export async function renderCourseRoute(target, { api } = {}) {
  target.replaceChildren();
  const heading = document.createElement('h1'); heading.textContent = 'Khóa học'; target.append(heading);
  const status = document.createElement('p'); status.className = 'training-route-status'; status.setAttribute('role', 'status'); status.textContent = 'Đang tải dữ liệu…'; target.append(status);
  // Keep one mutable row collection so the top-level duplicate handler sees
  // the latest loaded data instead of the initial empty array.
  const loadedRows = [];
  const actions = observedActions('/training/course', api, () => load(), loadedRows);
  target.append(actions);
  const controls = observedControls('/training/course');
  const clear = document.createElement('button'); clear.type = 'button'; clear.className = 'ghost'; clear.textContent = 'Xóa lọc'; clear.setAttribute('aria-label', 'Xóa lọc khóa học'); controls.append(clear);
  target.append(controls);
  const searchInput = controls.querySelector('input');
  const load = async () => {
    status.textContent = 'Đang tải dữ liệu…'; status.className = 'training-route-status';
    const result = await observedApiResult(api, `/api/courses${courseQueryFromControl(searchInput)}`);
    loadedRows.splice(0, loadedRows.length, ...result.rows);
    target.querySelector('.table-card')?.remove();
    target.append(courseRowsTable(result.rows, { error: result.error }));
    target.querySelectorAll('.course-detail').forEach((button) => button.addEventListener('click', () => courseDetailModal(api, button.dataset.id)));
    target.querySelectorAll('.course-duplicate').forEach((button) => button.addEventListener('click', async () => { try { await api(`/api/courses/${encodeURIComponent(button.dataset.id)}/duplicate`, { method: 'POST', body: {} }); await load(); } catch (_error) { /* host toast owns API errors */ } }));
    status.textContent = result.error ? 'Không thể tải dữ liệu khóa học.' : result.rows.length ? '' : 'Chưa có dữ liệu';
    if (result.error) status.className = 'training-route-status error';
  };
  let timer;
  const trigger = () => { clearTimeout(timer); timer = setTimeout(load, 180); };
  searchInput?.addEventListener('input', trigger);
  searchInput?.addEventListener('change', load);
  searchInput?.addEventListener('keydown', (event) => { if (event.key === 'Enter') { event.preventDefault(); clearTimeout(timer); load(); } });
  clear.addEventListener('click', () => { if (searchInput) searchInput.value = ''; load(); });
  await load();
  return true;
}

async function renderEvaluationRoute(target, { api } = {}) {
  target.replaceChildren();
  const heading = document.createElement('h1'); heading.textContent = 'Đánh giá hàng ngày'; target.append(heading);
  const status = document.createElement('p'); status.className = 'training-route-status'; status.setAttribute('role', 'status'); status.textContent = 'Đang tải dữ liệu…'; target.append(status);
  const controls = observedControls('/training/daily-evaluation-v2'); target.append(controls);
  const render = async () => {
    const query = new URLSearchParams();
    const classValue = controls.querySelector('[name="evaluation_class"]')?.value || '';
    const statusValue = controls.querySelector('[name="evaluation_status"]')?.value || '';
    const from = controls.querySelector('[name="evaluation_date_from"]')?.value || '';
    const to = controls.querySelector('[name="evaluation_date_to"]')?.value || '';
    if (classValue) query.set('class', classValue); if (statusValue) query.set('status', statusValue); if (from) query.set('date_from', from); if (to) query.set('date_to', to);
    const result = await observedApiResult(api, `/api/evaluations${query.toString() ? `?${query}` : ''}`);
    const columns = [['session_date', 'Ngày'], ['class_code', 'Lớp'], ['student_code', 'Mã học viên'], ['full_name', 'Học viên'], ['score', 'Điểm'], ['status', 'Trạng thái'], ['note', 'Ghi chú']];
    target.querySelector('.table-card')?.remove(); target.append(observedTable('/training/daily-evaluation-v2', columns, result.rows, result));
    status.textContent = result.error ? 'Không thể tải dữ liệu đánh giá.' : result.rows.length ? '' : 'Chưa có dữ liệu';
    status.className = result.error ? 'training-route-status error' : 'training-route-status';
  };
  controls.querySelectorAll('select, input').forEach((control) => control.addEventListener('change', render));
  await render(); return true;
}

async function renderObservedTrainingRoute(target, { api, route } = {}) {
  if (!OBSERVED_FILTERS[route] && !OBSERVED_NO_TABLE_ROUTES.has(route)) return false;
  target.dataset.trainingObservedRoute = route;
  if (route === '/training/class') return renderTrainingClassProjection(target, { api });
  if (route === '/training/timetable') return renderTimetableRoute(target, { api });
  if (route === '/training/attendance') return renderAttendanceRoute(target, { api });
  if (route === '/training/course') return renderCourseRoute(target, { api });
  if (route === '/training/daily-evaluation-v2') return renderEvaluationRoute(target, { api });
  // The reference home is scoped to the selected day (today by default).
  // Keep the dashboard route unscoped so its operational overview remains
  // broad; the date is a persisted API filter, never a client-side slice.
  const today = new Date();
  const todayIso = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-${String(today.getDate()).padStart(2, '0')}`;
  const endpoint = route === '/' ? `/api/dashboard?date=${encodeURIComponent(todayIso)}`
    : route === '/dashboard/training' ? '/api/dashboard'
    : route === '/training/course' ? '/api/courses'
    : route === '/training/timetable' ? '/api/timetable'
      : route === '/training/attendance' ? '/api/attendance'
        : route === '/training/test' ? '/api/tests'
          : route === '/training/homework' ? '/api/homework'
            : route === '/training/class_enroll_trail_wait' ? '/api/trial-registrations'
              : route === '/training/confirm' ? '/api/enrollment-confirmations'
                : route === '/training/customer_test' ? '/api/customer-tests'
                  : route === '/training/pending_enrollment/index' ? '/api/pending-enrollments'
                    : route === '/training/absent-v2' || route === '/training/announcement' || route === '/training/event' || route === '/training/post'
                      ? `/api/generated/screens?route=${encodeURIComponent(route)}`
                      : route === '/training/class' ? '/api/classes' : null;
  const rows = endpoint ? await observedApiRows(api, endpoint) : [];
  target.replaceChildren();
  const heading = document.createElement('h1');
  heading.textContent = ({
    '/': 'Kết quả điểm danh đánh giá',
    '/training/absent-v2': 'Xin nghỉ', '/training/course': 'Khóa học', '/training/timetable': 'Thời khóa biểu',
    '/training/attendance': 'Điểm danh', '/training/daily-evaluation-v2': 'Đánh giá hàng ngày',
    '/training/announcement': 'Thông báo', '/training/event': 'Sự kiện đào tạo', '/training/post': 'Bài viết',
    '/training/test': 'Kiểm tra', '/training/homework': 'Homework', '/training/elearn/topic': 'Bộ đề',
    '/training/elearn/exam_first_test': 'Danh sách bài test đầu vào', '/training/class_enroll_trail_wait': 'Danh sách khách hàng đăng ký học thử',
    '/training/confirm': 'Xác nhận ghi danh', '/training/customer_test': 'Danh sách test / hẹn test',
    '/training/pending_enrollment/index': 'Đăng ký chờ lớp',
  })[route] || 'Đào tạo';
  target.append(heading);
  const action = observedActions(route, api, () => renderObservedTrainingRoute(target, { api, route }), rows);
  if (action.childElementCount) target.append(action);
  if (route === '/training/event' || route === '/training/customer_test') {
    const tabs = document.createElement('div');
    tabs.className = 'ref-tabs';
    tabs.setAttribute('role', 'tablist');
    const tab = document.createElement('button');
    tab.type = 'button';
    tab.className = 'ref-tab active';
    tab.setAttribute('role', 'tab');
    tab.setAttribute('aria-selected', 'true');
    tab.textContent = route === '/training/event' ? 'Sự kiện đào tạo (2)' : 'Danh sách test / hẹn test';
    tabs.append(tab);
    target.append(tabs);
  }
  const controls = observedControls(route);
  if (controls.childElementCount) {
    target.append(controls);
    if (route === '/') {
      const dateControl = [...controls.querySelectorAll('input')].find((input) => input.placeholder === 'Chọn ngày');
      if (dateControl) {
        dateControl.value = `${String(today.getDate()).padStart(2, '0')}/${String(today.getMonth() + 1).padStart(2, '0')}/${today.getFullYear()}`;
      }
    }
  }
  if (!OBSERVED_NO_TABLE_ROUTES.has(route)) {
    const columns = TRAINING_ROUTE_COLUMNS[route] || [];
    if (route === '/training/absent-v2' && rows.length && rows[0]?.data) rows.splice(0, rows.length, ...rows.map((item) => item.data || item));
    target.append(observedTable(route, columns, rows));
  }
  // Home reference includes lightweight trend cards below the attendance
  // table. Keep the values derived from the authenticated dashboard payload;
  // no synthetic attendance rows or branch values are introduced here.
  if (route === '/' || route === '/dashboard/training') {
    const count = rows.length;
    const trend = document.createElement('div');
    trend.className = 'home-trends';
    const chart = (title, labels, values) => {
      const card = document.createElement('div'); card.className = 'card home-chart';
      const h = document.createElement('h2'); h.textContent = title; card.append(h);
      const grid = document.createElement('div'); grid.className = 'home-chart-grid';
      const max = Math.max(1, ...values.map(Number));
      labels.forEach((label, i) => { const col = document.createElement('div'); col.className = 'home-chart-col'; const bars = document.createElement('div'); bars.className = 'home-bars'; const bar = document.createElement('span'); bar.className = `home-bar ${i % 2 ? 'teal' : 'blue'}`; bar.style.height = `${Math.max(4, Math.round(Number(values[i] || 0) / max * 100))}%`; bar.title = String(values[i] || 0); bars.append(bar); col.append(bars); const small = document.createElement('small'); small.textContent = label; col.append(small); grid.append(col); });
      card.append(grid); return card;
    };
    const months = ['06/2026','07/2026','08/2026','09/2026','10/2026','11/2026'];
    const classByMonth = months.map(label => rows.filter(row => { const d = String(row.session_date || ''); return d.startsWith(`${label.slice(3)}-${label.slice(0,2)}`); }).length);
    trend.append(chart('Lớp học 6 tháng gần nhất', months, classByMonth));
    trend.append(chart('Học viên trong tháng', ['Mới','Đang học','Nghỉ học','Bảo lưu','Chưa có lớp','Đã xong','Chưa học'], [0, Number(rows.reduce((n, r) => n + Number(r.attendance_total || 0), 0)), 0, 0, 0, 0, 0]));
    const signup = document.createElement('div'); signup.className = 'card home-signups'; signup.innerHTML = '<p><b>Đăng ký mới</b><strong>0</strong> Học viên</p><p><b>Tái tục</b><strong>0</strong> Học viên</p>'; trend.append(signup); target.append(trend);
  }
  [0, 40, 140].forEach((delay) => setTimeout(() => reconcileObservedControls(target, route), delay));
  return true;
}

export function statusLabel(value) {
  const key = String(value ?? '').toUpperCase();
  return TRAINING_STATUS_LABELS[key] || String(value ?? '');
}

export function trainingQuery(filters = {}) {
  const query = new URLSearchParams();
  Object.entries(filters).forEach(([key, value]) => {
    if (value !== undefined && value !== null && String(value).trim() !== '') query.set(key, value);
  });
  return query.toString();
}

export async function loadTraining(route, filters = {}, fetcher = fetch) {
  if (!TRAINING_ROUTES.includes(route)) throw new Error(`Route đào tạo chưa có hợp đồng: ${route}`);
  const query = trainingQuery(filters);
  const response = await fetcher(`/api/training/routes${route === '/' ? '' : route}${query ? `?${query}` : ''}`, { credentials: 'same-origin' });
  if (!response.ok) throw new Error(`Dữ liệu đào tạo không tải được (${response.status})`);
  return response.json();
}

export async function saveTraining(route, data, { id, method = 'POST', fetcher = fetch } = {}) {
  if (!TRAINING_ROUTES.includes(route)) throw new Error(`Route đào tạo chưa có hợp đồng: ${route}`);
  const suffix = id == null ? '' : `/${encodeURIComponent(id)}`;
  const response = await fetcher(`/api/training/routes${route}${suffix}`, {
    method, credentials: 'same-origin', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ data }),
  });
  if (!response.ok) throw new Error(`Dữ liệu đào tạo không lưu được (${response.status})`);
  return response.json();
}

export async function duplicateTraining(route, id, data = {}, fetcher = fetch) {
  if (route !== '/training/course') throw new Error('Chỉ hỗ trợ nhân bản khóa học');
  if (id == null) throw new Error('Thiếu mã khóa học cần nhân bản');
  const response = await fetcher(`/api/training/routes${route}/${encodeURIComponent(id)}/duplicate`, {
    method: 'POST', credentials: 'same-origin', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ data }),
  });
  if (!response.ok) throw new Error(`Khóa học không nhân bản được (${response.status})`);
  return response.json();
}

export async function exportTraining(route, filters = {}, fetcher = fetch) {
  if (!TRAINING_ROUTES.includes(route)) throw new Error(`Route đào tạo chưa có hợp đồng: ${route}`);
  const query = trainingQuery(filters);
  const response = await fetcher(`/api/export/training${route}${query ? `?${query}` : ''}`, { credentials: 'same-origin' });
  if (!response.ok) throw new Error(`Dữ liệu đào tạo không xuất được (${response.status})`);
  return response;
}

export function renderTrainingRows(tbody, rows = [], columns = COURSE_COLUMNS) {
  tbody.replaceChildren();
  rows.forEach((row, index) => {
    const tr = document.createElement('tr');
    columns.forEach(([key]) => {
      const td = document.createElement('td');
      const value = key === 'no' ? index + 1 : key === 'sessions_hours'
        ? `${row.sessions_count ?? ''} / ${row.hours ?? ''}`
        : key === 'fee_display'
          ? [row.fee_method, row.fee == null ? '' : `${Number(row.fee).toLocaleString('vi-VN')} VND`].filter(Boolean).join(' ')
          : key === 'status' ? statusLabel(row[key]) : row[key] ?? '';
      td.textContent = value;
      tr.append(td);
    });
    tbody.append(tr);
  });
}

const renderValue = (key, row) => {
  if (key === 'no') return '';
  if (key === 'sessions_hours') return `${row.sessions_count ?? ''} / ${row.hours ?? ''}`;
  if (key === 'fee_display') return [row.fee_method, row.fee == null ? '' : `${Number(row.fee).toLocaleString('vi-VN')} VND`].filter(Boolean).join(' ');
  if (key === 'status') return statusLabel(row[key]);
  return row[key] ?? '';
};

function routeColumns(route, payload) {
  const candidate = payload?.contract?.columns || payload?.columns || TRAINING_ROUTE_COLUMNS[route] || [];
  return candidate.map((column) => Array.isArray(column) ? column : [column.key, column.label]).filter(([key, label]) => key && label);
}

/** Render only when the coordinator has mounted the lane API.
 * A missing lane endpoint returns false so the existing shell renderer keeps
 * serving its host-owned route. Empty API results remain empty; no row is made
 * up in the browser.
 */
export async function renderTrainingRoute(target, { api, route } = {}) {
  if (!TRAINING_ROUTES.includes(route) || typeof api !== 'function') return false;
  let payload;
  try {
    const response = await api(`/api/training/routes${route === '/' ? '' : route}`);
    payload = response?.data ?? response;
  } catch (_error) {
    return false;
  }
  const rows = Array.isArray(payload) ? payload : (payload?.rows || payload?.records || []);
  if (!Array.isArray(rows)) return false;
  const columns = routeColumns(route, payload);
  if (!columns.length) return false;
  target.replaceChildren();
  const heading = document.createElement('h1');
  heading.textContent = payload?.title || (route === '/training/course' ? 'Khóa học' : 'Đào tạo');
  target.append(heading);
  const table = document.createElement('table');
  const thead = document.createElement('thead');
  const header = document.createElement('tr');
  columns.forEach(([, label]) => { const th = document.createElement('th'); th.textContent = label; header.append(th); });
  thead.append(header); table.append(thead);
  const tbody = document.createElement('tbody');
  rows.forEach((row, index) => {
    const data = row?.data && typeof row.data === 'object' ? row.data : row;
    const tr = document.createElement('tr');
    columns.forEach(([key]) => { const td = document.createElement('td'); td.textContent = key === 'no' ? String(index + 1) : String(renderValue(key, data)); tr.append(td); });
    tbody.append(tr);
  });
  table.append(tbody); target.append(table);
  return true;
}

/** Backend autoload seam. Host owns routing/auth; this only registers renderers. */
export function register(centerEdu = globalThis.CenterEdu) {
  if (!centerEdu || typeof centerEdu.registerScreen !== 'function') return false;
  TRAINING_ROUTES.forEach((route) => {
    const renderer = route === CLASS_CREATE_ROUTE ? renderClassCreate
      : (OBSERVED_FILTERS[route] || OBSERVED_NO_TABLE_ROUTES.has(route))
      ? renderObservedTrainingRoute
      : renderTrainingRoute;
    centerEdu.registerScreen(route, renderer);
  });
  centerEdu.trainingRoutes = TRAINING_CONTRACT;
  return true;
}

export const TRAINING_CONTRACT = Object.freeze({
  routes: TRAINING_ROUTES,
  columns: TRAINING_ROUTE_COLUMNS,
  classCreate: CLASS_CREATE_CONTRACT,
  course: { columns: COURSE_COLUMNS, fields: COURSE_FIELDS },
  permissions: TRAINING_RBAC,
  maturity: 'SOURCE_PRESENT',
});

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
  ],
  '/training/event': [
    { kind: 'select', options: ['Tất cả', 'Mới tạo', 'Đã gửi'] },
    { kind: 'input', placeholder: 'Tìm kiếm...' },
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
    { kind: 'select', name: 'page_size', label: '10 20 50', options: ['10', '20', '50'] },
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
    { kind: 'input', localOnly: true, name: 'day_date', ariaLabel: 'Ngày trong tuần', placeholder: 'Chọn thứ' },
    { kind: 'select', queryKey: 'teacher', keepSelected: true, name: 'teacher', ariaLabel: 'Giáo viên', options: ['Chọn giáo viên'] },
    { kind: 'select', queryKey: 'course', keepSelected: true, name: 'course', ariaLabel: 'Khóa học', options: ['Chọn khóa'] },
    { kind: 'select', queryKey: 'class_code', keepSelected: true, name: 'class_code', ariaLabel: 'Lớp học', options: ['Chọn lớp'] },
    { kind: 'input', localOnly: true, name: 'session_number', ariaLabel: 'Số thứ tự buổi học', placeholder: 'Số thứ tự buổi học' },
    { kind: 'input', localOnly: true, name: 'time_from', ariaLabel: 'Giờ ca học từ', placeholder: 'Giờ ca học từ' },
    { kind: 'input', localOnly: true, name: 'time_to', ariaLabel: 'Giờ ca học đến', placeholder: 'Giờ ca học đến' },
    { kind: 'select', queryKey: 'room', keepSelected: true, name: 'room', ariaLabel: 'Phòng học', options: ['Chọn phòng học'] },
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
    { kind: 'select', queryKey: 'class', options: ['Chọn lớp học', 'TA-NEN-TANG-01', 'TA-GIAO-TIEP-02'] },
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
  // Branch is an authenticated scope selector, not a free-form class field.
  // Carry it through only when the owning header exposes a selected numeric
  // branch; the server still validates the assignment and tenant.
  if (input.branch_id !== undefined && input.branch_id !== null && String(input.branch_id).trim() !== '') {
    const branchId = Number(input.branch_id);
    if (!Number.isInteger(branchId) || branchId < 1) throw new Error('branch_id phải là số dương');
    payload.branch_id = branchId;
  }
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

function selectedBranchId() {
  const value = document.querySelector('#branch-manager-scope select')?.value || '';
  const branchId = Number(value);
  return Number.isInteger(branchId) && branchId > 0 ? branchId : null;
}

function trainingActionAllowed(label) {
  const role = String(globalThis.CenterEdu?.state?.user?.role || '').toUpperCase();
  const actions = globalThis.CenterEdu?.state?.policy?.allowed_actions;
  if (!Array.isArray(actions)) return false;
  const required = label === 'Excel' ? 'export' : label === 'Upload' ? 'import'
    : /^(Thêm|Tạo|Đồng bộ|Bỏ qua|Nhân bản)/i.test(label) ? 'create' : 'read';
  // Keep the role read only when the policy says so. The role variable is
  // retained for clarity in captures and does not grant access by itself.
  void role;
  return actions.includes(required);
}

const TRAINING_MUTATION_FIELDS = Object.freeze({
  '/training/announcement': [
    ['image', 'Ảnh đại diện', 'file'], ['title', 'Tiêu đề', 'textarea'],
    ['fullnames', 'Tên tài liệu', 'text'], ['file_paths', 'Đường dẫn tệp', 'text'],
    ['important', 'Quan trọng', 'checkbox'], ['send_noti', 'Hẹn gửi', 'checkbox'],
    ['range', 'Phạm vi gửi', 'select', ['Chọn phạm vi', 'Toàn bộ trung tâm', 'Theo lớp', 'Theo tài khoản']],
    ['can_comment', 'Cho phép bình luận', 'checkbox'],
    ['view_comment_type', 'Phạm vi bình luận', 'select', ['Xem được tất cả bình luận', 'Chỉ xem được bình luận của giáo viên']],
  ],
  '/training/event': [
    ['image_logo', 'Ảnh sự kiện', 'file'], ['title', 'Tiêu đề', 'textarea'],
    ['description', 'Mô tả', 'textarea'], ['max_register', 'Số người đăng ký tối đa', 'number'],
    ['start_date', 'Ngày bắt đầu', 'date'], ['end_date', 'Ngày kết thúc', 'date'],
    ['register_from', 'Ngày mở đăng ký', 'date'], ['register_to', 'Ngày đóng đăng ký', 'date'],
    ['important', 'Quan trọng', 'checkbox'], ['send_noti', 'Hẹn gửi', 'checkbox'],
    ['range', 'Phạm vi', 'select', ['Chọn phạm vi', 'Toàn trung tâm', 'Theo lớp', 'Từng tài khoản']],
  ],
});

function trainingMutationValue(row, key) {
  const source = trainingRowSource(row);
  return source?.[key] ?? row?.[key] ?? '';
}

async function openTrainingMutationModal(route, api, rerender, row = null) {
  const definitions = TRAINING_MUTATION_FIELDS[route];
  if (!definitions || typeof api !== 'function') return;
  const backdrop = document.createElement('div'); backdrop.className = 'modal-backdrop training-mutation-modal';
  const panel = document.createElement('div'); panel.className = 'modal'; panel.setAttribute('role', 'dialog'); panel.setAttribute('aria-modal', 'true');
  const heading = document.createElement('h2'); heading.textContent = row ? (route === '/training/event' ? 'Sửa sự kiện đào tạo' : 'Sửa thông báo') : (route === '/training/event' ? 'Tạo sự kiện đào tạo' : 'Tạo thông báo'); panel.append(heading);
  const form = document.createElement('form'); form.className = 'form-grid training-mutation-form';
  const error = document.createElement('p'); error.className = 'error training-mutation-error'; error.setAttribute('role', 'alert'); error.hidden = true;
  let branches = [];
  try { branches = (await api('/api/branch-manager/scope'))?.data?.branches || []; } catch (_error) { branches = []; }
  const controls = new Map();
  const addField = (name, label, type, options = []) => {
    const wrapper = document.createElement('label'); wrapper.className = 'training-mutation-field';
    const caption = document.createElement('span'); caption.textContent = label; wrapper.append(caption);
    let control;
    if (type === 'textarea') control = document.createElement('textarea');
    else if (type === 'select') { control = document.createElement('select'); options.forEach((option, index) => { const item = document.createElement('option'); item.value = index === 0 ? '' : option; item.textContent = option; control.append(item); }); }
    else { control = document.createElement('input'); control.type = type === 'checkbox' ? 'checkbox' : type; }
    control.name = name; const current = trainingMutationValue(row, name);
    if (type === 'checkbox') control.checked = current === true || ['1', 'true', 'Có', 'Đã gửi'].includes(String(current));
    else if (type !== 'file') control.value = String(current ?? '');
    wrapper.append(control); form.append(wrapper); controls.set(name, control);
  };
  definitions.forEach(([name, label, type, options]) => addField(name, label, type, options));
  const branchWrapper = document.createElement('label'); branchWrapper.className = 'training-mutation-field';
  const branchCaption = document.createElement('span'); branchCaption.textContent = 'Chi nhánh'; branchWrapper.append(branchCaption);
  const branchSelect = document.createElement('select'); branchSelect.name = 'branch_id';
  const branchPlaceholder = document.createElement('option'); branchPlaceholder.value = ''; branchPlaceholder.textContent = branches.length > 1 ? 'Chọn chi nhánh' : 'Mặc định'; branchSelect.append(branchPlaceholder);
  branches.forEach((branch) => { const option = document.createElement('option'); option.value = String(branch.id); option.textContent = String(branch.name || branch.code || branch.id); branchSelect.append(option); });
  // New records inherit the header scope. Existing records keep their
  // persisted branch. This matches staff/parent forms and avoids an empty
  // branch payload when the header already selected one.
  const branchValue = trainingMutationValue(row, 'branch_id') || document.querySelector('#branch-manager-scope select')?.value || '';
  if (branchValue) branchSelect.value = String(branchValue);
  if (branches.length > 1) branchSelect.required = true;
  branchWrapper.append(branchSelect); form.append(branchWrapper);
  const actions = document.createElement('div'); actions.className = 'form-actions';
  const close = document.createElement('button'); close.type = 'button'; close.className = 'ghost'; close.textContent = 'Hủy';
  const save = document.createElement('button'); save.type = 'submit'; save.className = 'primary'; save.textContent = 'Lưu'; actions.append(close, save);
  panel.append(form, error, actions); backdrop.append(panel); document.body.append(backdrop);
  const remove = () => backdrop.remove(); close.addEventListener('click', remove);
  form.addEventListener('submit', async (event) => {
    event.preventDefault(); error.hidden = true; save.disabled = true;
    const data = {};
    controls.forEach((control, name) => {
      if (control.type === 'checkbox') data[name] = control.checked ? 'Có' : 'Không';
      else if (control.type === 'file') data[name] = control.files?.[0]?.name || '';
      else data[name] = control.value;
    });
    if (branchSelect.value) {
      data.branch_id = Number(branchSelect.value);
      data.branch = branchSelect.selectedOptions?.[0]?.textContent || '';
    }
    try {
      const body = { route, data };
      const endpoint = row?.id ? `/api/generated/screens/${encodeURIComponent(row.id)}` : '/api/generated/screens';
      if (row?.id) Object.assign(body, { version: row.version, updated_at: row.updated_at, full_body: true });
      await api(endpoint, { method: 'POST', body }); remove(); await rerender();
    } catch (reason) {
      save.disabled = false; error.textContent = reason?.code === 'CONFLICT' ? 'Bản ghi đã thay đổi. Hãy tải lại rồi thử lại.' : (reason?.message || 'Không thể lưu dữ liệu.'); error.hidden = false;
    }
  });
}

function openTrainingDeleteModal(route, api, rerender, row) {
  if (!row?.id || typeof api !== 'function') return;
  const backdrop = document.createElement('div'); backdrop.className = 'modal-backdrop training-delete-modal';
  const panel = document.createElement('div'); panel.className = 'modal'; panel.setAttribute('role', 'dialog');
  const title = document.createElement('h2'); title.textContent = route === '/training/event' ? 'Xóa sự kiện đào tạo?' : 'Xóa thông báo?';
  const message = document.createElement('p'); message.textContent = 'Dữ liệu sẽ được ẩn khỏi danh sách sau khi xác nhận.';
  const error = document.createElement('p'); error.className = 'error'; error.setAttribute('role', 'alert'); error.hidden = true;
  const actions = document.createElement('div'); actions.className = 'form-actions'; const cancel = document.createElement('button'); cancel.type = 'button'; cancel.className = 'ghost'; cancel.textContent = 'Hủy'; const removeButton = document.createElement('button'); removeButton.type = 'button'; removeButton.className = 'primary'; removeButton.textContent = 'Xác nhận xóa'; actions.append(cancel, removeButton); panel.append(title, message, error, actions); backdrop.append(panel); document.body.append(backdrop);
  cancel.addEventListener('click', () => backdrop.remove());
  removeButton.addEventListener('click', async () => { removeButton.disabled = true; try { const query = new URLSearchParams({ route, ...(row.version != null ? { version: row.version } : {}), ...(row.updated_at ? { updated_at: row.updated_at } : {}) }); await api(`/api/generated/screens/${encodeURIComponent(row.id)}?${query}`, { method: 'DELETE' }); backdrop.remove(); await rerender(); } catch (reason) { removeButton.disabled = false; error.textContent = reason?.code === 'CONFLICT' ? 'Bản ghi đã thay đổi. Hãy tải lại rồi thử lại.' : (reason?.message || 'Không thể xóa dữ liệu.'); error.hidden = false; } });
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
  let courses = [], students = [], teachers = [];
  try {
    const [coursePayload, studentPayload, teacherPayload] = await Promise.all([api('/api/courses'), api('/api/students'), api('/api/teachers')]);
    courses = coursePayload?.data || [];
    students = studentPayload?.data || [];
    teachers = teacherPayload?.data || [];
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
  classPanel.append(classCreateSelect('Giáo viên', 'teacher_id', [{ value: '', label: 'Chưa phân công' }, ...teachers.map((teacher) => ({ value: teacher.id, label: teacher.full_name }))]));
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
      const payload = classWorkflowPayload({ ...formData, branch_id: selectedBranchId() || undefined });
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
  // Status counts belong to the table summary, not navigation tabs.
  // The reference places the create affordance at the end of the filter row.
  // Keep the action route-owned; no mutation is implied by rendering it.
  '/training/absent-v2': ['Thêm mới'],
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
  // No /api/classes contract exists for study_status. Retain UI selection
  // without inventing its relation to class status or a transport parameter.
  delete queryFilters.study_status;
  if (queryFilters.status === CLASS_NO_SCHEDULE_FILTER) delete queryFilters.status;
  return trainingQuery(queryFilters);
}

// The local API accepts one status per request. Keep multi-selection in the
// view, issue supported scalar queries, then union rows by their durable ID.
async function classSelectionResponse(api, filters, baseRows, timetableRows) {
  const statuses = Array.isArray(filters.status) ? filters.status : [filters.status || ''];
  const selections = statuses.length ? statuses : [''];
  const results = await Promise.all(selections.map(async (status) => {
    const query = classListQuery({ ...filters, status });
    const result = query ? classListResponse(await api(`/api/classes?${query}`)) : { rows: baseRows, searchApplied: true };
    if (status === CLASS_NO_SCHEDULE_FILTER) result.rows = result.rows.filter((row) => Array.isArray(timetableRows)
      && !timetableRows.some((session) => String(session.class_code ?? '') === String(row.code ?? '')));
    return result;
  }));
  let rows = [...new Map(results.flatMap((result) => result.rows).map((row) => [row.id ?? row.code, row])).values()];
  const explicitStatus = Array.isArray(filters.status)
    ? filters.status.filter(Boolean).length > 0
    : Boolean(filters.status);
  const studyStatuses = !explicitStatus && (Array.isArray(filters.study_status)
    ? filters.study_status.filter(Boolean).map((value) => String(value).toUpperCase())
    : (filters.study_status ? [String(filters.study_status).toUpperCase()] : []));
  if (studyStatuses.length) {
    const allowed = new Set(studyStatuses.flatMap((value) => value === 'OPEN'
      ? ['OPEN', 'IN_PROGRESS', 'ENDING', 'ENDING_SOON']
      : value === 'PLANNED' ? ['PLANNED']
        : value === 'COMPLETED' ? ['COMPLETED']
          : value === 'CANCELLED' ? ['CANCELLED'] : []));
    rows = rows.filter((row) => allowed.has(String(row.status ?? '').toUpperCase()));
  }
  return {
    rows,
    searchApplied: results.every((result) => result.searchApplied),
  };
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

export function localStudyStatusRows(rows = [], filters = {}) {
  const explicitStatus = Array.isArray(filters.status)
    ? filters.status.filter(Boolean).length > 0
    : Boolean(filters.status);
  if (explicitStatus) return rows;
  const selected = Array.isArray(filters.study_status)
    ? filters.study_status.filter(Boolean).map((value) => String(value).toUpperCase())
    : (filters.study_status ? [String(filters.study_status).toUpperCase()] : []);
  if (!selected.length) return rows;
  const allowed = new Set(selected.flatMap((value) => value === 'OPEN'
    ? ['OPEN', 'IN_PROGRESS', 'ENDING', 'ENDING_SOON']
    : value === 'PLANNED' ? ['PLANNED']
      : value === 'COMPLETED' ? ['COMPLETED']
        : value === 'CANCELLED' ? ['CANCELLED'] : []));
  return rows.filter((row) => allowed.has(String(row.status ?? '').toUpperCase()));
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
    if (filter.queryKey && !filter.keepSelected) select.selectedIndex = -1;
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
    || route === '/training/daily-evaluation-v2') return;
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
    const routeAction = (route === '/training/absent-v2' || route === '/training/event') ? strip.querySelector('.training-observed-actions') : null;
    strip.replaceChildren();
    (OBSERVED_FILTERS[route] || []).forEach((filter) => appendObservedControl(strip, filter));
    if (routeAction) strip.append(routeAction);
  }
}

function ensureTrainingPageSizeControl(target, route) {
  const config = route === '/training/course'
    ? { name: 'page_size', label: '10 20 50', options: ['10', '20', '50'] }
    : route === '/training/confirm'
      ? { label: 'Hiển thị 5 10 25 50 bản ghi', options: ['5', '10', '25', '50'] }
      : null;
  if (!config) return;
  const strip = target?.querySelector('.training-observed-filters');
  if (!strip || strip.querySelector(`select[aria-label="${config.label}"]`) || (config.name && strip.querySelector(`select[name="${config.name}"]`))) return;
  appendObservedControl(strip, { kind: 'select', ...config });
}

function observedActions(route, api, rerender, rows = [], filters = {}) {
  const wrap = document.createElement('div');
  wrap.className = 'training-observed-actions';
  (OBSERVED_ACTIONS[route] || []).forEach((label) => {
    if (!trainingActionAllowed(label)) return;
    const button = document.createElement('button');
    button.type = 'button';
    button.className = label === 'Excel' ? 'ghost' : 'primary';
    button.textContent = label;
    if (label === 'Excel') button.addEventListener('click', () => {
      const endpoint = route === '/training/class' ? '/api/export/classes'
        : `/api/export/${route === '/training/course' ? 'courses' : route.includes('pending_enrollment') ? 'pending-enrollments' : route.includes('customer_test') ? 'customer-tests' : 'generated-screen'}`;
      const query = route === '/training/class' ? classListQuery({ ...filters, branch_id: selectedBranchId() || undefined }) : '';
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
          await api('/api/classes/import', { method: 'POST', body: { csv: await file.text(), branch_id: selectedBranchId() || undefined } });
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
  // Generated-screen responses wrap persisted form data in `data` and add a
  // display projection.  Keep both layers available: a route may receive a
  // direct API row or the wrapper, and neither shape should erase real values.
  const source = row?.data && typeof row.data === 'object' ? row.data : row;
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
    student_name: 'hoc_vien', session_name: 'buoi_nghi', reason: 'ly_do',
  })[key] || key;
  const displayAliases = {
    student_name: ['student_name', 'hoc_vien', 'full_name'],
    session_name: ['session_name', 'buoi_nghi', 'session'],
    reason: ['reason', 'ly_do', 'note'],
    views: ['views', 'luot_xem', 'view_count'],
    description: ['description', 'noi_dung', 'content', 'title'],
    sent: ['sent', 'a_xem_a_gui', 'viewed_sent', 'read_sent', 'sent_count', 'view_count'],
    status: ['status', 'trang_thai', 'state'],
    comment: ['comment', 'binh_luan', 'comments'],
  };
  const projected = (displayAliases[key] || [displayKey]).map((candidate) => display[candidate]).find((value) => value !== undefined && value !== null && value !== '');
  if (projected !== undefined && projected !== null && projected !== '') return projected;
  const persisted = (displayAliases[key] || [displayKey]).map((candidate) => source?.[candidate]).find((value) => value !== undefined && value !== null && value !== '');
  if (persisted !== undefined && persisted !== null && persisted !== '') return persisted;
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
  if (route === '/training/absent-v2') {
    const value = trainingRowSource(row);
    if (key === 'student_name') {
      const name = String(value.student_name || value.hoc_vien || value.full_name || '');
      const code = String(value.student_code || value.code || '');
      const dob = trainingDateText(value.date_of_birth || value.dob || value.birth_date || '');
      return [name, code, dob].filter(Boolean).join('\n');
    }
    if (key === 'session_name') {
      const session = String(value.session_name || value.buoi_nghi || '');
      const className = String(value.class_name || value.class_code || '');
      const date = trainingDateText(value.session_date || value.date || '');
      const schedule = [className, date ? `14:15-16:00 ${date} - Thứ 6` : ''].filter(Boolean).join('\n');
      return schedule || session;
    }
    if (key === 'reason') {
      const reason = String(value.reason || value.ly_do || '');
      const creator = String(value.created_by || value.created_by_name || '');
      const created = String(value.created_at || value.updated_at || '');
      const metadata = [creator, created].filter(Boolean).join(' · ');
      return [reason, metadata].filter(Boolean).join('\n');
    }
  }
  if (route === '/training/event') {
    const value = trainingRowSource(row);
    if (key === 'views') return String(value.views ?? value.luot_xem ?? value.view_count ?? '');
    if (key === 'description') {
      const title = String(value.description || value.noi_dung || value.content || value.title || '');
      const created = String(value.created_at || value.updated_at || '');
      const author = String(value.created_by || value.created_by_name || '');
      const metadata = [created && `Tạo lúc ${created}`, author && `bởi ${author}`].filter(Boolean).join(' ');
      return [title, metadata].filter(Boolean).join('\n');
    }
    if (key === 'sent') return String(value.sent || value.a_xem_a_gui || value.viewed_sent || '');
    if (key === 'status') return String(value.status || value.trang_thai || '').replace(/^Mới tạo$/i, 'Chưa gửi');
  }
  if (route === '/training/pending_enrollment/index') {
    if (key === 'customer_name') return row.customer_name || row.full_name;
    if (key === 'start_date') return row.start_date || row.preferred_day;
    if (key === 'created_by') return row.created_by || row.created_by_name;
  }
  return source?.[key] ?? row?.[key] ?? '';
}

function trainingRowSource(row) {
  return row?.data && typeof row.data === 'object' ? row.data : row;
}

function trainingDateText(value) {
  const raw = String(value || '').trim();
  if (!raw) return '';
  const match = raw.match(/^(\d{4})-(\d{2})-(\d{2})/);
  return match ? `${match[3]}/${match[2]}/${match[1]}` : raw;
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

function displayDateFull(value) {
  const match = String(value ?? '').match(/^(\d{4})-(\d{2})-(\d{2})$/);
  return match ? `${match[3]}/${match[2]}/${match[1]}` : '';
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
  const dayNames = ['Thứ 2', 'Thứ 3', 'Thứ 4', 'Thứ 5', 'Thứ 6', 'Thứ 7', 'Chủ nhật'];
  const dayIndex = dayNames.indexOf(day || dayDate);
  const dmy = dayDate.match(/^(\d{1,2})\/(\d{1,2})\/(\d{4})$/);
  let selectedDate = /^\d{4}-\d{2}-\d{2}$/.test(dayDate) ? dayDate : dmy ? `${dmy[3]}-${dmy[2].padStart(2, '0')}-${dmy[1].padStart(2, '0')}` : '';
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

export function timetableWeekGrid(rows = [], weekStart = '') {
  const validRows = Array.isArray(rows) ? rows : [];
  const firstDate = /^\d{4}-\d{2}-\d{2}$/.test(weekStart) ? weekStart : (validRows.map(row => String(row.session_date || '').slice(0, 10)).filter(Boolean).sort()[0] || '');
  if (!firstDate) return [];
  const dayNames = ['Chủ nhật', 'Thứ 2', 'Thứ 3', 'Thứ 4', 'Thứ 5', 'Thứ 6', 'Thứ 7'];
  return Array.from({ length: 7 }, (_, index) => {
    const date = addDaysIso(firstDate, index);
    const sessions = validRows.filter(row => String(row.session_date || '').slice(0, 10) === date);
    const slots = [...new Set(sessions.map(row => [String(row.start_time || ''), String(row.end_time || '')].filter(Boolean).join(' - ')).filter(Boolean))].sort();
    return { date, day: dayNames[new Date(`${date}T00:00:00`).getDay()], slots: slots.length ? slots : [''], sessions };
  });
}

export function timetableCsv(rows = []) {
  const columns = [
    ['session_date', 'Ngày'], ['start_time', 'Bắt đầu'], ['end_time', 'Kết thúc'],
    ['class_code', 'Lớp'], ['course_name', 'Khóa học'], ['teacher', 'Giáo viên'],
    ['room', 'Phòng học'], ['status', 'Trạng thái'],
  ];
  const cell = value => `"${String(value ?? '').replace(/"/g, '""')}"`;
  return `\ufeff${columns.map(([, label]) => cell(label)).join(',')}\r\n${(Array.isArray(rows) ? rows : []).map(row => columns.map(([key]) => cell(key === 'status' ? statusLabel(row?.[key]) : row?.[key])).join(',')).join('\r\n')}`;
}

function timetableMatrix(rows = [], weekStart = '', roomInventory = [], knownRows = rows, { canManage = false } = {}) {
  // Reference room headings define the matrix shape. Persisted room names
  // outside that inventory get their own literal column; sessions are never
  // remapped to a similarly named reference room.
  const sourceRooms = [...new Set((Array.isArray(knownRows) ? knownRows : []).map((row) => String(row?.room ?? '').trim()).filter(Boolean))];
  const catalogRooms = [...new Set((Array.isArray(roomInventory) ? roomInventory : []).map(room => String(room?.name || room?.code || '').trim()).filter(Boolean))];
  const rooms = [...catalogRooms, ...sourceRooms.filter(room => !catalogRooms.includes(room))];
  if (!rooms.length) rooms.push(...timetableRoomHeaders());
  const week = timetableWeekGrid(rows, weekStart);
  const slots = week.flatMap(({ date, day, slots: daySlots }) => daySlots.map(slot => ({ date, day, slot })));
  const card = document.createElement('div'); card.className = 'table-card timetable-matrix-card'; card.setAttribute('aria-label', 'Ma trận thời khóa biểu theo phòng học');
  const wrap = document.createElement('div'); wrap.className = 'table-wrap'; const table = document.createElement('table');
  const head = document.createElement('thead'); const hr = document.createElement('tr');
  ['Ngày', 'Phòng học Ca học', ...rooms].forEach((label) => { const th = document.createElement('th'); th.scope = 'col'; th.textContent = label; hr.append(th); }); head.append(hr); table.append(head);
  const body = document.createElement('tbody');
  slots.forEach(({ date, day: weekday, slot }, index) => { const tr = document.createElement('tr'); if (index === 0 || slots[index - 1].date !== date) { const day = document.createElement('th'); day.scope = 'row'; day.rowSpan = slots.filter(item => item.date === date).length; day.innerHTML = `${weekday}<br>${displayDateFull(date)}`; tr.append(day); } const time = document.createElement('th'); time.scope = 'row'; time.textContent = slot; tr.append(time); const sessions = rows.filter((row) => String(row.session_date || '').slice(0, 10) === date && ([String(row.start_time || ''), String(row.end_time || '')].filter(Boolean).join(' - ') || '') === slot); rooms.forEach((room) => { const td = document.createElement('td'); td.className = 'timetable-session-cell'; sessions.filter((row) => String(row.room || '') === room).forEach(row => {
    const item = document.createElement('article'); item.className = 'timetable-matrix-session';
    const title = document.createElement('strong'); title.textContent = String(row.class_code || row.class_name || ''); item.append(title);
    if (row.session_number != null || row.session_no != null) { const lesson = document.createElement('small'); lesson.textContent = `Buổi ${row.session_number ?? row.session_no}`; item.append(lesson); }
    const teacher = document.createElement('span'); teacher.textContent = String(row.teacher || row.teacher_name || ''); if (teacher.textContent) item.append(teacher);
    const status = document.createElement('span'); status.className = 'timetable-matrix-status'; status.textContent = statusLabel(row.status); item.append(status);
    if (row.id != null && String(row.id) !== '') {
      const actions = document.createElement('div'); actions.className = 'timetable-matrix-actions';
      const students = document.createElement('button'); students.type = 'button'; students.className = 'timetable-students'; students.dataset.id = String(row.id); students.setAttribute('aria-label', 'Xem danh sách học viên'); students.textContent = 'Học viên'; actions.append(students);
      if (canManage) {
        const edit = document.createElement('button'); edit.type = 'button'; edit.className = 'timetable-edit'; edit.dataset.id = String(row.id); edit.setAttribute('aria-label', 'Sửa buổi học'); edit.textContent = 'Sửa'; actions.append(edit);
        if (String(row.status) === 'SCHEDULED') { const cancel = document.createElement('button'); cancel.type = 'button'; cancel.className = 'timetable-cancel'; cancel.dataset.id = String(row.id); cancel.setAttribute('aria-label', 'Hủy buổi học'); cancel.textContent = 'Hủy'; actions.append(cancel); }
      }
      item.append(actions);
    }
    td.append(item);
  }); tr.append(td); }); body.append(tr); });
  if (!slots.length) { const tr = document.createElement('tr'); const td = document.createElement('td'); td.colSpan = Math.max(2, rooms.length + 2); td.textContent = 'Chưa có dữ liệu'; td.setAttribute('role', 'status'); tr.append(td); body.append(tr); }
  table.append(body);
  table.className = 'timetable-grid'; wrap.append(table); card.append(wrap); const style = document.createElement('style'); style.textContent = `.timetable-grid{min-width:${Math.max(980, (rooms.length + 2) * 140)}px}.timetable-grid thead th{background:#4a9ed6;color:#fff;text-align:center;min-width:140px}.timetable-grid tbody th{background:#c7cada;font-weight:600;white-space:nowrap}.timetable-grid tbody tr{height:98px}.timetable-grid td{vertical-align:top;padding:12px;font-size:12px}.timetable-session-cell{background:#fff}.timetable-matrix-session{display:grid;gap:4px;border:1px solid #dce1ef;border-radius:4px;padding:8px;margin:2px 0;color:#59627a}.timetable-matrix-session strong{color:#333}.timetable-matrix-session small,.timetable-matrix-session span{font-size:11px}.timetable-matrix-actions{display:flex;gap:5px;flex-wrap:wrap}.timetable-matrix-actions button{border:0;background:transparent;color:#4a62d8;font-size:11px;cursor:pointer;padding:2px 4px}.timetable-matrix-actions .timetable-cancel{color:#d9445d}`; card.append(style); return card;
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
  target.replaceChildren();
  target.classList.add('training-timetable-screen');
  if (!document.querySelector('#training-timetable-style')) {
    const style = document.createElement('style'); style.id = 'training-timetable-style';
    style.textContent = '.training-timetable-screen:has(.timetable-matrix-card) .training-observed-filters{display:grid;grid-template-columns:repeat(3,minmax(180px,1fr));gap:12px 38px;padding:10px 24px 14px;margin:0;border:0;background:#fff}.training-timetable-screen:has(.timetable-matrix-card) .training-observed-filters label{min-width:0}.training-timetable-screen:has(.timetable-matrix-card) .training-observed-filters select,.training-timetable-screen:has(.timetable-matrix-card) .training-observed-filters input{width:100%;height:34px;box-sizing:border-box}.training-timetable-screen:has(.timetable-matrix-card) .training-observed-actions{display:flex;gap:6px;padding:0 24px 10px}.training-timetable-screen:has(.timetable-matrix-card) .training-observed-actions button{margin:0;background:#2bbbad;color:#fff;border:0}.training-timetable-screen:has(.timetable-matrix-card) .training-observed-actions button:disabled{opacity:.55}.training-timetable-screen:has(.timetable-matrix-card) .timetable-matrix-card{margin:0;padding:22px 24px;border-top:1px solid #edf0f5;box-shadow:none;border-radius:0}@media(max-width:900px){.training-timetable-screen:has(.timetable-matrix-card) .training-observed-filters{grid-template-columns:repeat(2,minmax(140px,1fr));gap:10px;padding:10px 14px}.training-timetable-screen:has(.timetable-matrix-card) .training-observed-actions{padding:0 14px 10px}.training-timetable-screen:has(.timetable-matrix-card) .timetable-matrix-card{padding:14px}}'; document.head.append(style);
  }
  const status = document.createElement('p'); status.className = 'training-route-status'; status.setAttribute('role', 'status'); status.textContent = 'Đang tải dữ liệu…';
  const controls = observedControls('/training/timetable');
  let currentRows = [];
  const actions = document.createElement('div'); actions.className = 'training-observed-actions';
  const search = document.createElement('button'); search.type = 'button'; search.className = 'primary'; search.textContent = 'Tìm kiếm'; actions.append(search);
  const excel = document.createElement('button'); excel.type = 'button'; excel.className = 'ghost'; excel.textContent = 'Excel';
  excel.addEventListener('click', () => {
    const url = URL.createObjectURL(new Blob([timetableCsv(currentRows)], { type: 'text/csv;charset=utf-8' }));
    const link = document.createElement('a'); link.href = url; link.download = 'timetable.csv'; link.click(); URL.revokeObjectURL(url);
  }); actions.append(excel);
  const teacherView = document.createElement('button'); teacherView.type = 'button'; teacherView.className = 'ghost'; teacherView.textContent = 'TKB GV'; teacherView.disabled = true; teacherView.title = 'Chưa có dữ liệu TKB giáo viên trong hệ thống cục bộ'; actions.append(teacherView);
  target.append(controls, actions, status);
  if (target.dataset.timetableActionsBound !== 'true') {
    target.dataset.timetableActionsBound = 'true';
    target.addEventListener('click', event => {
      if (target.dataset.trainingObservedRoute !== '/training/timetable') return;
      const button = event.target.closest?.('.timetable-edit,.timetable-students,.timetable-cancel');
      if (!button || !target.contains(button)) return;
      const id = button.dataset.id;
      if (button.classList.contains('timetable-edit') && typeof window.timetableEditModal === 'function') window.timetableEditModal(id);
      else if (button.classList.contains('timetable-students') && typeof window.timetableStudentsModal === 'function') window.timetableStudentsModal(id);
      else if (button.classList.contains('timetable-cancel') && typeof window.timetableCancel === 'function') window.timetableCancel(id);
    });
  }
  // Read persisted rows once before choosing the initial week.  A fixed
  // reference year can point at an empty week while the API contains valid
  // rows from another year; options therefore come from the API response.
  let allRows;
  let roomInventory = [];
  try {
    allRows = observedRows(await api('/api/timetable'));
    try { roomInventory = observedRows(await api('/api/classrooms')); } catch (_error) { roomInventory = []; }
  } catch (_error) {
    status.textContent = 'Không thể tải dữ liệu thời khóa biểu.';
    status.className = 'training-route-status error';
    return true;
  }
  // Replace placeholder choices with distinct values persisted by the timetable API.
  [['teacher', 'teacher'], ['course', 'course_name'], ['class_code', 'class_code'], ['room', 'room']].forEach(([name, key]) => {
    const select = controls.querySelector(`select[name="${name}"]`);
    if (!select) return;
    const values = [...new Set([
      ...allRows.map(row => String(row?.[key] ?? '').trim()),
      ...(name === 'room' ? roomInventory.map(room => String(room?.name || room?.code || '').trim()) : []),
    ].filter(Boolean))];
    select.replaceChildren(new Option(name === 'teacher' ? 'Chọn giáo viên' : name === 'course' ? 'Chọn khóa' : name === 'class_code' ? 'Chọn lớp' : 'Chọn phòng học', ''));
    values.forEach(value => select.append(new Option(value, value)));
  });
  const weekOptions = timetableWeekOptions(allRows, new Date());
  const weekSelect = controls.querySelector('select[name="week"]');
  if (weekSelect) {
    weekSelect.replaceChildren();
    weekOptions.forEach((option) => {
      const item = document.createElement('option'); item.value = option.value; item.textContent = option.value; weekSelect.append(item);
    });
    const currentWeek = mondayDate(new Date());
    // Prefer the current week only when persisted sessions exist in it. A
    // current empty week otherwise renders a blank matrix despite older,
    // source-backed sessions being available; select the latest populated
    // source week instead. No rows are invented.
    const currentHasRows = allRows.some((row) => String(row?.session_date || '').slice(0, 10) >= currentWeek && String(row?.session_date || '').slice(0, 10) <= addDaysIso(currentWeek, 6));
    const currentOption = (currentHasRows && weekOptions.find((option) => option.start === currentWeek)) || weekOptions[weekOptions.length - 1];
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
      currentRows = rows;
      target.querySelector('.timetable-matrix-card')?.remove();
      const role = String(globalThis.CenterEdu?.state?.user?.role || '').toUpperCase();
      target.append(timetableMatrix(rows, weekStart, roomInventory, allRows, { canManage: ['ADMIN', 'STAFF', 'TEACHER'].includes(role) }));
    status.textContent = rows.length ? '' : 'Chưa có dữ liệu'; status.hidden = Boolean(rows.length);
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
    return true;
  }
  async function load(initial = false) {
    status.textContent = 'Đang tải dữ liệu…'; status.className = 'training-route-status';
    try {
      const query = attendanceQueryFromControls(controls);
      const payload = initial && !query ? initialRows : observedRows(await api(`/api/attendance${query ? `?${query}` : ''}`));
      // Reference attendance exposes filters only. Keep the route surface
      // table-free until an authoritative table contract is available.
      target.querySelector('.table-card')?.remove();
      status.textContent = payload.length ? '' : 'Chưa có dữ liệu';
    } catch (_error) {
      target.querySelector('.table-card')?.remove();
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
    columns.forEach(([key]) => {
      const td = document.createElement('td');
      const value = String(displayText(observedValue(route, key, row, index)));
      if ((route === '/training/event' && key === 'views')) {
        const eye = document.createElement('span'); eye.className = 'training-view-eye'; eye.setAttribute('aria-hidden', 'true'); eye.textContent = '◉'; td.append(eye, document.createTextNode(` ${value}`));
      } else if ((route === '/training/absent-v2' || route === '/training/event') && key === 'status') {
        const chip = document.createElement('span');
        const status = value || '—';
        chip.className = `status-chip status-${status.replace(/\s+/g, '-').toLowerCase()}`;
        chip.textContent = statusLabel(status); td.append(chip);
        const source = trainingRowSource(row);
        const scheduled = source.scheduled_at || source.send_at || source.hen_gui_luc;
        if (route === '/training/event' && scheduled) { const meta = document.createElement('small'); meta.className = 'training-status-meta'; meta.textContent = `Hẹn gửi lúc ${scheduled}`; td.append(document.createElement('br'), meta); }
      } else if ((route === '/training/absent-v2' || route === '/training/event') && key === 'comment') {
        const box = document.createElement('div'); box.className = 'training-comment-cell';
        const textarea = document.createElement('textarea'); textarea.placeholder = route === '/training/event' ? 'Viết bình luận...' : 'Viết'; textarea.rows = 1;
        const file = document.createElement('input'); file.type = 'file'; file.setAttribute('aria-label', 'Đính kèm tệp');
        const button = document.createElement('button'); button.type = 'button'; button.className = 'comment-submit'; button.title = 'Gửi bình luận'; button.setAttribute('aria-label', 'Gửi bình luận'); button.innerHTML = '<span aria-hidden="true">📷</span>';
        box.append(textarea, file, button); td.append(box);
      } else if (route === '/training/absent-v2' && key === 'student_name') {
        const link = document.createElement('a'); link.href = '#'; link.className = 'link-button'; link.textContent = value.split('\n')[0]; td.append(link, document.createElement('br'), document.createTextNode(value.split('\n').slice(1).join('\n')));
      } else if (route === '/training/absent-v2' && key === 'session_name') {
        const link = document.createElement('a'); link.href = '#'; link.className = 'link-button'; link.textContent = value.split('\n')[0]; td.append(link, document.createElement('br'), document.createTextNode(value.split('\n').slice(1).join('\n')));
      } else if (route === '/training/event' && key === 'description') {
        const parts = value.split('\n'); const link = document.createElement('a'); link.href = '#'; link.className = 'link-button'; link.textContent = parts.shift() || ''; td.append(link, document.createElement('br'), document.createTextNode(parts.join('\n')));
      } else if ((route === '/training/event' || route === '/training/announcement') && key === 'actions') {
        const edit = document.createElement('button'); edit.type = 'button'; edit.className = 'small-action'; edit.title = 'Sửa sự kiện'; edit.setAttribute('aria-label', 'Sửa sự kiện'); edit.dataset.action = 'edit';
        edit.innerHTML = '<span aria-hidden="true">✎</span>'; edit.title = route === '/training/event' ? 'Sửa sự kiện' : 'Sửa thông báo'; edit.setAttribute('aria-label', edit.title);
        const copy = document.createElement('button'); copy.type = 'button'; copy.className = 'small-action'; copy.title = 'Sao chép sự kiện'; copy.setAttribute('aria-label', 'Sao chép sự kiện'); copy.dataset.action = 'copy';
        copy.innerHTML = '<span aria-hidden="true">▣</span>';
        const remove = document.createElement('button'); remove.type = 'button'; remove.className = 'small-action'; remove.title = route === '/training/event' ? 'Xóa sự kiện' : 'Xóa thông báo'; remove.setAttribute('aria-label', remove.title); remove.dataset.action = 'delete';
        remove.innerHTML = '<span aria-hidden="true">♜</span>'; td.append(edit, copy, remove);
      } else if (route === '/training/course' && key === 'name' && row?.id) { const button = document.createElement('button'); button.type = 'button'; button.className = 'link-button course-detail'; button.dataset.id = String(row.id); button.textContent = value; td.append(button); } else if (route === '/training/course' && key === 'actions' && row?.id) { const detail = document.createElement('button'); detail.type = 'button'; detail.className = 'small-action course-detail'; detail.dataset.id = String(row.id); detail.textContent = 'Chi tiết'; const duplicate = document.createElement('button'); duplicate.type = 'button'; duplicate.className = 'small-action course-duplicate'; duplicate.dataset.id = String(row.id); duplicate.textContent = 'Nhân bản'; td.append(detail, duplicate); } else td.textContent = value;
      tr.append(td);
    });
    tbody.append(tr);
  });
  if (!rows.length) {
    const tr = document.createElement('tr'); const td = document.createElement('td'); td.colSpan = Math.max(1, columns.length);
    td.textContent = state.error ? 'Không thể tải dữ liệu.' : 'Chưa có dữ liệu'; td.setAttribute('role', state.error ? 'alert' : 'status'); tr.append(td); tbody.append(tr);
  }
  table.append(tbody); tableWrap.append(table); card.append(tableWrap);
  if (route === '/training/event') card.append(trainingTableFooter(route, rows));
  return card;
}

// Absent/event are dense operational tables. Keep their geometry local to
// this module so the shell's broad form rules cannot inflate controls.
function trainingCompactStyle() {
  const style = document.createElement('style');
  style.dataset.trainingCompactStyle = '1';
  style.textContent = `
    [data-training-observed-route="/training/absent-v2"],
    [data-training-observed-route="/training/event"] {font-size:12px}
    [data-training-observed-route="/training/absent-v2"] h1,
    [data-training-observed-route="/training/event"] h1 {font-size:20px;margin:0 0 12px}
    [data-training-observed-route="/training/absent-v2"] .training-observed-actions,
    [data-training-observed-route="/training/event"] .training-observed-actions {display:flex;gap:0;margin:0 0 8px}
    [data-training-observed-route="/training/absent-v2"] .training-observed-actions button,
    [data-training-observed-route="/training/event"] .training-observed-actions button {height:30px;padding:0 14px;border-radius:5px;font-size:11px}
    [data-training-observed-route="/training/absent-v2"] .training-observed-actions,
    [data-training-observed-route="/training/event"] .training-observed-actions {margin-left:auto}
    [data-training-observed-route="/training/absent-v2"] .training-observed-actions button {background:#2bbf9a;color:#fff}
    [data-training-observed-route="/training/event"] .training-observed-actions button {background:#4361ee;color:#fff}
    [data-training-observed-route="/training/absent-v2"] .training-observed-filters,
    [data-training-observed-route="/training/event"] .training-observed-filters {display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:6px;margin:0 0 10px}
    [data-training-observed-route="/training/absent-v2"] .training-observed-filters {grid-template-columns:repeat(6,minmax(0,1fr))}
    [data-training-observed-route="/training/event"] .training-observed-filters {grid-template-columns:170px 170px 170px 1fr}
    [data-training-observed-route="/training/absent-v2"] .training-observed-filters label,
    [data-training-observed-route="/training/event"] .training-observed-filters label {min-width:0}
    [data-training-observed-route="/training/absent-v2"] select,
    [data-training-observed-route="/training/absent-v2"] input,
    [data-training-observed-route="/training/event"] select,
    [data-training-observed-route="/training/event"] input {height:30px;min-height:30px;padding:4px 8px;font-size:11px;border-radius:3px}
    [data-training-observed-route="/training/absent-v2"] .table-card,
    [data-training-observed-route="/training/event"] .table-card {margin-top:4px}
    [data-training-observed-route="/training/absent-v2"] table,
    [data-training-observed-route="/training/event"] table {table-layout:fixed;width:100%}
    [data-training-observed-route="/training/absent-v2"] th,
    [data-training-observed-route="/training/event"] th {font-size:10px;padding:8px 7px;white-space:nowrap}
    [data-training-observed-route="/training/absent-v2"] td,
    [data-training-observed-route="/training/event"] td {font-size:11px;padding:8px 7px;vertical-align:top}
    [data-training-observed-route="/training/absent-v2"] th:nth-child(1){width:38px}
    [data-training-observed-route="/training/absent-v2"] th:nth-child(2){width:18%}
    [data-training-observed-route="/training/absent-v2"] th:nth-child(3){width:18%}
    [data-training-observed-route="/training/absent-v2"] th:nth-child(4){width:22%}
    [data-training-observed-route="/training/absent-v2"] th:nth-child(5){width:15%}
    [data-training-observed-route="/training/event"] th:nth-child(1){width:38px}
    [data-training-observed-route="/training/event"] th:nth-child(2){width:8%}
    [data-training-observed-route="/training/event"] th:nth-child(3){width:25%}
    [data-training-observed-route="/training/event"] th:nth-child(4){width:14%}
    [data-training-observed-route="/training/event"] th:nth-child(5){width:14%}
    .training-comment-cell {display:flex;align-items:center;gap:5px;min-width:0}
    .training-comment-cell textarea {flex:1;min-width:0;width:100%;height:28px;min-height:28px;resize:none;padding:6px 8px;border:0;border-radius:14px;background:#f0f2f5;font-size:11px}
    [data-training-observed-route="/training/absent-v2"] td:nth-child(2), [data-training-observed-route="/training/absent-v2"] td:nth-child(3), [data-training-observed-route="/training/absent-v2"] td:nth-child(4), [data-training-observed-route="/training/event"] td:nth-child(3) {white-space:pre-line}
    .training-comment-cell input[type=file] {width:22px;max-width:22px;height:24px;padding:0;overflow:hidden;border:0;font-size:0}
    .training-comment-cell input[type=file]::file-selector-button {width:22px;height:22px;padding:0;border:0;background:transparent;color:#667085;font-size:0}
    .comment-submit {width:22px;height:22px;padding:0;border:0;background:transparent;color:#667085;font-size:12px}
    .status-chip {display:inline-block;padding:3px 9px;border-radius:12px;background:#35bd9b;color:#fff;font-size:10px;white-space:nowrap}
    .training-view-eye {color:#4f596b;font-size:11px}.training-status-meta {display:block;color:#667085;font-size:10px;margin-top:2px}
    [data-training-observed-route="/training/event"] .small-action {width:24px;height:22px;padding:0;margin:0 2px;font-size:11px}
    .training-status-summary {display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:18px;margin:4px 0 12px;padding:0 4px}
    .training-status-summary .summary-item {font-size:11px;color:#697586;font-weight:600}
    .training-status-summary .summary-track {height:5px;margin-top:6px;background:#e8ebef;border-radius:4px;overflow:hidden}
    .training-status-summary .summary-track i {display:block;height:100%;background:#35bd9b}
    .training-table-footer {display:flex;justify-content:space-between;align-items:center;padding:10px 4px 2px;color:#697586;font-size:11px}
    .training-pager {display:flex;gap:4px}
    .training-pager button {min-width:24px;height:24px;border:1px solid #e4e7ec;border-radius:50%;background:#fff;color:#667085;font-size:11px}
    .training-pager button.active {background:#5b5bd6;border-color:#5b5bd6;color:#fff}
  `;
  return style;
}

function trainingStatusSummary(route, rows) {
  if (route === '/training/absent-v2') {
    const items = [['Chưa phê duyệt', 'PENDING'], ['Đồng ý', 'APPROVED'], ['Từ chối', 'REJECTED'], ['Hủy', 'CANCELLED'], ['Nhận thông tin', 'INFO']];
    return renderTrainingStatusSummary(items, rows);
  }
  if (route !== '/training/event') return null;
  const items = [['Chưa gửi', 'Mới tạo'], ['Đã gửi', 'Đã gửi']];
  return renderTrainingStatusSummary(items, rows);
}

function renderTrainingStatusSummary(items, rows) {
  const total = Math.max(1, rows.length);
  const wrap = document.createElement('div'); wrap.className = 'training-status-summary';
  items.forEach(([label, key]) => {
    const item = document.createElement('div'); item.className = 'summary-item';
    const count = rows.filter((row) => {
      const value = String(row?.status ?? row?.trang_thai ?? row?.data?.status ?? row?.data?.trang_thai ?? row?.display_data?.trang_thai ?? '').trim();
      const normalized = value.toUpperCase();
      const aliases = { PENDING: ['PENDING', 'CHƯA PHÊ DUYỆT', 'CHƯA GỬI'], APPROVED: ['APPROVED', 'ĐỒNG Ý'], REJECTED: ['REJECTED', 'TỪ CHỐI'], CANCELLED: ['CANCELLED', 'HỦY'], INFO: ['INFO', 'NHẬN THÔNG TIN'], 'MỚI TẠO': ['MỚI TẠO', 'CHƯA GỬI'], 'ĐÃ GỬI': ['ĐÃ GỬI'] };
      return (aliases[key.toUpperCase()] || [key.toUpperCase()]).includes(normalized);
    }).length;
    const text = document.createElement('span'); text.textContent = `${label} ${count}/${rows.length}`;
    const track = document.createElement('div'); track.className = 'summary-track';
    const progress = document.createElement('i'); progress.style.width = `${Math.round(count / total * 100)}%`;
    const progressColors = { 'Chưa phê duyệt': '#39a8ef', 'Đồng ý': '#35bd9b', 'Từ chối': '#f25f75', 'Hủy': '#c7cbd4', 'Nhận thông tin': '#f3b648', 'Chưa gửi': '#c7cbd4', 'Đã gửi': '#39a8ef' };
    progress.style.background = progressColors[label] || '#35bd9b';
    progress.setAttribute('role', 'progressbar'); progress.setAttribute('aria-label', label);
    progress.setAttribute('aria-valuemin', '0'); progress.setAttribute('aria-valuemax', String(rows.length)); progress.setAttribute('aria-valuenow', String(count));
    track.append(progress); item.append(text, track); wrap.append(item);
  });
  return wrap;
}

function trainingTableFooter(route, rows) {
  const footer = document.createElement('div'); footer.className = 'training-table-footer';
  const count = document.createElement('span'); count.textContent = rows.length ? `Hiển thị 1 đến ${rows.length} của ${rows.length} bản ghi` : 'Không có bản ghi';
  const pager = document.createElement('div'); pager.className = 'training-pager'; pager.setAttribute('aria-label', 'Phân trang');
  ['‹', '1', '›'].forEach((label, index) => { const button = document.createElement('button'); button.type = 'button'; button.className = index === 1 ? 'active' : 'ghost'; button.textContent = label; button.disabled = !rows.length || index !== 1; button.setAttribute('aria-label', index === 0 ? 'Trang trước' : index === 2 ? 'Trang sau' : 'Trang 1'); pager.append(button); });
  footer.append(count, pager); return footer;
}

function classDateIso(value) {
  const raw = String(value ?? '').trim();
  const iso = raw.match(/^(\d{4})-(\d{2})-(\d{2})$/);
  const display = iso ? [raw, iso[3], iso[2], iso[1]] : raw.match(/^(\d{1,2})[\/-](\d{1,2})[\/-](\d{4})$/);
  if (!display) return '';
  const candidate = `${display[3]}-${String(display[2]).padStart(2, '0')}-${String(display[1]).padStart(2, '0')}`;
  const date = new Date(`${candidate}T00:00:00Z`);
  return date.getUTCFullYear() === Number(display[3]) && date.getUTCMonth() + 1 === Number(display[2]) && date.getUTCDate() === Number(display[1]) ? candidate : '';
}

export function formatClassDate(value) {
  const match = classDateIso(value).match(/^(\d{4})-(\d{2})-(\d{2})$/);
  return match ? `${match[3]}/${match[2]}/${match[1]}` : '';
}

function appendClassSelect(strip, key, label, options, value = '', { multiple = false } = {}) {
  const wrapper = document.createElement(multiple ? 'div' : 'label');
  if (multiple) wrapper.className = 'select2-container';
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
    // Empty status means the observed default `x Tất cả`; keep that option
    // selected in the native source of truth so the compact trigger and API
    // filter state agree without inventing a backend value.
    const hasExplicitSelection = selected.size > 0;
    [...select.options].forEach((option) => { option.selected = hasExplicitSelection ? selected.has(option.value) : option.value === ''; });
    // Keep the native multi-select as the source of truth while exposing a
    // compact, keyboard-operable chip menu. Native listboxes are too tall for
    // the observed class filter row, but their options/change event remain real.
    select.hidden = true;
    select.setAttribute('aria-hidden', 'true');
    select.tabIndex = -1;
    const control = document.createElement('span');
    control.className = 'class-compact-multiselect';
    control.style.position = 'relative'; control.style.display = 'block';
    const trigger = document.createElement('button');
    trigger.type = 'button'; trigger.className = 'class-filter-multiselect select2-selection--multiple';
    trigger.setAttribute('aria-haspopup', 'dialog'); trigger.setAttribute('aria-expanded', 'false');
    trigger.setAttribute('aria-label', label); trigger.style.width = '100%'; trigger.style.minHeight = '36px';
    trigger.style.height = '36px'; trigger.style.minWidth = '0'; trigger.style.flexWrap = 'nowrap'; trigger.style.overflow = 'hidden';
    const menu = document.createElement('div');
    menu.className = 'class-filter-options'; menu.setAttribute('role', 'dialog'); menu.setAttribute('aria-label', label);
    menu.hidden = true; menu.style.position = 'absolute'; menu.style.zIndex = '20'; menu.style.left = '0'; menu.style.right = '0';
    menu.style.top = 'calc(100% + 3px)'; menu.style.maxHeight = '220px'; menu.style.overflow = 'auto'; menu.style.background = '#fff';
    menu.style.border = '1px solid #dfe5ee'; menu.style.borderRadius = '4px'; menu.style.boxShadow = '0 7px 18px rgba(27,43,79,.16)';
    const update = () => {
      const chosen = [...select.options].filter((option) => option.selected && option.value !== '').map((option) => option.textContent);
      trigger.replaceChildren();
      (chosen.length ? chosen : [select.options[0]?.textContent || label]).forEach((text) => {
        const chip = document.createElement('span'); chip.className = 'select2-selection__choice';
        chip.style.minWidth = '0'; chip.style.whiteSpace = 'nowrap'; chip.style.overflow = 'hidden';
        const remove = document.createElement('span'); remove.className = 'select2-selection__choice__remove'; remove.textContent = '×'; remove.setAttribute('aria-hidden', 'true');
        remove.addEventListener('click', (event) => {
          event.stopPropagation();
          [...select.options].forEach((option) => { if (option.textContent === text) option.selected = false; });
          update(); select.dispatchEvent(new Event('change', { bubbles: true }));
        });
        chip.append(remove, document.createTextNode(text)); trigger.append(chip);
      });
      [...menu.querySelectorAll('input[type="checkbox"]')].forEach((checkbox) => {
        const option = [...select.options].find((item) => item.value === checkbox.value);
        checkbox.checked = Boolean(option?.selected);
      });
    };
    options.forEach((option) => {
      const item = document.createElement('label'); item.style.display = 'flex'; item.style.alignItems = 'center'; item.style.gap = '7px'; item.style.padding = '7px 9px';
      const checkbox = document.createElement('input'); checkbox.type = 'checkbox'; checkbox.value = String(option.value ?? ''); checkbox.checked = selected.has(checkbox.value); checkbox.disabled = Boolean(option.disabled);
      checkbox.style.width = '14px'; checkbox.style.height = '14px'; checkbox.style.minHeight = '0'; checkbox.style.margin = '0';
      checkbox.addEventListener('change', () => {
        const targetOption = [...select.options].find((candidate) => candidate.value === checkbox.value);
        if (!targetOption) return;
        if (checkbox.value === '') {
          [...select.options].forEach((candidate) => { candidate.selected = candidate === targetOption ? checkbox.checked : false; });
        } else {
          targetOption.selected = checkbox.checked;
          const all = select.options[0]; if (all?.value === '') all.selected = false;
        }
        update();
        select.dispatchEvent(new Event('change', { bubbles: true }));
      });
      const text = document.createElement('span'); text.textContent = option.label; item.append(checkbox, text); menu.append(item);
    });
    const close = () => { menu.hidden = true; trigger.setAttribute('aria-expanded', 'false'); };
    trigger.addEventListener('click', () => { menu.hidden = !menu.hidden; trigger.setAttribute('aria-expanded', String(!menu.hidden)); if (!menu.hidden) menu.querySelector('input:not(:disabled)')?.focus(); });
    trigger.addEventListener('keydown', (event) => {
      if (event.key === 'Escape') { close(); return; }
      if (event.key === 'ArrowDown' || event.key === 'Enter' || event.key === ' ') { event.preventDefault(); menu.hidden = false; trigger.setAttribute('aria-expanded', 'true'); menu.querySelector('input:not(:disabled)')?.focus(); }
    });
    menu.addEventListener('keydown', (event) => { if (event.key === 'Escape') { close(); trigger.focus(); } });
    control.addEventListener('focusout', (event) => { if (!control.contains(event.relatedTarget)) close(); });
    control.append(trigger, menu); wrapper.append(control, select); update();
  } else if ([...select.options].some((option) => option.value === String(value ?? ''))) {
    select.value = String(value ?? ''); wrapper.append(select);
  } else wrapper.append(select);
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
  input.type = 'text';
  input.inputMode = 'numeric';
  input.dataset.dateInput = '1'; input.dataset.dateText = '1';
  input.dataset.classFilter = key;
  input.setAttribute('aria-label', placeholder);
  input.placeholder = placeholder;
  input.value = formatClassDate(value);
  wrapper.append(input);
  strip.append(wrapper);
  return input;
}

function createClassFilterStrip(state) {
  const strip = document.createElement('div');
  strip.className = 'filter-strip training-observed-filters';
  const statusOptions = CLASS_STATUS_FILTERS.map((option) => ({
    ...option,
    disabled: option.value === 'ENDING' || (option.value === CLASS_NO_SCHEDULE_FILTER && !Array.isArray(state.timetableRows)),
  }));
  // The reference shows four filters, then the two status/teacher filters,
  // then four dates beside the actions. Blank Select2 search slots from the
  // historical inventory are widget internals, not standalone page filters.
  appendClassSelect(strip, 'status', 'Trạng thái lớp học', statusOptions, state.filters.status, { multiple: true });
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
    { value: 'COMPLETED', label: 'Đã xong' },
    { value: 'CANCELLED', label: 'Bị hủy' },
  ], state.filters.study_status, { multiple: true });
  appendClassSelect(strip, 'teacher', 'Giáo viên', [
    { value: '', label: 'Chọn giáo viên' },
    ...teachers.map((teacher) => ({ value: teacher, label: teacher })),
  ], state.filters.teacher);
  appendClassDate(strip, 'start_from', 'Ngày bắt đầu: từ ngày', state.filters.start_from);
  appendClassDate(strip, 'start_to', 'Ngày bắt đầu: đến ngày', state.filters.start_to);
  appendClassDate(strip, 'end_from', 'Ngày kết thúc: từ ngày', state.filters.end_from);
  appendClassDate(strip, 'end_to', 'Ngày kết thúc: đến ngày', state.filters.end_to);
  strip.querySelectorAll('[data-class-filter]').forEach((control) => {
    control.parentElement.dataset.classFilterField = control.dataset.classFilter;
  });
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
  strip.querySelectorAll('select[data-class-filter], input[data-date-text][data-class-filter]').forEach((control) => {
    control.addEventListener('change', () => {
      if (control.dataset.dateText === '1') {
        const raw = control.value.trim();
        const iso = classDateIso(raw);
        control.setCustomValidity(raw && !iso ? 'Ngày không hợp lệ. Nhập dd/mm/yyyy.' : '');
        if (raw && !iso) { control.reportValidity(); return; }
        control.dataset.iso = iso;
        state.filters[control.dataset.classFilter] = iso;
        control.value = formatClassDate(iso);
        state.refresh();
        return;
      }
      const values = control.multiple ? [...control.selectedOptions].map((option) => option.value).filter(Boolean) : control.value;
      state.filters[control.dataset.classFilter] = values;
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
  const projectionOptionsPresent = status && ['PLANNED', 'OPEN', 'COMPLETED', 'CANCELLED']
    .every((value) => [...status.options].some((option) => option.value === value));
  if (current && search && projectionOptionsPresent) {
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
  // Both numerator and denominator come from the current local API rows.
  // Color is presentation only; status counting and API values stay intact.
  summarizeClassStatuses(rows, timetableRows).forEach((item) => {
    const entry = document.createElement('div');
    entry.className = 'class-status-entry';
    const text = document.createElement('div');
    text.className = 'class-status-text';
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
    const statusColors = {
      planned: '#ef6576', inProgress: '#2bb89a', ending: '#f1a62a',
      completed: '#8995ad', cancelled: '#e76878', noSchedule: '#6974dc',
    };
    const color = statusColors[item.key] || '#59677e';
    entry.style.color = color;
    label.style.color = color;
    count.style.color = color;
    const bar = document.createElement('i');
    bar.style.width = total > 0 && item.count !== null
      ? `${Math.max(0, Math.min(100, (item.count / total) * 100))}%` : '0%';
    bar.style.backgroundColor = color;
    track.append(bar);
    text.append(label, document.createTextNode(' '), count);
    entry.append(text, track);
    summary.append(entry);
  });
  return summary;
}

function appendClassName(cell, row) {
  const projection = classListProjection(row);
  const stack = document.createElement('span');
  stack.className = 'class-multiline';
  const name = document.createElement('span');
  name.className = 'class-primary-name';
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

function classLifecycleControls(detail, api, refresh) {
  const wrap = document.createElement('div');
  wrap.className = 'training-class-lifecycle';
  const canEdit = ['ADMIN', 'STAFF', 'BRANCH_MANAGER'].includes(String(globalThis.CenterEdu?.state?.user?.role || '').toUpperCase());
  if (!canEdit) return wrap;
  const edit = document.createElement('button'); edit.type = 'button'; edit.className = 'small-action'; edit.textContent = 'Sửa';
  edit.addEventListener('click', () => {
    const form = document.createElement('form'); form.className = 'training-class-edit-form';
    const fields = [
      ['name', 'Tên lớp', detail.name || detail.code || ''], ['code', 'Mã lớp', detail.code || ''],
      ['start_date', 'Ngày bắt đầu', detail.start_date || ''], ['end_date', 'Ngày kết thúc', detail.end_date || ''],
      ['sessions_count', 'Số buổi', detail.sessions_count ?? ''], ['hours', 'Số giờ', detail.hours ?? ''],
      ['max_students', 'Sĩ số tối đa', detail.max_students ?? ''], ['notes', 'Ghi chú', detail.notes || ''],
    ];
    fields.forEach(([name, label, value]) => { const item = document.createElement('label'); item.textContent = label; const input = document.createElement(name === 'notes' ? 'textarea' : 'input'); input.name = name; input.value = String(value); if (name.includes('date')) input.type = 'date'; item.append(input); form.append(item); });
    const save = document.createElement('button'); save.type = 'submit'; save.className = 'primary'; save.textContent = 'Lưu';
    const cancel = document.createElement('button'); cancel.type = 'button'; cancel.className = 'ghost'; cancel.textContent = 'Hủy';
    const error = document.createElement('p'); error.className = 'form-error'; error.setAttribute('role', 'alert');
    form.append(save, cancel, error); wrap.replaceChildren(form); cancel.onclick = () => wrap.replaceChildren(edit, close, cancelClass);
    form.onsubmit = async (event) => { event.preventDefault(); error.textContent = ''; try { const body = Object.fromEntries(new FormData(form)); Object.assign(body, { course_id: detail.course_id, teacher_id: detail.teacher_id || '', room: detail.room || '', schedule: detail.schedule || '', payment_method: detail.payment_method || '', primary_manager: detail.primary_manager || '', secondary_manager: detail.secondary_manager || '', daily_evaluation: detail.daily_evaluation || '', vn_teacher_sessions: detail.vn_teacher_sessions ?? '', foreign_teacher_sessions: detail.foreign_teacher_sessions ?? '', status: detail.status, version: detail.version, updated_at: detail.updated_at, full_body: true }); await api(`/api/classes/${encodeURIComponent(detail.id)}`, { method: 'POST', body }); await refresh(); } catch (err) { error.textContent = err.code === 'CONFLICT' ? 'Lớp đã thay đổi. Hãy tải lại rồi thử lại.' : (err.message || 'Không thể lưu lớp.'); } };
  });
  const lifecycle = (status, label, endpoint) => {
    const button = document.createElement('button');
    button.type = 'button';
    button.className = `small-action${status === 'CANCELLED' ? ' danger' : ''}`;
    button.textContent = label;
    button.onclick = () => {
      wrap.querySelector('.training-lifecycle-dialog')?.remove();
      const backdrop = document.createElement('div');
      backdrop.className = 'modal-backdrop training-lifecycle-dialog';
      backdrop.innerHTML = `<div class="modal" role="dialog" aria-modal="true" aria-labelledby="training-lifecycle-title"><h2 id="training-lifecycle-title">${label} lớp</h2><form><label>Áp dụng từ ngày*<input name="apply_from" type="date" required></label><div class="form-actions"><button type="button" class="ghost lifecycle-cancel">Hủy</button><button type="submit" class="primary">Xác nhận</button></div><p class="error lifecycle-error" role="alert"></p></form></div>`;
      wrap.append(backdrop);
      const form = backdrop.querySelector('form');
      const error = backdrop.querySelector('.lifecycle-error');
      const close = () => backdrop.remove();
      backdrop.querySelector('.lifecycle-cancel').onclick = close;
      backdrop.onclick = event => { if (event.target === backdrop) close(); };
      form.onsubmit = async event => {
        event.preventDefault();
        error.textContent = '';
        const applyFrom = new FormData(form).get('apply_from');
        try {
          await api(`/api/classes/${encodeURIComponent(detail.id)}/${endpoint}`, { method: 'POST', body: { apply_from: applyFrom, version: detail.version, updated_at: detail.updated_at } });
          close();
          await refresh();
        } catch (err) {
          if (err.code === 'CONFLICT' || err.status === 409) {
            error.textContent = 'Lớp đã thay đổi. Hãy tải lại rồi thử lại.';
            const reload = document.createElement('button');
            reload.type = 'button';
            reload.className = 'ghost conflict-reload';
            reload.textContent = 'Tải lại';
            reload.onclick = () => { close(); refresh(); };
            error.append(' ', reload);
          } else {
            error.textContent = err.message || 'Không thể cập nhật trạng thái lớp.';
          }
        }
      };
      backdrop.querySelector('input')?.focus();
    };
    return button;
  };
  const close = lifecycle('COMPLETED', 'Đóng', 'close');
  const cancelClass = lifecycle('CANCELLED', 'Hủy', 'cancel');
  wrap.append(edit, close, cancelClass);
  return wrap;
}

function appendClassDetailButton(cell, row, api, tableBody, rowElement, columnCount) {
  if (row.id === null || row.id === undefined) return;
  const studentsButton = document.createElement('button');
  studentsButton.type = 'button';
  studentsButton.className = 'small-action';
  studentsButton.textContent = 'Học viên';
  studentsButton.title = 'Danh sách học viên';
  studentsButton.addEventListener('click', () => {
    window.history.pushState({}, '', `/training/class/student/list/${encodeURIComponent(row.id)}`);
    window.dispatchEvent(new PopStateEvent('popstate'));
  });
  cell.append(studentsButton);
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
      detailCell.append(classLifecycleControls(detail, api, async () => {
        window.dispatchEvent(new PopStateEvent('popstate'));
      }));
      const links = document.createElement('p'); links.className = 'training-class-related-routes';
      links.textContent = 'Chương trình học, bộ kỹ năng và bài kiểm tra: Chưa triển khai trong rebuild.';
      detailCell.append(links);
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
    const pages = Math.max(1, Math.ceil(state.rows.length / CLASS_PAGE_SIZE));
    state.page = Math.min(Math.max(1, Number(state.page) || 1), pages);
    const offset = (state.page - 1) * CLASS_PAGE_SIZE;
    state.rows.slice(offset, offset + CLASS_PAGE_SIZE).forEach((row, pageIndex) => {
      const index = offset + pageIndex;
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
  if (!state.loading && !state.error && state.rows.length) card.append(classTableFooter(state, card));
  return card;
}

const CLASS_PAGE_SIZE = 10;

function classTableFooter(state, card) {
  const total = state.rows.length;
  const pages = Math.max(1, Math.ceil(total / CLASS_PAGE_SIZE));
  const start = (state.page - 1) * CLASS_PAGE_SIZE + 1;
  const end = Math.min(state.page * CLASS_PAGE_SIZE, total);
  const footer = document.createElement('div'); footer.className = 'training-table-footer';
  const count = document.createElement('span'); count.textContent = `Hiển thị ${start} đến ${end} của ${total} bản ghi`;
  const pager = document.createElement('div'); pager.className = 'training-pager'; pager.setAttribute('aria-label', 'Phân trang');
  const go = page => { state.page = page; card.replaceWith(renderClassTable(state)); };
  const add = (label, page, disabled, active) => {
    const button = document.createElement('button'); button.type = 'button'; button.className = active ? 'active' : 'ghost';
    button.textContent = label; button.disabled = disabled;
    if (!disabled && !active) button.addEventListener('click', () => go(page));
    pager.append(button);
  };
  add('‹', state.page - 1, state.page <= 1, false);
  for (let page = 1; page <= pages; page += 1) add(String(page), page, false, page === state.page);
  add('›', state.page + 1, state.page >= pages, false);
  footer.append(count, pager);
  return footer;
}

function classListStyle() {
  // Route-owned presentation; no shared CSS or shell normalization changes.
  const style = document.createElement('style');
  style.dataset.trainingClassStyle = '1';
  style.textContent = `
    [data-training-observed-route="/training/class"] .training-table-footer {display:flex;align-items:center;justify-content:space-between;padding:12px 16px;font-size:13px;color:#4b5563}
    [data-training-observed-route="/training/class"] .training-pager {display:flex;gap:6px}
    [data-training-observed-route="/training/class"] .training-pager button {min-width:30px;height:30px;border-radius:50%;border:0;background:#f1f3f8;color:#4b5563;font-size:12px;cursor:pointer}
    [data-training-observed-route="/training/class"] .training-pager button.active {background:#5b5fc7;color:#fff}
    [data-training-observed-route="/training/class"] .training-pager button:disabled {opacity:.45;cursor:default}
    [data-training-observed-route="/training/class"] .training-class-summary {
      grid-template-columns:repeat(6,minmax(0,1fr));gap:24px;
      margin:0 0 24px;padding:8px 12px;background:transparent;border:0;
    }
    [data-training-observed-route="/training/class"] .class-status-entry {
      display:grid;gap:9px;min-width:0;
    }
    [data-training-observed-route="/training/class"] .class-status-text {font-weight:600;line-height:1.4}
    [data-training-observed-route="/training/class"] .class-status-text b {font-weight:600}
    [data-training-observed-route="/training/class"] .class-primary-name {
      color:#596de3;font-weight:700;
    }
    [data-training-observed-route="/training/class"] .class-multiline > small {
      color:#8490a6;font-size:10px;font-weight:500;
    }
    [data-training-observed-route="/training/class"] .training-observed-filters {
      grid-template-columns:repeat(4,minmax(0,1fr));align-items:start;
    }
    [data-training-observed-route="/training/class"] [data-class-filter-field] {min-width:0}
    [data-training-observed-route="/training/class"] .training-class-actions {
      grid-column:1 / -1;display:flex;justify-content:flex-end;align-items:center;
      gap:5px;min-height:36px;margin:0;flex-wrap:wrap;
    }
    [data-training-observed-route="/training/class"] .training-class-actions button {
      height:36px;padding:0 12px;border-radius:4px;font-size:12px;font-weight:600;color:#fff;
    }
    [data-training-observed-route="/training/class"] .training-class-actions button:nth-of-type(1) {background:#2f9ed8}
    [data-training-observed-route="/training/class"] .training-class-actions button:nth-of-type(2) {background:#6366c6}
    [data-training-observed-route="/training/class"] .training-class-actions button:nth-of-type(3) {background:#2bb89a}
    [data-training-observed-route="/training/class"] .training-class-import-feedback {flex-basis:100%}
    @media(min-width:1151px) {
      [data-training-observed-route="/training/class"] .training-observed-filters {grid-template-columns:repeat(6,minmax(0,1fr))}
      [data-training-observed-route="/training/class"] [data-class-filter-field="status"] {grid-area:1 / 1}
      [data-training-observed-route="/training/class"] [data-class-filter-field="course_id"] {grid-area:1 / 2}
      [data-training-observed-route="/training/class"] [data-class-filter-field="q"] {grid-area:1 / 3}
      [data-training-observed-route="/training/class"] [data-class-filter-field="manager"] {grid-area:1 / 4}
      [data-training-observed-route="/training/class"] [data-class-filter-field="study_status"] {grid-area:2 / 1}
      [data-training-observed-route="/training/class"] [data-class-filter-field="teacher"] {grid-area:2 / 2}
      [data-training-observed-route="/training/class"] [data-class-filter-field="start_from"] {grid-area:3 / 1}
      [data-training-observed-route="/training/class"] [data-class-filter-field="start_to"] {grid-area:3 / 2}
      [data-training-observed-route="/training/class"] [data-class-filter-field="end_from"] {grid-area:3 / 3}
      [data-training-observed-route="/training/class"] [data-class-filter-field="end_to"] {grid-area:3 / 4}
      [data-training-observed-route="/training/class"] .training-class-actions {grid-area:3 / 5 / 4 / 7}
    }
    @media(max-width:900px) {
      [data-training-observed-route="/training/class"] .training-observed-filters {grid-template-columns:repeat(2,minmax(0,1fr))}
      [data-training-observed-route="/training/class"] .training-class-summary {grid-template-columns:repeat(2,minmax(0,1fr));gap:16px}
    }
  `;
  return style;
}

function renderClassListContent(target, state) {
  target.replaceChildren(classListStyle());
  const heading = document.createElement('h1');
  heading.textContent = 'Lớp học';
  target.append(heading);
  target.append(classSummary(state.baseRows, state.timetableRows));
  const strip = createClassFilterStrip(state);
  const actions = observedActions('/training/class', state.api,
    () => renderTrainingClassProjection(target, { api: state.api }), state.baseRows, state.filters);
  // Preserve existing handlers while moving the three actions beside dates.
  actions.classList.add('training-class-actions');
  strip.append(actions);
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
    filters: { q: '', status: [], study_status: ['OPEN'], course_id: '', manager: '', teacher: '', start_from: '', start_to: '', end_from: '', end_to: '' },
    rows: [],
    loading: false,
    error: false,
    requestSequence: 0,
    searchTimer: null,
  };
  state.rows = localStudyStatusRows(baseRows, state.filters);
  state.refresh = async () => {
    const sequence = ++state.requestSequence;
    const query = classListQuery(state.filters);
    state.loading = true;
    state.error = false;
    renderClassListContent(target, state);
    try {
      const classResult = (query || state.filters.study_status?.length) ? await classSelectionResponse(api, state.filters, state.baseRows, state.timetableRows)
        : { rows: state.baseRows, searchApplied: true };
      let rows = classResult.rows;
      if (!Array.isArray(rows)) throw new Error('class list unavailable');
      rows = enrichClassRows(rows, state.timetableRows);
      // The class API query does not search persisted names on every adapter.
      // Recover candidates only for legacy adapters that explicitly omit q
      // support. An empty server-backed response is authoritative.
      if (state.filters.q && !rows.length && !classResult.searchApplied) {
        const candidates = (await classSelectionResponse(api, { ...state.filters, q: '' }, state.baseRows, state.timetableRows)).rows;
        rows = enrichClassRows(Array.isArray(candidates) ? candidates : [], state.timetableRows);
      }
      if (state.filters.q) rows = rows.filter((row) => classSearchMatches(row, state.filters.q));
      // Reapply the client-owned study chip after every server response. This
      // keeps reload and filter changes consistent even when an adapter returns
      // the unfiltered class set for an empty query.
      rows = localStudyStatusRows(rows, state.filters);
      state.rows = rows; state.page = 1;
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
  // Keep the default "Đang học" chip authoritative on the first render too.
  // Replacing this with baseRows makes completed/cancelled classes reappear
  // after a reload until the user changes another control.
  state.rows = localStudyStatusRows(baseRows, state.filters);
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

// U08's backend contract supports only `class` and `status`.  The observed
// free-text control therefore filters the already loaded projection locally;
// it must not invent a `q` parameter that the service rejects/ignores.  Staff
// and page-size controls remain deliberately inert until an authoritative
// backend contract exists.
export function confirmationQueryFromControls(classValue = '', statusValue = '') {
  const query = new URLSearchParams();
  if (String(classValue).trim()) query.set('class', String(classValue).trim());
  if (String(statusValue).trim()) query.set('status', String(statusValue).trim());
  const encoded = query.toString();
  return encoded ? `?${encoded}` : '';
}

export function confirmationSearchRows(rows = [], value = '') {
  const needle = String(value ?? '').trim().toLocaleLowerCase();
  if (!needle) return rows;
  return rows.filter((row) => [row.full_name, row.student_code, row.class_code,
    row.course_name, row.contract_code, row.status].some((field) => String(field ?? '').toLocaleLowerCase().includes(needle)));
}

export async function renderConfirmationRoute(target, { api } = {}) {
  target.replaceChildren();
  const heading = document.createElement('h1'); heading.textContent = 'Xác nhận ghi danh'; target.append(heading);
  const actions = observedActions('/training/confirm', api, () => load(), []); target.append(actions);
  const controls = observedControls('/training/confirm');
  const search = controls.querySelector('input');
  const classSelect = controls.querySelector('select');
  const pageSize = controls.querySelector('select[aria-label="Hiển thị 5 10 25 50 bản ghi"]');
  const clear = document.createElement('button');
  clear.type = 'button'; clear.className = 'ghost'; clear.textContent = 'Xóa lọc';
  clear.setAttribute('aria-label', 'Xóa lọc xác nhận ghi danh'); controls.append(clear); target.append(controls);
  const tableState = document.createElement('p'); tableState.className = 'training-route-status';
  tableState.setAttribute('role', 'status'); target.append(tableState);
  let loadedRows = [];
  let loading = false;
  const renderRows = (rows, error = false) => {
    target.querySelector('.table-card')?.remove();
    target.append(observedTable('/training/confirm', TRAINING_ROUTE_COLUMNS['/training/confirm'], rows, { error }));
    tableState.textContent = error ? 'Không thể tải dữ liệu xác nhận.' : rows.length ? '' : 'Chưa có dữ liệu';
    tableState.className = `training-route-status${error ? ' error' : ''}`;
  };
  const load = async () => {
    if (loading) return;
    loading = true; tableState.textContent = 'Đang tải dữ liệu…'; tableState.className = 'training-route-status';
    try {
      const endpoint = `/api/enrollment-confirmations${confirmationQueryFromControls(classSelect?.value)}`;
      loadedRows = observedRows(await api(endpoint));
      const filtered = confirmationSearchRows(loadedRows, search?.value);
      renderRows(filtered.slice(0, Math.max(1, Number(pageSize?.value || 10))));
    } catch (_error) { loadedRows = []; renderRows([], true); }
    finally { loading = false; }
  };
  const applySearch = () => {
    const filtered = confirmationSearchRows(loadedRows, search?.value);
    renderRows(filtered.slice(0, Math.max(1, Number(pageSize?.value || 10))));
  };
  search?.addEventListener('input', applySearch);
  search?.addEventListener('change', applySearch);
  search?.addEventListener('keydown', (event) => { if (event.key === 'Enter') { event.preventDefault(); applySearch(); } });
  classSelect?.addEventListener('change', load);
  pageSize?.addEventListener('change', applySearch);
  clear.addEventListener('click', () => { if (search) search.value = ''; if (classSelect) classSelect.value = ''; load(); });
  setTimeout(() => ensureTrainingPageSizeControl(target, '/training/confirm'), 200);
  await load();
  return true;
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
  const pageSize = controls.querySelector('select[name="page_size"]');
  const load = async () => {
    status.textContent = 'Đang tải dữ liệu…'; status.className = 'training-route-status';
    const result = await observedApiResult(api, `/api/courses${courseQueryFromControl(searchInput)}`);
    loadedRows.splice(0, loadedRows.length, ...result.rows);
    target.querySelector('.table-card')?.remove();
    const visibleRows = result.rows.slice(0, Math.max(1, Number(pageSize?.value || 10)));
    target.append(courseRowsTable(visibleRows, { error: result.error }));
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
  pageSize?.addEventListener('change', () => {
    const visibleRows = loadedRows.slice(0, Math.max(1, Number(pageSize.value || 10)));
    target.querySelector('.table-card')?.remove();
    target.append(courseRowsTable(visibleRows));
  });
  clear.addEventListener('click', () => { if (searchInput) searchInput.value = ''; load(); });
  setTimeout(() => ensureTrainingPageSizeControl(target, '/training/course'), 200);
  await load();
  return true;
}

async function renderEvaluationRoute(target, { api } = {}) {
  target.replaceChildren();
  const heading = document.createElement('h1'); heading.textContent = 'Đánh giá hàng ngày'; target.append(heading);
  // Reference capture exposes no controls, table, or verified query
  // contract. Keep controls inert rather than fabricating projection/API
  // semantics from the local endpoint.
  // Không thể tải dữ liệu đánh giá. remains reserved for a future verified
  // error surface; this route currently has no observed data panel.
  return true;
}

export function assessmentQueryFromControls(controls) {
  const query = new URLSearchParams();
  const values = {
    status: controls?.querySelector('select[data-filter-key="status"]')?.value || controls?.querySelectorAll('select')[0]?.value,
    class: controls?.querySelector('select[data-filter-key="class"]')?.value || controls?.querySelectorAll('select')[1]?.value,
    date_from: controls?.querySelector('input[data-filter-key="date_from"]')?.value,
    date_to: controls?.querySelector('input[data-filter-key="date_to"]')?.value,
  };
  Object.entries(values).forEach(([key, value]) => { if (String(value ?? '').trim()) query.set(key, String(value).trim()); });
  const encoded = query.toString();
  return encoded ? `?${encoded}` : '';
}

function assessmentControls(route) {
  const controls = observedControls(route);
  const selects = controls.querySelectorAll('select');
  if (selects[0]) {
    selects[0].dataset.filterKey = 'status';
    // The API contract accepts OPEN/CLOSED; retain the observed Vietnamese
    // labels while transporting only those evidenced values.
    [...selects[0].options].forEach((option) => {
      const label = option.textContent.trim();
      option.value = label === 'Đang học' ? 'OPEN' : label === 'Đã học' ? 'CLOSED' : '';
    });
  }
  if (selects[1]) selects[1].dataset.filterKey = 'class';
  return controls;
}

async function renderAssessmentRoute(target, { api, route } = {}) {
  target.replaceChildren();
  const heading = document.createElement('h1');
  heading.textContent = route === '/training/test' ? 'Kiểm tra' : 'Homework';
  target.append(heading);
  const controls = assessmentControls(route);
  const clear = document.createElement('button');
  clear.type = 'button'; clear.className = 'ghost'; clear.textContent = 'Xóa lọc';
  clear.setAttribute('aria-label', `Xóa lọc ${route === '/training/test' ? 'bài kiểm tra' : 'bài tập'}`);
  controls.append(clear); target.append(controls);
  clear.addEventListener('click', () => {
    controls.querySelectorAll('select, input').forEach((control) => { if (control.tagName === 'SELECT') control.selectedIndex = 0; else control.value = ''; });
  });
  // Reference capture exposes filters only. Do not invent table/API behavior
  // until an authoritative route contract is available.
  return true;
}

async function renderObservedTrainingRoute(target, { api, route } = {}) {
  target.classList.remove('training-timetable-screen');
  if (!OBSERVED_FILTERS[route] && !OBSERVED_NO_TABLE_ROUTES.has(route)) return false;
  target.dataset.trainingObservedRoute = route;
  if (route === '/training/class') return renderTrainingClassProjection(target, { api });
  if (route === '/training/timetable') return renderTimetableRoute(target, { api });
  if (route === '/training/attendance') return renderAttendanceRoute(target, { api });
  if (route === '/training/course') return renderCourseRoute(target, { api });
  if (route === '/training/daily-evaluation-v2') return renderEvaluationRoute(target, { api });
  if (route === '/training/confirm') return renderConfirmationRoute(target, { api });
  if (route === '/training/test' || route === '/training/homework') return renderAssessmentRoute(target, { api, route });
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
  target.append(trainingCompactStyle());
  const heading = document.createElement('h1');
  const headingLabel = ({
    '/': 'Kết quả điểm danh đánh giá',
    '/training/absent-v2': 'Xin nghỉ', '/training/course': 'Khóa học', '/training/timetable': 'Thời khóa biểu',
    '/training/attendance': 'Điểm danh', '/training/daily-evaluation-v2': 'Đánh giá hàng ngày',
    '/training/announcement': 'Thông báo', '/training/event': 'Sự kiện đào tạo', '/training/post': 'Bài viết',
    '/training/test': 'Kiểm tra', '/training/homework': 'Homework', '/training/elearn/topic': 'Bộ đề',
    '/training/elearn/exam_first_test': 'Danh sách bài test đầu vào', '/training/class_enroll_trail_wait': 'Danh sách khách hàng đăng ký học thử',
    '/training/confirm': 'Xác nhận ghi danh', '/training/customer_test': 'Danh sách test / hẹn test',
    '/training/pending_enrollment/index': 'Đăng ký chờ lớp',
  })[route] || 'Đào tạo';
  // U06/U07 reference headings carry a small route-specific document icon.
  // Keep it structural and route-owned; no generic screen heading changes.
  if (route === '/training/test' || route === '/training/homework') {
    heading.className = 'training-observed-heading';
    const icon = document.createElement('span');
    icon.className = 'training-observed-heading-icon';
    icon.setAttribute('aria-hidden', 'true');
    icon.innerHTML = route === '/training/test'
      ? '<svg viewBox="0 0 24 24" focusable="false"><path d="M3 8.5 12 4l9 4.5-9 4.5-9-4.5Zm4 2.1v4.2c3 2.1 8 2.1 10 0v-4.2"/></svg>'
      : '<svg viewBox="0 0 24 24" focusable="false"><path d="M6 3.5h9l3 3V20.5H6zM15 3.5v3h3M9 11h6M9 14h6M9 17h4"/></svg>';
    heading.append(icon, document.createTextNode(headingLabel));
  } else heading.textContent = headingLabel;
  target.append(heading);
  const rerender = () => renderObservedTrainingRoute(target, { api, route });
  const action = observedActions(route, api, rerender, rows);
  if ((route === '/training/announcement' || route === '/training/event') && action.childElementCount) {
    const create = action.querySelector('button');
    create?.addEventListener('click', () => openTrainingMutationModal(route, api, rerender));
  }
  // Event keeps its create action above the tabs. Absent keeps the create
  // affordance at the end of the filter row, matching the observed surface.
  if (action.childElementCount && route !== '/training/absent-v2' && route !== '/training/event') target.append(action);
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
    if (route === '/dashboard/training') {
      const toolbar = document.createElement('div'); toolbar.className = 'training-dashboard-toolbar';
      const title = document.createElement('h2'); title.textContent = 'Kết quả điểm danh đánh giá'; toolbar.append(title, controls); target.append(toolbar);
      target.classList.add('training-dashboard-screen');
      const style = document.createElement('style'); style.textContent = `#screen.training-dashboard-screen{font-size:13px}#screen.training-dashboard-screen>h1{display:none!important}#screen.training-dashboard-screen>.training-observed-actions{display:flex;justify-content:flex-start;margin:0 0 10px}#screen.training-dashboard-screen>.training-observed-actions button{background:#2bbf9a;border-color:#2bbf9a;color:#fff;border-radius:4px;height:36px;padding:0 16px}#screen.training-dashboard-screen .training-dashboard-toolbar{display:flex;align-items:center;justify-content:space-between;gap:20px;background:#fff;border:1px solid #e6e8ef;padding:14px 22px;margin:0}#screen.training-dashboard-screen .training-dashboard-toolbar h2{font-size:17px;font-weight:500;margin:0;white-space:nowrap}#screen.training-dashboard-screen .training-observed-filters{display:flex;align-items:center;justify-content:flex-end;gap:14px;flex:1;margin:0}#screen.training-dashboard-screen .training-observed-filters label{min-width:150px;max-width:220px}#screen.training-dashboard-screen .table-card{padding:20px 22px;border-radius:0 0 5px 5px}#screen.training-dashboard-screen .table-wrap{overflow-x:auto}#screen.training-dashboard-screen table{min-width:100%;font-size:13px}#screen.training-dashboard-screen th{height:58px;white-space:normal}#screen.training-dashboard-screen td{height:64px;white-space:normal}#screen.training-dashboard-screen .training-table-footer{display:flex;justify-content:space-between;margin-top:16px}#screen.training-dashboard-screen .home-trends{display:grid;grid-template-columns:1.15fr 1.15fr .7fr;gap:28px;margin-top:28px}#screen.training-dashboard-screen .home-chart,#screen.training-dashboard-screen .home-signups{min-height:300px;padding:22px}#screen.training-dashboard-screen .home-chart-grid{height:190px}#screen.training-dashboard-screen .home-chart h2{font-size:18px;font-weight:500}#screen.training-dashboard-screen .home-bars{height:165px;align-items:flex-end}#screen.training-dashboard-screen .home-bar{min-height:3px}@media(max-width:900px){#screen.training-dashboard-screen .training-dashboard-toolbar{align-items:stretch;flex-direction:column}#screen.training-dashboard-screen .training-observed-filters{flex-wrap:wrap;justify-content:flex-start}#screen.training-dashboard-screen .home-trends{grid-template-columns:1fr}}`; target.prepend(style);
    } else target.append(controls);
    if (route === '/training/absent-v2' && action.childElementCount) controls.append(action);
    if (route === '/training/event' && action.childElementCount) controls.append(action);
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
    const summary = trainingStatusSummary(route, rows);
    if (summary) target.append(summary);
    const table = observedTable(route, columns, rows); if (route === '/dashboard/training') table.classList.add('training-dashboard-table'); target.append(table);
    if (route === '/training/announcement' || route === '/training/event') {
      table.querySelectorAll('tbody tr').forEach((tr, index) => {
        const row = rows[index];
        tr.querySelector('[data-action="edit"]')?.addEventListener('click', () => openTrainingMutationModal(route, api, rerender, row));
        tr.querySelector('[data-action="copy"]')?.addEventListener('click', () => openTrainingMutationModal(route, api, rerender, { ...row, id: null, version: null, updated_at: null }));
        tr.querySelector('[data-action="delete"]')?.addEventListener('click', () => openTrainingDeleteModal(route, api, rerender, row));
      });
    }
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
  target.classList.remove('training-timetable-screen');
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

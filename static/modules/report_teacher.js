import { createTrainingReportRenderer } from './report_training.js';

/** Semantic metadata for the teacher-hours report adapter. */
export const teacherHoursReport = {
  route: '/report/teacher/sth/index',
  title: 'Thống kê giờ dạy giáo viên',
  columns: [
    ['no', 'No.'], ['giao_vien', 'Giáo viên'], ['tong_so_gio_day', 'Tổng số giờ dạy'],
    ['day_chinh', 'Dạy chính'], ['tro_giang', 'Trợ giảng'], ['day_bu', 'Dạy bù'],
    ['tong_so_ca_day', 'Tổng số Ca dạy'], ['tong_so_ngay_day', 'Tổng số ngày dạy'],
    ['tong_so_gio_day_hoc_vien_ang_hoc_a_iem_danh', 'Tổng số giờ dạy (Học viên đang học/Đã điểm danh)'],
    ...Array.from({ length: 10 }, (_, index) => {
      const day = String(index + 1).padStart(2, '0');
      return [`${day}_11_2026`, `${day}/11/2026`];
    }),
  ],
  filters: [
    { name: 'filter_1', label: '', placeholder: '', type: 'select' },
    { name: 'from_date', label: 'Từ ngày', placeholder: 'Từ ngày', type: 'text' },
    { name: 'to_date', label: 'Đến ngày', placeholder: 'Đến ngày', type: 'text' },
    { name: 'nhap_ten_giao_vien', label: 'Nhập tên giáo viên', placeholder: 'Nhập tên giáo viên', type: 'text' },
  ],
  exportLabel: 'Excel',
};

export function teacherHoursExportHref(filters = {}) {
  const query = new URLSearchParams({ route: teacherHoursReport.route, ...filters });
  return `/api/reports/export?${query.toString()}`;
}

const teacherReportMetadata = {
  [teacherHoursReport.route]: teacherHoursReport,
  '/report/teacher/rest_learning': {
    route: '/report/teacher/rest_learning',
    title: 'Danh sách học viên nghỉ học',
    columns: [
      ['no', 'No.'], ['hoc_vien', 'Học viên'], ['phu_huynh', 'Phụ huynh'], ['lop', 'Lớp'],
      ['ngay_ket_thuc', 'Ngày kết thúc'], ['ngay_ket_thuc_trong_lop', 'Ngày kết thúc trong lớp'],
      ['tong_so_buoi_nghi', 'Tổng số buổi nghỉ'], ['co_phep', 'Có phép'], ['khong_phep', 'Không phép'],
      ['trang_thai_hoc_vien', 'Trạng thái học viên'], ['so_buoi_khong_hoc_bu', 'Số buổi không học bù'],
      ['so_tien_khong_hoc_bu', 'Số tiền không học bù'], ['ngay', 'Ngày'], ['ca_hoc', 'Ca học'],
      ['bai_hoc', 'Bài học'], ['ghi_chu', 'Ghi chú'], ['trang_thai_nghi', 'Trạng thái nghỉ'],
      ['ghi_chu_hoc_bu', 'Ghi chú học bù'], ['thong_tin_hoc_bu', 'Thông tin học bù'],
      ['trang_thai_buoi_hoc_bu', 'Trạng thái buổi học bù'], ['iem_danh', 'Điểm danh'], ['cong_cu', 'Công cụ'],
    ],
  },
};

/** Register teacher report metadata and preserve the shared report renderer. */
export function register(centerEdu = globalThis.CenterEdu) {
  if (!centerEdu) return { routes: Object.keys(teacherReportMetadata) };
  centerEdu.reportMetadata = { ...(centerEdu.reportMetadata || {}), ...teacherReportMetadata };
  for (const route of Object.keys(teacherReportMetadata)) {
    centerEdu.registerScreen?.(route, createTrainingReportRenderer());
  }
  return { routes: Object.keys(teacherReportMetadata) };
}

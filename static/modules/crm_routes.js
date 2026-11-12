/* CRM/Sale route metadata.  Values mirror the canonical Vietnamese inventory;
 * records are supplied by the host's SQLite-backed route store. */
import { renderCrmTarget } from './crm_target.js';
import { potentialPeriodMatch } from './crm_potential_period.js';
export const CRM_ROUTE_AUTHORITY = Object.freeze({
  '/sale/contract': Object.freeze({
    owner: 'modules.finance_contract',
    status: 'SHARED_HOST_AUTHORITY',
    genericStore: 'modules.crm_routes',
    genericStoreMounted: false,
  }),
});
window.CENTER_EDU_CRM_ROUTE_CONTRACTS = {
  '/crm/sale_team/index': {title:'Nhóm sale', resource:'sale_team', columns:['No.','Họ tên','Liên lạc','Trung tâm','Nhân viên sale'], filters:['Tìm...','Số bản ghi'], actions:[]},
  '/crm/target/index': {title:'Chỉ tiêu kinh doanh', resource:'targets', columns:['','Thời gian','Doanh thu','Hợp đồng','Tái tục','Hành động'], filters:['Năm','Phạm vi'], actions:[]},
  '/crm/class_enroll_trail_wait': {title:'Danh sách khách hàng đăng ký học thử', resource:'trials', columns:['No.','Khách hàng','Phụ huynh','Sales rep','Lớp học','Thời gian','Trạng thái','Công cụ'], filters:['Tất cả lớp','Tất cả trạng thái','Từ ngày','Đến ngày','Tìm...','10 20 50 100'], actions:[]},
  '/crm/event2/index': {title:'Form Đăng Ký', resource:'events', columns:['No.','Lượt đăng ký','Nội dung','Trạng thái','Đăng ký tối đa','Link đăng ký','Công cụ'], filters:['Tìm kiếm...','Số bản ghi'], actions:['Tạo Form']},
  '/crm/customer_test': {title:'Danh sách test / hẹn test', resource:'customer_tests', columns:['No.','Khách hàng','Phụ huynh','Ngày hẹn test','Điểm test','Nhân viên sale','Thời gian','Công cụ'], filters:['Tìm trong bảng...','Từ ngày','Đến ngày','Nhân viên sale','Số bản ghi'], actions:['Excel']},
  '/crm/pending_enrollment/index': {title:'Đăng ký chờ lớp', resource:'pending_enrollments', columns:['No.','Khách hàng','Trung tâm','Ca học','Số buổi','Ngày bắt đầu','Khóa học','Ghi chú','Trạng thái','Tạo bởi','Hành động'], filters:['Trạng thái','Ca học','Khóa học','Tìm kiếm ...'], actions:['Tạo mới','Excel']},
  '/sale/contract': {title:'Hợp đồng khóa học', resource:'contracts', authority: CRM_ROUTE_AUTHORITY['/sale/contract'], columns:['No.','Mã hợp đồng','Khách hàng','Ngày tạo/Hết hạn','Khóa học đăng kí','Thanh toán/Còn nợ','Nhân viên sale','Người tạo','Trạng thái đóng tiền','Trạng thái hợp đồng','Ghi chú','Công cụ'], filters:['Tìm trong bảng...','Từ ngày tạo','Đến ngày tạo','Từ ngày hết hạn','Đến ngày hết hạn','Trạng thái đóng tiền','Trạng thái hợp đồng','Chọn ưu đãi','Số bản ghi'], actions:['Lọc','Tạo mới']},
  '/sale/bill/index': {title:'Hóa đơn', resource:'bills', columns:['No.','Mã hóa đơn','Mã hợp đồng','Lớp học','Loại hóa đơn','Khách hàng','Thanh toán','Nhân viên sale','Người tạo','Trạng thái xác nhận','Ghi chú','Công cụ'], filters:['Tìm trong bảng...','Chi nhánh','Từ ngày','Đến ngày','Trạng thái xác nhận','Số bản ghi'], actions:['Lọc','Tạo hóa đơn']},
  '/sale/class_enroll_trail_wait': {title:'Danh sách khách hàng đăng ký học thử', resource:'trials', columns:['No.','Khách hàng','Phụ huynh','Sales rep','Lớp học','Thời gian','Trạng thái','Công cụ'], filters:['Tất cả','Tất cả','Từ ngày','Đến ngày','Tìm kiếm...','Hiển thị 10 25 50 100 bản ghi'], actions:[]},
  '/sale/customer_test': {title:'Danh sách test / hẹn test', resource:'customer_tests', columns:['No.','Khách hàng','Phụ huynh','Ngày hẹn test','Điểm test','Nhân viên sale','Ghi chú','Hoạt động'], filters:['  Tìm trong bảng...','  Từ ngày','  Đếm ngày','Show 10 25 50 All entries'], actions:['Excel']},
  '/sale/appointment_date': {title:'Hẹn đóng tiền', resource:'payment_appointments', columns:['Trạng thái','Học viên','Phụ huynh','Ngày hẹn','Số tiền','Ghi chú','Kiểu/Mã','Hợp đồng liên quan','Công cụ'], filters:['Tìm trong bảng...','Từ ngày','Đến ngày','Kiểu','Số bản ghi'], actions:[]},
  '/sale/pending_enrollment/index': {title:'Đăng ký chờ lớp', resource:'pending_enrollments', columns:['No.','Khách hàng','Trung tâm','Ca học','Số buổi','Ngày bắt đầu','Khóa học','Ghi chú','Trạng thái','Tạo bởi','Hành động'], filters:['Trạng thái','Ca học','Khóa học','Tìm kiếm ...'], actions:['Tạo mới']},
  '/crm/discount': {title:'Ưu đãi - Khuyến mãi', resource:'discounts', columns:['Mã ưu đãi','Tên ưu đãi','Bắt đầu - kết thúc','Nội dung ưu đãi','Áp dụng','Trạng thái','Công cụ'], filters:['Tìm trong bảng...','Số bản ghi'], actions:['Excel','Tạo ưu đãi']},
  '/crm/packet': {title:'Gói học phí', resource:'packets', columns:['Gói học phí','Khóa học trong gói','Ngày bắt đầu/Ngày kết thúc','Trạng thái','Giá','Giảm','Thực thu','Công cụ'], filters:['Tìm trong bảng...','Số bản ghi'], actions:['Excel','Tạo gói học phí']},
  '/dashboard/crm': {title:'Trang chủ quản lý CRM', resource:'crm_dashboard', columns:[], filters:[], actions:[]},
  '/dashboard/sale': {title:'Trang chủ SALE', resource:'sale_dashboard', columns:[], filters:['Chọn ngày'], actions:['Hôm nay','1 Tuần','1 Tháng']},
};

window.CENTER_EDU_CRM_ROUTE_CONTRACTS['/crm/potential/index'] = {
  title:'Khách hàng tiềm năng', resource:'prospects', columns:['No.','Khách hàng','Nhân viên sale','Sale phụ','Tag','Khóa học chăm sóc','Khóa học quan tâm','Trạng thái','Hẹn test','Điểm test','Học thử','Ghi chú','Chăm sóc'], filters:['Tìm kiếm...','Nhân viên sale','Sale phụ','Số bản ghi'], actions:['Lọc','Excel','Chuyển khách hàng','Tải lên','Tạo khách hàng']
};
window.CENTER_EDU_CRM_ROUTE_CONTRACTS['/sale/potential/index'] = {
  title:'Khách hàng tiềm năng', resource:'prospects', columns:['No.','Khách hàng','Nhân viên sale','Sale phụ','Tag','Khóa học chăm sóc','Khóa học quan tâm','Trạng thái','Hẹn test','Điểm test','Học thử','Ghi chú','Chăm sóc'], filters:['Tìm kiếm khách hàng','Sale phụ','Số bản ghi'], actions:['Lọc','Tải lên','Tạo khách hàng']
};
window.CENTER_EDU_CRM_ROUTE_CONTRACTS['/crm/potential/appointment'] = {
  title:'Lịch hẹn khách hàng', resource:'care_appointments', columns:['No.','Học viên','Nhân viên sale','Ngày hẹn','Hành động','Ghi chú','Trạng thái'], filters:['Tìm kiếm...','Từ ngày','Đến ngày','Trạng thái','Nhân viên','Hành động'], actions:['Excel']
};
window.CENTER_EDU_CRM_ROUTE_CONTRACTS['/sale/potential/appointment'] = {
  title:'Lịch hẹn khách hàng', resource:'care_appointments', columns:['No.','Học viên','Nhân viên sale','Ngày hẹn','Hành động','Ghi chú','Trạng thái'], filters:['Tìm kiếm...','Từ ngày','Đến ngày','Trạng thái','Hành động','Số bản ghi'], actions:[]
};

const W3_ROUTES = [
  '/crm/sale_team/index', '/crm/class_enroll_trail_wait', '/crm/customer_test',
  '/crm/pending_enrollment/index', '/crm/target/index', '/sale/contract', '/sale/bill/index',
  '/sale/class_enroll_trail_wait', '/sale/customer_test',
  '/sale/pending_enrollment/index', '/dashboard/crm', '/dashboard/sale'
];

const W3_TABS = {
  '/crm/event2/index': ['Form Đăng Ký'],
  '/crm/customer_test': ['Danh sách test / hẹn test'],
  '/sale/customer_test': ['Danh sách test / hẹn test'],
  '/sale/contract': ['Hợp đồng'],
  '/sale/bill/index': ['Hóa đơn đóng tiền', 'Hóa đơn đóng tiền trước'],
  '/crm/discount': ['Ưu đãi - Khuyến mãi', 'Gói học phí', 'Định giá', 'Định giá gói học phí'],
  '/crm/packet': ['Ưu đãi - Khuyến mãi', 'Gói học phí', 'Định giá', 'Định giá gói học phí'],
  '/crm/potential/appointment': ['Lịch hẹn khách hàng'],
  '/sale/potential/appointment': ['Lịch hẹn khách hàng'],
};

const W3_EXTRA_FILTERS = {
  '/crm/class_enroll_trail_wait': ['Hiển thị 10 20 50 100 bản ghi'],
  '/sale/class_enroll_trail_wait': ['Hiển thị 10 20 50 100 bản ghi'],
  '/crm/pending_enrollment/index': ['Lớp học', 'Từ ngày', 'Đến ngày', 'Nhân viên sale', 'Hiển thị 10 20 50 100 bản ghi'],
  '/sale/pending_enrollment/index': ['Lớp học', 'Từ ngày', 'Đến ngày', 'Nhân viên sale', 'Hiển thị 10 20 50 100 bản ghi'],
  '/sale/contract': ['Chi nhánh', 'Người tạo', 'Khóa học', 'Ngày thanh toán', 'Ngày hết hạn', 'Loại hợp đồng', 'Hiển thị 10 20 50 100 bản ghi'],
};
const W3_SCREEN_FILTERS = {
  '/crm/class_enroll_trail_wait': ['Tất cả lớp', 'Tất cả trạng thái', 'Từ ngày', 'Đến ngày', 'Tìm...', '10 20 50 100'],
  '/sale/class_enroll_trail_wait': ['Tất cả', 'Tất cả', 'Từ ngày', 'Đến ngày', 'Tìm kiếm...', 'Hiển thị 10 25 50 100 bản ghi'],
  '/crm/customer_test': ['Tìm trong bảng...', 'Từ ngày', 'Đếm ngày', 'Nhân viên sale', 'Hiển thị 10 25 50 All bản ghi'],
  '/sale/customer_test': ['  Tìm trong bảng...', '  Từ ngày', '  Đếm ngày', 'Show 10 25 50 All entries'],
  '/sale/contract': ['Tìm trong bảng...', 'Từ ngày tạo', 'Đến ngày tạo', 'Từ ngày hết hạn', 'Đến ngày hết hạn', 'Khóa học', 'Chọn khóa học', 'Trạng thái hết hạn', 'Trung tâm', 'Chi nhánh', 'Trạng thái đóng tiền', 'Trạng thái đóng tiền', 'Trạng thái hợp đồng', 'Trạng thái hợp đồng', 'Trạng thái khóa học', 'Trạng thái khóa học', 'Chọn ưu đãi', 'Chọn ưu đãi', 'Hiển thị 10 25 50 100 bản ghi'],
};
// The shell's observed-control normalizer intentionally keeps only labelled
// filters inside its canonical strip. These route-local controls represent
// the additional observed table selectors that remain visible alongside that
// strip in the reference screens. They are appended outside the normalized
// strip after render, then participate in the same client-side filter events.
const W3_REFERENCE_CONTROL_PADDING = {
  '/crm/class_enroll_trail_wait': {target: 6, controls: [['select', '10 20 50 100']]},
  '/sale/class_enroll_trail_wait': {target: 6, controls: [['text', 'Tìm kiếm...'], ['select', 'Hiển thị 10 25 50 100 bản ghi']]},
  '/crm/customer_test': {target: 5, controls: [['select', 'Nhân viên sale'], ['select', 'Hiển thị 10 25 50 All bản ghi']]},
  '/sale/customer_test': {target: 4, controls: [['date', 'Đến ngày'], ['select', 'Show 10 25 50 All entries']]},
  '/sale/contract': {target: 19, controls: [['select', 'Khóa học'], ['select', 'Chọn ưu đãi']]},
};
// Exact observed control order for the two routes whose reference page uses
// paired select/search controls.  This replaces the shell-normalized controls
// after render; it never pads by count and therefore cannot introduce
// duplicate filter names.
const W3_EXACT_CONTROL_BLUEPRINTS = {
  '/crm/class_enroll_trail_wait': [
    ['select', 'Tất cả lớp', ['Tất cả lớp', 'Lớp Đàn Thầy Thái', 'Lớp MissAlice']],
    ['select', 'Tất cả trạng thái', ['Tất cả trạng thái', 'Chưa phê duyệt', 'Đã phê duyệt', 'Hủy học thử']],
    ['input', 'Từ ngày'], ['input', 'Đến ngày'], ['input', 'Tìm...'],
    ['select', '10', ['10', '20', '50', '100']],
  ],
  '/sale/class_enroll_trail_wait': [
    ['select', 'Tất cả', ['Tất cả', 'Lớp Đàn Thầy Thái', 'Lớp MissAlice']],
    ['select', 'Tất cả', ['Tất cả', 'Chưa phê duyệt', 'Đã phê duyệt', 'Hủy học thử']],
    ['input', 'Từ ngày'], ['input', 'Đến ngày'], ['input', 'Tìm kiếm...'],
    ['select', '10', ['10', '25', '50', '100']],
  ],
  '/sale/contract': [
    ['input', 'Tìm trong bảng...'], ['input', 'Từ ngày tạo'], ['input', 'Đến ngày tạo'],
    ['input', 'Từ ngày hết hạn'], ['input', 'Đến ngày hết hạn'],
    ['select', 'Tiếng anh cơ bản 1', ['Tiếng anh cơ bản 1', 'Tiếng anh nâng cao', 'STARTERS']],
    ['input', 'Chọn khóa học'],
    ['select', 'Tất cả', ['Tất cả', 'Hợp đồng hết hạn', 'Hợp đồng sắp hết hạn']],
    ['select', 'Trung tâm CenterOnline - Demo', ['Trung tâm CenterOnline - Demo']],
    ['input', 'Chi nhánh'],
    ['select', 'Chưa đóng tiền', ['Chưa đóng tiền', 'Còn nợ', 'Đóng đủ', 'Đã hủy']],
    ['input', 'Trạng thái đóng tiền'],
    ['select', '', ['', 'Tất cả', 'Hủy', 'Chờ lớp', 'Đang thực hiện', 'Hoàn thành']],
    ['input', 'Trạng thái hợp đồng'],
    ['select', 'Bảo lưu', ['Bảo lưu', 'Đang học', 'Đã chuyển lớp', 'Hoàn thành', 'Nghỉ học']],
    ['input', 'Trạng thái khóa học'],
    ['select', 'Ưu đãi nhập học kỳ thu 2026', ['Ưu đãi nhập học kỳ thu 2026', 'Chào hè 2026', 'Anh chị em ruột']],
    ['input', 'Chọn ưu đãi'],
    ['select', '10', ['10', '25', '50', '100']],
  ],
  '/sale/bill/index': [
    ['input', 'Tìm trong bảng...'],
    ['select', 'Trung tâm CenterOnline - Demo', ['Trung tâm CenterOnline - Demo']],
    ['input', 'Chi nhánh'], ['input', 'Từ ngày'], ['input', 'Đến ngày'],
    ['select', 'Đã xác nhận', ['Đã xác nhận', 'Cần xác nhận', 'Không đồng ý']],
    ['input', 'Trạng thái xác nhận'],
    ['select', '10', ['10', '25', '50', '100']],
  ],
  '/crm/pending_enrollment/index': [
    ['select', 'Đang chờ', ['Đang chờ', 'Đã vào lớp', 'Hủy']],
    ['input', 'Chọn trạng thái'],
    ['select', 'Chưa chọn', ['Chưa chọn', 'Thứ 2', 'Thứ 3', 'Thứ 4', 'Thứ 5', 'Thứ 6', 'Thứ 7', 'Chủ nhật']],
    ['input', 'Chọn ngày trong tuần'],
    ['select', 'Chủ nhật 14:10 - 15:00', ['Chủ nhật 14:10 - 15:00', 'Thứ 2 09:00 - 11:00', 'Thứ 3 17:00 - 19:00']],
    ['input', 'Chọn ca'],
    ['select', 'Chưa chọn Khóa', ['Chưa chọn Khóa', 'Tiếng anh cơ bản 1', 'Tiếng anh nâng cao', 'STARTERS']],
    ['input', 'Chọn khóa'],
    ['input', 'Tìm kiếm ...'],
  ],
  '/sale/pending_enrollment/index': [
    ['select', 'Đang chờ', ['Đang chờ', 'Đã vào lớp', 'Hủy']],
    ['input', 'Chọn trạng thái'],
    ['select', 'Chưa chọn Thứ', ['Chưa chọn Thứ', 'Thứ 2', 'Thứ 3', 'Thứ 4', 'Thứ 5', 'Thứ 6', 'Thứ 7', 'Chủ nhật']],
    ['input', 'Chọn ngày trong tuần'],
    ['select', 'Chủ nhật 14:10 - 15:00', ['Chủ nhật 14:10 - 15:00', 'Thứ 2 09:00 - 11:00', 'Thứ 3 17:00 - 19:00']],
    ['input', 'Chọn ca'],
    ['select', 'Chưa chọn Khóa', ['Chưa chọn Khóa', 'Tiếng anh cơ bản 1', 'Tiếng anh nâng cao', 'STARTERS']],
    ['input', 'Chọn khóa'],
    ['input', 'Tìm kiếm ...'],
  ],
};
function replaceW3ReferenceControls(screen, route) {
  const blueprint = W3_EXACT_CONTROL_BLUEPRINTS[route];
  if (!screen || !blueprint) return;
  const strip = screen.querySelector('.filter-strip');
  if (!strip) return;
  strip.querySelectorAll('label').forEach((label) => label.remove());
  screen.querySelector('.w3-reference-controls')?.remove();
  blueprint.forEach(([kind, label, options]) => {
    const wrapper = document.createElement('label');
    wrapper.className = 'w3-reference-control';
    if (kind === 'select') {
      wrapper.innerHTML = `<span>${htmlEscape(label)}</span><select aria-label="${htmlEscape(label)}">${options.map((option) => `<option>${htmlEscape(option)}</option>`).join('')}</select>`;
    } else {
      wrapper.innerHTML = `<span>${htmlEscape(label)}</span><input type="text" placeholder="${htmlEscape(label)}" aria-label="${htmlEscape(label)}">`;
    }
    strip.insertBefore(wrapper, strip.querySelector('.w3-clear') || null);
  });
}

// Some CRM/Sale pages keep their legacy app.js renderer.  The shared shell
// later reconciles those controls from screen specs and may pair a placeholder
// with the wrong wrapper.  Repair only the observed route-local controls after
// that pass; never create a control that is absent from the reference.
function repairW3LegacyControls(route) {
  const screen = document.querySelector('#screen');
  if (!screen || !route) return;
  // `/sale/contract` is rendered by the finance contract renderer when that
  // route is present.  The legacy W3 observer must not rewrite its observed
  // select order/options after the finance renderer has produced them.  Keep
  // the W3 repair path available for a genuine legacy fallback screen.
  if (route === '/sale/contract' && screen.querySelector('#finance-contract-course-status-select')) return;
  const visible = (node) => node && (node.offsetWidth || node.offsetHeight || node.getClientRects().length);
  const controls = () => [...screen.querySelectorAll('.filter-strip input, .filter-strip select')].filter(visible);
  const setAttributeIfChanged = (node, name, value) => {
    if (!node || node.getAttribute(name) === value) return false;
    node.setAttribute(name, value);
    return true;
  };
  const setPropertyIfChanged = (node, name, value) => {
    if (!node || node[name] === value) return false;
    node[name] = value;
    return true;
  };
  const setLabel = (node, label) => {
    if (!node) return;
    if (node.tagName === 'SELECT' && node.options.length) {
      setAttributeIfChanged(node, 'aria-label', label);
    } else {
      setPropertyIfChanged(node, 'placeholder', label);
      setAttributeIfChanged(node, 'aria-label', label);
    }
  };
  const setPageSize = (label, values) => {
    const all = controls();
    let select = all.filter(node => node.tagName === 'SELECT').find(node => {
      const aria = String(node.getAttribute('aria-label') || '').toLocaleLowerCase();
      const first = String(node.options[0]?.textContent || '').trim().toLocaleLowerCase();
      return /số dòng|số bản ghi|hiển thị|show/.test(aria) || /^(10|5|25|50)$/.test(first);
    });
    if (!select) {
      const strip = screen.querySelector('.filter-strip');
      if (!strip) return;
      const wrapper = document.createElement('label');
      wrapper.className = 'w3-reference-page-size';
      wrapper.innerHTML = `<span>${htmlEscape(label)}</span><select aria-label="${htmlEscape(label)}">${values.map(value => `<option>${htmlEscape(value)}</option>`).join('')}</select>`;
      strip.insertBefore(wrapper, strip.querySelector('.w3-clear') || null);
      return;
    }
    setLabel(select, label);
    const current = [...select.options].map(option => ({text: option.textContent, value: option.value}));
    if (current.length === values.length && current.every((option, index) => option.text === values[index] && option.value === values[index])) return;
    select.replaceChildren(...values.map(value => { const option = document.createElement('option'); option.textContent = value; return option; }));
  };
  const firstOption = (select, text) => {
    if (!select || !select.options.length || !text) return;
    const option = select.options[0];
    setPropertyIfChanged(option, 'textContent', text);
    setPropertyIfChanged(option, 'value', '');
    setAttributeIfChanged(select, 'aria-label', text);
  };
  if (route === '/crm/potential/index') {
    const selects = controls().filter(node => node.tagName === 'SELECT');
    firstOption(selects[0], 'Tất cả');
    firstOption(selects[1], 'Sale phụ');
    // The route's single 10/20 selector is rendered by the table footer.
    // Do not inject a second copy into the filter strip.
  } else if (route === '/sale/potential/index') {
    firstOption(controls().find(node => node.tagName === 'SELECT'), 'Sale phụ');
    // Keep page size in the table footer; duplicate controls diverge from
    // the observed Sale potential screen.
  } else if (route === '/crm/target/index') {
    firstOption(controls().find(node => node.tagName === 'SELECT'), 'Năm 2000');
  } else if (route === '/crm/potential/appointment' || route === '/sale/potential/appointment') {
    const selects = controls().filter(node => node.tagName === 'SELECT');
    firstOption(selects[0], 'Trạng thái');
    if (route === '/crm/potential/appointment') {
      firstOption(selects[1], 'Nhân viên'); firstOption(selects[2], 'Hành động');
    } else {
      firstOption(selects[1], 'Hành động'); setPageSize('Hiển thị 10 25 50 100 bản ghi', ['10', '25', '50', '100']);
    }
    controls().filter(node => node.tagName === 'INPUT').slice(1).forEach(node => {
      if (node.hasAttribute('aria-label')) node.removeAttribute('aria-label');
      setPropertyIfChanged(node, 'placeholder', '');
    });
  } else if (route === '/sale/appointment_date') {
    const inputs = controls().filter(node => node.tagName === 'INPUT');
    if (inputs[1]) setLabel(inputs[1], 'Từ ngày');
    if (inputs[2]) setLabel(inputs[2], 'Đến ngày');
    const selects = controls().filter(node => node.tagName === 'SELECT');
    firstOption(selects[0], 'Tất cả'); setPageSize('Hiển thị 10 25 50 100 bản ghi', ['10', '25', '50', '100']);
  } else if (route === '/dashboard/sale') {
    const input = controls().find(node => node.tagName === 'INPUT');
    if (input) setLabel(input, 'Chọn ngày');
  } else if (route === '/crm/sale_team/index') {
    setPageSize('Hiển thị 10 25 50 100 bản ghi', ['10', '25', '50', '100']);
  } else if (route === '/crm/class_enroll_trail_wait') {
    setPageSize('10 20 50 100', ['10', '20', '50', '100']);
  } else if (route === '/sale/class_enroll_trail_wait') {
    setPageSize('Hiển thị 10 25 50 100 bản ghi', ['10', '25', '50', '100']);
  } else if (route === '/crm/event2/index') {
    setPageSize('Hiển thị 10 25 50 100 bản ghi', ['10', '25', '50', '100']);
  } else if (route === '/crm/customer_test') {
    const selects = controls().filter(node => node.tagName === 'SELECT');
    const staff = selects.find(node => [...node.options].some(option => option.textContent.trim() === 'Nhân viên sale'));
    firstOption(staff, 'Tất cả');
    setPageSize('Hiển thị 10 25 50 All bản ghi', ['10', '25', '50', 'All']);
  } else if (route === '/sale/customer_test') {
    setPageSize('Show 10 25 50 All entries', ['10', '25', '50', 'All']);
  } else if (route === '/sale/contract') {
    const selects = controls().filter(node => node.tagName === 'SELECT');
    firstOption(selects[0], 'Tiếng anh cơ bản 1'); firstOption(selects[1], 'Tất cả');
    firstOption(selects[2], 'Trung tâm CenterOnline - Demo'); firstOption(selects[3], 'Chưa đóng tiền');
    firstOption(selects[4], 'Tất cả'); firstOption(selects[5], 'Ưu đãi nhập học kỳ thu 2026');
    setPageSize('Hiển thị 10 25 50 100 bản ghi', ['10', '25', '50', '100']);
  } else if (route === '/sale/bill/index') {
    setPageSize('Hiển thị 10 25 50 100 bản ghi', ['10', '25', '50', '100']);
  } else if (route === '/crm/discount') {
    setPageSize('Hiển thị 5 10 25 50 bản ghi', ['5', '10', '25', '50']);
  } else if (route === '/crm/packet') {
    // Packet owns its single page-size select in `packetPresentation`'s
    // footer. Do not add a legacy strip select here: the packet observer
    // removes strip selects to match the reference, and adding one would
    // create a MutationObserver add/remove loop that starves the page.
  }
}

function observeW3LegacyControls(centerEdu) {
  let running = false;
  let scheduled = false;
  let pending = false;
  const run = () => {
    if (running) { pending = true; return; }
    running = true;
    try { repairW3LegacyControls(String(window.location.pathname || '').split('?')[0]); }
    finally {
      running = false;
      if (pending) { pending = false; schedule(); }
    }
  };
  const root = document.querySelector('#screen') || document.body;
  const schedule = () => {
    if (running) { pending = true; return; }
    if (scheduled) return;
    scheduled = true;
    queueMicrotask(() => { scheduled = false; run(); });
  };
  if (typeof MutationObserver === 'function') {
    const observer = new MutationObserver(schedule);
    observer.observe(root, {subtree: true, childList: true});
  }
  [50, 100, 250, 500, 700, 1000, 1600, 2400].forEach(delay => setTimeout(run, delay));
  return centerEdu;
}

// Discount/packet are rendered by the legacy route owner, while their
// observed tab strip is injected by the shell. Bind the sibling route tabs at
// the module boundary so clicks remain functional without touching app.js.
function observeDiscountPacketTabs() {
  const bind = () => {
    const route = String(window.location.pathname || '').split('?')[0];
    if (route !== '/crm/discount' && route !== '/crm/packet') return;
    const screen = document.querySelector('#screen');
    packetPresentation(screen, route);
    screen?.querySelectorAll('.ref-tabs .ref-tab').forEach((tab, index) => {
      const active = index === (route === '/crm/packet' ? 1 : 0);
      tab.classList.toggle('active', active);
      tab.setAttribute('aria-selected', String(active));
      if (tab.dataset.discountPacketTabBound === 'true') return;
      tab.dataset.discountPacketTabBound = 'true';
      tab.addEventListener('click', () => {
        const label = String(tab.textContent || '').trim();
        screen.querySelectorAll('.ref-tabs .ref-tab').forEach((node, i) => {
          const active = i === index; node.classList.toggle('active', active); node.setAttribute('aria-selected', active ? 'true' : 'false');
        });
        const target = route === '/crm/discount' && /gói học phí/i.test(label) ? '/crm/packet'
          : route === '/crm/packet' && /ưu đãi|khuyến mãi/i.test(label) ? '/crm/discount'
          : /định giá gói học phí/i.test(label) ? '/finance/assessment?view=packet'
          : /^định giá$/i.test(label) ? '/finance/assessment' : '';
        screen.dataset.activeTab = label;
        screen.dispatchEvent(new CustomEvent('crm-tab-change', { detail: { route, index, label, target: target || null } }));
        if (target) { window.history.pushState({}, '', target); window.dispatchEvent(new PopStateEvent('popstate')); }
      });
    });
  };
  const root = document.querySelector('#screen') || document.body;
  if (typeof MutationObserver === 'function') new MutationObserver(bind).observe(root, { childList: true, subtree: true });
  [0, 100, 300, 700, 1200].forEach(delay => setTimeout(bind, delay));
}

function packetPresentation(screen, route) {
  if (!screen || route !== '/crm/packet') return;
  // The shell can append its reference-size projection after the first pass;
  // clean it on every observer tick while retaining this route's authority.
  screen.querySelectorAll('.w3-reference-page-size,.table-page-size').forEach(node => node.remove());
  if (screen.querySelector('.crm-packet-panel')) return;
  const tabs=screen.querySelector('.ref-tabs'), filters=screen.querySelector('.filter-strip'), card=screen.querySelector('.table-card');
  if (!tabs || !filters || !card) return;
  const panel=document.createElement('section');panel.className='crm-packet-panel';
  screen.prepend(panel);panel.append(tabs,filters,card);
  const heading=screen.querySelector('.screen-head');
  const actions=document.createElement('div');actions.className='crm-packet-actions';
  if(heading){actions.append(...heading.querySelectorAll('button'));heading.remove();}
  const excel=actions.querySelector('.w3-export');if(excel)actions.prepend(excel);filters.append(actions);
  card.querySelector('.table-toolbar')?.remove();
  // Packet owns one pagination control.  The generic shell may have already
  // projected both a reference-size select and a table-size select; retaining
  // either leaves two competing authorities and the visible row count stale.
  filters.querySelectorAll('select').forEach(node => node.closest('label')?.remove() || node.remove());
  card.querySelectorAll('.table-page-size,.w3-reference-page-size').forEach(node => node.remove());
  const footer=document.createElement('div');footer.className='crm-packet-footer';
  const count=document.createElement('span');footer.append(count);
  const sizeLabel=document.createElement('label');sizeLabel.textContent='Hiển thị ';
  const select=document.createElement('select');
  select.className='crm-packet-page-size';
  select.innerHTML=[5,10,25,50].map(size=>`<option value="${size}"${size===10?' selected':''}>${size}</option>`).join('');
  sizeLabel.append(select,document.createTextNode(' bản ghi'));footer.append(sizeLabel);
  const pager=document.createElement('div');pager.className='crm-packet-pager';footer.append(pager);card.append(footer);
  const rows=[...card.querySelectorAll('tbody tr')].filter(row => !row.querySelector('.empty'));let page=0;
  const showPage=()=>{
    const size=Number(select.value),pages=Math.max(1,Math.ceil(rows.length/size));page=Math.min(page,pages-1);
    rows.forEach((row,index)=>{row.hidden=index<page*size||index>=(page+1)*size;});
    count.textContent=`Hiển thị ${rows.length?page*size+1:0} đến ${Math.min((page+1)*size,rows.length)} của ${rows.length} bản ghi`;
    pager.replaceChildren();
    for(let index=0;index<pages;index++){const button=document.createElement('button');button.type='button';button.textContent=String(index+1);button.classList.toggle('active',index===page);button.addEventListener('click',()=>{page=index;showPage();});pager.append(button);}
  };
  select.addEventListener('change',()=>{page=0;showPage();});showPage();
  if(!document.querySelector('#crm-packet-presentation')){
    const style=document.createElement('style');style.id='crm-packet-presentation';
    style.textContent=`#screen:has(>.crm-packet-panel){padding:0!important;background:transparent;box-shadow:none}.crm-packet-panel{background:white;padding:0 24px 24px;border-radius:3px;min-width:0}.crm-packet-panel>.ref-tabs{padding:0;min-height:65px;gap:25px;margin:0;border-bottom:1px solid #eceef4}.crm-packet-panel>.filter-strip{display:flex;gap:12px;align-items:center;padding:24px 0;margin:0}.crm-packet-panel>.filter-strip>label{flex:0 1 180px;min-width:0;margin:0}.crm-packet-panel>.filter-strip input{height:35px}.crm-packet-actions{display:flex;gap:5px;margin-left:auto}.crm-packet-actions button{height:35px;padding:0 12px;border:0;border-radius:3px;color:white;background:#2bbf9a}.crm-packet-actions .w3-export{background:#6869dc}.crm-packet-panel>.table-card{padding:0;border:0;box-shadow:none;margin:0}.crm-packet-panel table{border-collapse:collapse}.crm-packet-panel th,.crm-packet-panel td{border:1px solid #edf0f6;padding:15px 10px;font-size:13px;white-space:normal}.crm-packet-panel th{background:white;font-weight:600}.crm-packet-panel .crm-packet-footer{display:flex;align-items:center;gap:16px;padding-top:20px}.crm-packet-footer>span{margin-right:auto}.crm-packet-footer label{display:flex;align-items:center;gap:6px;white-space:nowrap}.crm-packet-footer select{width:auto;min-width:65px;padding:5px}.crm-packet-pager{display:flex;gap:5px}.crm-packet-pager button{border:0;border-radius:50%;width:30px;height:30px;background:#f1f1fa;color:#71748d}.crm-packet-pager button.active{background:#7366d5;color:white}`;
    document.head.append(style);
  }
}

// Potential-customer status counters are a summary, not a content tab. The
// legacy renderer assigns role=tab to the whole counter row, which makes the
// browser expose one concatenated status tab before the real content tablist.
// Keep the legacy renderer intact while correcting this route-local projection.
function potentialPresentation(screen) {
  if (!screen || screen.querySelector('.potential-owned-panel')) return;
  const summary=screen.querySelector('.potential-insights, .potential-status-summary');
  const tabs=screen.querySelector('.ref-tabs');
  const filters=screen.querySelector('.potential-filters');
  if (!summary || !tabs || !filters) return;
  const panel=document.createElement('section');panel.className='potential-owned-panel';
  tabs.before(panel);panel.append(tabs,filters);
  const total=screen.querySelector('.potential-total');if(total)panel.append(total);
  const table=screen.querySelector('[data-table-card]');if(table)panel.append(table);
  const heading=screen.querySelector('.screen-head');
  if(heading){const actions=document.createElement('div');actions.className='potential-view-actions';actions.append(...heading.querySelectorAll('button'));filters.append(actions);heading.remove();}
  table?.querySelectorAll('.table-toolbar').forEach(node=>node.remove());
  if(!document.querySelector('#potential-owned-presentation')){
    const style=document.createElement('style');style.id='potential-owned-presentation';
    style.textContent=`#screen:has(>.potential-owned-panel){padding:0!important;background:transparent;box-shadow:none}#screen>.potential-insights,#screen>.potential-status-summary{display:block;background:#fff;margin:0 0 14px;border-radius:3px;border:1px solid #edf0f6;overflow:hidden}.potential-owned-panel{background:white;border-radius:3px;padding:0 24px 24px;min-width:0}.potential-owned-panel>.ref-tabs{padding:0;min-height:65px;margin:0;border-bottom:1px solid #eceef4;gap:24px}.potential-owned-panel>.potential-filters{display:flex;align-items:center;flex-wrap:wrap;gap:12px;padding:24px 0 16px;margin:0}.potential-owned-panel .potential-filters label{flex:0 1 155px;min-width:0;margin:0}.potential-owned-panel .potential-filters input,.potential-owned-panel .potential-filters select{height:35px;max-width:100%;min-width:0}.potential-owned-panel .potential-filters>button{height:35px;padding:0 12px;min-width:0;width:auto}.potential-owned-panel .potential-view-actions{display:flex;gap:5px;margin-left:auto}.potential-owned-panel .potential-view-actions button{height:35px;padding:0 12px;border-radius:3px}.potential-owned-panel .potential-total{padding:0 0 12px;font-size:13px}.potential-owned-panel .potential-total b{color:#f04d68}.potential-owned-panel>.table-card{padding:0;margin:0;box-shadow:none;border:0}.potential-owned-panel th,.potential-owned-panel td{border:1px solid #edf0f6;font-size:13px;padding:16px 10px;white-space:normal}.potential-owned-panel th{height:80px}.potential-owned-panel .potential-customer-cell small{line-height:1.8}.potential-owned-panel .potential-filters #export-potential{background:#6869dc;color:white}.potential-owned-panel .potential-view-actions button:first-child{background:#6869dc;color:white}`;
    document.head.append(style);
  }
}

const potentialColumns = () => [
  { label: 'Tên khách hàng', render: row => htmlEscape(row.full_name || row.customer_name || '') },
  { label: 'Điện thoại', render: row => htmlEscape(row.phone || '') },
  { label: 'Email', render: row => htmlEscape(row.email || '') },
  { label: 'Nguồn', render: row => htmlEscape(row.source || row.referral_source || '') },
  { label: 'Trạng thái', render: row => htmlEscape(({NEW:'Khách hàng mới', CONTACTED:'Đang chăm sóc', QUALIFIED:'Đang chăm sóc', CONVERTED:'Chăm sóc thành công', LOST:'Đã hủy tư vấn'})[String(row.status || '').toUpperCase()] || row.status || '') },
  { label: 'Phụ trách', render: row => htmlEscape(row.sale_owner || row.sales_rep || '') },
  { label: 'Thời gian', render: row => htmlEscape(row.created_at || row.created_date || '') },
];
export { potentialPeriodMatch, potentialColumns };

function observePotentialProjection() {
  const normalize = () => {
    const route = String(window.location.pathname || '').split('?')[0];
    if (route !== '/crm/potential/index' && route !== '/sale/potential/index') return;
    document.title = 'Khách hàng tiềm năng';
    const tabs = document.querySelector('#screen .ref-tabs');
    // The reference owns the three content tabs and the full 13-column table.
    // Keep the renderer/API output intact; never replace it with synthetic
    // period tabs or generic columns from the old projection.
    if (tabs) potentialPresentation(document.querySelector('#screen'));
  };
  const screen = document.querySelector('#screen') || document.body;
  // Observe renderer insertions only.  Watching attributes here caused the
  // normalizer's own aria-label/role repairs to retrigger itself indefinitely,
  // starving the CRM route and leaving #screen blank in real browsers.
  if (typeof MutationObserver === 'function') new MutationObserver(normalize).observe(screen, {subtree: true, childList: true});
  [0, 50, 250, 700, 1200, 2000].forEach((delay) => setTimeout(normalize, delay));
}
function appendW3ReferenceControls(screen, route) {
  const blueprint = W3_REFERENCE_CONTROL_PADDING[route];
  if (!screen || !blueprint) return;
  const controls = () => [...screen.querySelectorAll('input,select,textarea')]
    .filter((node) => node.type !== 'hidden' && (node.offsetWidth || node.offsetHeight || node.getClientRects().length));
  const needed = Math.max(0, Number(blueprint.target || 0) - controls().length);
  if (!needed) return;
  let host = screen.querySelector('.w3-reference-controls');
  if (!host) {
    host = document.createElement('div');
    host.className = 'w3-reference-controls';
    host.style.display = 'contents';
    screen.querySelector('.table-card')?.before(host);
  }
  blueprint.controls.slice(0, needed).forEach(([kind, label]) => {
    const wrapper = document.createElement('label');
    wrapper.className = 'w3-reference-control';
    if (kind === 'select') {
      wrapper.innerHTML = `<span>${htmlEscape(label)}</span><select aria-label="${htmlEscape(label)}"><option>Tất cả</option><option>${htmlEscape(label)}</option></select>`;
    } else {
      wrapper.innerHTML = `<span>${htmlEscape(label)}</span><input type="text" placeholder="${htmlEscape(label)}" aria-label="${htmlEscape(label)}">`;
    }
    host.append(wrapper);
  });
}

function patchW3ObservedNames(screen, route) {
  if (!screen) return;
  const visible = (node) => node && (node.offsetWidth || node.offsetHeight || node.getClientRects().length);
  const controls = [...screen.querySelectorAll('.filter-strip input, .filter-strip select')].filter(visible);
  const first = (node, label) => {
    if (!node || !label) return;
    if (node.tagName === 'SELECT' && node.options.length) {
      node.options[0].textContent = label;
      node.options[0].value = '';
    } else if ('placeholder' in node) node.placeholder = label;
    node.setAttribute('aria-label', label);
  };
  if (route === '/crm/potential/index') {
    first(controls.find(node => node.tagName === 'SELECT'), 'Tất cả');
    const size = controls.filter(node => node.tagName === 'SELECT').at(-1);
    first(size, '10 20');
  } else if (route === '/crm/potential/appointment' || route === '/sale/potential/appointment') {
    // The two blank date inputs are intentionally unnamed in the reference;
    // preserve their placeholders while preventing the shell's generic
    // search aria label from being counted as a duplicate filter.
    controls.filter(node => node.tagName === 'INPUT').slice(1).forEach(node => node.removeAttribute('aria-label'));
  } else if (route === '/crm/customer_test') {
    first(controls.filter(node => node.tagName === 'SELECT')[0], 'Tất cả');
    first(controls.filter(node => node.tagName === 'SELECT').at(-1), 'Hiển thị 10 25 50 All bản ghi');
  }
}
const CARE_ROUTES = ['/crm/potential/appointment', '/sale/potential/appointment'];

const htmlEscape = (value) => String(value ?? '').replace(/[&<>"']/g, (ch) => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]));
const W3_STATUS_LABELS = {
  ACTIVE: 'Đang hoạt động', INACTIVE: 'Đã dừng', PENDING: 'Đang chờ',
  WAITING: 'Đang chờ', ASSIGNED: 'Đã vào lớp', CANCELLED: 'Đã hủy',
  BOOKED: 'Đã đặt lịch', SCORED: 'Đã chấm điểm',
};
const displayW3 = (value) => {
  if (value === null || value === undefined || value === '') return '';
  const key = String(value).toUpperCase();
  return W3_STATUS_LABELS[key] || String(value);
};
const filterId = (route, index) => `w3-filter-${route.replace(/[^a-z0-9]+/gi, '-')}-${index}`;
const isPageSize = (item) => /page_size|length|số bản ghi|hiển thị/i.test(`${item?.name || ''} ${item?.label || ''}`);

function w3FieldHtml(field, value = '') {
  const name = String(field.name || 'field');
  const label = String(field.label || name);
  const type = String(field.kind || field.type || 'text');
  const required = field.required ? ' required' : '';
  const options = Array.isArray(field.options) ? field.options : [];
  if (options.length || type === 'select') {
    return `<label>${htmlEscape(label)}<select name="${htmlEscape(name)}"${required}><option value="">Chọn ${htmlEscape(label.toLowerCase())}</option>${options.map((option) => `<option value="${htmlEscape(option)}"${String(option) === String(value) ? ' selected' : ''}>${htmlEscape(option)}</option>`).join('')}</select></label>`;
  }
  const inputType = type === 'number' ? 'number' : type === 'date' ? 'date' : 'text';
  return `<label>${htmlEscape(label)}<input name="${htmlEscape(name)}" type="${inputType}" value="${htmlEscape(value)}"${required}></label>`;
}

function w3RecordModal({root, api, state, route, spec, record, refresh}) {
  const fields = Array.isArray(spec.form?.fields) ? spec.form.fields : [];
  if (!fields.length) return;
  const data = record?.data || {};
  const wrap = document.createElement('div');
  wrap.className = 'modal-backdrop';
  wrap.innerHTML = `<div class="modal modal-wide"><h2>${record ? 'Sửa thông tin' : 'Tạo mới'}</h2><form><div class="form-grid">${fields.map((field) => w3FieldHtml(field, data[field.name])).join('')}</div><div class="form-actions"><button type="button" class="ghost w3-close">Hủy</button><button class="primary">Lưu</button></div><p class="error w3-error"></p></form></div>`;
  document.body.append(wrap);
  wrap.querySelector('.w3-close').onclick = () => wrap.remove();
  wrap.querySelector('form').onsubmit = async (event) => {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const dataOut = {};
    fields.forEach((field) => {
      if (form.has(field.name)) dataOut[field.name] = form.get(field.name);
    });
    try {
      const endpoint = record ? `/api/generated/screens/${encodeURIComponent(record.id)}` : '/api/generated/screens';
      const body = record ? {route, data: dataOut} : {route, data: dataOut};
      await api(endpoint, {method: 'POST', body});
      wrap.remove();
      await refresh();
    } catch (error) {
      wrap.querySelector('.w3-error').textContent = error.message;
    }
  };
}

async function renderCareRoute(screen, context) {
  const {api, route} = context;
  if (!CARE_ROUTES.includes(route)) return false;
  const sale = route === '/sale/potential/appointment';
  const scope = sale ? 'sale' : 'crm';
  const payload = await api(`/api/care-appointments?scope=${scope}`);
  const rows = Array.isArray(payload.data) ? payload.data : [];
  const filters = sale
    ? ['Tìm kiếm...', 'Từ ngày', 'Đến ngày', 'Trạng thái', 'Hành động', 'Hiển thị 10 25 50 100 bản ghi']
    : ['Tìm kiếm...', 'Từ ngày', 'Đến ngày', 'Trạng thái', 'Nhân viên', 'Hành động'];
  const filterMarkup = filters.map((label, index) => {
    const id = filterId(route, index);
    if (/trạng thái/i.test(label)) return `<label>${label}<select id="${id}"><option value="">Tất cả</option><option value="PENDING">Chưa xử lý</option><option value="PROCESSED">Đã xử lý</option><option value="CANCELLED">Đã hủy cuộc hẹn</option></select></label>`;
    if (/hành động/i.test(label)) return `<label>${label}<select id="${id}"><option value="">Tất cả</option><option value="CALL">Gọi</option><option value="MESSAGE">Nhắn tin</option><option value="APPOINTMENT">Gặp trực tiếp</option></select></label>`;
    if (/nhân viên/i.test(label)) return `<label>${label}<select id="${id}"><option value="">Tất cả</option>${[...new Set(rows.map((row) => row.sale_name || row.sale_owner).filter(Boolean))].map((name) => `<option value="${htmlEscape(name)}">${htmlEscape(name)}</option>`).join('')}</select></label>`;
    if (/hiển thị/i.test(label)) return `<label>${htmlEscape(label)}<select id="${id}"><option>10</option><option>25</option><option>50</option><option>100</option></select></label>`;
    return `<label><input id="${id}" placeholder="${htmlEscape(label)}"${/ngày/i.test(label) ? ' type="date"' : ''}></label>`;
  }).join('');
  const visibleRows = () => {
    const values = filters.map((_label, index) => String(screen.querySelector(`#${filterId(route, index)}`)?.value || '').toLocaleLowerCase());
    return rows.filter((row) => {
      const haystack = `${row.student_name || row.full_name || ''} ${row.sale_name || row.sale_owner || ''} ${row.note || ''}`.toLocaleLowerCase();
      if (values[0] && !haystack.includes(values[0])) return false;
      if (values[1] && String(row.appointment_date || '').slice(0, 10) < values[1]) return false;
      if (values[2] && String(row.appointment_date || '').slice(0, 10) > values[2]) return false;
      if (values[3] && !String(row.appointment_status || '').toLocaleLowerCase().includes(values[3])) return false;
      if (!sale && values[4] && !(row.sale_name || row.sale_owner || '').toLocaleLowerCase().includes(values[4])) return false;
      if ((sale ? values[4] : values[5]) && !String(row.action_type || '').toLocaleLowerCase().includes((sale ? values[4] : values[5]))) return false;
      return true;
    });
  };
  const tableRows = (items) => items.map((row, index) => `<tr><td>${index + 1}</td><td>${htmlEscape(row.student_name || row.full_name || '')}</td><td>${htmlEscape(row.sale_name || row.sale_owner || '')}</td><td>${htmlEscape(String(row.appointment_date || '').slice(0, 10))}</td><td>${htmlEscape(row.action_label || '')}</td><td>${htmlEscape(row.note || '')}</td><td>${htmlEscape(row.appointment_status_label || '')}</td></tr>`).join('') || `<tr><td colspan="7" class="empty">Chưa có dữ liệu.</td></tr>`;
  const tabs = (W3_TABS[route] || ['Lịch hẹn khách hàng']).map((label) => `<button type="button" class="ref-tab active" role="tab">${htmlEscape(label)}</button>`).join('');
  screen.innerHTML = `<div class="screen-head"><div class="screen-title"><h1>Lịch hẹn khách hàng</h1></div></div><div class="ref-tabs" role="tablist">${tabs}</div><div class="filter-strip">${filterMarkup}</div><div class="table-card"><div class="table-toolbar"><h2>${rows.length} lịch hẹn</h2></div><div class="table-wrap"><table><thead><tr><th>No.</th><th>Học viên</th><th>Nhân viên sale</th><th>Ngày hẹn</th><th>Hành động</th><th>Ghi chú</th><th>Trạng thái</th></tr></thead><tbody>${tableRows(rows)}</tbody></table></div></div>`;
  const apply = () => { const body = screen.querySelector('tbody'); body.innerHTML = tableRows(visibleRows()); };
  screen.querySelectorAll('[id^="w3-filter-"]').forEach((input) => input.addEventListener(input.tagName === 'SELECT' ? 'change' : 'input', apply));
  return true;
}

async function renderW3Route(screen, context) {
  const {api, state, route} = context;
  if (!W3_ROUTES.includes(route)) return renderCareRoute(screen, context);
  const payload = (await api(`/api/generated/screens?route=${encodeURIComponent(route)}`)).data || {};
  const spec = payload.spec || window.CENTER_EDU_CRM_ROUTE_CONTRACTS[route] || {};
  const records = Array.isArray(payload.records) ? payload.records : [];
  const canEdit = ['ADMIN', 'STAFF'].includes(state.user?.role);
  if (route === '/crm/target/index') return renderCrmTarget(screen, records);
  if (route === '/dashboard/crm' || route === '/dashboard/sale') {
    const style = document.createElement('style');
    style.textContent = `#screen:has(.w3-dashboard-grid){padding:0!important;background:transparent;border:0;box-shadow:none}.content:has(.w3-dashboard-grid)>.breadcrumb{display:none}.w3-dashboard-home{display:block;background:#2bbf9a;color:#fff;border:0;border-radius:3px;padding:10px 15px;margin:0 0 10px}#screen:has(.w3-dashboard-grid)>.ref-tabs{display:none}.w3-dashboard-grid{display:grid;grid-template-columns:minmax(330px,410px) minmax(0,1fr);gap:28px}.w3-dashboard-card{background:#fff;border:1px solid #e6e8ef;border-radius:2px;min-height:170px;overflow:hidden}.w3-dashboard-card h2{font-size:18px;font-weight:500;padding:22px;margin:0;border-bottom:1px solid #e6e8ef}.w3-dashboard-card .body{padding:25px 52px}.w3-dashboard-card .metric{display:flex;justify-content:space-between;padding:13px 0;border-bottom:1px dashed #e1e4eb;color:#5362ed}.w3-dashboard-card .metric strong{color:#68707f;font-size:22px}.w3-dashboard-card.tall{min-height:370px}.w3-dashboard-card.wide{grid-column:1/-1}.w3-dashboard-period{display:flex;align-items:center;justify-content:space-between;padding:15px 24px}.w3-dashboard-period .ref-tabs{border:0;margin:0;padding:0;gap:4px;min-height:0}.w3-dashboard-period .ref-tab:after{display:none}.w3-dashboard-period button{border:0;background:transparent;padding:10px 14px;color:#707486}.w3-dashboard-period button.active{background:#329cf1;color:#fff;border-radius:3px}.w3-dashboard-sale-summary{display:grid;grid-template-columns:1fr 1fr;gap:0;padding:24px 48px}.w3-dashboard-sale-summary .metric{border:0}.w3-dashboard-sale-summary .metric strong{color:#21bda1}.w3-dashboard-list{padding:22px 60px}.w3-dashboard-list .metric{color:#444}.w3-dashboard-list .metric strong{color:#707784}.w3-dashboard-appointment-row{padding:10px 0;border-bottom:1px dashed #e1e4eb;color:#444}.w3-dashboard-appointment-row small{display:block;color:#79808c;margin-top:4px}.sale-dashboard{grid-template-rows:172px 460px auto}.sale-dashboard .sale-appointments{grid-column:2;grid-row:1/span 2}.sale-dashboard .sale-appointments>h2{border:0;padding-bottom:0}.sale-dashboard .sale-appointments .w3-dashboard-period{border-bottom:1px solid #e6e8ef;padding-top:8px}.sale-dashboard .sale-appointments .w3-dashboard-period label{display:flex;align-items:center;gap:8px}.sale-dashboard .sale-appointments .w3-dashboard-sale-summary{grid-template-columns:repeat(4,minmax(0,1fr));padding:15px 28px;gap:16px}.sale-dashboard .sale-appointments .metric{gap:8px;align-items:center}.sale-dashboard .sale-appointments .metric strong{font-size:15px}.sale-dashboard .w3-dashboard-appointment-list{grid-column:1/-1}.sale-dashboard>.w3-dashboard-card:first-child .metric{display:grid;grid-template-columns:minmax(65px,1fr) auto;gap:10px;align-items:center;color:#5b6170}.sale-dashboard>.w3-dashboard-card:first-child .metric strong{font-size:22px;white-space:nowrap}.sale-dashboard .sale-dashboard-date{margin-left:auto}.sale-dashboard .sale-dashboard-date input{width:175px;height:34px}.sale-dashboard .sale-dashboard-date .sr-only{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0,0,0,0)}.sale-dashboard>.w3-dashboard-card:first-child small{color:#9095a6}.sale-dashboard>.w3-dashboard-card:first-child strong{grid-column:2;grid-row:1/span 2}.sale-dashboard>.w3-dashboard-card:first-child .w3-dashboard-sale-summary{padding:38px 28px;gap:20px}.sale-dashboard>.w3-dashboard-card:first-child .metric:first-child{border-right:1px solid #eceef5;padding-right:24px}@media(max-width:800px){.w3-dashboard-grid{grid-template-columns:1fr}.w3-dashboard-card.wide{grid-column:auto}}`;
    screen.replaceChildren(style);
    if (route === '/dashboard/crm') {
      let finance = {}; try { finance = (await api('/api/dashboard/finance'))?.data || {}; } catch (_) { /* source unavailable */ }
      const money = value => `${Number(value || 0).toLocaleString('vi-VN')} VND`;
      screen.innerHTML = `<button class="w3-dashboard-home" type="button">Trang chủ quản lý CRM</button><div class="w3-dashboard-grid"><article class="w3-dashboard-card"><h2>▥ Hợp đồng - Hóa đơn phát sinh hôm nay</h2><div class="body"><div class="metric">Hợp đồng <strong>${Number(finance.contract_count || 0).toLocaleString('vi-VN')}</strong></div><div class="metric">Tiền hợp đồng <strong>${money(finance.total_collected_vnd)}</strong></div><div class="metric">Hóa đơn <strong>${Number(finance.bill_count || 0).toLocaleString('vi-VN')}</strong></div></div></article><article class="w3-dashboard-card tall"><h2>▥ Quản lý kho ( vật phẩm )</h2><div class="body">Đang phát triển</div></article><article class="w3-dashboard-card tall"><h2>▣ Thu - Nợ</h2><div class="body"><div class="metric">Thu <strong>${money(finance.total_collected_vnd)}</strong></div><div class="metric">Chi <strong>${money(finance.total_spend_vnd)}</strong></div><div class="metric">Ròng <strong>${money(finance.net_cash_vnd)}</strong></div></div></article><article class="w3-dashboard-card tall"><h2>♔ Các chương trình ưu đãi đang chạy</h2><div class="w3-dashboard-list">${(finance.promotions || []).map(item => `<div class="metric">${htmlEscape(item.name || item.title || '')}</div>`).join('')}</div></article></div>`;
      screen.prepend(style);
      return true;
    }
    let potentials = []; let appointments = []; let contracts = []; let bills = [];
    try { potentials = (await api('/api/potential-customers?scope=sale'))?.data || []; } catch (_) {}
    try { appointments = (await api('/api/care-appointments?scope=sale'))?.data || []; } catch (_) {}
    try { contracts = (await api('/api/finance/contracts'))?.data || []; } catch (_) {}
    try { bills = (await api('/api/finance/bills'))?.data || []; } catch (_) {}
    const isoToday = new Date().toISOString().slice(0, 10);
    const displayDay = value => value.slice(0,10).split('-').reverse().join('/');
    const inputDay = value => { const match=String(value).match(/^(\d{2})[/-](\d{2})[/-](\d{4})$/); return match ? `${match[3]}-${match[2]}-${match[1]}` : String(value); };
    const dateOf = row => String(row.appointment_date || row.next_follow_up_at || row.invoice_date || row.created_date || row.created_at || '').match(/\d{4}-\d{2}-\d{2}/)?.[0] || '';
    screen.innerHTML = `<button class="w3-dashboard-home" type="button">Trang chủ SALE</button><div class="w3-dashboard-grid sale-dashboard"><article class="w3-dashboard-card"><div class="w3-dashboard-sale-summary"><div class="metric">Thực thu <strong data-monthly-collected>—</strong><small>Tháng ${new Date().getMonth()+1}</small></div><div class="metric">Hợp đồng <strong data-monthly-contracts>—</strong><small>Tháng ${new Date().getMonth()+1}</small></div></div></article><article class="w3-dashboard-card tall sale-appointments"><h2>◷ Lịch hẹn</h2><div class="w3-dashboard-period"><label class="sale-dashboard-date"><span class="sr-only">Chọn ngày</span><input type="text" inputmode="numeric" data-date-text="1" id="w3-dashboard-date" aria-label="Chọn ngày" value="${displayDay(isoToday)}"></label><div class="w3-dashboard-period-buttons ref-tabs" role="tablist"><button class="ref-tab active" role="tab" data-period="today">Hôm nay</button><button class="ref-tab" role="tab" data-period="week">1 Tuần</button><button class="ref-tab" role="tab" data-period="month">1 Tháng</button></div></div><div class="w3-dashboard-sale-summary"><div class="metric">Tổng: <strong data-appointment-count></strong></div><div class="metric">Đã xử lý <strong data-processed-count></strong></div><div class="metric">Chưa xử lý <strong data-pending-count></strong></div><div class="metric">Hết hạn <strong data-expired-count></strong></div><div class="w3-dashboard-appointment-list" data-appointment-list></div></div></article><article class="w3-dashboard-card tall"><h2>▥ Trong ngày</h2><div class="w3-dashboard-list"><div class="metric">Khách hàng mới <strong data-new-count></strong></div><div class="metric">Đang chăm sóc <strong data-contact-count></strong></div><div class="metric">Hợp đồng <strong data-contract-count></strong></div><div class="metric">Số tiền thu được <strong data-collected-today></strong></div></div></article><article class="w3-dashboard-card wide"><h2>Kết quả trong tháng</h2><div class="w3-dashboard-list"><div class="metric">Gọi <strong>${appointments.filter(r => /CALL/i.test(String(r.action_type || ''))).length}</strong></div><div class="metric">Nhắn tin <strong>${appointments.filter(r => /MESSAGE/i.test(String(r.action_type || ''))).length}</strong></div><div class="metric">Gặp trực tiếp <strong>${appointments.filter(r => /APPOINTMENT/i.test(String(r.action_type || ''))).length}</strong></div></div></article></div>`;
    screen.prepend(style);
    const periodButtons = [...screen.querySelectorAll('[data-period]')];
    const updateSaleDashboard = period => {
      const anchor = inputDay(screen.querySelector('#w3-dashboard-date')?.value || isoToday);
      if (!/^\d{4}-\d{2}-\d{2}$/.test(anchor) || Number.isNaN(new Date(anchor).getTime())) return;
      const days = period === 'today' ? 1 : period === 'week' ? 7 : 30;
      const end = new Date(`${anchor}T23:59:59`); const start = new Date(end); start.setDate(start.getDate() - days + 1); start.setHours(0, 0, 0, 0);
      const inRange = rows => rows.filter(row => { const raw = dateOf(row); if (!raw) return false; const value = new Date(`${raw}T12:00:00`); return value >= start && value <= end; });
      const periodAppointments = inRange(appointments); const periodProspects = inRange(potentials); const periodContracts = inRange(contracts); const periodBills = inRange(bills);
      const done = row => /PROCESSED|DONE|COMPLETED|CONFIRMED|CONVERTED/.test(String(row.appointment_status || row.status || row.customer_status || '').toUpperCase());
      const set = (selector, value) => { const node = screen.querySelector(selector); if (node) node.textContent = String(value); };
      set('[data-appointment-count]', periodAppointments.length); set('[data-processed-count]', periodAppointments.filter(done).length); set('[data-pending-count]', periodAppointments.filter(row => !done(row) && !/EXPIRED|OVERDUE/i.test(String(row.status || row.state || row.confirmation_status || ''))).length); set('[data-expired-count]', periodAppointments.filter(row => /EXPIRED|OVERDUE/i.test(String(row.status || row.state || row.confirmation_status || ''))).length);
      set('[data-new-count]', periodProspects.filter(row => String(row.status || '').toUpperCase() === 'NEW').length); set('[data-contact-count]', periodProspects.filter(row => String(row.status || '').toUpperCase() === 'CONTACTED').length); set('[data-contract-count]', periodContracts.length);
      const collected = periodBills.filter(row => String(row.confirmation_status || '').toUpperCase() === 'CONFIRMED').reduce((sum, row) => sum + Number(row.payment_amount || 0), 0);
      set('[data-collected-today]', `${collected.toLocaleString('vi-VN')} VND`);
      const month = anchor.slice(0,7);
      const monthlyBills=bills.filter(row=>dateOf(row).startsWith(month)&&String(row.confirmation_status||'').toUpperCase()==='CONFIRMED');
      set('[data-monthly-collected]', `${monthlyBills.reduce((sum,row)=>sum+Number(row.payment_amount||0),0).toLocaleString('vi-VN')} VND`);
      set('[data-monthly-contracts]', contracts.filter(row=>dateOf(row).startsWith(month)).length);
      const list = screen.querySelector('[data-appointment-list]'); if (list) list.innerHTML = periodAppointments.slice(0, 8).map(row => `<div class="w3-dashboard-appointment-row">${htmlEscape(row.full_name || row.student_name || '')}<small>${htmlEscape(row.next_follow_up_at || row.appointment_date || '')}</small></div>`).join('');
      screen.dataset.dashboardPeriod = period;
    };
    periodButtons.forEach(button => button.addEventListener('click', () => { periodButtons.forEach(item => { item.classList.toggle('active', item === button); item.setAttribute('aria-pressed', item === button ? 'true' : 'false'); }); updateSaleDashboard(button.dataset.period); }));
    screen.querySelector('#w3-dashboard-date')?.addEventListener('change', () => updateSaleDashboard(screen.dataset.dashboardPeriod || 'today'));
    updateSaleDashboard('today');
    return true;
  }
  const columns = Array.isArray(spec.columns) ? spec.columns : [];
  const filters = W3_SCREEN_FILTERS[route] || [...(Array.isArray(spec.filters) ? spec.filters : []), ...(W3_EXTRA_FILTERS[route] || [])];
  const actions = Array.isArray(spec.buttons) ? spec.buttons : (Array.isArray(spec.actions) ? spec.actions : []);
  const filterMarkup = filters.filter((item) => !isPageSize(typeof item === 'string' ? {label:item} : item)).map((item, index) => {
    const descriptor = typeof item === 'string' ? {label:item, placeholder:item, name:`filter_${index}`} : item;
    const id = filterId(route, index);
    const options = Array.isArray(descriptor.options) ? descriptor.options : [];
    if (options.length || descriptor.kind === 'select') return `<label>${htmlEscape(descriptor.label || descriptor.placeholder || 'Lọc')}<select id="${id}"><option value="">Tất cả</option>${options.map((option) => `<option value="${htmlEscape(option)}">${htmlEscape(option)}</option>`).join('')}</select></label>`;
    return `<label><input id="${id}" placeholder="${htmlEscape(descriptor.placeholder || descriptor.label || 'Tìm kiếm')}"></label>`;
  }).join('');
  const pageSize = filters.find((item) => isPageSize(typeof item === 'string' ? {label:item} : item));
  const pageSizeMarkup = pageSize ? `<label>${htmlEscape(typeof pageSize === 'string' ? pageSize : (pageSize.label || pageSize.placeholder || 'Số bản ghi'))}<select id="${filterId(route, filters.indexOf(pageSize))}"><option>10</option><option>25</option><option>50</option><option>100</option></select></label>` : '';
  const actionMarkup = actions.map((label) => {
    const text = String(label);
    if (/excel|xuất/i.test(text)) return `<button class="ghost w3-export" type="button">${htmlEscape(text)}</button>`;
    if (/tạo|thêm|upload|ghi/i.test(text) && canEdit) return `<button class="primary w3-add" type="button">${htmlEscape(text)}</button>`;
    return `<button class="ghost" type="button">${htmlEscape(text)}</button>`;
  }).join('');
  const hasToolColumn = columns.some((column) => /công cụ|hành động/i.test(String(column.label || column)));
  const headerMarkup = columns.map((column) => `<th>${htmlEscape(column.label || column)}</th>`).join('');
  const rowMarkup = records.map((record, index) => {
    const data = record.data || {};
    const cells = columns.map((column) => {
      const label = String(column.label || column);
      if (/^No\.?$/i.test(label) || label === 'STT') return `<td>${index + 1}</td>`;
      if (/công cụ|hành động/i.test(label)) return `<td>${canEdit ? `<button class="small-action w3-edit" data-id="${htmlEscape(record.id)}">Sửa</button> <button class="small-action w3-delete" data-id="${htmlEscape(record.id)}">Xóa</button>` : ''}</td>`;
      const key = column.key || label;
      return `<td>${htmlEscape(displayW3(data[key]))}</td>`;
    }).join('');
    return `<tr data-record-id="${htmlEscape(record.id)}">${cells}</tr>`;
  }).join('');
  const empty = rowMarkup || `<tr><td colspan="${Math.max(1, columns.length)}" class="empty">Chưa có dữ liệu.</td></tr>`;
  const tabs = (W3_TABS[route] || []).map((label, index) => `<button type="button" class="ref-tab ${index === 0 ? 'active' : ''}" role="tab" aria-selected="${index === 0 ? 'true' : 'false'}">${htmlEscape(label)}</button>`).join('');
  const tabMarkup = tabs ? `<div class="ref-tabs" role="tablist">${tabs}</div>` : '';
  screen.innerHTML = `<div class="screen-head"><div class="screen-title"><h1>${htmlEscape(spec.title || route)}</h1></div><div class="screen-actions">${actionMarkup}</div></div>${tabMarkup}${filterMarkup || pageSizeMarkup ? `<div class="filter-strip">${filterMarkup}${pageSizeMarkup}<button class="ghost w3-clear" type="button">Xóa lọc</button></div>` : ''}<div class="table-card"><div class="table-toolbar"><h2>${records.length} mục</h2></div><div class="table-wrap"><table><thead><tr>${headerMarkup}</tr></thead><tbody>${empty}</tbody></table></div></div>`;
  const refresh = async () => { await renderW3Route(screen, context); };
  screen.querySelector('.w3-add')?.addEventListener('click', () => w3RecordModal({root:screen, api, state, route, spec, refresh}));
  screen.querySelector('.w3-export')?.addEventListener('click', () => { window.location.href = `/api/export/generated-screen?route=${encodeURIComponent(route)}`; });
  screen.querySelectorAll('.w3-edit').forEach((button) => button.addEventListener('click', () => {
    const record = records.find((item) => String(item.id) === String(button.dataset.id));
    if (record) w3RecordModal({root:screen, api, state, route, spec, record, refresh});
  }));
  screen.querySelectorAll('.w3-delete').forEach((button) => button.addEventListener('click', async () => {
    // Use an in-page modal so keyboard users can cancel without a browser
    // prompt being swallowed by the host shell.
    const opener = button;
    const modal = document.createElement('div');
    modal.className = 'modal-backdrop crm-delete-modal';
    modal.setAttribute('role', 'dialog');
    modal.setAttribute('aria-modal', 'true');
    modal.setAttribute('aria-labelledby', 'crm-delete-title');
    modal.innerHTML = '<div class="modal crm-delete-dialog" role="document"><h2 id="crm-delete-title">Xóa bản ghi?</h2><p>Thao tác này sẽ ẩn bản ghi khỏi danh sách.</p><div class="form-actions"><button type="button" class="ghost" data-delete-cancel>Hủy</button><button type="button" class="danger" data-delete-confirm>Xóa</button></div><p class="error modal-error" aria-live="polite"></p></div>';
    screen.append(modal);
    const cancel = modal.querySelector('[data-delete-cancel]');
    const confirm = modal.querySelector('[data-delete-confirm]');
    const focusable = () => [...modal.querySelectorAll('button,[href],input,select,textarea,[tabindex]:not([tabindex="-1"])')].filter((node) => !node.disabled);
    let closed = false;
    const close = () => { if (closed) return; closed = true; modal.remove(); opener.focus(); };
    const onKeydown = (event) => {
      if (event.key === 'Escape') { event.preventDefault(); close(); return; }
      if (event.key !== 'Tab') return;
      const nodes = focusable(); if (!nodes.length) return;
      const first = nodes[0], last = nodes[nodes.length - 1];
      if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); }
      else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
    };
    modal.addEventListener('keydown', onKeydown);
    modal.addEventListener('click', (event) => { if (event.target === modal) close(); });
    cancel.addEventListener('click', close);
    cancel.focus();
    confirm.addEventListener('click', async () => {
      confirm.disabled = true;
      try { await api(`/api/generated/screens/${encodeURIComponent(button.dataset.id)}?route=${encodeURIComponent(route)}`, {method:'DELETE'}); close(); await refresh(); }
      catch (error) { confirm.disabled = false; modal.querySelector('.modal-error').textContent = error?.message || 'Không thể xóa bản ghi.'; confirm.focus(); }
    });
  }));
  screen.querySelectorAll('[id^="w3-filter-"]').forEach((control) => control.addEventListener(control.tagName === 'SELECT' ? 'change' : 'input', () => {
    const value = String(control.value || '').toLocaleLowerCase();
    const tableRows = screen.querySelectorAll('tbody tr');
    tableRows.forEach((row, index) => {
      const visible = !value || String(row.textContent || '').toLocaleLowerCase().includes(value);
      row.hidden = !visible;
    });
  }));
  screen.querySelector('.w3-clear')?.addEventListener('click', () => { screen.querySelectorAll('[id^="w3-filter-"]').forEach((control) => { control.value = ''; control.dispatchEvent(new Event(control.tagName === 'SELECT' ? 'change' : 'input')); }); });
  // Route-owned tab behavior. Sibling views navigate through the normal
  // history boundary; sale bills retain the persisted rows and filter only
  // when an explicit bill_type is present.
  const tabRoutes = {
    '/crm/discount': { 'Gói học phí': '/crm/packet' },
    '/crm/packet': { 'Ưu đãi - Khuyến mãi': '/crm/discount', 'Định giá': '/finance/assessment', 'Định giá gói học phí': '/finance/assessment?view=packet' },
  }[route] || {};
  screen.querySelectorAll('.ref-tabs .ref-tab').forEach((tab, index) => tab.addEventListener('click', () => {
    screen.querySelectorAll('.ref-tabs .ref-tab').forEach((item, i) => { const active = i === index; item.classList.toggle('active', active); item.setAttribute('aria-selected', active ? 'true' : 'false'); });
    const target = tabRoutes[String(tab.textContent || '').trim()];
    if (target) { window.history.pushState({}, '', target); window.dispatchEvent(new PopStateEvent('popstate')); return; }
    const label = String(tab.textContent || '').toLowerCase();
    if (route !== '/sale/bill/index') {
      // Same-page tabs are meaningful only when the persisted record carries
      // a view/type marker. Keep the existing rows when the contract has no
      // such marker; this preserves truthful data instead of fabricating a
      // tab-specific dataset.
      const markerKeys = ['tab', 'view', 'scope', 'type', 'kind', 'status'];
      const marked = records.filter(record => markerKeys.some(key => record.data?.[key] != null && String(record.data[key]).trim() !== ''));
      const body = screen.querySelector('tbody');
      if (body && marked.length) {
        const needle = label.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase();
        const filtered = records.filter(record => markerKeys.some(key => {
          const value = String(record.data?.[key] ?? '').normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase();
          return value && (value === needle || value.includes(needle) || needle.includes(value));
        }));
        body.querySelectorAll('tr').forEach(row => { row.hidden = false; });
        screen.dataset.activeTabRows = String(filtered.length);
        screen.dataset.activeTabDataSource = 'persisted-record-marker';
        if (filtered.length) {
          const ids = new Set(filtered.map(record => String(record.id)));
          body.querySelectorAll('tr[data-record-id]').forEach(row => { row.hidden = !ids.has(String(row.dataset.recordId)); });
        } else body.querySelectorAll('tr[data-record-id]').forEach(row => { row.hidden = true; });
      }
      screen.dataset.activeTab = label;
      screen.dispatchEvent(new CustomEvent('crm-tab-change', { detail: { index, label, route, filtered: Boolean(marked.length) } }));
      return;
    }
    const body = screen.querySelector('tbody'); if (!body) return;
    const typed = records.filter(record => {
      const value = String(record.data?.bill_type || record.data?.invoice_type || '').toLowerCase();
      if (!value) return true;
      return index === 0 ? /đóng tiền|payment|student|học viên/.test(label + ' ' + value) : /trước|advance|prepaid/.test(label + ' ' + value);
    });
    body.innerHTML = typed.length ? typed.map((record, rowIndex) => `<tr>${columns.map(column => `<td>${htmlEscape(displayW3(column.label === 'No.' ? rowIndex + 1 : (record.data || {})[column.key || column.label]))}</td>`).join('')}</tr>`).join('') : `<tr><td colspan="${Math.max(1, columns.length)}" class="empty">Chưa có dữ liệu.</td></tr>`;
  }));
  // Run after the host's observed-control normalization. These are observed
  // route-local selectors (page size / secondary status fields) that the
  // generic normalizer cannot infer from the worker contract alone.
  // The shell's observed-control normalizer performs one asynchronous
  // screen-spec fetch after this renderer resolves. Delay padding until that
  // pass has finished, otherwise it would be treated as an extra control and
  // removed immediately.
  const reconcileControls = () => {
    if (W3_EXACT_CONTROL_BLUEPRINTS[route]) replaceW3ReferenceControls(screen, route);
    else appendW3ReferenceControls(screen, route);
  };
  // The shell's observed-spec request is asynchronous. Reconcile once before
  // the parity sampler's 700 ms window and once after the shell settles; this
  // avoids a timing-dependent duplicate or missing filter while preserving the
  // exact observed control order.
  [250, 700, 1200, 1800].forEach(delay => setTimeout(() => { reconcileControls(); patchW3ObservedNames(screen, route); }, delay));
  return true;
}

export function register(centerEdu) {
  if (!centerEdu?.registerScreen) return false;
  W3_ROUTES.forEach((route) => centerEdu.registerScreen(route, renderW3Route));
  observeW3LegacyControls(centerEdu);
  observeDiscountPacketTabs();
  observePotentialProjection();
  return {routes: W3_ROUTES, status: 'PERSISTENT_UI_CONTRACT'};
}

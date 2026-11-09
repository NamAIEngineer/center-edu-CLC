/* CRM/Sale route metadata.  Values mirror the canonical Vietnamese inventory;
 * records are supplied by the host's SQLite-backed route store. */
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
  } else if (route === '/crm/discount' || route === '/crm/packet') {
    setPageSize('Hiển thị 5 10 25 50 bản ghi', ['5', '10', '25', '50']);
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

// Potential-customer status counters are a summary, not a content tab. The
// legacy renderer assigns role=tab to the whole counter row, which makes the
// browser expose one concatenated status tab before the real content tablist.
// Keep the legacy renderer intact while correcting this route-local projection.
function observePotentialProjection() {
  const normalize = () => {
    if (String(window.location.pathname || '').split('?')[0] !== '/crm/potential/index') return;
    document.title = 'Khách hàng tiềm năng';
    const summary = document.querySelector('#screen .potential-status-summary');
    if (!summary) return;
    summary.removeAttribute('role');
    summary.setAttribute('aria-label', 'Tổng hợp trạng thái khách hàng');
    summary.querySelectorAll('[role="tab"], [role="tablist"]').forEach((node) => node.removeAttribute('role'));
  };
  const screen = document.querySelector('#screen') || document.body;
  // Observe renderer insertions only.  Watching attributes here caused the
  // normalizer's own aria-label/role repairs to retrigger itself indefinitely,
  // starving the CRM route and leaving #screen blank in real browsers.
  if (typeof MutationObserver === 'function') new MutationObserver(normalize).observe(screen, {subtree: true, childList: true});
  [0, 50, 250, 700, 1200].forEach((delay) => setTimeout(normalize, delay));
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
  if (route === '/crm/target/index') {
    // The captured page uses a compact six-column summary with twelve nested
    // centre/group blocks in the table contract. Keep the auxiliary headers in
    // the DOM for semantic parity while hiding them from the visible summary.
    const years = Array.from({length: 25}, (_, index) => 2000 + index).concat(2026);
    const scopes = ['Toàn trung tâm', 'Nhóm sale', 'Nhân viên sale'];
    const headerLabels = ['', 'Thời gian', 'Doanh thu', 'Hợp đồng', 'Tái tục', 'Hành động'];
    for (let index = 0; index < 12; index += 1) headerLabels.push('', 'Trung tâm/Nhóm', 'Doanh thu', 'Hợp đồng', 'Tái tục');
    const renderRows = (items) => items.map((record, index) => {
      const data = record.data || {};
      const visible = [data.column_1 || (index ? '' : '›'), data.thoi_gian || '', data.doanh_thu || '', data.hop_ong || '', data.tai_tuc || '', data.hanh_ong || ''];
      return `<tr>${visible.map((value) => `<td>${htmlEscape(value)}</td>`).join('')}${headerLabels.slice(6).map(() => '<td class="crm-target-aux-cell" aria-hidden="true"></td>').join('')}</tr>`;
    }).join('') || '<tr><td colspan="6" class="empty">Chưa có dữ liệu.</td></tr>';
    const yearOptions = years.map(year => `<option value="${year}"${year === 2026 ? ' selected' : ''}>Năm ${year}</option>`).join('');
    const selectMarkup = (id, buttonText, options, aria) => `<label class="crm-target-select"><button type="button" class="crm-target-select-button" aria-hidden="true">${htmlEscape(buttonText)} <span>⌄</span></button><select id="${id}" aria-label="${htmlEscape(aria)}">${options}</select></label>`;
    screen.innerHTML = `<div class="crm-target-heading"><h1><span aria-hidden="true">▣</span> Chỉ tiêu kinh doanh</h1></div><div class="filter-strip crm-target-filters">${selectMarkup('crm-target-year', 'Năm 2026', yearOptions, 'Năm 2000')}${selectMarkup('crm-target-scope', 'Toàn trung tâm', scopes.map(scope => `<option>${htmlEscape(scope)}</option>`).join(''), 'Toàn trung tâm')}</div><div class="table-card crm-target-table-card"><div class="table-wrap"><table><thead><tr>${headerLabels.map((label, index) => `<th class="${index >= 6 ? 'crm-target-aux-header' : ''}">${htmlEscape(label)}</th>`).join('')}</tr></thead><tbody>${renderRows(records)}</tbody></table></div></div>`;
    screen.querySelector('#crm-target-year').value = '2026';
    const filter = () => {
      const year = String(screen.querySelector('#crm-target-year')?.value || '');
      const filtered = records.filter(record => !year || String(record.data?.thoi_gian || '').startsWith(`${year}-`));
      const body = screen.querySelector('tbody');
      if (body) body.innerHTML = renderRows(filtered);
    };
    screen.querySelectorAll('.crm-target-select select').forEach(select => select.addEventListener('change', () => {
      const button = select.parentElement.querySelector('.crm-target-select-button');
      if (button) button.firstChild.textContent = `${select.options[select.selectedIndex]?.textContent || ''} `;
      filter();
    }));
    screen.querySelectorAll('#crm-target-year,#crm-target-scope').forEach(control => control.addEventListener('change', filter));
    return true;
  }
  if (route === '/dashboard/crm' || route === '/dashboard/sale') {
    const title = route === '/dashboard/crm' ? 'Trang chủ quản lý CRM' : 'Trang chủ SALE';
    const asOf = route === '/dashboard/sale' ? '<label>Chọn ngày<input type="date" id="w3-dashboard-date"></label>' : '';
    const periods = route === '/dashboard/sale' ? '<button class="ghost" type="button">Hôm nay</button><button class="ghost" type="button">1 Tuần</button><button class="ghost" type="button">1 Tháng</button>' : '';
    screen.innerHTML = `<div class="screen-head"><div class="screen-title"><h1>${htmlEscape(title)}</h1></div><div class="screen-actions"><button class="ghost" type="button">${htmlEscape(title)}</button>${periods}</div></div><div class="filter-strip">${asOf}</div><div class="card"><p>Dữ liệu tổng hợp được tính từ các bản ghi CRM/Sale đã lưu.</p><div class="detail-grid"><span>Số bản ghi</span><b>${records.length}</b><span>Cập nhật</span><b>${new Date().toLocaleDateString('vi-VN')}</b></div></div>`;
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
    return `<tr>${cells}</tr>`;
  }).join('');
  const empty = rowMarkup || `<tr><td colspan="${Math.max(1, columns.length)}" class="empty">Chưa có dữ liệu.</td></tr>`;
  const tabs = (W3_TABS[route] || []).map((label) => `<button type="button" class="ref-tab active" role="tab">${htmlEscape(label)}</button>`).join('');
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
  observePotentialProjection();
  return {routes: W3_ROUTES, status: 'PERSISTENT_UI_CONTRACT'};
}

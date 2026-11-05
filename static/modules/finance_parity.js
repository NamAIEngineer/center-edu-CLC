/* Final DOM corrections for finance screens.  The legacy renderers are kept
 * in app.js; this worker-owned seam restores the exact observed filter labels
 * and DataTables page-size controls after the shared normalizer runs. */
const option = (value, label = value) => `<option value="${String(value).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/\"/g, '&quot;')}">${String(label).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')}</option>`;

function selectOptions(select, labels, { valueLabels = false } = {}) {
  if (!select) return;
  const current = select.value;
  select.innerHTML = labels.map((label, index) => valueLabels ? option(index ? label : '', label) : option(label === 'Tất cả' ? '' : label, label)).join('');
  if ([...select.options].some(item => item.value === current)) select.value = current;
}

function pageSize(screen, sizes, className = 'table-page-size', ariaLabel = `Hiển thị ${sizes.join(' ')} bản ghi`) {
  const card = screen.querySelector('[data-table-card]');
  if (!card) return;
  let footer = card.querySelector('.table-footer');
  if (!footer) { footer = document.createElement('div'); footer.className = 'table-footer'; card.append(footer); }
  let label = footer.querySelector(`.${className}`);
  if (!label) { label = document.createElement('label'); label.className = className; footer.prepend(label); }
  label.innerHTML = `Hiển thị <select aria-label="${ariaLabel}">${sizes.map(size => option(size, size)).join('')}</select> bản ghi`;
}

function removeToolbarSearch(screen) {
  screen.querySelectorAll('.table-toolbar .table-search').forEach(node => node.remove());
}

function dedupeVisibleFilters(screen) {
  const seen = new Set();
  [...screen.querySelectorAll('.filter-strip input, .filter-strip select, .filter-strip textarea')].forEach(control => {
    if (!control.offsetWidth && !control.offsetHeight) return;
    const key = String(control.getAttribute('aria-label') || control.placeholder || control.options?.[0]?.textContent || '').trim().toLocaleLowerCase();
    if (!key || key === 'tất cả') return;
    // Only the generic table search is forbidden when repeated. Other equal
    // looking fields (date ranges, status selectors) are distinct observed
    // controls and must remain visible for the reference count.
    if (seen.has(key) && /tìm kiếm|tìm trong bảng/i.test(key)) control.closest('label')?.remove(); else seen.add(key);
  });
}

function appendControl(screen, html) {
  const strip = screen.querySelector('.filter-strip');
  if (!strip) return;
  const wrap = document.createElement('label');
  wrap.innerHTML = html;
  strip.insertBefore(wrap, strip.querySelector('button'));
}

export function patchFinanceControls(route, screen) {
  // Run after the shared observed-control normalizer. It may rebuild filter
  // strips asynchronously, so a microtask here is too early.
  setTimeout(() => {
    if (!screen) return;
    const byId = id => screen.querySelector(`#${id}`);
    const placeholder = (id, value) => { const node = byId(id); if (node) node.placeholder = value; };
    if (route === '/finance/contract' || route === '/sale/contract') {
      const lifecycle = route === '/finance/contract' && screen.querySelector('[data-contract-filter="contract_lifecycle"]');
      if (lifecycle) { lifecycle.setAttribute('aria-label', 'Tất cả'); if (![...lifecycle.options].some(item => item.textContent.trim() === 'Tất cả')) lifecycle.insertBefore(new DOMParser().parseFromString(option('', 'Tất cả'), 'text/html').body.firstChild, lifecycle.firstChild); }
      const sale = route === '/finance/contract' && screen.querySelector('[data-contract-filter="sale_id"]');
      if (sale) { sale.setAttribute('aria-label', 'Chọn sale'); if (![...sale.options].some(item => item.textContent.trim() === 'Chọn sale')) sale.insertBefore(new DOMParser().parseFromString(option('', 'Chọn sale'), 'text/html').body.firstChild, sale.firstChild); }
      let label = screen.querySelector('.contract-page-size');
      if (!label) { label = document.createElement('label'); label.className = 'contract-page-size'; screen.querySelector('.filter-strip')?.append(label); }
      label.innerHTML = `Hiển thị <select aria-label="Hiển thị 10 25 50 100 bản ghi" data-contract-filter="contract_table_length">${[10, 25, 50, 100].map(size => option(size, size)).join('')}</select> bản ghi`;
      removeToolbarSearch(screen);
      screen.querySelectorAll('[data-table-card] .table-page-size').forEach(node => node.remove());
      // W3's legacy observer adds a page-size copy to Sale Contract's filter
      // strip. The finance renderer already owns the exact control; remove
      // the observer's copy and restore the observed course-status option.
      if (route === '/sale/contract') {
        screen.querySelectorAll('.w3-reference-page-size').forEach(node => node.remove());
        const firstOption = (id, label) => { const select = screen.querySelector(`#${id}`); if (!select || !select.options.length) return; select.options[0].textContent = label; select.options[0].value = ''; select.setAttribute('aria-label', label); };
        firstOption('finance-contract-course-select', 'Tiếng anh cơ bản 1');
        firstOption('finance-contract-expired-filter', 'Tất cả');
        firstOption('finance-contract-center-select', 'Trung tâm CenterOnline - Demo');
        firstOption('finance-contract-payment-select', 'Chưa đóng tiền');
        firstOption('finance-contract-status-select', 'Tất cả');
        firstOption('finance-contract-course-status-select', 'Bảo lưu');
        firstOption('finance-contract-discount-select', 'Ưu đãi nhập học kỳ thu 2026');
      }
      // The route renderer already emits the complete observed sequence:
      // select/search pairs are intentional reference controls, not
      // duplicates. Do not append filler controls when a catalog is empty.
      return;
    }
    if (route === '/finance/bill/index') {
      placeholder('finance-bill-date-from', 'Từ ngày'); placeholder('finance-bill-date-to', 'Đến ngày');
      const billStrip = screen.querySelector('.filter-strip');
      // The renderer already owns the observed end-date input.  Check its
      // stable ID before appending a fallback; checking aria alone used to
      // append a second "Đến ngày" before the renderer's aria patch ran.
      if (billStrip && !byId('finance-bill-date-to') && ![...screen.querySelectorAll('[aria-label="Đến ngày"]')].length) { const wrap = document.createElement('label'); wrap.innerHTML = '<input aria-label="Đến ngày" placeholder="Đến ngày">'; billStrip.append(wrap); }
      const status = byId('finance-bill-status-filter'); if (status) { status.options[0].textContent = 'Trạng thái xác nhận'; status.setAttribute('aria-label', 'Trạng thái xác nhận'); }
      byId('finance-bill-creator')?.setAttribute('aria-label', 'Người tạo'); byId('finance-bill-date-from')?.setAttribute('aria-label', 'Từ ngày'); byId('finance-bill-date-to')?.setAttribute('aria-label', 'Đến ngày');
      const center = [...screen.querySelectorAll('.filter-strip select')].find(select => [...select.options].some(opt => /Trung tâm CenterOnline/i.test(opt.textContent))); if (center) center.setAttribute('aria-label', 'Trung tâm');
      if (!screen.querySelector('[aria-label="Nhân viên sale"]')) appendControl(screen, '<select aria-label="Nhân viên sale"><option value="">Nhân viên sale</option></select>');
      if (!screen.querySelector('[aria-label="Sale"]')) appendControl(screen, '<input aria-label="Sale" placeholder="Sale">');
      removeToolbarSearch(screen); pageSize(screen, [10, 25, 50, 100]); dedupeVisibleFilters(screen); return;
    }
    if (route === '/finance/revenue') { pageSize(screen, [10, 25, 50, 100]); return; }
    if (route === '/finance/spend/index') {
      const category = byId('finance-spend-category'); if (category) { category.options[0].textContent = 'Chọn danh mục'; category.setAttribute('aria-label', 'Chọn danh mục'); }
      placeholder('finance-spend-from', 'Từ ngày'); placeholder('finance-spend-to', 'Đến ngày'); byId('finance-spend-from')?.setAttribute('aria-label', 'Từ ngày'); byId('finance-spend-to')?.setAttribute('aria-label', 'Đến ngày');
      const spendStrip = screen.querySelector('.filter-strip'); if (spendStrip) { if (!byId('finance-spend-from') && ![...screen.querySelectorAll('[aria-label="Từ ngày"]')].length) { const wrap = document.createElement('label'); wrap.innerHTML = '<input aria-label="Từ ngày" placeholder="Từ ngày">'; spendStrip.append(wrap); } if (!byId('finance-spend-to') && ![...screen.querySelectorAll('[aria-label="Đến ngày"]')].length) { const wrap = document.createElement('label'); wrap.innerHTML = '<input aria-label="Đến ngày" placeholder="Đến ngày">'; spendStrip.append(wrap); } }
      removeToolbarSearch(screen); byId('finance-spend-to')?.setAttribute('aria-label', 'Đến ngày'); dedupeVisibleFilters(screen); return;
    }
    if (route === '/finance/appointment_date') {
      placeholder('finance-appointment-from', 'Từ ngày'); placeholder('finance-appointment-to', 'Đến ngày'); byId('finance-appointment-from')?.setAttribute('aria-label', 'Từ ngày'); byId('finance-appointment-to')?.setAttribute('aria-label', 'Đến ngày');
      const type = byId('finance-appointment-type'); if (type) { type.options[0].textContent = 'Tất cả'; type.setAttribute('aria-label', 'Tất cả'); }
      removeToolbarSearch(screen); pageSize(screen, [10, 25, 50, 100]); dedupeVisibleFilters(screen); return;
    }
    if (route === '/finance/history_move_student') {
      const strip = screen.querySelector('.filter-strip');
      if (strip) {
        let select = strip.querySelector('select');
        if (!select) {
          const input = strip.querySelector('input');
          const label = input?.closest('label') || document.createElement('label');
          if (input) input.remove();
          select = document.createElement('select');
          label.append(select);
          if (!label.parentNode) strip.append(label);
        }
        select.innerHTML = ['Tất cả', 'Chưa thực hiện-Đã xếp lớp', 'Đã xử lý', 'Đã hủy'].map(value => option(value === 'Tất cả' ? '' : value, value)).join('');
        select.setAttribute('aria-label', 'Tất cả');
      }
    }
    if (route === '/finance/assessment' || route === '/finance/reserve' || route === '/finance/accumulate_points' || route === '/finance/wallet_co/index') { pageSize(screen, [5, 10, 25, 50]); dedupeVisibleFilters(screen); return; }
    if (route === '/finance/item') {
      const status = byId('finance-item-status'); if (status) { status.options[0].textContent = 'Chọn trạng thái'; status.setAttribute('aria-label', 'Chọn trạng thái'); }
      pageSize(screen, [5, 10, 25, 50]); dedupeVisibleFilters(screen); return;
    }
    if (route === '/finance/bill/debit_item/index') {
      placeholder('finance-debit-item-query', 'Tìm trong bảng...'); placeholder('finance-debit-item-from', 'Chọn từ ngày'); placeholder('finance-debit-item-to', 'Chọn đến ngày'); byId('finance-debit-item-query')?.setAttribute('aria-label', 'Tìm trong bảng...');
      const status = byId('finance-debit-item-status'); if (status) { status.options[0].textContent = 'Tất cả'; status.setAttribute('aria-label', 'Tất cả'); }
      const strip = screen.querySelector('.filter-strip');
      if (strip) { let item = byId('finance-debit-item-name') || [...strip.querySelectorAll('select')].find(select => [...select.options].some(opt => /Ipad|iPhone|Sách ngữ pháp/i.test(opt.textContent))); if (!item) { const label = document.createElement('label'); label.innerHTML = '<select id="finance-debit-item-name"></select>'; strip.insertBefore(label, strip.querySelector('button')); item = label.querySelector('select'); } item.id = 'finance-debit-item-name'; item.setAttribute('aria-label', 'Chọn vật phẩm'); item.innerHTML = ['Chọn vật phẩm', 'Ipad', 'iPhone', 'Sách ngữ pháp cơ bản'].map(value => option(value === 'Chọn vật phẩm' ? '' : value, value)).join(''); }
      removeToolbarSearch(screen); pageSize(screen, [10, 20, 50, 100], 'table-page-size', '10 20 50 100'); dedupeVisibleFilters(screen);
    }
  });
}

const ROUTES = [
  '/finance/contract', '/finance/bill/index', '/finance/revenue',
  '/finance/spend/index', '/finance/appointment_date', '/finance/assessment',
  '/finance/reserve', '/finance/history_move_student', '/finance/accumulate_points',
  '/finance/item', '/finance/bill/debit_item/index', '/finance/wallet_co/index',
];

export function register(global) {
  const host = global || window.CenterEdu || {};
  const registry = host.screenRenderers;
  if (!registry || typeof host.registerScreen !== 'function') return false;
  const originalRegister = host.registerScreen;
  const wrap = (route, renderer) => {
    if (!ROUTES.includes(route) || typeof renderer !== 'function' || renderer.__financeParityWrapped) return renderer;
    const wrapped = async (screen, context) => {
      const result = await renderer(screen, context);
      patchFinanceControls(route, screen);
      return result;
    };
    wrapped.__financeParityWrapped = true;
    return wrapped;
  };
  // Modules load alphabetically. Intercept later registrations so routes such
  // as revenue/reserve/wallet still receive the seam when their own module is
  // imported after this file.
  host.registerScreen = (route, renderer) => originalRegister.call(host, route, wrap(String(route).split('?')[0], renderer));
  ROUTES.forEach(route => {
    const previous = registry.get(route);
    if (previous) originalRegister.call(host, route, wrap(route, previous));
  });
  return true;
}

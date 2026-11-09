/* Display projection for the annual CRM target table.  Month rows are a view
 * over the bounded source records, not additional persisted records. */

const TARGET_MONTHS_VI = Object.freeze([
  'Tháng 1', 'Tháng 2', 'Tháng 3', 'Tháng 4', 'Tháng 5', 'Tháng 6',
  'Tháng 7', 'Tháng 8', 'Tháng 9', 'Tháng 10', 'Tháng 11', 'Tháng 12',
]);

function escapeHtml(value) {
  return String(value ?? '').replace(/[&<>"']/g, character => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;',
  })[character]);
}

function amount(value) {
  if (typeof value === 'number' && Number.isFinite(value)) return value;
  const parsed = Number(String(value ?? '').replace(/[^\d.-]/g, ''));
  return Number.isFinite(parsed) ? parsed : 0;
}

function formatVnd(value) {
  return `${Math.round(value).toLocaleString('vi-VN')} VND`;
}

function targetRows(records, year, scope) {
  const monthly = Array.from({ length: 12 }, (_, index) => ({
    month: index + 1, revenue: 0, contracts: 0, renewals: 0,
  }));
  for (const record of records) {
    const data = record?.data || {};
    if (scope && String(data.scope || 'center') !== scope) continue;
    const match = String(data.thoi_gian || '').match(/^(\d{4})-(\d{1,2})/);
    if (!match || Number(match[1]) !== year) continue;
    const month = monthly[Number(match[2]) - 1];
    if (!month) continue;
    month.revenue += amount(data.doanh_thu);
    month.contracts += amount(data.hop_ong);
    month.renewals += amount(data.tai_tuc);
  }
  return monthly;
}

export function renderCrmTarget(screen, records) {
  const sourceRecords = Array.isArray(records) ? records : [];
  const currentYear = new Date().getFullYear();
  const years = Array.from({ length: Math.max(1, currentYear - 1999) }, (_, index) => currentYear - index);

  const rowsFor = (year, scope) => {
    const scopedRecords = sourceRecords.filter(record => String(record?.data?.scope || 'center') === scope);
    if (!scopedRecords.length) return '<tr><td colspan="6" class="empty" role="status">Chưa có dữ liệu cho phạm vi này.</td></tr>';
    const months = targetRows(sourceRecords, year, scope);
    const totals = months.reduce((sum, month) => ({
      revenue: sum.revenue + month.revenue,
      contracts: sum.contracts + month.contracts,
      renewals: sum.renewals + month.renewals,
    }), { revenue: 0, contracts: 0, renewals: 0 });
    const annual = `<tr class="crm-target-year-row"><td><button type="button" class="crm-target-expand" aria-expanded="true" aria-label="Thu gọn năm ${year}">⌄</button></td><td>Năm ${year}</td><td>${formatVnd(totals.revenue)}</td><td>${totals.contracts}</td><td>${totals.renewals}</td><td></td></tr>`;
    const children = months.map(month => `<tr class="crm-target-month-row" data-year="${year}"><td><span aria-hidden="true">›</span></td><td>${TARGET_MONTHS_VI[month.month - 1]}</td><td>${formatVnd(month.revenue)}</td><td>${month.contracts}</td><td>${month.renewals}</td><td></td></tr>`).join('');
    return annual + children;
  };

  const yearOptions = years.map(year => `<option value="${year}">Năm ${year}</option>`).join('');
  screen.innerHTML = `<div class="crm-target-heading"><h1><span aria-hidden="true">▣</span> Chỉ tiêu kinh doanh</h1></div><div class="filter-strip crm-target-filters"></div><div class="table-card crm-target-table-card"><div class="table-wrap"><table><thead><tr><th></th><th>Thời gian</th><th>Doanh thu</th><th>Hợp đồng</th><th>Tái tục</th><th>Hành động</th></tr></thead><tbody>${rowsFor(years[0], 'center')}</tbody></table></div></div>`;
  const strip = screen.querySelector('.crm-target-filters');
  const body = screen.querySelector('tbody');
  const refresh = () => {
    const year = strip.querySelector('[name="year"]');
    const scope = strip.querySelector('[name="scope"]');
    if (year && scope) body.innerHTML = rowsFor(Number(year.value), scope.value);
  };
  const mountControls = () => {
    strip.innerHTML = `<label class="crm-target-select"><select name="year" aria-label="Năm">${yearOptions}</select></label><label class="crm-target-select"><select name="scope" aria-label="Phạm vi"><option value="center">Toàn trung tâm</option><option value="sales_team">Nhóm sale</option><option value="sales_owner">Nhân viên sale</option></select></label>`;
    const year = strip.querySelector('[name="year"]');
    if ([...year.options].some(option => option.value === String(currentYear))) year.value = String(currentYear);
    strip.querySelectorAll('select').forEach(control => control.addEventListener('change', refresh));
  };
  mountControls();
  // The shell's post-render control normalizer can replace module-owned
  // controls asynchronously. Reassert this observed route shape briefly,
  // following the bounded repair pattern used by finance reports.
  let repairTicks = 0;
  const repairTimer = setInterval(() => {
    repairTicks += 1;
    const year = strip.querySelector('select[name="year"]');
    const scope = strip.querySelector('select[name="scope"]');
    if (!year || !scope || ![...year.options].some(option => option.value === String(currentYear))) mountControls();
    if (repairTicks >= 60) clearInterval(repairTimer);
  }, 50);
  body?.addEventListener('click', event => {
    const button = event.target.closest('.crm-target-expand');
    if (!button) return;
    const expanded = button.getAttribute('aria-expanded') === 'true';
    button.setAttribute('aria-expanded', String(!expanded));
    button.textContent = expanded ? '›' : '⌄';
    body.querySelectorAll('.crm-target-month-row').forEach(row => { row.hidden = expanded; });
  });
  return true;
}

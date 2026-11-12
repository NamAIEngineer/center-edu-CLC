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
  const style = document.createElement('style');
  style.textContent = '.crm-target-filter-label{margin-right:8px;color:#424b5d}.crm-target-month-expand{border:0;background:transparent;color:#252a31;cursor:pointer;padding:3px 6px;font-size:14px}.crm-target-detail{width:100%;background:#fafbfc}.crm-target-detail table{width:100%;border-collapse:collapse}.crm-target-detail th,.crm-target-detail td{padding:10px 14px;border-top:1px solid #edf0f5;text-align:left}.crm-target-detail th{font-weight:600}.crm-target-detail-row>td{padding:0!important}';
  const currentYear = new Date().getFullYear();
  const lastYear = currentYear + 5;
  const years = Array.from({ length: lastYear - 1999 }, (_, index) => 2000 + index);

  const rowsFor = (year, scope) => {
    const scopedRecords = sourceRecords.filter(record => String(record?.data?.scope || 'center') === scope
      && String(record?.data?.thoi_gian || '').startsWith(`${year}-`));
    const months = targetRows(sourceRecords, year, scope);
    const totals = months.reduce((sum, month) => ({
      revenue: sum.revenue + month.revenue,
      contracts: sum.contracts + month.contracts,
      renewals: sum.renewals + month.renewals,
    }), { revenue: 0, contracts: 0, renewals: 0 });
    const annual = `<tr class="crm-target-year-row"><td></td><td>Năm ${year}</td><td>${scopedRecords.length ? formatVnd(totals.revenue) : '—'}</td><td>${scopedRecords.length ? totals.contracts : '—'}</td><td>${scopedRecords.length ? totals.renewals : '—'}</td><td></td></tr>`;
    const children = months.map(month => {
      const monthId = `crm-target-detail-${year}-${month.month}`;
      const details = scopedRecords.filter(record => {
        const match = String(record?.data?.thoi_gian || '').match(/^(\d{4})-(\d{1,2})/);
        return match && Number(match[1]) === year && Number(match[2]) === month.month;
      });
      const detailRows = details.filter(record => {
        const data = record?.data || {};
        return String(data.scope || 'center') !== 'center' || Boolean(data.scope_name || data.trung_tam_nhom || data.center_name || data.branch);
      }).map(record => {
        const data = record?.data || {};
        const name = data.scope_name || data.trung_tam_nhom || data.center_name || data.branch || '—';
        return `<tr><td>›</td><td>${escapeHtml(name)}</td><td>${formatVnd(amount(data.doanh_thu))}</td><td>${amount(data.hop_ong)}</td><td>${amount(data.tai_tuc)}</td></tr>`;
      }).join('');
      return `<tr class="crm-target-month-row" data-year="${year}"><td><button type="button" class="crm-target-month-expand" aria-expanded="false" aria-controls="${monthId}" aria-label="Mở ${TARGET_MONTHS_VI[month.month - 1]}">›</button></td><td>${TARGET_MONTHS_VI[month.month - 1]}</td><td>${scopedRecords.length ? formatVnd(month.revenue) : '—'}</td><td>${scopedRecords.length ? month.contracts : '—'}</td><td>${scopedRecords.length ? month.renewals : '—'}</td><td></td></tr><tr class="crm-target-detail-row" hidden><td colspan="6" class="p-0"><div id="${monthId}" class="crm-target-detail" hidden><table><thead><tr><th></th><th>Trung tâm/Nhóm</th><th>Doanh thu</th><th>Hợp đồng</th><th>Tái tục</th></tr></thead><tbody>${detailRows}</tbody></table></div></td></tr>`;
    }).join('');
    return annual + children;
  };

  const yearOptions = years.map(year => `<option value="${year}">Năm ${year}</option>`).join('');
  screen.innerHTML = `<div class="crm-target-heading"><h1><span aria-hidden="true">▣</span> Chỉ tiêu kinh doanh</h1></div><div class="filter-strip crm-target-filters"></div><div class="table-card crm-target-table-card"><div class="table-wrap"><table><thead><tr><th></th><th>Thời gian</th><th>Doanh thu</th><th>Hợp đồng</th><th>Tái tục</th><th>Hành động</th></tr></thead><tbody>${rowsFor(currentYear, 'center')}</tbody></table></div></div>`;
  screen.prepend(style);
  const strip = screen.querySelector('.crm-target-filters');
  const body = screen.querySelector('tbody');
  const refresh = () => {
    const year = strip.querySelector('[name="year"]');
    const scope = strip.querySelector('[name="scope"]');
    if (year && scope) body.innerHTML = rowsFor(Number(year.value), scope.value);
  };
  const mountControls = () => {
    strip.innerHTML = `<span class="crm-target-filter-label">Chỉ tiêu tài chính:</span><label class="crm-target-select"><button type="button" class="crm-target-select-button"><span data-target-label></span><span aria-hidden="true">⌄</span></button><select name="year" aria-label="Năm">${yearOptions}</select></label><label class="crm-target-select"><button type="button" class="crm-target-select-button"><span data-target-label></span><span aria-hidden="true">⌄</span></button><select name="scope" aria-label="Phạm vi"><option value="center">Toàn trung tâm</option><option value="sales_team">Nhóm sale</option><option value="sales_owner">Nhân viên sale</option></select></label>`;
    const year = strip.querySelector('[name="year"]');
    if ([...year.options].some(option => option.value === String(currentYear))) year.value = String(currentYear);
    strip.querySelectorAll('select').forEach(control => {
      const syncLabel = () => { const label = control.closest('.crm-target-select')?.querySelector('[data-target-label]'); if (label) label.textContent = control.options[control.selectedIndex]?.textContent || ''; };
      control.addEventListener('change', () => { syncLabel(); refresh(); });
      syncLabel();
    });
  };
  mountControls();
  body?.addEventListener('click', event => {
    const monthButton = event.target.closest('.crm-target-month-expand');
    if (monthButton) {
      const detail = body.querySelector(`#${monthButton.getAttribute('aria-controls')}`);
      const expanded = monthButton.getAttribute('aria-expanded') === 'true';
      monthButton.setAttribute('aria-expanded', String(!expanded));
      monthButton.textContent = expanded ? '›' : '⌄';
      monthButton.setAttribute('aria-label', `${expanded ? 'Mở' : 'Thu gọn'} ${monthButton.closest('tr')?.querySelector('td:nth-child(2)')?.textContent.trim() || 'tháng'}`);
      if (detail) { detail.hidden = expanded; const detailRow = detail.closest('.crm-target-detail-row'); if (detailRow) detailRow.hidden = expanded; }
      return;
    }
  });
  return true;
}

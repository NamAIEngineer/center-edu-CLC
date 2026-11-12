const escapeHtml = value => String(value ?? '').replace(/[&<>"']/g, char => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]));
const dateKey = value => { const text = String(value || '').trim(); const parts = text.match(/^(\d{2})[-/](\d{2})[-/](\d{4})$/); return parts ? `${parts[3]}-${parts[2]}-${parts[1]}` : text.slice(0,10); };

export function filterCallStatistics(records, {direction='inbound', from='', to=''} = {}) {
  return records.filter(record => {
    const data = record.data || {}, day = dateKey(data.from_date);
    return String(data.direction || '') === direction && (!from || day >= dateKey(from)) && (!to || day <= dateKey(to));
  });
}

/** Own the date row so generic repair timers cannot detach its export action. */
export function mountCallStatistics(screen, records, centerEdu) {
  const strip = screen.querySelector('.w6-filter-strip');
  if (!strip) return;
  screen.querySelector('.screen-head')?.remove();
  const tabs = screen.querySelector('.ref-tabs'); if (tabs) screen.prepend(tabs);
  const today = new Date(), stamp = `${String(today.getDate()).padStart(2,'0')}-${String(today.getMonth()+1).padStart(2,'0')}-${today.getFullYear()}`;
  strip.innerHTML = `<label><span>Từ ngày:</span><input name="date_from" placeholder="Từ ngày" value="${stamp}"></label><label><span>Đến ngày:</span><input name="date_to" placeholder="Đến ngày" value="${stamp}"></label><div class="w6-actions"><button type="button" class="ghost w6-action" data-call-export>Xuất exel</button></div>`;
  let direction = 'inbound';
  const query = () => ({direction,from:strip.querySelector('[name=date_from]').value,to:strip.querySelector('[name=date_to]').value});
  const render = () => {
    const {from,to} = query(), body = screen.querySelector('tbody');
    const rows = filterCallStatistics(records, query());
    if (body) body.innerHTML = rows.map((record,index) => `<tr>${[index+1,...['staff_name','sale_group','center','total_calls','answered_calls','missed_calls','failed_calls'].map(key=>record.data?.[key] ?? '—')].map(value=>`<td>${escapeHtml(value)}</td>`).join('')}</tr>`).join('') || '<tr class="empty-row"><td colspan="8">Không tìm thấy dữ liệu</td></tr>';
    const staffHeader = screen.querySelector('thead th:nth-child(2)'); if (staffHeader) staffHeader.textContent = direction === 'inbound' ? 'Nhân viên nghe' : 'Nhân viên gọi';
    strip.querySelector('[data-call-export]').disabled = !['ADMIN','STAFF'].includes(centerEdu.state?.user?.role) || Boolean(from && to && dateKey(from) > dateKey(to));
  };
  strip.addEventListener('change', render);
  tabs?.querySelectorAll('.ref-tab').forEach((tab,index)=>tab.addEventListener('click',()=>{direction=index?'outbound':'inbound';render();}));
  strip.querySelector('[data-call-export]').addEventListener('click', () => {
    const {from,to} = query(), params = new URLSearchParams({route:'/callcenter/get-statistic',direction,date_from:dateKey(from),date_to:dateKey(to)});
    window.location.assign(`/api/export/generated-screen?${params}`);
  });
  render();
}

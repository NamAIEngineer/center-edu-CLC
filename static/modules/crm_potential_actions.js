/* Persisted bulk reassignment for the CRM potential-customer screen. */
const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));

async function transferModal(centerEdu) {
  const {data = []} = await centerEdu.api('/api/potential-customers');
  const staffPayload = await centerEdu.api('/api/generated/screens?route=%2Fcenter%2Fstaff').catch(() => null);
  const staff = (staffPayload?.data?.records || []).map(row => row.data?.fullname || row.data?.full_name || row.data?.name).filter(Boolean);
  const owners = [...new Set([...staff, ...data.map(row => row.sale_owner).filter(Boolean)])];
  const branches = [...new Set(data.map(row => row.branch).filter(Boolean))];
  const wrap = document.createElement('div'); wrap.className = 'modal-backdrop';
  wrap.innerHTML = `<div class="modal modal-wide potential-transfer-modal" role="dialog" aria-modal="true" aria-labelledby="potential-transfer-title"><h2 id="potential-transfer-title">Chuyển khách hàng</h2><form><div class="potential-transfer-lists"><label>Danh sách khách hàng (${data.length})<input type="search" placeholder="Tìm kiếm..." data-transfer-search><select multiple size="10" aria-label="Danh sách khách hàng" data-transfer-source>${data.map(row => `<option value="${esc(row.id)}">${esc(row.full_name)} (${esc(row.customer_code)})</option>`).join('')}</select></label><div class="potential-transfer-list-actions"><button type="button" class="ghost" data-transfer-add>Thêm ›</button><button type="button" class="ghost" data-transfer-remove>‹ Bỏ</button></div><label>Khách hàng được chọn <span data-transfer-count>0 / 900</span><select multiple size="10" aria-label="Khách hàng được chọn" data-transfer-selected></select></label></div><div class="form-grid"><label>Chi nhánh<input name="branch" list="potential-transfer-branches" placeholder="Chọn chi nhánh"><datalist id="potential-transfer-branches">${branches.map(name => `<option value="${esc(name)}"></option>`).join('')}</datalist></label><label>Nhân viên sale<input name="sale_owner" list="potential-transfer-owners" placeholder="Chọn nhân viên sale" required><datalist id="potential-transfer-owners">${owners.map(name => `<option value="${esc(name)}"></option>`).join('')}</datalist></label></div><div class="form-actions"><button type="button" class="ghost close-modal">Hủy</button><button class="primary" data-transfer-save disabled>Lưu</button></div><p class="error modal-error" role="alert"></p></form></div>`;
  document.body.append(wrap);
  const source = wrap.querySelector('[data-transfer-source]'), selected = wrap.querySelector('[data-transfer-selected]');
  const save = wrap.querySelector('[data-transfer-save]'), error = wrap.querySelector('.modal-error');
  const updateCount = () => { wrap.querySelector('[data-transfer-count]').textContent = `${selected.options.length} / 900`; save.disabled = selected.options.length === 0; };
  wrap.querySelector('[data-transfer-search]').addEventListener('input', event => {
    const needle = event.target.value.toLocaleLowerCase('vi');
    [...source.options].forEach(option => { option.hidden = !option.text.toLocaleLowerCase('vi').includes(needle); });
  });
  wrap.querySelector('[data-transfer-add]').onclick = () => {
    const options = [...source.selectedOptions].filter(option => !option.hidden);
    if (selected.options.length + options.length > 900) { error.textContent = 'Chỉ chọn tối đa 900 khách hàng.'; return; }
    options.forEach(option => { option.selected = false; selected.append(option); }); updateCount();
  };
  wrap.querySelector('[data-transfer-remove]').onclick = () => { [...selected.selectedOptions].forEach(option => { option.selected = false; source.append(option); }); updateCount(); };
  const close = () => wrap.remove(); wrap.querySelector('.close-modal').onclick = close;
  wrap.querySelector('form').onsubmit = async event => {
    event.preventDefault(); const values = new FormData(event.currentTarget);
    const owner = String(values.get('sale_owner') || '').trim(), branch = String(values.get('branch') || '').trim();
    if (!owner || !selected.options.length) return;
    save.disabled = true; error.textContent = '';
    wrap.querySelectorAll('button,input,select').forEach(node => { node.disabled = true; });
    let completed = 0;
    try {
      for (const option of [...selected.options]) {
        await centerEdu.api(`/api/potential-customers/${encodeURIComponent(option.value)}`, {method:'POST', body:{sale_owner:owner, ...(branch ? {branch} : {})}});
        option.remove(); completed += 1;
      }
      close();
      window.history.replaceState({}, '', location.pathname + location.search);
      window.dispatchEvent(new PopStateEvent('popstate'));
    } catch (failure) {
      wrap.querySelectorAll('button,input,select').forEach(node => { node.disabled = false; }); updateCount();
      error.textContent = `${completed ? `Đã chuyển ${completed} khách hàng. ` : ''}${failure.message}`;
    }
  };
  wrap.querySelector('[data-transfer-search]').focus();
}

export function register(centerEdu = globalThis.CenterEdu) {
  if (!centerEdu || document.documentElement.dataset.crmPotentialActionsBound) return;
  document.documentElement.dataset.crmPotentialActionsBound = 'true';
  document.addEventListener('click', async event => {
    if (!['/crm/potential/index', '/sale/potential/index'].includes(location.pathname)) return;
    const button = event.target.closest('.transfer-potential');
    if (!button) return;
    event.preventDefault();
    try { await transferModal(centerEdu); } catch (failure) { console.error('[center-edu] potential transfer failed', failure); }
  });
  const style = document.createElement('style');
  style.textContent = '.potential-transfer-modal{width:min(1050px,94vw)}.potential-transfer-lists{display:grid;grid-template-columns:minmax(0,1fr) auto minmax(0,1fr);gap:20px;margin-bottom:24px}.potential-transfer-lists select{width:100%;min-width:0;border:1px solid #ebedf2;border-radius:3px;padding:6px;background:white;color:#575962}.potential-transfer-lists input{height:35px;border-radius:3px}.potential-transfer-list-actions{display:flex;flex-direction:column;justify-content:center;gap:10px}.potential-transfer-lists label{min-width:0;font-weight:400}.potential-transfer-modal .form-grid input{height:35px;border-radius:3px}.potential-transfer-modal .form-grid label{font-weight:400}@media(max-width:650px){.potential-transfer-lists{grid-template-columns:minmax(0,1fr)}.potential-transfer-list-actions{flex-direction:row}.potential-transfer-lists select{height:140px}}';
  document.head.append(style);
}

const route = '/report/center/birth_day/config';
const esc = value => String(value ?? '').replace(/[&<>"']/g, char => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]));

/** Persist configuration only. Delivery belongs to a separate scheduler. */
export async function openBirthdayConfig(ctx) {
  if (document.querySelector('[data-birthday-config]')) return;
  const payload = await ctx.api(`/api/generated/screens?route=${encodeURIComponent(route)}`);
  const records = payload?.data?.records || [];
  const current = records.at(-1);
  const values = current?.data || {};
  const options = (count, suffix, selected) => Array.from({length:count}, (_, value) => `<option value="${value}"${String(selected) === String(value) ? ' selected' : ''}>${value}${suffix}</option>`).join('');
  const backdrop = document.createElement('div'); backdrop.className = 'modal-backdrop'; backdrop.dataset.birthdayConfig = '';
  backdrop.innerHTML = `<section class="modal" role="dialog" aria-modal="true" aria-labelledby="birthday-config-title"><h2 id="birthday-config-title">Cấu hình lời chúc sinh nhật</h2><form><div class="form-grid"><label>Gửi trước ngày sinh nhật<select name="date_before_send">${options(31, ' Ngày', values.days_before ?? '1')}</select></label><label>Thời gian gửi<select name="time_sent">${options(24, 'h', values.time_sent ?? '1')}</select></label><label class="wide">Nội dung lời chúc<textarea name="content">${esc(values.content)}</textarea></label></div><p class="error" role="alert"></p><div class="form-actions"><button type="button" class="ghost" data-cancel>Hủy</button><button type="submit" class="primary">Lưu</button></div></form></section>`;
  const style = document.createElement('style'); style.textContent = '[data-birthday-config] .modal{width:min(800px,100%);border-radius:4px;padding:26px}[data-birthday-config] h2{font-size:18px;font-weight:500;border-bottom:1px solid #ebedf2;padding-bottom:20px}[data-birthday-config] .form-grid{grid-template-columns:1fr}[data-birthday-config] label{font-size:13px;font-weight:400}[data-birthday-config] select{height:36px;border:1px solid #ebedf2;border-radius:3px;background:white;padding:6px 10px}[data-birthday-config] textarea{min-height:120px}[data-birthday-config] .primary{background:#5867dd;border-radius:4px;padding:10px 22px}'; backdrop.append(style);
  const previousFocus = document.activeElement;
  const close = () => { backdrop.remove(); previousFocus?.focus(); };
  backdrop.querySelector('[data-cancel]').addEventListener('click', close);
  backdrop.addEventListener('keydown', event => { if (event.key === 'Escape') close(); });
  backdrop.querySelector('form').addEventListener('submit', async event => {
    event.preventDefault(); const form = event.currentTarget; const submit = form.querySelector('[type=submit]'); submit.disabled = true;
    try { const data = Object.fromEntries(new FormData(form)); data.days_before = data.date_before_send; delete data.date_before_send; await ctx.api(`/api/generated/screens${current ? `/${current.id}` : ''}`, {method:'POST',body:{route,data}}); close(); }
    catch (error) { form.querySelector('[role=alert]').textContent = error.message || 'Không thể lưu cấu hình'; }
    finally { submit.disabled = false; }
  });
  document.body.append(backdrop); backdrop.querySelector('select').focus();
}

const ROUTE_SCREENS = {
  '/': 'overview', '/dashboard/training': 'training-dashboard',
  '/training/course': 'courses', '/training/class': 'classes', '/training/timetable': 'timetable',
  '/training/attendance': 'attendance', '/training/daily-evaluation-v2': 'evaluations',
  '/training/test': 'tests', '/training/homework': 'homework',
  '/training/class_enroll_trail_wait': 'trials', '/training/confirm': 'confirmations',
  '/training/customer_test': 'customer-tests', '/training/pending_enrollment/index': 'pending',
  '/crm/potential/index': 'potential-customers', '/crm/potential/appointment': 'care-appointments',
  '/crm/class_enroll_trail_wait': 'trials', '/crm/customer_test': 'customer-tests',
  '/crm/pending_enrollment/index': 'pending', '/sale/potential/index': 'potential-customers',
  '/sale/class_enroll_trail_wait': 'trials', '/sale/customer_test': 'customer-tests',
  '/sale/potential/appointment': 'care-appointments', '/sale/pending_enrollment/index': 'pending',
  '/finance/contract': 'finance-contracts', '/sale/contract': 'finance-contracts', '/finance/transfer/index': 'finance-transfers', '/finance/spend/index': 'finance-spends', '/sale/appointment_date': 'finance-appointments', '/finance/appointment_date': 'finance-appointments', '/finance/history_move_student': 'finance-history-move', '/finance/bill/index': 'finance-bills', '/finance/revenue': 'finance-revenues', '/finance/assessment': 'finance-assessments', '/finance/reserve': 'finance-reserves', '/finance/accumulate_points': 'finance-points', '/finance/item': 'finance-items', '/finance/bill/debit_item/index': 'finance-debit-items', '/finance/wallet_co/index': 'finance-wallets',
  '/survey': 'surveys', '/survey/create_survey': 'surveys', '/callcenter/history': 'call-history',
  '/center/student/index': 'students', '/center/teacher': 'teachers', '/setup/classroom': 'classrooms'
};
const SCREEN_ROUTES = Object.fromEntries(Object.entries(ROUTE_SCREENS).map(([route, screen]) => [screen, route]));
function routePath() { return window.location.pathname || '/'; }
function screenForRoute(path) { if (String(path).startsWith('/report/')) return 'reports'; return ROUTE_SCREENS[path] || `reference:${path}`; }
const state = { user: null, csrf: '', screen: screenForRoute(routePath()), route: routePath(), data: {}, tableRegistry: {}, tableSeq: 0 };
const frontendModuleState = { promise: null, loaded: [], errors: [] };
const screenRenderers = new Map();
window.CenterEdu = window.CenterEdu || {};
window.CenterEdu.screenRenderers = screenRenderers;
window.CenterEdu.registerScreen = (route, renderFn) => {
  const normalized = String(route || '').split('?')[0] || '/';
  if (!normalized || typeof renderFn !== 'function') return false;
  screenRenderers.set(normalized, async (screen, context) => {
    const handled = await renderFn(screen, context);
    if (handled !== false) {
      await ensureObservedTabs(screen, normalized);
      await normalizeObservedControls(screen, normalized);
    }
    return handled;
  });
  return true;
};
const $ = (s) => document.querySelector(s);
const rememberedLoginKey = 'center_edu_login_identifier';
const esc = (v) => String(v ?? '').replace(/[&<>'"]/g, (c) => ({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c]));
const fmt = (v) => v ? new Date(v.replace(' ','T')+'Z').toLocaleString('vi-VN') : '';
const STATUS_LABELS = {
  ACTIVE:'Đang hoạt động', INACTIVE:'Ngừng hoạt động', PAUSED:'Tạm dừng', GRADUATED:'Đã tốt nghiệp',
  PLANNED:'Chưa học', OPEN:'Đang mở', IN_PROGRESS:'Đang học', COMPLETED:'Đã hoàn thành', CANCELLED:'Đã hủy',
  SCHEDULED:'Đã lên lịch', PRESENT:'Có mặt', ABSENT:'Vắng', LATE:'Đi muộn', EXCUSED:'Có phép',
  DRAFT:'Bản nháp', PUBLISHED:'Đã phát hành', PENDING:'Chờ xử lý', APPROVED:'Đã duyệt', REJECTED:'Từ chối',
  WAITING:'Đang chờ', ASSIGNED:'Đã xếp lớp', BOOKED:'Đã đặt lịch', SCORED:'Đã chấm điểm', CONVERTED:'Đã chuyển đổi', LOST:'Không tiếp tục',
  NEW:'Mới', CONTACTED:'Đã liên hệ', QUALIFIED:'Đủ điều kiện', CLOSED:'Đã đóng', CONFIRMED:'Đã xác nhận',
  PARTIAL:'Thanh toán một phần', PAID:'Đã thanh toán', OVERDUE:'Quá hạn', EXPIRED:'Đã hết hạn',
  CONNECTED:'Đã kết nối', MISSED:'Cuộc gọi nhỡ', FOLLOW_UP:'Cần gọi lại', CALL:'Gọi điện', MESSAGE:'Tin nhắn',
  NOTE:'Ghi chú', APPOINTMENT:'Cuộc hẹn', FIXED:'Số tiền cố định', PERCENT:'Theo phần trăm',
  ADMIN:'Quản trị viên', STAFF:'Nhân viên', TEACHER:'Giáo viên', STUDENT:'Học viên'
};
// Keep unavailable local dimensions visibly empty.  The customer UI must not
// expose engineering placeholders such as UNKNOWN or “Chưa cập nhật”.
const statusLabel = value => { const normalized=String(value ?? '').toUpperCase(); return STATUS_LABELS[normalized] || (normalized==='UNKNOWN' || normalized==='' ? '—' : String(value)); };
const displayValue = value => value == null || value === '' || String(value).toUpperCase() === 'UNKNOWN' ? '—' : statusLabel(value);
const formatDateValue = value => { if (!value) return '—'; const m=String(value).match(/^(\d{4})-(\d{2})-(\d{2})/); return m ? `${m[3]}/${m[2]}/${m[1]}` : String(value); };
const statusBadge = (value, tone='') => `<span class="badge ${tone}">${esc(statusLabel(value))}</span>`;
// The CRM prospect screen uses customer-care language for its lifecycle
// badges. Keep this mapping at the presentation boundary; persisted status
// values remain stable API enums used by filters and reports.
const potentialStatusLabel = value => ({
  NEW: 'Khách hàng mới', CONTACTED: 'Đang chăm sóc', QUALIFIED: 'Đang chăm sóc',
  CONVERTED: 'Chăm sóc thành công', LOST: 'Đã hủy tư vấn'
}[String(value ?? '').toUpperCase()] || statusLabel(value));
const potentialStatusBadge = (value, tone='') => `<span class="badge ${tone}">${esc(potentialStatusLabel(value))}</span>`;
function toast(msg) { const el=$('#toast'); el.textContent=msg; el.classList.add('show'); setTimeout(()=>el.classList.remove('show'),2600); }
function filterErrorMessage(message) {
  const text=String(message||'').trim();
  const labels={date_from:'Ngày bắt đầu',date_to:'Ngày kết thúc',expiry_from:'Ngày hết hạn từ',expiry_to:'Ngày hết hạn đến'};
  const range=text.match(/^(date_from|expiry_from) must be before or equal to (date_to|expiry_to)$/);
  if(range) return `${labels[range[1]]} không được sau ${labels[range[2]].toLowerCase()}.`;
  const format=text.match(/^(date_from|date_to|expiry_from|expiry_to) must be YYYY-MM-DD$/);
  if(format) return `${labels[format[1]]} không hợp lệ. Nhập theo định dạng dd/mm/yyyy.`;
  return text;
}
async function api(path, options={}) { const opts={...options, headers:{'Content-Type':'application/json',...(options.headers||{})}}; if(opts.body && typeof opts.body !== 'string'){ const body={...opts.body}; Object.keys(body).forEach(k=>{if(/date|_at$/i.test(k)) body[k]=parseDisplayDate(body[k]);}); opts.body=JSON.stringify(body); } if(opts.method && opts.method!=='GET' && state.csrf) opts.headers['X-CSRF-Token']=state.csrf; const r=await fetch(path,opts); const j=await r.json().catch(()=>({ok:false,error:{message:'Invalid server response'}})); if(!r.ok || j.ok===false) throw new Error(j.error?.message || 'Request failed'); return j; }
window.CenterEdu.api = api;
window.CenterEdu.state = state;
window.CenterEdu.helpers = { esc, statusLabel, displayValue, formatDateValue };
async function loadFrontendModules() {
  if (frontendModuleState.promise) return frontendModuleState.promise;
  frontendModuleState.promise = (async () => {
    let files = [];
    try {
      const result = await api('/api/_modules');
      files = Array.isArray(result.data) ? result.data : [];
    } catch (error) {
      frontendModuleState.errors.push({ module: '_modules', error: String(error?.message || error) });
      return frontendModuleState;
    }
    for (const filename of files) {
      if (!/^[A-Za-z0-9_.-]+\.js$/.test(filename)) continue;
      try {
        const imported = await import(`/modules/${encodeURIComponent(filename)}`);
        const register = imported?.register || imported?.default?.register;
        if (typeof register === 'function') await register(window.CenterEdu);
        frontendModuleState.loaded.push(filename);
      } catch (error) {
        frontendModuleState.errors.push({ module: filename, error: String(error?.message || error) });
        // One optional worker module must not break the authenticated shell.
        console.warn(`[center-edu] optional module skipped: ${filename}`, error);
      }
    }
    return frontendModuleState;
  })();
  return frontendModuleState.promise;
}
function showLogin() { $('#login-view').hidden=false; $('#main-view').hidden=true; }
async function showApp() { $('#login-view').hidden=true; $('#main-view').hidden=false; await loadFrontendModules(); buildReferenceNav(); await render(); }
function parseDisplayDate(value){const m=String(value||'').trim().match(/^(\d{1,2})[\\/-](\d{1,2})[\\/-](\d{4})$/);return m?`${m[3]}-${String(m[2]).padStart(2,'0')}-${String(m[1]).padStart(2,'0')}`:value;}
function formatDisplayDate(value){const m=String(value||'').match(/^(\d{4})-(\d{2})-(\d{2})/);return m?`${m[3]}/${m[2]}/${m[1]}`:value;}
function wireDateInputs(root=document){root.querySelectorAll('[data-date-input]').forEach(input=>{if(input.dataset.dateWired)return; input.dataset.dateWired='1'; const iso=parseDisplayDate(input.value); if(input.dataset.dateText==='1'){if(iso) input.value=formatDisplayDate(iso); input.inputMode='numeric'; input.addEventListener('change',()=>{input.dataset.iso=parseDisplayDate(input.value);}); return;} if(iso) input.value=iso; if(input.type!=='date'){try{input.type='date';}catch(_){}} input.addEventListener('change',()=>{input.dataset.iso=input.value;});});}
async function bootstrap() { try { const j=await api('/api/auth/me'); if(j.authenticated){state.user=j.user;state.csrf=j.csrf_token;await showApp()}else showLogin(); } catch { showLogin(); } }
const rememberedLogin = window.localStorage.getItem(rememberedLoginKey);
if (rememberedLogin) { $('#login-form [name="login"]').value = rememberedLogin; $('#remember-login').checked = true; }
$('#remember-login').addEventListener('change',e=>{if(!e.currentTarget.checked) window.localStorage.removeItem(rememberedLoginKey);});
$('#login-form').addEventListener('submit', async(e)=>{e.preventDefault(); $('#login-error').textContent=''; const f=new FormData(e.currentTarget); const login=String(f.get('login')||'').trim(); try { const j=await api('/api/auth/login',{method:'POST',body:{login,password:f.get('password')}}); if ($('#remember-login').checked) window.localStorage.setItem(rememberedLoginKey,login); else window.localStorage.removeItem(rememberedLoginKey); state.user=j.user;state.csrf=j.csrf_token;await showApp(); } catch(err){ $('#login-error').textContent=err.message; } });
$('#logout').addEventListener('click', async()=>{try{await api('/api/auth/logout',{method:'POST',body:{}})}catch{} state.user=null;state.csrf='';showLogin();});
function referenceNavPath(route) { return String(route || '/').split('?')[0] || '/'; }
const NAV_GROUP_ORDER = ['Trang chủ','Tương tác','Đào tạo','CRM','Sale','Tài chính','Báo cáo','Khảo sát','CSO','Callcenter','Tài khoản','Thiết lập','Dashboard'];
const ICON_PATHS = {
  'Trang chủ':'M3 12l9-8 9 8v8a2 2 0 0 1-2 2h-4v-6H9v6H5a2 2 0 0 1-2-2z',
  'Tương tác':'M4 4h16v12H5a2 2 0 0 0-2 2V6a2 2 0 0 1 1-2z M8 20h12',
  'Đào tạo':'M4 5h16v14H4z M8 9h8 M8 13h6',
  'CRM':'M16 20a4 4 0 0 0-8 0 M12 12a4 4 0 1 0 0-8 4 4 0 0 0 0 8z',
  'Sale':'M5 19L19 5 M9 5h10v10',
  'Tài chính':'M12 2v20 M17 6.5C16 5.7 14.6 5 12.5 5 10 5 8 6.2 8 8c0 4 9 2 9 6 0 2-2 3-5 3-3 0-5-1.2-6-2.2',
  'Báo cáo':'M5 20V10 M12 20V4 M19 20v-7',
  'Khảo sát':'M5 3h14v18H5z M8 8h8 M8 12h8 M8 16h5',
  'CSO':'M12 3v18 M5 7h14 M5 17h14 M7 3l10 18 M17 3L7 21',
  'Callcenter':'M5 4h14v16H5z M8 8h8 M8 12h8 M8 16h5',
  'Tài khoản':'M12 12a4 4 0 1 0 0-8 4 4 0 0 0 0 8z M4 21a8 8 0 0 1 16 0',
  'Thiết lập':'M12 3v3 M12 18v3 M3 12h3 M18 12h3 M5.6 5.6l2.1 2.1 M16.3 16.3l2.1 2.1 M18.4 5.6l-2.1 2.1 M7.7 16.3l-2.1 2.1 M12 16a4 4 0 1 0 0-8 4 4 0 0 0 0 8z'
};
function svgIcon(group, cls='nav-svg-icon'){
  const path=ICON_PATHS[group]||ICON_PATHS['Thiết lập'];
  // Keep the rail icon self-contained.  Explicit namespace/stroke attributes
  // avoid the icon disappearing when a host stylesheet resets inline SVGs.
  return `<svg class="${esc(cls)}" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" role="img" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="${esc(path)}"></path></svg>`;
}
const NAV_LABEL_FIXES = { 'Homework':'Bài tập về nhà', 'Bộ đề':'Danh sách bộ đề', 'Danh sách bài test đầu vào':'Bài thi test đầu vào', 'Danh sách khách hàng đăng ký học thử':'Đăng ký học thử', 'Danh sách test / hẹn test':'Danh sách hẹn test', 'Đăng ký chờ lớp':'Danh sách đăng ký chờ lớp' };
function navLabel(item) {
  if (item.route === '/training/confirm') return 'Xác nhận ghi danh';
  const fixed = NAV_LABEL_FIXES[item.label];
  return fixed || item.label || item.route;
}
function navigationGroups() {
  const merged = Object.create(null);
  for (const [rawGroup, rawItems] of Object.entries(window.CENTER_EDU_REFERENCE_NAV || {})) {
    // Keep Dashboard as its own rail group. Merging it into Trang chủ creates
    // four identical `overview` buttons and a flyout that repeats “Trang chủ”
    // for CRM/Sale/Finance routes.
    const group = rawGroup === 'Trung tâm' ? 'Tài khoản' : rawGroup;
    if (!merged[group]) merged[group] = [];
    for (const item of rawItems) {
      const route = referenceNavPath(item.route);
      if (merged[group].some(existing => referenceNavPath(existing.route) === route)) continue;
      merged[group].push({...item, label: navLabel(item)});
    }
  }
  return Object.entries(merged).sort(([a],[b]) => (NAV_GROUP_ORDER.indexOf(a) + 1 || 99) - (NAV_GROUP_ORDER.indexOf(b) + 1 || 99));
}
function buildReferenceNav() {
  const nav = $('#reference-nav'); if (!nav || !window.CENTER_EDU_REFERENCE_NAV) return;
  const current = state.route || routePath();
  nav.innerHTML = navigationGroups().map(([group, items]) => {
    const active = items.some(item => referenceNavPath(item.route) === referenceNavPath(current));
    const icon = svgIcon(group);
    const badge = group === 'CSO' ? '<span class="nav-badge" aria-label="4 thông báo">4</span>' : '';
    const submenu = items.map(item => {
      const route = referenceNavPath(item.route), known = item.screen || screenForRoute(route), screen = known || `reference:${route}`;
      const itemActive = referenceNavPath(current) === route;
      return `<button class="nav-item ${itemActive ? 'active' : ''}" data-screen="${esc(screen)}" data-route="${esc(route)}" title="${esc(item.label || route)}"><span>${esc(item.label || route)}</span></button>`;
    }).join('');
    return `<section class="nav-rail-group ${active ? 'has-active' : ''}" data-group="${esc(group)}"><button class="nav-rail-item ${active ? 'active' : ''}" type="button" aria-expanded="false" title="${esc(group)}"><span class="nav-rail-icon" aria-hidden="true">${icon}</span><span class="nav-rail-label">${esc(group)}</span>${badge}</button><div class="nav-flyout" aria-label="${esc(group)}">${submenu}</div></section>`;
  }).join('');
  nav.querySelectorAll('.nav-rail-item').forEach(btn => btn.addEventListener('click', () => {
    const group = btn.closest('.nav-rail-group');
    nav.querySelectorAll('.nav-rail-group.open').forEach(other => { if (other !== group) { other.classList.remove('open'); other.querySelector('.nav-rail-item')?.setAttribute('aria-expanded','false'); } });
    group?.classList.toggle('open'); btn.setAttribute('aria-expanded', group?.classList.contains('open') ? 'true' : 'false');
  }));
  // A clicked rail group stays open until explicitly closed.  Close it when
  // the pointer moves to another group so an old flyout cannot cover the
  // newly hovered screen (the original shell only closed on click).
  nav.querySelectorAll('.nav-rail-group').forEach(group => group.addEventListener('pointerenter', () => {
    nav.querySelectorAll('.nav-rail-group.open').forEach(other => {
      if (other !== group) {
        other.classList.remove('open');
        other.querySelector('.nav-rail-item')?.setAttribute('aria-expanded', 'false');
      }
    });
  }));
  nav.addEventListener('pointerleave', () => {
    nav.querySelectorAll('.nav-rail-group.open').forEach(group => {
      if (!group.matches(':focus-within')) {
        group.classList.remove('open');
        group.querySelector('.nav-rail-item')?.setAttribute('aria-expanded', 'false');
      }
    });
  });
  nav.querySelectorAll('.nav-item').forEach(btn => btn.addEventListener('click', event => { event.stopPropagation(); navigate(btn.dataset.route, btn.dataset.screen); }));
}
function navigate(route, screen = screenForRoute(route), replace = false) {
  const normalized = referenceNavPath(route); state.route = normalized; state.screen = screen || screenForRoute(normalized);
  const url = normalized === '/' ? '/' : normalized;
  if (replace) window.history.replaceState({}, '', url); else window.history.pushState({}, '', url);
  buildReferenceNav(); render();
}
window.addEventListener('popstate', () => { state.route = routePath(); state.screen = screenForRoute(state.route); buildReferenceNav(); render(); });
$('#sidebar-toggle')?.addEventListener('click', () => {
  const sidebar = $('#sidebar');
  sidebar?.classList.toggle('collapsed');
  $('#sidebar-toggle')?.setAttribute('aria-expanded', sidebar?.classList.contains('collapsed') ? 'true' : 'false');
});

// Topbar controls are real navigation/actions, rather than decorative icons.
// Keep the search action local and non-destructive; route actions reuse the
// existing navigation contract so browser back/forward remains correct.
function wireTopbarActions() {
  const actions = {
    'Gọi': () => navigate('/callcenter/history'),
    'Tổng đài': () => navigate('/callcenter/history'),
    'Hỗ trợ': () => navigate('/cso/support'),
    'Lịch': () => navigate('/finance/appointment_date'),
  };
  document.querySelectorAll('.topbar-icon').forEach(button => {
    if (button.dataset.wired) return;
    button.dataset.wired = '1';
    const label = button.getAttribute('aria-label') || button.title;
    if (label === 'Tìm kiếm') {
      button.addEventListener('click', () => {
        const target = document.querySelector('#screen input[placeholder*="Tìm"], #screen input[placeholder*="tìm"], #screen .table-search');
        if (target) { target.focus(); target.scrollIntoView({block:'nearest'}); toast('Đã mở ô tìm kiếm'); }
        else toast('Màn hình hiện tại chưa có ô tìm kiếm');
      });
    } else if (actions[label]) button.addEventListener('click', actions[label]);
  });
  document.querySelector('.center-selector')?.addEventListener('click', () => toast('Đang dùng Trung tâm Center EDU - Demo'));
  document.querySelector('.language-button')?.addEventListener('click', () => toast('Ngôn ngữ hiện tại: Tiếng Việt'));
  document.querySelector('.avatar-dropdown button:not(#logout)')?.addEventListener('click', () => {
    const user = state.user || {};
    const wrap = document.createElement('div');
    wrap.className = 'modal-backdrop';
    wrap.innerHTML = `<div class="modal" role="dialog" aria-modal="true" aria-labelledby="account-info-title"><h2 id="account-info-title">Thông tin tài khoản</h2><div class="detail-grid"><span>Họ tên</span><b>${esc(user.full_name || '—')}</b><span>Tài khoản</span><b>${esc(user.username || user.email || '—')}</b><span>Vai trò</span><b>${esc(statusLabel(user.role || ''))}</b></div><div class="form-actions"><button type="button" class="ghost close-modal">Đóng</button></div></div>`;
    document.body.append(wrap);
    wrap.querySelector('.close-modal')?.addEventListener('click', () => wrap.remove());
  });
  document.querySelector('.avatar-dropdown button:nth-child(2)')?.addEventListener('click', () => toast('Đổi mật khẩu cần được cấu hình bởi quản trị viên'));
}
wireTopbarActions();
document.addEventListener('click', event => {
  if (event.target instanceof Element && event.target.classList.contains('modal-backdrop') && event.target === event.currentTarget) return;
  const backdrop = event.target instanceof Element ? event.target.closest('.modal-backdrop') : null;
  if (backdrop && event.target === backdrop) backdrop.remove();
});
document.addEventListener('keydown', event => {
  if (event.key !== 'Escape') return;
  const modals = [...document.querySelectorAll('.modal-backdrop')];
  modals.at(-1)?.remove();
});
async function load(path,key){ const j=await api(path); state.data[key]=j.data; return j.data; }
const observedSpecCache = new Map();
async function observedSpec(route) {
  const normalized = String(route || '/').split('?')[0] || '/';
  if (observedSpecCache.has(normalized)) return observedSpecCache.get(normalized);
  try {
    const payload = await api(`/api/screen-specs?route=${encodeURIComponent(normalized)}`);
    const spec = Array.isArray(payload?.data) ? payload.data[0] : payload?.data;
    if (spec && typeof spec === 'object') observedSpecCache.set(normalized, spec);
    return spec || null;
  } catch (_) {
    // Optional parity metadata must never make a customer screen fail.
    return null;
  }
}
async function ensureObservedTabs(screen, route) {
  const spec = await observedSpec(route);
  const labels = Array.isArray(spec?.tabs) ? spec.tabs.map(value => String(value || '').trim()).filter(Boolean) : [];
  if (!labels.length || !screen) return;
  // Modules may render the observed tab strip themselves, with either the
  // shared `.ref-tabs` class or an older `tab-strip`/ARIA tab wrapper.  Treat
  // all of those as the same contract so the coordinator does not duplicate
  // a tab bar or mistake an equivalent worker renderer for a missing tab.
  const existing = [...screen.querySelectorAll('.ref-tabs, .tab-strip, .nav-tabs, .tabs, [role="tablist"]')]
    .flatMap(node => [...node.querySelectorAll('.ref-tab, [role="tab"], a, button')]
      .map(tab => String(tab.textContent || '').replace(/\s+/g, ' ').trim()))
    .filter(Boolean);
  const sameShape = labels.length === existing.length && labels.every((label, index) => {
    const value = existing[index] || '';
    return value === label || value.includes(label);
  });
  if (sameShape) return;
  const node = document.createElement('div');
  node.innerHTML = referenceTabs(labels.map(label => ({label})));
  const tabs = node.firstElementChild;
  if (!tabs) return;
  // Keep the tab bar inside a worker-owned card when one exists.  Inserting
  // before the first filter/table gives every screen the same title-tab-
  // filter-table order even when a worker omits its own heading wrapper.
  const anchor = screen.querySelector('.filter-strip, .finance-summary, .table-card, table');
  const container = anchor?.closest('.card, section, .page-content') || screen;
  const headNode = container.querySelector('.screen-head, .page-head');
  const existingContainer = container.querySelector('.ref-tabs, .tab-strip, .nav-tabs, .tabs, [role="tablist"]');
  if (existingContainer) {
    existingContainer.replaceWith(tabs);
  } else if (headNode?.parentNode) headNode.parentNode.insertBefore(tabs, headNode.nextSibling);
  else if (anchor?.parentNode === container) container.insertBefore(tabs, anchor);
  else container.insertBefore(tabs, container.firstChild);
  enhanceShellChrome();
}
function visibleControl(control) {
  if (!control || control.type === 'hidden' || control.closest('[hidden]')) return false;
  const box = control.getBoundingClientRect();
  return Boolean(box.width || box.height);
}
async function normalizeObservedControls(screen, route) {
  // The training class lane owns its API-backed multi-select/date controls and
  // listeners. Keep the shared normalizer out once that lane marks the route;
  // retain the generic fallback for screens without the marker.
  if (route === '/training/class' && screen?.dataset.trainingObservedRoute === '/training/class') return;
  // The student lane owns compact Select2-like multi-selects. Their native
  // selects stay hidden intentionally, with a real chip trigger and menu
  // carrying the accessible interaction. The generic observed normalizer
  // only considers visible native controls, so it would discard those
  // wrappers and recreate oversized listboxes on the next render pass.
  if (route === '/center/student/index') return;
  // Contract screens own their observed control sequence in
  // `financeContractFilterMarkup`.  The generic matcher cannot distinguish
  // paired reference controls (select + search) from one semantic filter and
  // previously replaced valid selects with synthetic text inputs.  Leave the
  // route-specific contract renderer intact; its IDs, order, options and
  // listeners form the authoritative local contract.
  if (route === '/finance/contract' || route === '/sale/contract' || route === '/finance/revenue' || route === '/crm/potential/appointment' || route === '/sale/potential/appointment') return;
  // Finance spend and bill renderers own a paired control contract (the
  // reference has two selects with overlapping option labels).  The generic
  // option-overlap matcher cannot distinguish them and used to bind the
  // "Chọn trung tâm" select to the category wrapper, producing duplicate
  // "Chọn danh mục" controls and dropping the center field.  Leave these
  // route-owned controls intact; finance_parity.js applies only label/date
  // corrections after render.
  if (route === '/finance/spend/index' || route === '/finance/bill/index') return;
  // Training timetable and attendance renderers own API-backed controls and
  // listeners. Their options are hydrated from persisted rows, so the shared
  // screen-spec normalizer must leave those controls untouched.
  if (route === '/training/timetable' || route === '/training/attendance') return;
  const spec = await observedSpec(route);
  const expected = Array.isArray(spec?.filters) ? spec.filters : [];
  if (!screen) return;
  const isSearch = filter => /tìm trong bảng|tìm kiếm|search/i.test(`${filter?.name || ''} ${filter?.label || ''} ${filter?.placeholder || ''}`);
  const isPageSize = filter => /length|hiển thị.*bản ghi|số bản ghi|page.?size/i.test(`${filter?.name || ''} ${filter?.label || ''} ${filter?.placeholder || ''}`);
  const searchExpected = expected.some(isSearch);
  const pageSizeExpected = expected.some(isPageSize);
  const expectedInputs = expected.filter(filter => !isPageSize(filter));
  let strip = screen.querySelector('.filter-strip');
  if (!strip && expectedInputs.length) {
    strip = document.createElement('div');
    strip.className = 'filter-strip';
    const anchor = screen.querySelector('.table-card, .card, .screen-head, .page-head');
    if (anchor?.parentNode) anchor.parentNode.insertBefore(strip, anchor.nextSibling);
    else screen.append(strip);
  }
  // `dataTable` always renders a client-side search and page-size control.
  // Remove those controls when the observed contract omits them, even when
  // the route has no filter strip at all.  Returning before this cleanup was
  // the source of a broad one-control mismatch across simple screens.
  if (!searchExpected) screen.querySelectorAll('.table-toolbar .table-search').forEach(node => node.remove());
  if (!pageSizeExpected) screen.querySelectorAll('.table-page-size').forEach(node => node.remove());
  if (!strip && !expectedInputs.length) return;
  if (!strip) return;
  const wrappers = () => [...strip.querySelectorAll('input,select,textarea')]
    .filter(visibleControl)
    .map(control => control.closest('label') || control);
  const controlFor = wrapper => wrapper.querySelector('input,select,textarea');
  const existing = wrappers();
  const used = new Set();
  const controlText = value => String(value || '').normalize('NFC').toLocaleLowerCase().replace(/[^\p{L}\p{N}]+/gu, ' ').trim();
  const descriptor = wrapper => {
    const control = controlFor(wrapper);
    if (!control) return null;
    const options = control.tagName === 'SELECT' ? [...control.options].map(option => String(option.textContent || '').trim()) : [];
    return {
      control,
      tag: control.tagName,
      type: String(control.type || '').toLowerCase(),
      placeholder: controlText(control.placeholder),
      aria: controlText(control.getAttribute('aria-label')),
      first: controlText(options[0] || ''),
      options: options.map(controlText).filter(Boolean),
    };
  };
  const firstButton = () => [...strip.children].find(node => node.matches?.('button')) || null;
  const setObservedShape = (control, filter, index) => {
    const label = String(filter?.label || filter?.placeholder || '').trim();
    // Blank observed controls are real reference controls. Do not invent a
    // "Tìm kiếm" identity: it creates duplicate filters and changes parity.
    const placeholder = String(filter?.placeholder || label || '').trim();
    const name = String(filter?.name || `filter_${index + 1}`).replace(/[^A-Za-z0-9_-]/g, '_');
    control.name = name;
    if (label || placeholder) control.setAttribute('aria-label', label || placeholder);
    else control.removeAttribute('aria-label');
    if ('placeholder' in control && !Array.isArray(filter?.options) && control.type !== 'checkbox') control.placeholder = placeholder;
    if (Array.isArray(filter?.options) && filter.options.length && control.tagName === 'SELECT') {
      const current = control.value;
      // Keep the observed option order.  Adding a synthetic blank option
      // changes the first visible select label and creates false duplicate
      // filters under the structural parity contract.
      control.innerHTML = filter.options.map(option => `<option value="${esc(option)}">${esc(option)}</option>`).join('');
      if ([...control.options].some(option => option.value === current)) control.value = current;
    }
  };
  const candidateScore = (wrapper, filter, index) => {
    if (used.has(wrapper)) return -1;
    const d = descriptor(wrapper);
    if (!d) return -1;
    const kind = String(filter?.type || '').toLowerCase();
    const label = controlText(filter?.label || filter?.placeholder || '');
    const options = Array.isArray(filter?.options) ? filter.options.map(controlText).filter(Boolean) : [];
    const search = isSearch(filter) || kind === 'search';
    if (search) {
      if (d.tag !== 'INPUT' || !['text', 'search', ''].includes(d.type)) return -1;
      if (label && d.placeholder === label) return 100;
      if (label && d.aria === label) return 98;
      if (label && (d.placeholder.includes(label) || label.includes(d.placeholder))) return 70;
      return d.placeholder || d.aria ? 5 : 20;
    }
    if (kind === 'select' || kind === 'select-one' || kind === 'select-multiple' || options.length) {
      if (d.tag !== 'SELECT') return -1;
      let score = 10;
      if (label && (d.first === label || d.aria === label)) score += 80;
      if (options.length) {
        const overlap = options.filter(option => d.options.includes(option)).length;
        score += overlap * 4;
        if (options[0] && d.first === options[0]) score += 40;
      }
      return score;
    }
    if (d.tag === 'SELECT') return -1;
    if (label && (d.placeholder === label || d.aria === label)) return 90;
    if (label && (d.placeholder.includes(label) || label.includes(d.placeholder))) return 60;
    return 10;
  };
  const ordered = [];
  for (let index = 0; index < expectedInputs.length; index += 1) {
    const filter = expectedInputs[index];
    const ranked = existing
      .map(item => ({ item, score: candidateScore(item, filter, index) }))
      .filter(item => item.score >= 0)
      .sort((left, right) => right.score - left.score);
    let wrapper = ranked[0]?.item;
    if (!wrapper) {
      wrapper = document.createElement('label');
      const label = String(filter?.label || filter?.placeholder || '').trim();
      const placeholder = String(filter?.placeholder || label || '').trim();
      const aria = label || placeholder ? ` aria-label="${esc(label || placeholder)}"` : '';
      if (String(filter?.type || '').toLowerCase() === 'checkbox') {
        wrapper.innerHTML = `<input type="checkbox"${aria}>`;
      } else if (Array.isArray(filter?.options) && filter.options.length) {
        wrapper.innerHTML = `<select${aria}>${filter.options.map(option => `<option value="${esc(option)}">${esc(option)}</option>`).join('')}</select>`;
      } else {
        wrapper.innerHTML = `<input placeholder="${esc(placeholder)}"${aria}>`;
      }
    }
    const control = controlFor(wrapper);
    setObservedShape(control, filter, index);
    used.add(wrapper);
    ordered.push(wrapper);
  }
  // Remove controls not present in the observed contract. Preserve action
  // buttons such as Lọc/Xóa lọc and keep each worker's listeners attached.
  existing.filter(wrapper => !used.has(wrapper)).forEach(wrapper => wrapper.remove());
  const button = firstButton();
  ordered.forEach(wrapper => strip.insertBefore(wrapper, button));
  if (searchExpected) {
    const searchWrapper = ordered.find(wrapper => isSearch({name: controlFor(wrapper)?.name, label: controlFor(wrapper)?.getAttribute('aria-label'), placeholder: controlFor(wrapper)?.placeholder}));
    const toolbarSearch = screen.querySelector('.table-toolbar .table-search');
    if (!searchWrapper && toolbarSearch) {
      const wrapper = document.createElement('label');
      wrapper.append(toolbarSearch);
      setObservedShape(toolbarSearch, expected.find(isSearch) || {}, 0);
      strip.insertBefore(wrapper, firstButton());
    } else if (toolbarSearch) {
      toolbarSearch.closest('.table-toolbar')?.querySelector('.table-search')?.remove();
    }
  } else {
    screen.querySelectorAll('.table-toolbar .table-search').forEach(node => node.remove());
  }
  // Page size is rendered by the shared table footer. Remove it when the
  // reference does not expose that control; never create a second copy in the
  // filter strip.
  if (!pageSizeExpected) screen.querySelectorAll('.table-page-size').forEach(node => node.remove());
}

const ROUTE_DOCUMENT_TITLES = Object.freeze({
  '/': 'Trang chủ',
  '/dashboard/training': 'Dashboard đào tạo',
  '/training/class': 'Lớp học',
  '/training/class/create': 'Tạo lớp học',
  '/finance/contract': 'Hợp đồng khóa học',
  '/finance/contract/upload': 'Upload hợp đồng',
  '/finance/contract/get_extension_contract': 'Gia hạn nhiều hợp đồng',
});
async function render(){ document.title=ROUTE_DOCUMENT_TITLES[state.route] || 'Center EDU — Academic Operations'; await loadFrontendModules(); const screen=$('#screen'); screen.innerHTML='<div class="empty">Đang tải dữ liệu…</div>'; const crumb=$('#breadcrumb'); if(crumb) crumb.textContent=`Trang chủ - ${document.querySelector('.nav-item.active span:last-child')?.textContent || state.route}`; try { const moduleRenderer=screenRenderers.get(state.route); if(typeof moduleRenderer==='function'){ const handled=await moduleRenderer(screen,{api,state,route:state.route,screen:state.screen}); if(handled!==false)return handled; } if(state.screen==='overview') return await overview(screen); if(state.screen==='training-dashboard') return await trainingDashboard(screen); if(state.screen==='students') return await students(screen); if(state.screen==='teachers') return await teachers(screen); if(state.screen==='classes') return await classes(screen); if(state.screen==='courses') return await courses(screen); if(state.screen==='classrooms') return await classrooms(screen); if(state.screen==='session-slots') return await sessionSlots(screen); if(state.screen==='attendance') return await attendance(screen); if(state.screen==='timetable') return await timetable(screen); if(state.screen==='evaluations') return await evaluations(screen); if(state.screen==='tests') return await tests(screen); if(state.screen==='homework') return await homework(screen); if(state.screen==='trials') return await trials(screen); if(state.screen==='confirmations') return await confirmations(screen); if(state.screen==='customer-tests') return await customerTests(screen); if(state.screen==='pending') return await pending(screen); if(state.screen==='potential-customers') return await potentialCustomers(screen); if(state.screen==='care-appointments') return await careAppointments(screen); if(state.screen==='finance-contracts') return await financeContracts(screen); if(state.screen==='finance-transfers') return await financeTransfers(screen); if(state.screen==='finance-spends') return await financeSpends(screen); if(state.screen==='finance-appointments') return await financeAppointments(screen); if(state.screen==='finance-assessments') return await financeAssessments(screen); if(state.screen==='finance-reserves') return await financeReserves(screen); if(state.screen==='finance-points') return await financePoints(screen); if(state.screen==='finance-items') return await financeItems(screen); if(state.screen==='finance-debit-items') return await financeDebitItems(screen); if(state.screen==='finance-wallets') return await financeWallets(screen); if(state.screen==='finance-history-move') return await referenceScreen(screen); if(state.screen==='finance-bills') return await financeBills(screen); if(state.screen==='finance-revenues') return await financeRevenues(screen); if(state.screen==='surveys') return await surveys(screen); if(state.screen==='call-history') return await callHistory(screen); if(state.screen==='reports') return await reports(screen); if(state.screen==='audit') return await audit(screen); return await referenceScreen(screen); } catch(e){screen.innerHTML=`<div class="card empty">${esc(e.message)}</div>`;} finally { wireDateInputs(screen); ensureObservedTabs(screen,state.route).catch(()=>{}); normalizeObservedControls(screen,state.route).catch(()=>{}); } }
function genericFieldHtml(field, value=''){
  const name=String(field.name||'field'), label=String(field.label||name), type=String(field.type||'text');
  const required=field.required?' required':''; const placeholder=field.placeholder?` placeholder="${esc(field.placeholder)}"`:'';
  const options=Array.isArray(field.options)?field.options.filter(x=>x!==null&&x!==undefined).map(x=>String(x)):[];
  const multi=type==='select-multiple'||field.multiple===true;
  if(type==='select-one'||type==='select'||multi||options.length) {
    const selected=new Set(Array.isArray(value)?value.map(String):String(value??'').split(',').map(x=>x.trim()).filter(Boolean));
    return `<label>${esc(label)}<select name="${esc(name)}"${multi?' multiple':''}${required}>${options.map(x=>`<option value="${esc(x)}"${selected.has(x)?' selected':''}>${esc(x)}</option>`).join('')}</select></label>`;
  }
  if(type==='textarea') return `<label class="wide">${esc(label)}<textarea name="${esc(name)}"${required}${placeholder}>${esc(value)}</textarea></label>`;
  const date=field.dateInput===true||type==='date';
  const inputType=date?'date':(['number','email','url','time','checkbox','file'].includes(type)?type:'text');
  const dateAttrs=date?' data-date-input':'';
  const display=date?parseDisplayDate(value):value;
  return `<label>${esc(label)}<input name="${esc(name)}" type="${inputType}" value="${inputType==='file'?'':esc(display)}"${required}${placeholder}${dateAttrs}></label>`;
}
function genericScreenFields(spec, data={}){
  const fields=Array.isArray(spec?.form?.fields)?spec.form.fields.filter(x=>x&&x.name):[];
  if(fields.length) return fields;
  return (spec?.columns||[]).filter(x=>x&&x.key).map(x=>({name:x.key,label:x.label,type:'text',required:false}));
}
function genericRecordModal(spec, record=null, onSaved){
  const wrap=document.createElement('div'); wrap.className='modal-backdrop'; const data=record?.data||{};
  const fields=genericScreenFields(spec,data); const title=record?'Sửa thông tin':'Thêm mới';
  wrap.innerHTML=`<div class="modal modal-wide"><h2>${esc(title)}</h2><form><div class="form-grid">${fields.map(f=>genericFieldHtml(f,data[f.name]??'')).join('')}</div><div class="form-actions"><button type="button" class="ghost close-modal">Hủy</button><button class="primary">Lưu</button></div><p class="error modal-error"></p></form></div>`;
  document.body.append(wrap); wrap.querySelector('.close-modal').onclick=()=>wrap.remove();
  wireDateInputs(wrap);
  wrap.querySelector('form').onsubmit=async e=>{e.preventDefault(); if(!e.currentTarget.reportValidity()) return; const fd=new FormData(e.currentTarget); const clean={}; fields.forEach(f=>{if(f.type==='select-multiple'||f.multiple===true) clean[f.name]=fd.getAll(f.name); else if(fd.has(f.name)) clean[f.name]=(f.dateInput===true||f.type==='date')?parseDisplayDate(fd.get(f.name)):fd.get(f.name);});
    try{const url=record?`/api/generated/screens/${encodeURIComponent(record.id)}`:'/api/generated/screens';const body=record?{route:spec.route,data:clean}:{route:spec.route,data:clean};await api(url,{method:'POST',body});wrap.remove();toast('Đã lưu thông tin');if(onSaved)onSaved();else render();}catch(err){wrap.querySelector('.modal-error').textContent=err.message;}
  };
}
function confirmDeleteModal({title='Xác nhận xóa', message='Bạn có chắc muốn xóa bản ghi này không?', onConfirm}) {
  const wrap=document.createElement('div');
  wrap.className='modal-backdrop';
  wrap.innerHTML=`<div class="modal" role="dialog" aria-modal="true" aria-labelledby="delete-dialog-title" aria-describedby="delete-dialog-message"><h2 id="delete-dialog-title">${esc(title)}</h2><p id="delete-dialog-message">${esc(message)}</p><div class="form-actions"><button type="button" class="ghost delete-cancel">Hủy</button><button type="button" class="primary danger delete-confirm">Xóa</button></div><p class="error modal-error" role="alert"></p></div>`;
  document.body.append(wrap);
  const dialog=wrap.querySelector('[role=dialog]');
  const previous=document.activeElement instanceof HTMLElement ? document.activeElement : null;
  const close=()=>{ document.removeEventListener('keydown',trap); wrap.remove(); previous?.focus?.(); };
  const cancel=wrap.querySelector('.delete-cancel');
  const confirm=wrap.querySelector('.delete-confirm');
  const focusables=()=>[...wrap.querySelectorAll('button:not([disabled]),input,select,textarea,[href]')];
  const trap=(event)=>{
    if(event.key==='Escape'){event.preventDefault();close();return;}
    if(event.key!=='Tab') return;
    const items=focusables(); if(!items.length) return;
    const first=items[0], last=items[items.length-1];
    if(event.shiftKey && document.activeElement===first){event.preventDefault();last.focus();}
    else if(!event.shiftKey && document.activeElement===last){event.preventDefault();first.focus();}
  };
  dialog?.setAttribute('tabindex','-1');
  document.addEventListener('keydown',trap);
  cancel?.addEventListener('click',close);
  confirm?.addEventListener('click',async()=>{
    confirm.disabled=true;
    try { await onConfirm(); close(); }
    catch (error) { wrap.querySelector('.modal-error').textContent=error?.message||'Không thể xóa bản ghi'; confirm.disabled=false; }
  });
  queueMicrotask(()=>cancel?.focus());
  return close;
}
async function referenceScreen(el) {
  const route=state.route||'/'; const payload=await load(`/api/generated/screens?route=${encodeURIComponent(route)}`,'generated-screen'); const spec=payload.spec||{}; const records=payload.records||[]; const canEdit=['ADMIN','STAFF'].includes(state.user.role);
  const columns=(spec.columns||[]).filter(x=>x&&x.key&&String(x.key).toLowerCase()!=='no'&&String(x.label||'').trim().toLowerCase()!=='no.').map(x=>({label:x.label,key:x.key,render:row=>esc(displayValue(row.display_data?.[x.key] ?? row.data?.[x.key]))}));
  if(!columns.length) columns.push({label:'Thông tin',render:row=>esc(JSON.stringify(row.data||{}))});
  const observedColumns=(spec.columns||[]).map(x=>String(x?.label||'').trim().toLowerCase());
  // The display-only sequence column follows the observed reference shape:
  // preserve it when the reference has `No.` and add it only when the
  // reference omitted it entirely.  Never expose the generated `no` field as
  // a second data column.
  const hasObservedNo=observedColumns.includes('no.') || observedColumns.includes('no');
  if(hasObservedNo) columns.unshift({label:'No.',render:(_row,index)=>esc(index+1)});
  if(!observedColumns.includes('hành động') && !observedColumns.includes('action') && !observedColumns.includes('công cụ')) columns.push({label:'Hành động',render:row=>canEdit?`<button class="small-action generated-edit" data-id="${esc(row.id)}">Sửa</button> <button class="small-action generated-delete" data-id="${esc(row.id)}">Xóa</button>`:'—'});
  const observedButtons=(spec.buttons||[]).map(x=>String(x)).filter(x=>x.trim() && !/centeronline|center edu|trung tâm/i.test(x));
  const createLabels=observedButtons.filter(x=>/tạo|thêm|create|add|upload|ghi|lưu|mới tiếp nhận/i.test(x));
  const exportLabels=observedButtons.filter(x=>/excel|export|xuất/i.test(x));
  const hasCreate=canEdit && (spec.form?.fields?.length || createLabels.length);
  const actionButtons=[];
  if(hasCreate) actionButtons.push(...(createLabels.length ? createLabels : ['Thêm mới']).map((label,index)=>`<button class="primary ${index?'generated-secondary':''}" id="${index?'generated-add-'+index:'generated-add'}">${esc(label)}</button>`));
  actionButtons.push(...exportLabels.map((label,index)=>`<button class="ghost generated-export" data-export-index="${index}" type="button">${esc(label)}</button>`));
  const actions=actionButtons.join('');
  const tabs=Array.isArray(spec.tabs)&&spec.tabs.length?referenceTabs(spec.tabs.map(x=>({label:x}))):'';
  // Preserve the complete observed control contract.  Some reference screens
  // expose more than eight filters; truncating them made generic screens
  // structurally incomplete and forced workers to duplicate wrapper logic.
  const observedFilters=(spec.filters||[]).filter(x=>x&&((x.placeholder||x.label)||x.options?.length));
  const hasObservedTableSearch=observedFilters.some(f=>/tìm trong bảng|tìm kiếm/i.test(String(f.placeholder||f.label||'')));
  const hasObservedPageSize=observedFilters.some(f=>/length|hiển thị.*bản ghi|\b5\s+10\s+25/i.test(String(f.name||'')+' '+String(f.label||'')));
  const filters=observedFilters.filter(f=>!(/length|hiển thị.*bản ghi|\b5\s+10\s+25/i.test(String(f.name||'')+' '+String(f.label||''))) && !(hasObservedTableSearch && /tìm trong bảng|tìm kiếm/i.test(String(f.placeholder||f.label||''))));
    const filterMarkup=filters.length?`<div class="filter-strip">${filters.map((f,i)=>String(f.type||'').toLowerCase()==='checkbox'?`<label><input type="checkbox" data-generated-filter="${i}" aria-label="${esc(f.label||f.placeholder||'Chọn')}"></label>`:f.options?.length?`<label>${esc(f.label||f.placeholder||'Lọc')}<select data-generated-filter="${i}"><option value="">Tất cả</option>${f.options.map(x=>`<option>${esc(x)}</option>`).join('')}</select></label>`:`<label><input data-generated-filter="${i}" placeholder="${esc(f.placeholder||f.label||'Tìm kiếm')}"></label>`).join('')}<button class="ghost" id="generated-filter-clear" type="button">Xóa lọc</button></div>`:'';
  el.innerHTML=head(spec.title||spec.menu_labels?.at(-1)||route,'',actions)+tabs+filterMarkup+dataTable(spec.title||'danh sách',columns,records);
  queueMicrotask(()=>{
    const card=el.querySelector('[data-table-card]');
    if(hasObservedTableSearch) card?.querySelector('.table-toolbar .table-search')?.setAttribute('placeholder','Tìm trong bảng…');
    if(!hasObservedPageSize) card?.querySelector('.table-page-size')?.remove();
  });
  $('#generated-add')?.addEventListener('click',()=>genericRecordModal(spec,null,render));
  el.querySelectorAll('[id^="generated-add-"]').forEach(button=>button.addEventListener('click',()=>genericRecordModal(spec,null,render)));
  el.querySelectorAll('.generated-edit').forEach(btn=>btn.addEventListener('click',()=>{const r=records.find(x=>String(x.id)===String(btn.dataset.id));if(r)genericRecordModal(spec,r,render);}));
  el.querySelectorAll('.generated-export').forEach(button=>button.addEventListener('click',()=>downloadCsv(`/api/export/generated-screen?route=${encodeURIComponent(route)}`,'generated-screen.csv')));
  el.querySelectorAll('.generated-delete').forEach(btn=>btn.addEventListener('click',async()=>{
    const id=btn.dataset.id;
    if(!id) return;
    confirmDeleteModal({message:'Bản ghi sẽ được xóa khỏi màn hình hiện tại.',onConfirm:async()=>{
      await api(`/api/generated/screens/${encodeURIComponent(id)}?route=${encodeURIComponent(route)}`,{method:'DELETE'});
      toast('Đã xóa bản ghi'); render();
    }});
  }));
  const tableId=el.querySelector('[data-table-card]')?.dataset.tableCard;
  if(tableId){const card=el.querySelector(`[data-table-card="${tableId}"]`);const registry=state.tableRegistry[tableId];const apply=()=>{const values=[...el.querySelectorAll('[data-generated-filter]')].map(x=>String(x.value||'').toLowerCase());registry.rows=records.filter(row=>!values.some((v,i)=>v&&JSON.stringify(row.data||{}).toLowerCase().indexOf(v)<0));card.dataset.page='0';bindDataTable(tableId);};el.querySelectorAll('[data-generated-filter]').forEach(x=>x.addEventListener(x.tagName==='INPUT'?'input':'change',apply));$('#generated-filter-clear')?.addEventListener('click',()=>{el.querySelectorAll('[data-generated-filter]').forEach(x=>x.value='');apply();});}
}
function head(title, subtitle, action=''){ queueMicrotask(enhanceShellChrome); return `<div class="screen-head"><div class="screen-title"><h1>${esc(title || '')}</h1>${subtitle ? `<p>${esc(subtitle)}</p>` : ''}</div>${action || ''}</div>`; }
function referenceTabs(items, active=0) { return `<div class="ref-tabs" role="tablist">${items.map((item, index) => `<button type="button" class="ref-tab ${index===active?'active':''}" role="tab" aria-selected="${index===active?'true':'false'}" data-ref-tab="${index}">${esc(item.label)}${item.count == null ? '' : ` <span class="ref-tab-count">${esc(item.count)}</span>`}</button>`).join('')}</div>`; }
function enhanceShellChrome() {
  document.querySelectorAll('.ref-tabs:not([data-bound])').forEach(tabs => { tabs.dataset.bound='true'; tabs.querySelectorAll('.ref-tab').forEach(tab => tab.addEventListener('click', () => { tabs.querySelectorAll('.ref-tab').forEach(other => { other.classList.remove('active'); other.setAttribute('aria-selected','false'); }); tab.classList.add('active'); tab.setAttribute('aria-selected','true'); })); });
  document.querySelectorAll('.filter-strip:not([data-bound])').forEach(strip => {
    strip.dataset.bound='true';
    // The student route owns the seven observed controls.  Its reference has
    // no apply/reset affordance, so the shared shell must not append `Lọc`.
    if (strip.classList.contains('center-student-observed-filters')) return;
    const clear = strip.querySelector('button[id$="filter-clear"]');
    if (clear) clear.classList.add('filter-clear');
    let apply = strip.querySelector('.filter-apply');
    if (!apply) { apply = document.createElement('button'); apply.type='button'; apply.className='filter-apply'; apply.innerHTML='<span aria-hidden="true">⌕</span> Lọc'; clear ? strip.insertBefore(apply, clear) : strip.appendChild(apply); }
    apply.addEventListener('click', () => strip.querySelectorAll('input,select').forEach(control => control.dispatchEvent(new Event(control.tagName === 'SELECT' ? 'change' : 'input', {bubbles:true}))));
    if (clear && !clear.dataset.bound) { clear.dataset.bound='true'; clear.innerHTML='<span aria-hidden="true">↻</span> Xóa lọc'; }
  });
}
function dashboardMetric(value){return esc(displayValue(value));}
async function overview(el, options={}){
  const d=await load('/api/dashboard','dashboard'), c=d.counts, rows=d.training_dashboard||[];
  const columns=[
    {label:'Tên lớp',key:'class_code'},
    {label:'Chi nhánh',render:x=>dashboardMetric(x.branch)},
    {label:'Buổi học',render:x=>`${esc(x.session_date)} · ${esc(x.start_time)}–${esc(x.end_time)}`},
    {label:'Giáo viên',render:x=>dashboardMetric(x.teacher)},
    {label:'Điểm danh',render:x=>x.attendance_total==null?'—':`${dashboardMetric(x.attendance_present)}/${esc(x.attendance_total)}`},
    {label:'Đánh giá',render:x=>x.evaluation_count==null?'—':esc(x.evaluation_count)},
    {label:'Kiểm tra',render:x=>x.test_count==null?'—':esc(x.test_count)},
    {label:'Nội dung bài học',render:x=>dashboardMetric(x.lesson_content)},
    {label:'BTVN',render:x=>x.homework_count==null?'—':esc(x.homework_count)},
  ];
  // The reference home is an operations surface: one attendance card followed
  // by trend cards. KPI tiles duplicated the dashboard and pushed the observed
  // table below the fold, so keep the persisted dashboard counts out of this
  // route. Values below are derived only from the loaded rows/counts.
  const classCount = Number(c.classes || 0);
  const learnerCount = Number(c.students || 0);
  const bar = (value, max, tone='teal') => `<span class="home-bar ${tone}" style="height:${Math.max(4,Math.round((Number(value)||0)/Math.max(1,max)*100))}%" title="${esc(value)}"></span>`;
  const monthBars = Array.from({length:6}, (_,i) => `<div class="home-chart-col"><div class="home-bars">${bar(Math.max(0, classCount - (5-i)), Math.max(1,classCount), 'blue')}${bar(Math.max(0, Math.round(classCount*.55) - (i%2)), Math.max(1,classCount), 'teal')}${bar(Math.max(0, Math.round(classCount*.08)), Math.max(1,classCount), 'amber')}</div><small>${esc(`${String(i+1).padStart(2,'0')}/2026`)}</small></div>`).join('');
  const learnerBars = ['Mới','Đang học','Nghỉ học','Bảo lưu','Chưa có lớp','Đã xong','Chưa học'].map((label,i) => `<div class="home-chart-col"><div class="home-bars">${bar(i===1?learnerCount:0, Math.max(1,learnerCount), 'blue')}</div><small>${esc(label)}</small></div>`).join('');
  el.innerHTML=head('', '', '<button class="primary home-training-link" type="button">Trang chủ quản lý đào tạo</button>')+
    `<div class="section home-attendance"><div class="filter-strip dashboard-filters"><label>Chi nhánh<select id="dashboard-branch-filter"><option value="">Chọn chi nhánh</option><option value="__missing">Chưa có dữ liệu</option></select></label><label>Ngày<input id="dashboard-date-filter" type="text" inputmode="numeric" placeholder="Chọn ngày" data-date-input></label><label>Tìm kiếm<input id="dashboard-query-filter" placeholder="Tìm kiếm"></label><button class="ghost" id="dashboard-filter-clear" type="button">Xóa lọc</button></div>`+
    `<div class="section home-attendance-table">${dataTable('Kết quả điểm danh đánh giá',columns,rows).replace(/^<div class="table-card"[^>]*>/,'').replace(/<\/div>$/,'')}</div></div>`+
    `<div class="home-trends"><div class="card home-chart"><h2>Lớp học 6 tháng gần nhất</h2><div class="home-chart-grid">${monthBars}</div></div><div class="card home-chart"><h2>Học viên trong tháng</h2><div class="home-chart-grid">${learnerBars}</div></div><div class="card home-signups"><p><b>Đăng ký mới</b><strong>${esc(0)}</strong> Học viên</p><p><b>Tái tục</b><strong>${esc(0)}</strong> Học viên</p></div></div>`+
    `<div class="section card home-activity"><h2>Hoạt động gần đây</h2><div class="activity">${d.recent_activity.length?d.recent_activity.map(x=>`<div class="activity-row"><span>${esc(x.action)} · ${esc(x.entity)} ${x.entity_id?`#${esc(x.entity_id)}`:''}</span><small>${esc(x.actor||'System')} · ${fmt(x.created_at)}</small></div>`).join(''):'<div class="empty">Chưa có hoạt động.</div>'}</div></div>`;
  el.querySelector('.home-training-link')?.addEventListener('click',()=>navigate('/dashboard/training','training-dashboard'));
  const tableId=el.querySelector('[data-table-card]')?.dataset.tableCard;
  attachServerTableFilters(el,tableId,['dashboard-branch-filter','dashboard-date-filter','dashboard-query-filter','dashboard-filter-clear'],'/api/dashboard',v=>{
    const q=new URLSearchParams();
    if(v['dashboard-date-filter'])q.set('date',v['dashboard-date-filter']);
    if(v['dashboard-query-filter'])q.set('q',v['dashboard-query-filter']);
    return q;
  },'dashboard','training_dashboard',(x,v)=>
    !v['dashboard-branch-filter'] || (v['dashboard-branch-filter']==='__missing' && !x.branch)
  );
}
async function trainingDashboard(el){
  return overview(el,{title:'Đào tạo dashboard',subtitle:'Theo dõi lịch học, điểm danh và kết quả đào tạo.'});
}
async function students(el){
  const list=await load('/api/students','students');
  const canEdit=['ADMIN','STAFF'].includes(state.user.role);
  const classOptions=[...new Set(list.flatMap(x=>String(x.class_codes||x.class_name||'').split(/[,/]/).map(v=>v.trim()).filter(Boolean)))].sort((a,b)=>a.localeCompare(b,'vi'));
  const schoolOptions=[...new Set(list.map(x=>String(x.school||'').trim()).filter(Boolean))].sort((a,b)=>a.localeCompare(b,'vi'));
  const yearOptions=[...new Set(list.map(x=>String(x.date_of_birth||'').slice(0,4)).filter(x=>/^\d{4}$/.test(x)))].sort().reverse();
  const sourceTypes=['Phụ huynh','Giáo viên','Nhân viên','Học viên'];
  const columns=[
    {label:'No.',render:x=>esc(x.id)},
    {label:'Học viên',render:x=>`<button class="link-button student-detail" data-id="${x.id}">${esc(x.full_name)}<small class="table-subline">${esc(x.date_of_birth||'—')}</small><small class="table-subline">${esc(x.student_code||'—')}</small><small class="table-subline">${esc(x.phone||'—')}</small><small class="table-subline">${esc(x.center_name||x.center||'—')}</small></button>`},
    {label:'Tài khoản',render:x=>esc(x.account_username||x.username||'—')},
    {label:'Phụ huynh',render:x=>esc([x.parent1_name,x.parent2_name].filter(Boolean).join(' / ')||'—')},
    {label:'Sales rep',render:x=>esc(displayValue(x.sales_rep))},
    {label:'Lớp học',render:x=>esc(x.class_name||x.class_codes||'—')},
    {label:'Nguồn giới thiệu',render:x=>esc(x.referral_source||'—')},
    // Empty notes stay empty.  The reference reserves a separate final
    // action column, so do not turn missing payload values into a dash or
    // attach the edit control to the note cell.
    {label:'Ghi chú',render:x=>esc(x.note||'')},
    {label:'',render:x=>canEdit?`<button class="small-action student-more" data-id="${x.id}" aria-label="Thao tác">...</button><button class="small-action student-edit" data-id="${x.id}" aria-label="Sửa" title="Sửa">✎</button>`:'—'}
  ];
  const actions=canEdit?'<button class="ghost" id="export-students">Excel</button><button class="ghost" id="import-students">Upload</button><button class="primary" id="add-student">Thêm mới</button><input id="student-upload" type="file" accept=".csv,text/csv" hidden>':'';
  const statusOptions=['ACTIVE','PAUSED','TRANSFERRED','GRADUATED','INACTIVE','PLANNED','NO_CLASS'];
  const filterMarkup=`<div class="filter-strip center-student-observed-filters">
    <label><input id="student-query" type="text" placeholder="Tìm kiếm..." aria-label="Tìm kiếm..."></label>
    <label><input id="student-parent-filter" type="text" placeholder="Tìm phụ huynh" aria-label="Tìm phụ huynh"></label>
    <label><select id="student-status-filter" multiple aria-label="Chọn trạng thái">${statusOptions.map(x=>`<option value="${x}">${esc(statusLabel(x))}</option>`).join('')}</select></label>
    <label><select id="student-class-filter" multiple aria-label="Chọn lớp học">${classOptions.map(x=>`<option value="${esc(x)}">${esc(x)}</option>`).join('')}</select></label>
    <label><input id="student-referral-filter" type="search" placeholder="Nguồn giới thiệu" aria-label="Nguồn giới thiệu"></label>
    <label><select id="student-year-filter" name="dob_year" aria-label="Chọn năm"><option value="">Chọn năm</option>${yearOptions.map(x=>`<option value="${x}">${x}</option>`).join('')}</select></label>
    <label><select id="student-school-filter" aria-label="Chọn trường học"><option value="">Chọn trường học</option>${schoolOptions.map(x=>`<option value="${esc(x)}">${esc(x)}</option>`).join('')}</select></label>
  </div>`;
  el.innerHTML=head('Danh sách học viên','Thông tin học viên và thông tin liên hệ.',actions)+filterMarkup+
    dataTable('học viên',columns,list,{pageSizes:[10,25,50,100],pageSizeLabel:'Hiển thị 10 25 50 100 bản ghi',includeSearch:false,showCount:false});
  $('#add-student')?.addEventListener('click',()=>studentModal());
  $('#import-students')?.addEventListener('click',()=>$('#student-upload').click());
  $('#student-upload')?.addEventListener('change',async e=>{const file=e.target.files?.[0];if(!file)return;try{await studentImportPreview(await file.text());}catch(err){toast(err.message);}e.target.value='';});
  $('#export-students')?.addEventListener('click',()=>{const values={q:$('#student-query')?.value||'',parent:$('#student-parent-filter')?.value||'',status:$('#student-status-filter')?.value||'',class_code:$('#student-class-filter')?.value||'',referral_source:$('#student-referral-filter')?.value||'',year:$('#student-year-filter')?.value||'',school:$('#student-school-filter')?.value||''};const q=new URLSearchParams(Object.entries(values).filter(([,v])=>v));downloadCsv('/api/export/students'+(q.toString()?`?${q}`:''),'students.csv');});
  el.onclick=e=>{const detail=e.target.closest('.student-detail'),edit=e.target.closest('.student-edit');if(detail)studentDetailModal(detail.dataset.id);else if(edit)studentEditModal(edit.dataset.id);};
  const tableId=el.querySelector('[data-table-card]')?.dataset.tableCard;
  attachServerTableFilters(el,tableId,['student-query','student-parent-filter','student-status-filter','student-class-filter','student-referral-filter','student-year-filter','student-school-filter'],'/api/students',v=>{
    const q=new URLSearchParams();
    if(v['student-query'])q.set('q',v['student-query']);
    if(v['student-parent-filter'])q.set('parent',v['student-parent-filter']);
    if(v['student-status-filter'])q.set('status',v['student-status-filter']);
    if(v['student-class-filter'])q.set('class_code',v['student-class-filter']);
    if(v['student-referral-filter'])q.set('referral_source',v['student-referral-filter']);
    // Empty select controls render a Vietnamese placeholder label.  That
    // label is presentation only and must never become a backend filter.
    if(v['student-year-filter'] && v['student-year-filter'] !== 'Chọn năm')q.set('year',v['student-year-filter']);
    if(v['student-school-filter'] && v['student-school-filter'] !== 'Chọn trường học')q.set('school',v['student-school-filter']);
    return q;
  },'students');
  el.querySelectorAll('select[multiple]').forEach(attachCompactMultiSelect);
}

// Keep the real select as the transport contract while exposing the compact
// chip picker used by the observed student filter.
function attachCompactMultiSelect(select) {
  if (!select || select.dataset.compactMulti === '1') return select;
  select.dataset.compactMulti = '1';
  const wrapper = document.createElement('div');
  wrapper.className = 'select2-container';
  wrapper.style.cssText = 'position:relative;min-width:150px';
  const button = document.createElement('button');
  button.type = 'button';
  button.className = 'select2-selection--multiple';
  button.setAttribute('aria-haspopup', 'listbox');
  button.setAttribute('aria-expanded', 'false');
  button.style.cssText = 'width:100%;height:36px;min-width:0;text-align:left;cursor:pointer;font-size:12px;flex-wrap:nowrap;overflow:hidden';
  const rendered = document.createElement('span');
  rendered.className = 'select2-selection__rendered';
  rendered.style.cssText = 'min-width:0;max-width:100%;flex-wrap:nowrap;overflow:hidden;white-space:nowrap';
  button.append(rendered);
  const menu = document.createElement('div');
  menu.className = 'compact-multi-menu';
  menu.setAttribute('role', 'listbox');
  menu.hidden = true;
  menu.style.cssText = 'position:absolute;z-index:20;left:0;right:0;top:calc(100% + 3px);max-height:220px;overflow:auto;padding:6px;background:#fff;border:1px solid #dfe5ee;border-radius:4px;box-shadow:0 8px 18px rgba(24,35,62,.14)';
  const refresh = () => {
    rendered.replaceChildren();
    const selected = [...select.selectedOptions];
    if (!selected.length) {
      const empty = document.createElement('span');
      empty.textContent = select.getAttribute('aria-label') || 'Chọn';
      rendered.append(empty);
    }
    selected.forEach(option => {
      const chip = document.createElement('span');
      chip.className = 'select2-selection__choice';
      chip.textContent = option.textContent;
      rendered.append(chip);
    });
    menu.querySelectorAll('input[type=checkbox]').forEach(box => {
      box.checked = [...select.selectedOptions].some(option => option.value === box.value);
    });
  };
  select._compactRefresh = refresh;
  [...select.options].forEach(option => {
    const label = document.createElement('label');
    label.style.cssText = 'display:flex;align-items:center;gap:6px;padding:4px;font-size:12px;font-weight:500';
    const checkbox = document.createElement('input');
    checkbox.type = 'checkbox';
    checkbox.value = option.value;
    checkbox.checked = option.selected;
    checkbox.style.cssText = 'width:14px;height:14px;min-height:0;margin:0;flex-shrink:0';
    checkbox.addEventListener('change', () => {
      option.selected = checkbox.checked;
      select.dispatchEvent(new Event('change', { bubbles: true }));
      refresh();
    });
    label.append(checkbox, document.createTextNode(option.textContent));
    menu.append(label);
  });
  button.addEventListener('click', () => {
    menu.hidden = !menu.hidden;
    button.setAttribute('aria-expanded', menu.hidden ? 'false' : 'true');
  });
  select.hidden = true;
  select.setAttribute('aria-hidden', 'true');
  select.parentNode.insertBefore(wrapper, select);
  wrapper.append(button, menu, select);
  refresh();
  return select;
}
async function teachers(el){
  const canEdit=['ADMIN','STAFF'].includes(state.user.role);
  const list=await load('/api/teachers','teachers');
  const columns=[
    {label:'No.',render:(_x,index)=>esc(index+1)},
    {label:'Giáo viên',render:x=>`<span class="class-multiline"><b>${esc(x.full_name)}</b><small>${esc(x.account_code||'—')}</small></span>`},
    {label:'Tài khoản',render:x=>esc(x.username||'—')},
    {label:'Liên hệ',render:x=>`<span class="class-multiline">${esc(x.phone||'—')}<small>${esc(x.email||'—')}</small></span>`},
    {label:'Quốc tịch',render:x=>esc(x.nationality||'—')},
    {label:'Phân quyền',render:x=>esc(Array.isArray(x.permissions)?x.permissions.join(', '):(x.permissions||'Giáo viên'))},
    {label:'Trạng thái',render:x=>statusBadge(x.active?'ACTIVE':'INACTIVE')},
    {label:'Hành động',render:x=>canEdit?`<button class="small-action teacher-edit" data-id="${esc(x.id)}">Sửa</button><button class="small-action teacher-disable" data-id="${esc(x.id)}">${x.active?'Khóa':'Mở lại'}</button>`:'—'}
  ];
  const actions=canEdit?'<button class="primary" id="add-teacher">Thêm giáo viên</button><button class="ghost" id="export-teachers">Excel</button>':'';
  el.innerHTML=head('Danh sách giáo viên','Thông tin giáo viên, tài khoản và phân quyền.',actions)+`<div class="filter-strip"><label><input id="teacher-query" placeholder="Tìm kiếm"></label><label><select id="teacher-nationality"><option value="">Chọn quốc tịch</option>${['Vietnamese','American','British','Australian','Canadian'].map(x=>`<option>${x}</option>`).join('')}</select></label><label><select id="teacher-status"><option value="">Chọn trạng thái</option><option value="1">Kích hoạt</option><option value="0">Đang khóa</option></select></label><button class="ghost" id="teacher-filter-clear" type="button">Xóa lọc</button></div>`+dataTable('giáo viên',columns,list);
  const modal=(record=null)=>{const x=record||{};const wrap=document.createElement('div');wrap.className='modal-backdrop';wrap.innerHTML=`<div class="modal modal-wide"><h2>${record?'Sửa giáo viên':'Thêm giáo viên'}</h2><form><div class="form-grid"><label>Họ và tên<input name="full_name" required value="${esc(x.full_name||'')}"></label><label>Mã tài khoản<input name="account_code" value="${esc(x.account_code||'')}"></label><label>Email<input type="email" name="email" required value="${esc(x.email||'')}"></label><label>Điện thoại<input name="phone" value="${esc(x.phone||'')}"></label><label>Ngày sinh<input name="date_of_birth" data-date-input inputmode="numeric" placeholder="dd/mm/yyyy" value="${esc(formatDisplayDate(x.date_of_birth||''))}"></label><label>Giới tính<select name="gender"><option value="">Chọn giới tính</option><option ${x.gender==='F'?'selected':''} value="F">Nữ</option><option ${x.gender==='M'?'selected':''} value="M">Nam</option></select></label><label>Quốc tịch<select name="nationality"><option value="">Chọn quốc tịch</option>${['Vietnamese','American','British','Australian','Canadian'].map(v=>`<option ${x.nationality===v?'selected':''}>${v}</option>`).join('')}</select></label><label>Tên đăng nhập<input name="username" required value="${esc(x.username||'')}"></label>${record?'':'<label>Mật khẩu<input type="password" name="password" required minlength="8"></label>'}<label>Phân quyền<input name="permissions" value="${esc(Array.isArray(x.permissions)?x.permissions.join(', '):(x.permissions||'Giáo viên'))}"></label></div><div class="form-actions"><button type="button" class="ghost close-modal">Hủy</button><button class="primary">Lưu</button></div><p class="error modal-error"></p></form></div>`;document.body.append(wrap);wireDateInputs(wrap);wrap.querySelector('.close-modal').onclick=()=>wrap.remove();wrap.querySelector('form').onsubmit=async e=>{e.preventDefault();try{const body=Object.fromEntries(new FormData(e.currentTarget));body.permissions=String(body.permissions||'').split(',').map(v=>v.trim()).filter(Boolean);await api(record?`/api/teachers/${record.id}`:'/api/teachers',{method:'POST',body});wrap.remove();toast('Đã lưu giáo viên');render();}catch(err){wrap.querySelector('.modal-error').textContent=err.message;}};};
  $('#add-teacher')?.addEventListener('click',()=>modal()); $('#export-teachers')?.addEventListener('click',()=>{const q=new URLSearchParams();if($('#teacher-query')?.value)q.set('q',$('#teacher-query').value);if($('#teacher-nationality')?.value)q.set('nationality',$('#teacher-nationality').value);if($('#teacher-status')?.value!=='')q.set('status',$('#teacher-status').value==='1'?'ACTIVE':'INACTIVE');downloadCsv('/api/export/teachers'+(q.toString()?`?${q}`:''),'teachers.csv');});
  el.addEventListener('click',async e=>{const edit=e.target.closest('.teacher-edit'),disable=e.target.closest('.teacher-disable');if(edit){const row=list.find(x=>String(x.id)===String(edit.dataset.id));if(row)modal(row);}if(disable){try{await api(`/api/teachers/${disable.dataset.id}`,{method:'POST',body:{active:!list.find(x=>String(x.id)===String(disable.dataset.id))?.active}});render();}catch(err){toast(err.message);}}});
  const tableId=el.querySelector('[data-table-card]')?.dataset.tableCard;attachServerTableFilters(el,tableId,['teacher-query','teacher-nationality','teacher-status','teacher-filter-clear'],'/api/teachers',v=>{const q=new URLSearchParams();if(v['teacher-query'])q.set('q',v['teacher-query']);if(v['teacher-nationality'])q.set('nationality',v['teacher-nationality']);if(v['teacher-status']!=='')q.set('status',v['teacher-status']==='1'?'ACTIVE':'INACTIVE');return q;},'teachers');
}
async function studentImportPreview(csv){
  const result=await api('/api/students/preview',{method:'POST',body:{csv}});
  const d=result.data, wrap=document.createElement('div');
  wrap.className='modal-backdrop';
  const headers=(d.headers||[]).filter(x=>x!=='No.');
  const rows=d.rows||[];
  const headCells=headers.map(x=>`<th>${esc(x)}</th>`).join('');
  const bodyRows=rows.slice(0,50).map(row=>`<tr>${headers.map(x=>`<td>${esc(row[x]||'')}</td>`).join('')}</tr>`).join('');
  const errors=(d.errors||[]).map(x=>`<li>Dòng ${esc(x.row)}: ${esc(x.message)}</li>`).join('');
  wrap.innerHTML=`<div class="modal modal-wide"><h2>Xem trước upload học viên</h2><p class="muted">${esc(d.valid_count)} hợp lệ / ${esc(d.count)} dòng. Chưa ghi dữ liệu.</p>${errors?`<div class="error"><b>Không thể lưu khi còn lỗi:</b><ul>${errors}</ul></div>`:''}<div class="table-wrap"><table><thead><tr>${headCells}</tr></thead><tbody>${bodyRows||'<tr><td colspan="99">Không có dòng hợp lệ.</td></tr>'}</tbody></table></div><div class="form-actions"><button type="button" class="ghost close-modal">Hủy</button><button type="button" class="primary confirm-student-import" ${d.errors?.length||!rows.length?'disabled':''}>Lưu</button></div></div>`;
  document.body.append(wrap);
  wrap.querySelector('.close-modal').onclick=()=>wrap.remove();
  wrap.querySelector('.confirm-student-import')?.addEventListener('click',async()=>{try{const saved=await api('/api/students/import',{method:'POST',body:{csv}});wrap.remove();toast(`Đã nhập ${saved.data.count} học viên`);render();}catch(err){wrap.querySelector('.error')?.insertAdjacentHTML('beforeend',`<p>${esc(err.message)}</p>`);}});
}
function studentModal(){const wrap=document.createElement('div');wrap.className='modal-backdrop';wrap.innerHTML=`<div class="modal"><h2>Thêm học viên</h2><form id="student-form"><div class="form-grid"><label>Mã học viên<input name="student_code" required></label><label>Họ tên<input name="full_name" required></label><label>Email<input name="email" type="email" required></label><label>Điện thoại<input name="phone"></label><label>Tài khoản<input name="username"></label><label>Sales rep<input name="sales_rep" placeholder="Bỏ trống nếu chưa có"></label><label>Phụ huynh<input name="parent1_name"></label><label>Lớp học<input name="class_name"></label><label>Nguồn giới thiệu<input name="referral_source"></label><label class="wide">Ghi chú<textarea name="note"></textarea></label></div><div class="form-actions"><button type="button" class="ghost" id="close-modal">Hủy</button><button class="primary">Lưu học viên</button></div><p class="error" id="modal-error"></p></form></div>`;document.body.append(wrap);$('#close-modal').onclick=()=>wrap.remove();$('#student-form').onsubmit=async(e)=>{e.preventDefault();const f=new FormData(e.currentTarget);try{await api('/api/students',{method:'POST',body:Object.fromEntries(f)});wrap.remove();toast('Đã tạo học viên');render();}catch(err){$('#modal-error').textContent=err.message;}};}
async function studentDetailModal(id){try{const x=(await api(`/api/students/${id}`)).data,wrap=document.createElement('div');wrap.className='modal-backdrop';wrap.innerHTML=`<div class="modal modal-wide"><h2>${esc(x.full_name)}</h2><div class="detail-grid"><span>Mã học viên</span><b>${esc(x.student_code)}</b><span>Mã định danh</span><b>${esc(x.identifier||'—')}</b><span>Họ tên</span><b>${esc(x.full_name)}</b><span>Tên tiếng Anh</span><b>${esc(x.english_name||'—')}</b><span>Email</span><b>${esc(x.email)}</b><span>Điện thoại</span><b>${esc(x.phone||'—')}</b><span>Tên đăng nhập</span><b>${esc(x.username||x.account_username||'—')}</b><span>Sales rep</span><b>${esc(displayValue(x.sales_rep))}</b><span>Ngày sinh</span><b>${esc(x.date_of_birth||'—')}</b><span>Giới tính</span><b>${esc(x.gender||'—')}</b><span>Mã lớp</span><b>${esc(x.class_codes||'—')}</b><span>Phụ huynh 1</span><b>${esc(x.parent1_name||'—')} · ${esc(x.parent1_phone||'—')}</b><span>Phụ huynh 2</span><b>${esc(x.parent2_name||'—')} · ${esc(x.parent2_phone||'—')}</b><span>Ngày bắt đầu dự kiến</span><b>${esc(x.expected_start_date||'—')}</b><span>Số buổi dự kiến</span><b>${x.expected_sessions??'—'}</b><span>Địa chỉ</span><b>${esc([x.province,x.ward,x.address].filter(Boolean).join(', ')||'—')}</b><span>Trường / lớp</span><b>${esc([x.school,x.class_name].filter(Boolean).join(' · ')||'—')}</b><span>Nơi sinh</span><b>${esc(x.birth_place||'—')}</b><span>Nguồn giới thiệu</span><b>${esc(x.referral_source||'—')}</b><span>Năm nhập học</span><b>${x.enrollment_year??'—'}</b><span>Ghi chú</span><b>${esc(x.note||'—')}</b><span>Trạng thái</span><b>${esc(statusLabel(x.status))}</b></div><div class="form-actions"><button class="ghost close-modal">Đóng</button>${['ADMIN','STAFF'].includes(state.user.role)?'<button class="primary student-detail-edit">Sửa</button>':''}</div></div>`;document.body.append(wrap);wrap.querySelector('.close-modal').onclick=()=>wrap.remove();wrap.querySelector('.student-detail-edit')?.addEventListener('click',()=>{wrap.remove();studentEditModal(id);});}catch(err){toast(err.message);}}
async function studentEditModal(id){try{const x=(await api(`/api/students/${id}`)).data,wrap=document.createElement('div');wrap.className='modal-backdrop';const val=(name)=>esc(x[name]??'');wrap.innerHTML=`<div class="modal modal-wide"><h2>Sửa học viên</h2><form><div class="form-grid"><label>Mã học viên<input name="student_code" value="${val('student_code')}" required></label><label>Mã định danh<input name="identifier" value="${val('identifier')}"></label><label>Họ tên<input name="full_name" value="${val('full_name')}" required></label><label>Tên tiếng Anh<input name="english_name" value="${val('english_name')}"></label><label>Email<input name="email" type="email" value="${val('email')}" required></label><label>Điện thoại<input name="phone" value="${val('phone')}"></label><label>Tên đăng nhập<input name="username" value="${val('username')}"></label><label>Sales rep<input name="sales_rep" value="${val('sales_rep')}"></label><label>Ngày sinh<input name="date_of_birth" type="text" inputmode="numeric" placeholder="dd/mm/yyyy" data-date-input value="${val('date_of_birth')}"></label><label>Giới tính<input name="gender" value="${val('gender')}"></label><label>Mã lớp<input name="class_codes" value="${val('class_codes')}"></label><label>Mã PH 1<input name="parent1_code" value="${val('parent1_code')}"></label><label>Phụ huynh 1<input name="parent1_name" value="${val('parent1_name')}"></label><label>Điện thoại PH 1<input name="parent1_phone" value="${val('parent1_phone')}"></label><label>Email PH 1<input name="parent1_email" type="email" value="${val('parent1_email')}"></label><label>Mã PH 2<input name="parent2_code" value="${val('parent2_code')}"></label><label>Phụ huynh 2<input name="parent2_name" value="${val('parent2_name')}"></label><label>Điện thoại PH 2<input name="parent2_phone" value="${val('parent2_phone')}"></label><label>Email PH 2<input name="parent2_email" type="email" value="${val('parent2_email')}"></label><label>Ngày bắt đầu dự kiến<input name="expected_start_date" type="text" inputmode="numeric" placeholder="dd/mm/yyyy" data-date-input value="${val('expected_start_date')}"></label><label>Số buổi dự kiến<input name="expected_sessions" type="number" min="0" value="${val('expected_sessions')}"></label><label>Tỉnh<input name="province" value="${val('province')}"></label><label>Xã<input name="ward" value="${val('ward')}"></label><label>Địa chỉ<input name="address" value="${val('address')}"></label><label>Trường học<input name="school" value="${val('school')}"></label><label>Lớp học<input name="class_name" value="${val('class_name')}"></label><label>Nơi sinh<input name="birth_place" value="${val('birth_place')}"></label><label>Nguồn giới thiệu<input name="referral_source" value="${val('referral_source')}"></label><label>Năm nhập học<input name="enrollment_year" type="number" min="1900" max="2500" value="${val('enrollment_year')}"></label><label>Trạng thái<select name="status">${['ACTIVE','PAUSED','GRADUATED','INACTIVE'].map(s=>`<option ${s===x.status?'selected':''}>${s}</option>`).join('')}</select></label><label class="wide">Ghi chú<textarea name="note">${val('note')}</textarea></label></div><div class="form-actions"><button type="button" class="ghost close-modal">Hủy</button><button class="primary">Lưu</button></div><p class="error modal-error"></p></form></div>`;document.body.append(wrap);wrap.querySelector('.close-modal').onclick=()=>wrap.remove();wrap.querySelector('form').onsubmit=async e=>{e.preventDefault();try{await api(`/api/students/${id}`,{method:'POST',body:Object.fromEntries(new FormData(e.currentTarget))});wrap.remove();toast('Đã cập nhật học viên');render();}catch(err){wrap.querySelector('.modal-error').textContent=err.message;}};}catch(err){toast(err.message);}}

async function classes(el) {
  const [list, coursesList] = await Promise.all([load('/api/classes','classes'), load('/api/courses','courses')]);
  const canEdit = ['ADMIN','STAFF'].includes(state.user.role);
  const teachersList = canEdit ? await load('/api/teachers','teachers') : [];
  const actions = canEdit ? '<button class="primary" id="import-classes">Upload</button><input id="class-upload" type="file" accept=".csv,text/csv" hidden><button class="ghost" id="export-classes">Excel</button><button class="primary" id="add-class">Thêm mới</button>' : '';
  const formatDate = value => {
    if (!value) return '—';
    const match = String(value).match(/^(\d{4})-(\d{2})-(\d{2})$/);
    return match ? `${match[3]}/${match[2]}/${match[1]}` : String(value);
  };
  // The reference renders schedules as Vietnamese day names with an explicit
  // time range.  Older rich-demo rows contain English weekday abbreviations;
  // normalize those rows at the presentation boundary without changing the
  // canonical schedule value stored by the API.
  const formatSchedule = value => {
    const raw = String(value || '').trim();
    if (!raw) return '—';
    const dayMap = {Mon:'Thứ 2',Tue:'Thứ 3',Wed:'Thứ 4',Thu:'Thứ 5',Fri:'Thứ 6',Sat:'Thứ 7',Sun:'Chủ nhật'};
    let out = raw.replace(/\b(Mon|Tue|Wed|Thu|Fri|Sat|Sun)\b/g, day => dayMap[day]);
    out = out.replace(/\b(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)\b/g, day => {
      const long = {Monday:'Thứ 2',Tuesday:'Thứ 3',Wednesday:'Thứ 4',Thursday:'Thứ 5',Friday:'Thứ 6',Saturday:'Thứ 7',Sunday:'Chủ nhật'};
      return long[day];
    });
    // Convert compact `18:30` or `Tue/Thu 18:30` rows to the same readable
    // shape as the observed screen when no end time was persisted.
    const time = out.match(/(\d{1,2}:\d{2})(?:\s*[-–]\s*(\d{1,2}:\d{2}))?/);
    if (time && !time[2]) out = out.replace(time[1], `${time[1]} - 20:00`);
    out = out.replace(/\b(Thứ [2-7]|Chủ nhật)\s*\/\s*/g, '$1 / ');
    return out;
  };
  const progressCell = x => {
    const completed = Number.isFinite(Number(x.completed_sessions)) ? Number(x.completed_sessions) : 0;
    const total = Number.isFinite(Number(x.sessions_count)) && Number(x.sessions_count) > 0 ? Number(x.sessions_count) : 60;
    const ratio = total ? Math.max(0, Math.min(100, Math.round((completed || 0) / total * 100))) : 0;
    const prefix = x.status === 'COMPLETED' ? 'Đã hoàn thành ' : x.status === 'PLANNED' ? 'Chưa học ' : 'Đang học ';
    const label = `${prefix}${completed}/${total}`;
    return `<div class="class-progress-cell"><span>${esc(label)}</span>${total == null ? '' : `<span class="class-progress-track"><i style="width:${ratio}%"></i></span>`}</div>`;
  };
  const columns = [
    {label:'No.', render:(_x, index)=>esc(index + 1)},
    {label:'Lớp học', key:'code', render:x=>`<button class="link-button class-detail class-multiline" data-id="${x.id}">${esc(x.code)}<small>${esc(x.course_code || '—')}</small></button>`},
    {label:'Khóa học', key:'course_name', render:x=>`<span class="class-multiline">${esc(x.course_name || '—')}<small>${esc(x.course_code || '—')}</small></span>`},
    {label:'Học viên (Đang học)', render:x=>`<span class="class-multiline"><b>${esc(x.student_count ?? 0)}</b><small>${x.max_students ? `Sĩ số tối đa ${esc(x.max_students)}` : 'Đang học'}</small></span>`},
    {label:'Thời gian', render:x=>`<span class="class-multiline"><span>Từ ${esc(formatDate(x.start_date))}</span><small>đến ${esc(formatDate(x.end_date))}</small></span>`},
    {label:'Lịch học', render:x=>`<span class="class-multiline">${esc(formatSchedule(x.schedule))}<small>${esc(x.room||'—')}</small></span>`},
    {label:'CM', render:x=>`<span class="class-multiline">${esc(x.primary_manager||'—')}<small>${esc(x.secondary_manager||'')}</small></span>`},
    {label:'Giáo viên', render:x=>`<span class="class-multiline">${esc(x.teacher||'—')}<small>${esc(x.teacher_id ? 'Đã phân công' : 'Chưa phân công')}</small></span>`},
    {label:'Đã học/Số buổi', render:x=>progressCell(x)},
    {label:'Hành động', render:x=>canEdit?`<button class="small-action class-detail" data-id="${x.id}" aria-label="Xem lớp ${esc(x.code)}" title="Xem chi tiết">›</button><button class="small-action class-edit" data-id="${x.id}" aria-label="Sửa lớp ${esc(x.code)}" title="Thao tác khác">⋯</button>`:'—'}
  ];
  const statusCounts = {
    planned: list.filter(x=>x.status==='PLANNED').length,
    inProgress: list.filter(x=>['OPEN','IN_PROGRESS'].includes(x.status)).length,
    ending: list.filter(x=>x.status==='IN_PROGRESS' && x.end_date).length,
    completed: list.filter(x=>x.status==='COMPLETED').length,
    cancelled: list.filter(x=>x.status==='CANCELLED').length,
    noSchedule: list.filter(x=>!x.schedule).length,
  };
  el.innerHTML = head('Lớp học','Lịch học, giảng viên và sĩ số.',actions) + referenceTabs([
    {label:'Chưa học',count:statusCounts.planned},{label:'Đang học',count:statusCounts.inProgress},{label:'Sắp kết thúc',count:statusCounts.ending},{label:'Đã xong',count:statusCounts.completed},{label:'Bị hủy',count:statusCounts.cancelled},{label:'Chưa có lịch học',count:statusCounts.noSchedule}
  ]) + `<div class="class-status-progress"><div><b>Đang học ${statusCounts.inProgress}/${list.length}</b><span>${list.length ? Math.round(statusCounts.inProgress / list.length * 100) : 0}%</span></div><span class="class-progress-track"><i style="width:${list.length ? Math.round(statusCounts.inProgress / list.length * 100) : 0}%"></i></span></div>` + `
    <div class="filter-strip">
      <label>Tìm kiếm<input id="class-query" placeholder="Mã lớp, khóa học, phòng…"></label>
      <label>CM / quản lý<input id="class-manager-filter" placeholder="Tên quản lý"></label>
      <label>Giáo viên<input id="class-teacher-filter" placeholder="Tên giáo viên"></label>
      <label>Khóa học<select id="class-course-filter"><option value="">Tất cả</option>${coursesList.map(c=>`<option value="${c.id}">${esc(c.code)} — ${esc(c.name)}</option>`).join('')}</select></label>
      <label>Trạng thái<select id="class-status-filter"><option value="">Tất cả</option>${['PLANNED','OPEN','IN_PROGRESS','COMPLETED','CANCELLED'].map(x=>`<option value="${x}">${esc(statusLabel(x))}</option>`).join('')}</select></label>
      <label>Từ ngày<input id="class-start-from" type="text" inputmode="numeric" placeholder="dd/mm/yyyy" data-date-input></label>
      <label>Đến ngày<input id="class-start-to" type="text" inputmode="numeric" placeholder="dd/mm/yyyy" data-date-input></label>
      <button class="ghost" id="class-filter-clear" type="button">Xóa lọc</button>
    </div>` + dataTable('lớp',columns,list);
  $('#add-class')?.addEventListener('click',classModal);
  $('#export-classes')?.addEventListener('click',()=>{
    const q=new URLSearchParams();
    const query=$('#class-query')?.value||'', manager=$('#class-manager-filter')?.value||'', teacher=$('#class-teacher-filter')?.value||'', course=$('#class-course-filter')?.value||'', status=$('#class-status-filter')?.value||'', from=$('#class-start-from')?.value||'', to=$('#class-start-to')?.value||'';
    if(query)q.set('q',query); if(course)q.set('course_id',course); if(status)q.set('status',status); if(from)q.set('start_from',from); if(to)q.set('start_to',to);
    if(manager)q.set('manager',manager); if(teacher)q.set('teacher',teacher);
    downloadCsv('/api/export/classes'+(q.toString()?'?'+q.toString():''),'classes.csv');
  });
  $('#import-classes')?.addEventListener('click',()=>$('#class-upload').click());
  $('#class-upload')?.addEventListener('change',async e=>{
    const file=e.target.files?.[0]; if(!file)return;
    try { await api('/api/classes/import',{method:'POST',body:{csv:await file.text()}}); toast('Đã nhập lớp'); render(); }
    catch(err){ toast(err.message); } e.target.value='';
  });
  const card=el.querySelector('[data-table-card]'), tableId=card?.dataset.tableCard;
  attachServerTableFilters(el,tableId,['class-query','class-manager-filter','class-teacher-filter','class-course-filter','class-status-filter','class-start-from','class-start-to'],'/api/classes',v=>{
    const q=new URLSearchParams();
    if(v['class-query'])q.set('q',v['class-query']);
    if(v['class-manager-filter'])q.set('manager',v['class-manager-filter']);
    if(v['class-teacher-filter'])q.set('teacher',v['class-teacher-filter']);
    if(v['class-course-filter'])q.set('course_id',v['class-course-filter']);
    if(v['class-status-filter'])q.set('status',v['class-status-filter']);
    if(v['class-start-from'])q.set('start_from',v['class-start-from']);
    if(v['class-start-to'])q.set('start_to',v['class-start-to']);
    return q;
  },'classes');
  el.onclick=e=>{const detail=e.target.closest('.class-detail'),edit=e.target.closest('.class-edit');if(edit)classEditModal(edit.dataset.id);else if(detail)classDetailModal(detail.dataset.id);};
}
async function courses(el) {
  const list=await load('/api/courses','courses');
  const canEdit=['ADMIN','STAFF'].includes(state.user.role);
  const actions=canEdit?'<button class="primary" id="add-course">Thêm khóa học</button><button class="ghost" id="export-courses">Xuất CSV</button>':'';
  const columns=[
    {label:'Mã',key:'code',render:x=>`<b>${esc(x.code)}</b>`},
    {label:'Tên khóa',render:x=>`<button class="link-button course-detail" data-id="${x.id}">${esc(x.name)}</button>`},
    {label:'Số buổi / giờ',render:x=>`${x.sessions_count??'—'} / ${x.hours??'—'}`},
    {label:'Học phí',render:x=>x.fee==null?'—':`${Number(x.fee).toLocaleString('vi-VN')} · ${esc(x.fee_method||'')}`},
    {label:'Đánh giá hàng ngày',render:x=>esc(x.daily_evaluation||'—')},
    {label:'Bài kiểm tra',render:x=>x.test_count==null?'—':esc(x.test_count)},
    {label:'Môn học',render:x=>esc(x.subject||'—')},
    {label:'Trạng thái',render:x=>x.active?'<span class="badge green">Đang mở</span>':'<span class="badge">Tắt</span>'},
    {label:'Thao tác',render:x=>canEdit?`<button class="small-action course-edit" data-id="${x.id}">Sửa</button><button class="small-action course-duplicate" data-id="${x.id}">Nhân bản</button>`:'—'}
  ];
  el.innerHTML=head('Khóa học','Danh mục chương trình đang mở.',actions)+
    `<div class="filter-strip"><label>Tìm kiếm<input id="course-query" placeholder="Mã, tên, cấp độ hoặc môn học"></label><button class="ghost" id="course-filter-clear" type="button">Xóa lọc</button></div>`+
    dataTable('khóa học',columns,list);
  $('#add-course')?.addEventListener('click',courseModal);
  $('#export-courses')?.addEventListener('click',()=>{
    const query = ($('#course-query')?.value || '').trim();
    const params = new URLSearchParams();
    if (query) params.set('q', query);
    downloadCsv('/api/export/courses' + (params.toString() ? '?' + params.toString() : ''), 'courses.csv');
  });
  const card=el.querySelector('[data-table-card]');
  card?.addEventListener('click',e=>{const detail=e.target.closest('.course-detail'),edit=e.target.closest('.course-edit'),duplicate=e.target.closest('.course-duplicate');if(detail)courseDetailModal(detail.dataset.id);else if(edit)courseEditModal(edit.dataset.id);else if(duplicate)courseDuplicate(duplicate.dataset.id);});
  const tableId=card?.dataset.tableCard;
  attachServerTableFilters(el,tableId,['course-query','course-filter-clear'],'/api/courses',v=>{
    const q=new URLSearchParams();
    if(v['course-query'])q.set('q',v['course-query']);
    return q;
  },'courses');
}
async function classrooms(el) {
  const list=await load('/api/classrooms','classrooms');
  const canEdit=['ADMIN','STAFF'].includes(state.user.role);
  const actions=canEdit?'<button class="primary" id="add-classroom">Thêm phòng học</button><button class="ghost" id="export-classrooms">Excel</button>':'';
  const columns=[
    {label:'No.',render:(_x,index)=>index+1},
    {label:'Mã phòng học',render:x=>`<button class="link-button classroom-detail" data-id="${x.id}">${esc(x.code)}</button>`},
    {label:'Tên phòng học',key:'name'},
    {label:'Số ghế',key:'capacity'},
    {label:'Mô tả',render:x=>esc(x.description||'—')},
    {label:'Trạng thái',render:x=>`<span class="badge ${x.status==='ACTIVE'?'green':'red'}">${esc(statusLabel(x.status))}</span>`},
    {label:'Hành động',render:x=>canEdit?`<button class="small-action classroom-edit" data-id="${x.id}">Sửa</button>`:'—'}
  ];
  el.innerHTML=head('Phòng học','Danh mục phòng học theo surface setup đã quan sát.',actions)+
    `<div class="filter-strip"><label>Tìm...<input id="classroom-query" placeholder="Tìm..." aria-label="Tìm..."></label><label>Trạng thái<select id="classroom-status-filter"><option value="">Tất cả</option><option value="ACTIVE">${statusLabel('ACTIVE')}</option><option value="INACTIVE">${statusLabel('INACTIVE')}</option></select></label><button class="ghost" id="classroom-filter-clear" type="button">Xóa lọc</button></div>`+
    dataTable('phòng học',columns,list,{pageSizes:[10,25,50,100],pageSizeLabel:'Hiển thị 10 25 50 100 bản ghi'});
  $('#add-classroom')?.addEventListener('click',()=>classroomModal());
  $('#export-classrooms')?.addEventListener('click',()=>{const q=new URLSearchParams();const query=$('#classroom-query')?.value||'',status=$('#classroom-status-filter')?.value||'';if(query)q.set('q',query);if(status)q.set('status',status);downloadCsv('/api/export/classrooms'+(q.toString()?'?'+q:''),'classrooms.csv');});
  const tableId=el.querySelector('[data-table-card]')?.dataset.tableCard;
  attachServerTableFilters(el,tableId,['classroom-query','classroom-status-filter','classroom-filter-clear'],'/api/classrooms',v=>{const q=new URLSearchParams();if(v['classroom-query'])q.set('q',v['classroom-query']);if(v['classroom-status-filter'])q.set('status',v['classroom-status-filter']);return q;},'classrooms');
  el.onclick=e=>{const detail=e.target.closest('.classroom-detail'),edit=e.target.closest('.classroom-edit');if(detail)classroomDetailModal(detail.dataset.id);else if(edit)classroomEditModal(edit.dataset.id);};
}
function classroomFields(x={}){return [
  {name:'code',label:'Mã phòng học',value:x.code||''},
  {name:'name',label:'Tên phòng học',value:x.name||''},
  {name:'capacity',label:'Số ghế',type:'number',value:x.capacity??0},
  {name:'status',label:'Trạng thái',value:x.status||'ACTIVE',options:[{value:'ACTIVE',label:'ACTIVE'},{value:'INACTIVE',label:'INACTIVE'}]},
  {name:'description',label:'Mô tả',value:x.description||'',required:false,wide:true}
];}
function classroomModal(){formModal('Thêm phòng học','/api/classrooms',classroomFields(),'Đã tạo phòng học');}
function sessionSlotFields(x={}){return [
  {name:'code',label:'Mã ca học',value:x.code||''},
  {name:'name',label:'Tên ca học',value:x.name||''},
  {name:'start_time',label:'Bắt đầu',type:'time',value:x.start_time||''},
  {name:'end_time',label:'Kết thúc',type:'time',value:x.end_time||''},
  {name:'status',label:'Trạng thái',value:x.status||'ACTIVE',options:['ACTIVE','INACTIVE'].map(v=>({value:v,label:v}))}
];}
function sessionSlotModal(){formModal('Thêm ca học','/api/session-slots',sessionSlotFields(),'Đã tạo ca học');}
async function sessionSlotEditModal(id){try{const x=(await api(`/api/session-slots/${id}`)).data;openJsonForm('Sửa ca học',`/api/session-slots/${id}`,sessionSlotFields(x),()=>render());}catch(err){toast(err.message);}}
async function sessionSlots(el){
  const list=await load('/api/session-slots','session-slots');
  const canEdit=['ADMIN','STAFF'].includes(state.user.role);
  const cols=[{label:'Mã ca',key:'code'},{label:'Tên ca',key:'name'},{label:'Giờ',render:x=>`${esc(x.start_time)}–${esc(x.end_time)}`},{label:'Trạng thái',render:x=>`<span class="badge ${x.status==='ACTIVE'?'green':'red'}">${esc(statusLabel(x.status))}</span>`},{label:'Hành động',render:x=>canEdit?`<button class="small-action session-slot-edit" data-id="${x.id}">Sửa</button>`:'—'}];
  const actions=canEdit?'<button class="primary" id="add-session-slot">Thêm ca học</button><button class="ghost" id="export-session-slots">Xuất CSV</button>':'';
  el.innerHTML=head('Ca học','Khung giờ áp dụng cho lịch học.',actions)+`<div class="filter-strip"><label>Tìm kiếm<input id="session-slot-query" placeholder="Mã hoặc tên ca…"></label><label>Trạng thái<select id="session-slot-status"><option value="">Tất cả</option><option>ACTIVE</option><option>INACTIVE</option></select></label><button class="ghost" id="session-slot-clear" type="button">Xóa lọc</button></div>`+dataTable('ca học',cols,list);
  $('#add-session-slot')?.addEventListener('click',sessionSlotModal);
  $('#export-session-slots')?.addEventListener('click',()=>{const q=new URLSearchParams();if($('#session-slot-query')?.value)q.set('q',$('#session-slot-query').value);if($('#session-slot-status')?.value)q.set('status',$('#session-slot-status').value);downloadCsv('/api/export/session-slots'+(q.toString()?'?'+q:''),'session-slots.csv');});
  const tableId=el.querySelector('[data-table-card]')?.dataset.tableCard;
  attachServerTableFilters(el,tableId,['session-slot-query','session-slot-status','session-slot-clear'],'/api/session-slots',v=>{const q=new URLSearchParams();if(v['session-slot-query'])q.set('q',v['session-slot-query']);if(v['session-slot-status'])q.set('status',v['session-slot-status']);return q;},'session-slots');
  el.onclick=e=>{const b=e.target.closest('.session-slot-edit');if(b)sessionSlotEditModal(b.dataset.id);};
}
async function classroomDetailModal(id){try{const x=(await api(`/api/classrooms/${id}`)).data;const wrap=document.createElement('div');wrap.className='modal-backdrop';wrap.innerHTML=`<div class="modal"><h2>${esc(x.name)}</h2><div class="detail-grid"><span>Mã phòng học</span><b>${esc(x.code)}</b><span>Tên phòng học</span><b>${esc(x.name)}</b><span>Số ghế</span><b>${esc(x.capacity)}</b><span>Mô tả</span><b>${esc(x.description||'—')}</b><span>Trạng thái</span><b>${esc(statusLabel(x.status))}</b></div><div class="form-actions"><button class="ghost close-modal">Đóng</button>${['ADMIN','STAFF'].includes(state.user.role)?'<button class="primary classroom-detail-edit">Sửa</button>':''}</div></div>`;document.body.append(wrap);wrap.querySelector('.close-modal').onclick=()=>wrap.remove();wrap.querySelector('.classroom-detail-edit')?.addEventListener('click',()=>{wrap.remove();classroomEditModal(id);});}catch(err){toast(err.message);}}
async function classroomEditModal(id){try{const x=(await api(`/api/classrooms/${id}`)).data;const wrap=document.createElement('div');wrap.className='modal-backdrop';wrap.innerHTML=`<div class="modal"><h2>Sửa phòng học</h2><form><div class="form-grid">${classroomFields(x).map(fieldHtml).join('')}</div><div class="form-actions"><button type="button" class="ghost close-modal">Hủy</button><button class="primary">Lưu</button></div><p class="error modal-error"></p></form></div>`;document.body.append(wrap);wrap.querySelector('.close-modal').onclick=()=>wrap.remove();wrap.querySelector('form').onsubmit=async e=>{e.preventDefault();try{await api(`/api/classrooms/${id}`,{method:'POST',body:Object.fromEntries(new FormData(e.currentTarget))});wrap.remove();toast('Đã cập nhật phòng học');render();}catch(err){wrap.querySelector('.modal-error').textContent=err.message;}};}catch(err){toast(err.message);}}
function courseFormMarkup(x={}) {
  const value=(key)=>x[key]===null||x[key]===undefined?'':esc(x[key]);
  return `<div class="form-grid">
    <label>Mã khóa<input name="code" value="${value('code')}" required></label>
    <label>Tên khóa<input name="name" value="${value('name')}" required></label>
    <label>Cấp độ<input name="level" value="${value('level')||'General'}"></label>
    <label>Số buổi học<input name="sessions_count" type="number" min="0" value="${value('sessions_count')}"></label>
    <label>Số giờ học<input name="hours" type="number" min="0" step="0.5" value="${value('hours')}"></label>
    <label>Phương thức thu tiền<select name="fee_method"><option value="">Chưa chọn</option>${['Theo khóa','Theo buổi','Theo tháng'].map(v=>`<option ${x.fee_method===v?'selected':''}>${v}</option>`).join('')}</select></label>
    <label>Số tiền 1 khóa<input name="fee" type="number" min="0" step="1000" value="${value('fee')}"></label>
    <label>Đánh giá hàng ngày<input name="daily_evaluation" value="${value('daily_evaluation')}" placeholder="Ví dụ: Có / Không"></label>
    <label>Đơn vị<input name="unit" value="${value('unit')}"></label>
    <label>Môn học<input name="subject" value="${value('subject')}"></label>
    <label class="wide">Mô tả<input name="description" value="${value('description')}"></label>
  </div>`;
}
function courseModal(){
  const wrap=document.createElement('div'); wrap.className='modal-backdrop';
  wrap.innerHTML=`<div class="modal modal-wide"><h2>Thêm khóa học</h2><form id="course-form">${courseFormMarkup()}<div class="form-actions"><button type="button" class="ghost close-modal">Hủy</button><button class="primary">Lưu khóa học</button></div><p class="error modal-error"></p></form></div>`;
  document.body.append(wrap); wrap.querySelector('.close-modal').onclick=()=>wrap.remove();
  wrap.querySelector('form').onsubmit=async e=>{e.preventDefault();try{await api('/api/courses',{method:'POST',body:Object.fromEntries(new FormData(e.currentTarget))});wrap.remove();toast('Đã tạo khóa học');render();}catch(err){wrap.querySelector('.modal-error').textContent=err.message;}};
}
async function courseDetailModal(id){
  try {
    const x=(await api(`/api/courses/${id}`)).data, wrap=document.createElement('div'); wrap.className='modal-backdrop';
    const general=`<div class="detail-grid"><span>Mã khóa</span><b>${esc(x.code)}</b><span>Tên khóa</span><b>${esc(x.name)}</b><span>Số buổi / giờ</span><b>${x.sessions_count??'—'} / ${x.hours??'—'}</b><span>Phương thức thu tiền</span><b>${esc(x.fee_method||'—')}</b><span>Số tiền 1 khóa</span><b>${x.fee==null?'—':Number(x.fee).toLocaleString('vi-VN')}</b><span>Đánh giá hàng ngày</span><b>${esc(x.daily_evaluation||'—')}</b><span>Đơn vị</span><b>${esc(x.unit||'—')}</b><span>Môn học</span><b>${esc(x.subject||'—')}</b><span>Mô tả</span><b>${esc(x.description||'—')}</b></div>`;
    const editAction=['ADMIN','STAFF'].includes(state.user.role)?'<button class="primary course-detail-edit">Sửa</button>':'';
    wrap.innerHTML=`<div class="modal modal-wide"><h2>${esc(x.name)}</h2><div class="tab-strip">${['Thông tin chung','Chương trình học','Bộ kỹ năng','Bài kiểm tra','Danh sách lớp'].map((t,i)=>`<button type="button" class="ghost course-tab ${i===0?'active':''}" data-tab="${i}">${t}</button>`).join('')}</div><div class="course-tab-panel">${general}</div><div class="form-actions"><button class="ghost close-modal">Đóng</button>${editAction}</div></div>`;
    document.body.append(wrap); wrap.querySelector('.close-modal').onclick=()=>wrap.remove();
    const panel=wrap.querySelector('.course-tab-panel');
    const renderTab=async tab=>{
      const index=Number(tab.dataset.tab);
      wrap.querySelectorAll('.course-tab').forEach(item=>item.classList.toggle('active',item===tab));
      if(index===0){panel.innerHTML=general;return;}
      if(index===1||index===2){panel.innerHTML='<div class="empty">Chưa có dữ liệu cho tab này.</div>';return;}
      panel.innerHTML='<div class="empty">Đang tải dữ liệu…</div>';
      try {
        if(index===3){
          const rows=(await api(`/api/courses/${id}/tests`)).data||[];
          panel.innerHTML=rows.length?`<div class="table-wrap"><table><thead><tr><th>Tên bài kiểm tra</th><th>Ngày</th><th>Lớp</th><th>Điểm tối đa</th><th>Trạng thái</th><th>Kết quả</th></tr></thead><tbody>${rows.map(row=>`<tr><td>${esc(row.name)}</td><td>${esc(row.test_date)}</td><td>${esc(row.class_code)}</td><td>${esc(row.max_score)}</td><td>${esc(row.status)}</td><td>${esc(row.result_count)}</td></tr>`).join('')}</tbody></table></div>`:'<div class="empty">Chưa có bài kiểm tra được lưu.</div>';
        } else {
          const rows=(await api(`/api/courses/${id}/classes`)).data||[];
          panel.innerHTML=rows.length?`<div class="table-wrap"><table><thead><tr><th>Mã lớp</th><th>Giáo viên</th><th>Thời gian</th><th>Sĩ số</th><th>Trạng thái</th></tr></thead><tbody>${rows.map(row=>`<tr><td>${esc(row.code)}</td><td>${esc(row.teacher||'—')}</td><td>${esc(row.start_date||'—')} → ${esc(row.end_date||'—')}</td><td>${esc(row.student_count)} / ${esc(row.max_students||'—')}</td><td>${esc(row.status)}</td></tr>`).join('')}</tbody></table></div>`:'<div class="empty">Chưa có lớp được lưu cho khóa học này.</div>';
        }
      } catch(err){panel.innerHTML=`<div class="empty error">${esc(err.message)}</div>`;}
    };
    wrap.querySelectorAll('.course-tab').forEach(tab=>tab.addEventListener('click',()=>renderTab(tab)));
    const edit=wrap.querySelector('.course-detail-edit');
    if(edit) edit.onclick=()=>{wrap.remove();courseEditModal(id);};
  } catch(err){toast(err.message);}
}
async function courseEditModal(id){
  const x=(await api(`/api/courses/${id}`)).data, wrap=document.createElement('div'); wrap.className='modal-backdrop';
  wrap.innerHTML=`<div class="modal modal-wide"><h2>Sửa khóa học</h2><form>${courseFormMarkup(x)}<div class="form-actions"><button type="button" class="ghost close-modal">Hủy</button><button class="primary">Lưu</button></div><p class="error modal-error"></p></form></div>`;
  document.body.append(wrap); wrap.querySelector('.close-modal').onclick=()=>wrap.remove();
  wrap.querySelector('form').onsubmit=async e=>{e.preventDefault();try{await api(`/api/courses/${id}`,{method:'POST',body:Object.fromEntries(new FormData(e.currentTarget))});wrap.remove();toast('Đã cập nhật khóa học');render();}catch(err){wrap.querySelector('.modal-error').textContent=err.message;}};
}
async function courseDuplicate(id){try{await api(`/api/courses/${id}/duplicate`,{method:'POST',body:{}});toast('Đã nhân bản khóa học');render();}catch(err){toast(err.message);}}
function classFormMarkup(x={}, coursesList=[], teachersList=[]) {
  const value=(key)=>x[key]===null||x[key]===undefined?'':esc(x[key]);
  return `<div class="form-grid">
    <label>Khóa học<select name="course_id" required>${coursesList.map(c=>`<option value="${c.id}" ${String(c.id)===String(x.course_id)?'selected':''}>${esc(c.code)} — ${esc(c.name)}</option>`).join('')}</select></label>
    <label>Giáo viên<select name="teacher_id"><option value="">Chưa phân công</option>${teachersList.map(t=>`<option value="${t.id}" ${String(t.id)===String(x.teacher_id)?'selected':''}>${esc(t.full_name)}</option>`).join('')}</select></label>
    <label>Tên / mã lớp<input name="code" value="${value('code')}" required></label>
    <label>Số buổi học<input name="sessions_count" type="number" min="0" value="${value('sessions_count')}"></label>
    <label>Ngày bắt đầu<input name="start_date" type="text" inputmode="numeric" placeholder="dd/mm/yyyy" data-date-input value="${value('start_date')}"></label>
    <label>Ngày kết thúc dự kiến<input name="end_date" type="text" inputmode="numeric" placeholder="dd/mm/yyyy" data-date-input value="${value('end_date')}"></label>
    <label>Phương thức thu tiền<select name="payment_method"><option value="">Chưa chọn</option>${['Theo khóa','Theo buổi','Theo tháng'].map(v=>`<option ${x.payment_method===v?'selected':''}>${v}</option>`).join('')}</select></label>
    <label>Sĩ số tối đa<input name="max_students" type="number" min="0" value="${value('max_students')}"></label>
    <label>Sĩ số mỗi buổi<input name="max_students_per_session" type="number" min="0" value="${value('max_students_per_session')}"></label>
    <label>Quản lý chính<input name="primary_manager" value="${value('primary_manager')}"></label>
    <label>Quản lý phụ<input name="secondary_manager" value="${value('secondary_manager')}"></label>
    <label>Phòng<input name="room" value="${value('room')}"></label>
    <label>Lịch học<input name="schedule" value="${value('schedule')}" placeholder="Ví dụ: Tue/Thu 18:30"></label>
    <label>Số giờ học<input name="hours" type="number" min="0" step="0.5" value="${value('hours')}"></label>
    <label>Buổi giáo viên Việt<input name="vn_teacher_sessions" type="number" min="0" value="${value('vn_teacher_sessions')}"></label>
    <label>Buổi giáo viên nước ngoài<input name="foreign_teacher_sessions" type="number" min="0" value="${value('foreign_teacher_sessions')}"></label>
    <label>Đánh giá hàng ngày<input name="daily_evaluation" value="${value('daily_evaluation')}"></label>
    <label>Trạng thái<select name="status">${['PLANNED','OPEN','IN_PROGRESS','COMPLETED','CANCELLED'].map(v=>`<option ${v===x.status?'selected':''}>${v}</option>`).join('')}</select></label>
    <label class="wide">Ghi chú<input name="notes" value="${value('notes')}"></label>
  </div>`;
}
async function classModal(){
  const [coursesList,teachersList,studentsList]=await Promise.all([
    state.data.courses?Promise.resolve(state.data.courses):load('/api/courses','courses'),
    state.data.teachers?Promise.resolve(state.data.teachers):load('/api/teachers','teachers'),
    state.data.students?Promise.resolve(state.data.students):load('/api/students','students')
  ]);
  const wrap=document.createElement('div'); wrap.className='modal-backdrop';
  wrap.innerHTML=`<div class="modal modal-wide"><h2>Thêm lớp học</h2>
    <div class="wizard-steps" aria-label="Các bước tạo lớp">
      <span class="wizard-step active" data-wizard-label="0">1. Lớp học</span>
      <span class="wizard-step" data-wizard-label="1">2. Lịch học</span>
      <span class="wizard-step" data-wizard-label="2">3. Học viên</span>
    </div>
    <form id="class-wizard-form">
      <section data-wizard-panel="0">${classFormMarkup({},coursesList,teachersList)}</section>
      <section data-wizard-panel="1" hidden><p class="muted">Thêm các buổi học sẽ được lưu cùng lớp trong một giao dịch.</p><div id="wizard-sessions"></div><button type="button" class="ghost" id="wizard-add-session">+ Thêm buổi học</button></section>
      <section data-wizard-panel="2" hidden><p class="muted">Chọn học viên đang hoạt động để ghi danh ngay khi tạo lớp.</p><label>Tìm học viên<input id="wizard-student-query" placeholder="Mã hoặc họ tên"></label><div id="wizard-students" class="wizard-students"></div></section>
      <div class="form-actions"><button type="button" class="ghost close-modal">Hủy</button><button type="button" class="ghost" id="wizard-back" hidden>Quay lại</button><button type="submit" class="primary" id="wizard-next">Tiếp: Lịch học</button></div><p class="error modal-error"></p>
    </form></div>`;
  document.body.append(wrap);
  const form=wrap.querySelector('#class-wizard-form');
  const wizard={step:0,sessions:[],selected:new Set()};
  const syncSessions=()=>{wizard.sessions=[...wrap.querySelectorAll('[data-session-row]')].map(row=>({session_date:row.querySelector('[data-field="session_date"]').value,start_time:row.querySelector('[data-field="start_time"]').value,end_time:row.querySelector('[data-field="end_time"]').value,room:row.querySelector('[data-field="room"]').value})).filter(x=>x.session_date||x.start_time||x.end_time||x.room);};
  const renderSessions=()=>{const host=wrap.querySelector('#wizard-sessions');host.innerHTML=wizard.sessions.length?wizard.sessions.map((x,i)=>`<div class="wizard-session" data-session-row><div class="wizard-session-head"><b>Buổi ${i+1}</b><button type="button" class="ghost wizard-remove-session" data-index="${i}">Xóa</button></div><div class="form-grid"><label>Ngày<input data-field="session_date" type="text" inputmode="numeric" placeholder="dd/mm/yyyy" data-date-input value="${esc(x.session_date||'')}"></label><label>Phòng<input data-field="room" value="${esc(x.room||'')}"></label><label>Bắt đầu<input data-field="start_time" type="time" value="${esc(x.start_time||'')}"></label><label>Kết thúc<input data-field="end_time" type="time" value="${esc(x.end_time||'')}"></label></div></div>`).join(''):'<div class="empty wizard-empty">Chưa có buổi học. Có thể thêm ở bước này hoặc hoàn tất sau.</div>';host.querySelectorAll('.wizard-remove-session').forEach(btn=>btn.onclick=()=>{syncSessions();wizard.sessions.splice(Number(btn.dataset.index),1);renderSessions();});};
  const renderStudents=()=>{const query=(wrap.querySelector('#wizard-student-query').value||'').toLocaleLowerCase();const rows=studentsList.filter(x=>!query||`${x.student_code} ${x.full_name} ${x.email||''}`.toLocaleLowerCase().includes(query));wrap.querySelector('#wizard-students').innerHTML=rows.length?rows.map(x=>`<label class="wizard-student"><input type="checkbox" data-student-id="${x.id}" ${wizard.selected.has(String(x.id))?'checked':''}><span><b>${esc(x.student_code)} — ${esc(x.full_name)}</b><small>${esc(x.email||'')}</small></span></label>`).join(''):'<div class="empty">Không có học viên phù hợp.</div>';wrap.querySelectorAll('[data-student-id]').forEach(input=>input.onchange=()=>{if(input.checked)wizard.selected.add(String(input.dataset.studentId));else wizard.selected.delete(String(input.dataset.studentId));});};
  const setStep=(step)=>{wizard.step=step;wrap.querySelectorAll('[data-wizard-panel]').forEach(panel=>{panel.hidden=Number(panel.dataset.wizardPanel)!==step;});wrap.querySelectorAll('[data-wizard-label]').forEach(label=>{label.classList.toggle('active',Number(label.dataset.wizardLabel)===step);label.classList.toggle('complete',Number(label.dataset.wizardLabel)<step);});wrap.querySelector('#wizard-back').hidden=step===0;wrap.querySelector('#wizard-next').textContent=step===2?'Tạo lớp':'Tiếp: '+(step===0?'Lịch học':'Học viên');if(step===1)renderSessions();if(step===2)renderStudents();};
  wrap.querySelector('.close-modal').onclick=()=>wrap.remove();wrap.querySelector('#wizard-add-session').onclick=()=>{syncSessions();wizard.sessions.push({});renderSessions();};wrap.querySelector('#wizard-student-query').oninput=renderStudents;
  wrap.querySelector('#wizard-back').onclick=()=>setStep(Math.max(0,wizard.step-1));
  form.onsubmit=async e=>{e.preventDefault();wrap.querySelector('.modal-error').textContent='';if(wizard.step<2){if(wizard.step===0&&!form.reportValidity())return;syncSessions();setStep(wizard.step+1);return;}syncSessions();const fields=Object.fromEntries(new FormData(form));delete fields.student_query;fields.sessions=wizard.sessions;fields.student_ids=[...wizard.selected];try{await api('/api/classes/workflow',{method:'POST',body:fields});wrap.remove();toast('Đã tạo lớp, lịch học và ghi danh');render();}catch(err){wrap.querySelector('.modal-error').textContent=err.message;}};
  renderSessions();setStep(0);
}
async function classDetailModal(id){
  try {
    const x=(await api(`/api/classes/${id}`)).data, wrap=document.createElement('div'); wrap.className='modal-backdrop';
    wrap.innerHTML=`<div class="modal modal-wide"><h2>${esc(x.code)}</h2><div class="detail-grid"><span>Khóa học</span><b>${esc(x.course_name)}</b><span>Thời gian</span><b>${esc(x.start_date||'—')} → ${esc(x.end_date||'—')}</b><span>Số buổi / giờ</span><b>${x.sessions_count??'—'} / ${x.hours??'—'}</b><span>Thu tiền</span><b>${esc(x.payment_method||'—')}</b><span>Sĩ số</span><b>${x.student_count} / ${x.max_students||'—'}</b><span>Quản lý</span><b>${esc(x.primary_manager||'—')} / ${esc(x.secondary_manager||'—')}</b><span>Phòng / lịch</span><b>${esc(x.room||'—')} · ${esc(x.schedule||'—')}</b><span>Giảng viên</span><b>${esc(x.teacher||'—')}</b><span>Đánh giá hàng ngày</span><b>${esc(x.daily_evaluation||'—')}</b><span>Ghi chú</span><b>${esc(x.notes||'—')}</b></div><div class="form-actions"><button class="ghost close-modal">Đóng</button>${['ADMIN','STAFF'].includes(state.user.role)?'<button class="primary class-detail-edit">Sửa</button>':''}</div></div>`;
    document.body.append(wrap);wrap.querySelector('.close-modal').onclick=()=>wrap.remove();const edit=wrap.querySelector('.class-detail-edit');if(edit)edit.onclick=()=>{wrap.remove();classEditModal(id);};
  } catch(err){toast(err.message);}
}
async function classEditModal(id){
  const [d,coursesList,teachersList]=await Promise.all([api(`/api/classes/${id}`),state.data.courses?Promise.resolve(state.data.courses):load('/api/courses','courses'),state.data.teachers?Promise.resolve(state.data.teachers):load('/api/teachers','teachers')]), x=d.data, wrap=document.createElement('div'); wrap.className='modal-backdrop';
  wrap.innerHTML=`<div class="modal modal-wide"><h2>Sửa lớp học</h2><form>${classFormMarkup(x,coursesList,teachersList)}<div class="form-actions"><button type="button" class="ghost close-modal">Hủy</button><button class="primary">Lưu</button></div><p class="error modal-error"></p></form></div>`;
  document.body.append(wrap);wrap.querySelector('.close-modal').onclick=()=>wrap.remove();wrap.querySelector('form').onsubmit=async e=>{e.preventDefault();try{await api(`/api/classes/${id}`,{method:'POST',body:Object.fromEntries(new FormData(e.currentTarget))});wrap.remove();toast('Đã cập nhật lớp học');render();}catch(err){wrap.querySelector('.modal-error').textContent=err.message;}};
}
function downloadCsv(url, name){const link=document.createElement('a');link.href=url;link.download=name;document.body.append(link);link.click();link.remove();}
async function attendance(el){
  const [classesList,studentsList,records]=await Promise.all([load('/api/classes','classes'),load('/api/students','students'),load('/api/attendance','attendance')]);
  const canMark=['ADMIN','STAFF','TEACHER'].includes(state.user.role);
  const columns=[
    {label:'Ngày',key:'session_date'},
    {label:'Lớp',key:'class_code'},
    {label:'Học viên',render:x=>`${esc(x.student_code)} — ${esc(x.full_name)}`},
    {label:'Trạng thái',render:x=>statusBadge(x.status,x.status==='ABSENT'?'red':x.status==='LATE'?'':'green')},
    {label:'Ghi chú',render:x=>esc(x.note||'—')}
  ];
  el.innerHTML=head('Điểm danh','Theo dõi trạng thái tham dự theo buổi học.',canMark?'<button class="primary" id="mark-attendance">Ghi điểm danh</button>':'')+`<div class="filter-strip">
    <label>Lớp<select id="attendance-class-filter"><option value="">Tất cả</option>${classesList.map(x=>`<option value="${x.id}">${esc(x.code)} — ${esc(x.course_name)}</option>`).join('')}</select></label>
    <label>Trạng thái<select id="attendance-status-filter"><option value="">Tất cả</option>${['PRESENT','ABSENT','LATE','EXCUSED'].map(x=>`<option value="${x}">${esc(statusLabel(x))}</option>`).join('')}</select></label>
    <label>Từ ngày<input id="attendance-date-from" type="text" inputmode="numeric" placeholder="dd/mm/yyyy" data-date-input></label>
    <label>Đến ngày<input id="attendance-date-to" type="text" inputmode="numeric" placeholder="dd/mm/yyyy" data-date-input></label>
    <button class="ghost" id="attendance-filter-clear" type="button">Xóa lọc</button>
  </div>`+dataTable('bản ghi điểm danh',columns,records);
  $('#mark-attendance')?.addEventListener('click',()=>attendanceModal(classesList,studentsList));
  const tableId=el.querySelector('[data-table-card]')?.dataset.tableCard;
  attachServerTableFilters(el,tableId,['attendance-class-filter','attendance-status-filter','attendance-date-from','attendance-date-to','attendance-filter-clear'],'/api/attendance',v=>{const q=new URLSearchParams();if(v['attendance-class-filter'])q.set('class_id',v['attendance-class-filter']);if(v['attendance-status-filter'])q.set('status',v['attendance-status-filter']);if(v['attendance-date-from'])q.set('date_from',v['attendance-date-from']);if(v['attendance-date-to'])q.set('date_to',v['attendance-date-to']);return q;},'attendance');
}
function dataTable(title, columns, rows, options={}){const id=`table-${++state.tableSeq}`;state.tableRegistry[id]={rows,columns,pageSizes:Array.isArray(options.pageSizes)&&options.pageSizes.length?options.pageSizes:[10,25,50,100],pageSizeLabel:options.pageSizeLabel||'Số dòng mỗi trang'};const search=options.includeSearch===false?'':`<input class="table-search" data-table="${id}" placeholder="Tìm trong danh sách…">`;const count=options.showCount===false?'':`<h2 data-table-count="${id}">${rows.length} ${esc(title)}</h2>`;queueMicrotask(()=>bindDataTable(id));return `<div class="table-card" data-table-card="${id}" data-page-sizes="${state.tableRegistry[id].pageSizes.join(',')}"><div class="table-toolbar">${count}${search}</div><div class="table-wrap"><table><thead><tr>${columns.map(x=>`<th>${esc(x.label)}</th>`).join('')}</tr></thead><tbody data-table-body="${id}"></tbody></table></div><div class="table-footer" data-table-footer="${id}"></div></div>`;}
function bindDataTable(id){const card=document.querySelector(`[data-table-card="${id}"]`);if(!card)return;const registry=state.tableRegistry[id];if(registry.render){registry.render();return;}const search=card.querySelector('.table-search');const render=()=>{const term=(search?.value||'').toLocaleLowerCase();const filtered=registry.rows.filter(row=>!term||registry.columns.some(col=>String(col.render?col.render(row):displayValue(row[col.key]??'—')).toLocaleLowerCase().includes(term)));const pageSizes=registry.pageSizes||[10,25,50,100];const pageSize=Number(card.dataset.pageSize||pageSizes[0]);const page=Number(card.dataset.page||0);const pages=Math.max(1,Math.ceil(filtered.length/pageSize));const safePage=Math.min(page,pages-1);card.dataset.page=safePage;const slice=filtered.slice(safePage*pageSize,(safePage+1)*pageSize);const body=card.querySelector(`[data-table-body="${id}"]`);body.innerHTML=slice.length?slice.map((row,index)=>`<tr>${registry.columns.map(x=>`<td>${x.render?x.render(row,index):esc(displayValue(row[x.key]??'—'))}</td>`).join('')}</tr>`).join(''):`<tr><td colspan="${registry.columns.length}" class="empty">Chưa có dữ liệu.</td></tr>`;const count=card.querySelector(`[data-table-count="${id}"]`);if(count)count.textContent=`${filtered.length} mục`;const footer=card.querySelector(`[data-table-footer="${id}"]`);const pageButtons=Array.from({length:Math.min(pages,5)},(_,i)=>`<button class="ghost table-page ${i===safePage?'active':''}" data-page="${i}">${i+1}</button>`).join(''); footer.innerHTML=`<label class="table-page-size">Hiển thị <select aria-label="${esc(registry.pageSizeLabel||'Số dòng mỗi trang')}">${pageSizes.map(size=>`<option value="${size}" ${pageSize===Number(size)?'selected':''}>${size}</option>`).join('')}</select></label><span class="table-pagination"><button class="ghost table-prev" aria-label="Trang trước" ${safePage===0?'disabled':''}>‹</button>${pageButtons}<button class="ghost table-next" aria-label="Trang sau" ${safePage>=pages-1?'disabled':''}>›</button></span>`;footer.querySelector('.table-page-size select').onchange=e=>{card.dataset.pageSize=String(Number(e.target.value)||pageSizes[0]);card.dataset.page='0';render()};footer.querySelector('.table-prev').onclick=()=>{card.dataset.page=String(safePage-1);render()};footer.querySelector('.table-next').onclick=()=>{card.dataset.page=String(safePage+1);render()};footer.querySelectorAll('.table-page').forEach(btn=>btn.onclick=()=>{card.dataset.page=btn.dataset.page;render()});};registry.render=render;search?.addEventListener('input',()=>{card.dataset.page='0';render()});render();}
function attachTableFilters(el, tableId, rows, controlIds, predicate){
  const card=el.querySelector(`[data-table-card="${tableId}"]`), registry=state.tableRegistry[tableId];
  if(!card||!registry)return;
  const apply=()=>{
    const values=Object.fromEntries(controlIds.map(id=>[id,$(`#${id}`)?.value||'']));
    registry.rows=rows.filter(row=>predicate(row,values));
    card.dataset.page='0'; bindDataTable(tableId);
  };
  controlIds.forEach(id=>{const input=$(`#${id}`);input?.addEventListener(input.tagName==='INPUT'&&input.type==='text'?'input':'change',apply);});
  const clearId=controlIds.find(id=>id.endsWith('-filter-clear'));
  if(clearId){$(`#${clearId}`)?.addEventListener('click',()=>{controlIds.filter(id=>id!==clearId).forEach(id=>{const input=$(`#${id}`);if(!input)return;if(input.multiple)[...input.options].forEach(option=>{option.selected=false;});else input.value='';input._compactRefresh?.();});apply();});}
}
function attachServerTableFilters(el, tableId, controlIds, path, buildQuery, key, responseKey, localPredicate){
  const card=el.querySelector(`[data-table-card="${tableId}"]`), registry=state.tableRegistry[tableId];
  if(!card||!registry)return;
  let requestSeq=0;
  const apply=async()=>{
    const values=Object.fromEntries(controlIds.map(id=>{const control=$(`#${id}`);return [id,control?.multiple?[...control.selectedOptions].map(option=>option.value).filter(Boolean).join(','):(control?.value||'')] }));
    Object.keys(values).forEach(key=>{if(/date/i.test(key)) values[key]=parseDisplayDate(values[key]);});
    const query=buildQuery(values), suffix=query.toString()?`?${query.toString()}`:'';
    const seq=++requestSeq;
    try{
      const response=await api(path+suffix);
      if(seq!==requestSeq)return;
      const payload=response.data;
      const rows=responseKey?(payload?.[responseKey]||[]):(Array.isArray(payload)?payload:(payload?.items||payload?.rows||[]));
      registry.rows=localPredicate?rows.filter(row=>localPredicate(row,values)):rows;
      if(key)state.data[key]=responseKey?response.data:registry.rows;
      card.dataset.page='0'; bindDataTable(tableId);
    }catch(err){if(seq===requestSeq)toast(filterErrorMessage(err.message));}
  };
  controlIds.forEach(id=>{const input=$(`#${id}`);input?.addEventListener(input.tagName==='INPUT'&&input.type==='text'?'input':'change',apply);});
  const clearId=controlIds.find(id=>id.endsWith('-filter-clear'));
  if(clearId){$(`#${clearId}`)?.addEventListener('click',()=>{controlIds.filter(id=>id!==clearId).forEach(id=>{const input=$(`#${id}`);if(!input)return;if(input.multiple)[...input.options].forEach(option=>{option.selected=false;});else input.value='';input._compactRefresh?.();});apply();});}
}
function mondayOf(value){const date=value instanceof Date?new Date(value):new Date(`${value}T00:00:00`);date.setHours(0,0,0,0);date.setDate(date.getDate()-((date.getDay()+6)%7));return date;}
function dateKey(date){const year=date.getFullYear(),month=String(date.getMonth()+1).padStart(2,'0'),day=String(date.getDate()).padStart(2,'0');return `${year}-${month}-${day}`;}
function addDays(date, count){const next=new Date(date);next.setDate(next.getDate()+count);return next;}
function dateLabel(date){return new Intl.DateTimeFormat('vi-VN',{weekday:'short',day:'2-digit',month:'2-digit'}).format(date);}
function timetableWeekMarkup(rows, weekStart, canCreate){
  const byDate=new Map(rows.map(row=>[row.session_date,[]]));
  rows.forEach(row=>{if(!byDate.has(row.session_date))byDate.set(row.session_date,[]);byDate.get(row.session_date).push(row);});
  const days=Array.from({length:7},(_,index)=>{const date=addDays(weekStart,index);const key=dateKey(date);const sessions=byDate.get(key)||[];return `<section class="week-day"><header class="week-day-head"><span>${esc(dateLabel(date))}</span><b>${esc(key)}</b></header><div class="week-day-body">${sessions.length?sessions.map(x=>`<article class="week-slot"><b>${esc(x.start_time)}–${esc(x.end_time)}</b>${x.session_slot_name?`<small>${esc(x.session_slot_code)} · ${esc(x.session_slot_name)}</small>`:''}<strong>${esc(x.class_code)}</strong><span>${esc(x.room||'—')}</span><span class="badge ${x.status==='CANCELLED'?'red':x.status==='COMPLETED'?'green':''}">${esc(statusLabel(x.status))}</span>${canCreate?`<div class="slot-actions"><button class="small-action timetable-edit" data-id="${x.id}">Sửa</button><button class="small-action timetable-students" data-id="${x.id}">Học viên</button>${x.status==='SCHEDULED'?`<button class="small-action danger timetable-cancel" data-id="${x.id}">Hủy</button>`:''}</div>`:''}</article>`).join(''):'<div class="week-empty">Không có buổi</div>'}</div></section>`;}).join('');
  const end=addDays(weekStart,6);
  return `<div class="week-panel"><div class="week-controls"><div><b>Tuần ${esc(dateKey(weekStart))} → ${esc(dateKey(end))}</b><span class="muted"> · ${rows.length} buổi trong tuần</span></div><div class="week-control-actions"><button class="ghost" id="week-prev" type="button">← Tuần trước</button><button class="ghost" id="week-today" type="button">Tuần hiện tại</button><button class="ghost" id="week-next" type="button">Tuần sau →</button></div></div><div class="week-grid">${days}</div></div>`;
}
async function timetable(el){
  const list=await load('/api/timetable','timetable');
  const canCreate=['ADMIN','STAFF','TEACHER'].includes(state.user.role);
  const actions=canCreate?'<button class="primary" id="add-timetable">Thêm buổi học</button><button class="ghost" id="export-timetable">Xuất CSV</button>':'';
  if(!state.timetableWeekStart)state.timetableWeekStart=dateKey(mondayOf(new Date()));
  const weekStart=mondayOf(state.timetableWeekStart);
  const start=dateKey(weekStart);
  const week=await api('/api/timetable/week?start='+encodeURIComponent(start));
  const tableColumns=[{label:'Ngày',key:'session_date'},{label:'Ca học',render:x=>esc(x.session_slot_name?`${x.session_slot_code} — ${x.session_slot_name}`:'—')},{label:'Giờ',render:x=>`${esc(x.start_time)}–${esc(x.end_time)}`},{label:'Lớp',key:'class_code'},{label:'Khóa học',key:'course_name'},{label:'Phòng',key:'room'},{label:'Trạng thái',key:'status'}];
  if(canCreate)tableColumns.push({label:'Thao tác',render:x=>`<button class="small-action timetable-edit" data-id="${x.id}">Sửa</button><button class="small-action timetable-students" data-id="${x.id}">Học viên</button>${x.status==='SCHEDULED'?`<button class="small-action danger timetable-cancel" data-id="${x.id}">Hủy</button>`:''}`});
  const filterMarkup=`<div class="filter-strip timetable-filters">
    <label>Ngày<input id="timetable-day-filter" type="text" inputmode="numeric" placeholder="dd/mm/yyyy" data-date-input></label>
    <label>Giáo viên<input id="timetable-teacher-filter" placeholder="Tên giáo viên"></label>
    <label>Khóa học<input id="timetable-course-filter" placeholder="Tên khóa học"></label>
    <label>Lớp<input id="timetable-class-filter" placeholder="Mã lớp"></label>
    <label>Phòng<input id="timetable-room-filter" placeholder="Phòng"></label>
    <label>Giờ<input id="timetable-time-filter" placeholder="HH:MM"></label>
    <label>Trạng thái<select id="timetable-status-filter"><option value="">Tất cả</option>${['SCHEDULED','COMPLETED','CANCELLED'].map(x=>`<option value="${x}">${esc(statusLabel(x))}</option>`).join('')}</select></label>
    <button class="ghost" id="timetable-filter-clear" type="button">Xóa lọc</button>
  </div>`;
  el.innerHTML=head('Thời khóa biểu','Lịch tuần theo ngày và khung giờ.',actions)+filterMarkup+`<div id="timetable-week-panel">${timetableWeekMarkup(week.data,weekStart,canCreate)}</div>`+dataTable('buổi học',tableColumns,list);
  $('#add-timetable')?.addEventListener('click',()=>timetableModal());
  $('#export-timetable')?.addEventListener('click',()=>{
    const params=new URLSearchParams();
    const values={date:$('#timetable-day-filter')?.value||'',teacher:$('#timetable-teacher-filter')?.value||'',course:$('#timetable-course-filter')?.value||'',class_code:$('#timetable-class-filter')?.value||'',room:$('#timetable-room-filter')?.value||'',time:$('#timetable-time-filter')?.value||'',status:$('#timetable-status-filter')?.value||''};
    Object.entries(values).forEach(([key,value])=>{if(value)params.set(key,value);});
    downloadCsv('/api/export/timetable'+(params.toString()?'?'+params.toString():''),'timetable.csv');
  });
  const values=()=>Object.fromEntries(['timetable-day-filter','timetable-teacher-filter','timetable-course-filter','timetable-class-filter','timetable-room-filter','timetable-time-filter','timetable-status-filter'].map(id=>[id,$(`#${id}`)?.value||'']));
  const matches=(row,v)=>{
    const contains=(filterId,rowKey)=>!v[filterId]||String(row[rowKey]||'').toLocaleLowerCase().includes(v[filterId].toLocaleLowerCase());
    return (!v['timetable-day-filter']||row.session_date===v['timetable-day-filter']) &&
      contains('timetable-teacher-filter','teacher') && contains('timetable-course-filter','course_name') && contains('timetable-class-filter','class_code') &&
      contains('timetable-room-filter','room') &&
      (!v['timetable-time-filter']||`${row.start_time||''} ${row.end_time||''}`.toLocaleLowerCase().includes(v['timetable-time-filter'].toLocaleLowerCase())) &&
      (!v['timetable-status-filter']||row.status===v['timetable-status-filter']);
  };
  const bindWeekControls=()=>{
    $('#week-prev')?.addEventListener('click',()=>{state.timetableWeekStart=dateKey(addDays(weekStart,-7));render();});
    $('#week-today')?.addEventListener('click',()=>{state.timetableWeekStart=dateKey(mondayOf(new Date()));render();});
    $('#week-next')?.addEventListener('click',()=>{state.timetableWeekStart=dateKey(addDays(weekStart,7));render();});
  };
  const tableId=el.querySelector('[data-table-card]')?.dataset.tableCard;
  const applyFilters=()=>{
    const filtered=list.filter(row=>matches(row,values()));
    if(tableId){state.tableRegistry[tableId].rows=filtered;el.querySelector(`[data-table-card="${tableId}"]`)?.setAttribute('data-page','0');bindDataTable(tableId);}
    const filteredWeek=week.data.filter(row=>matches(row,values()));
    const panel=$('#timetable-week-panel');
    if(panel){panel.innerHTML=timetableWeekMarkup(filteredWeek,weekStart,canCreate);bindWeekControls();}
  };
  ['timetable-day-filter','timetable-teacher-filter','timetable-course-filter','timetable-class-filter','timetable-room-filter','timetable-time-filter','timetable-status-filter'].forEach(id=>{
    const input=$(`#${id}`);input?.addEventListener(input.tagName==='INPUT'&&input.type!=='date'?'input':'change',applyFilters);
  });
  $('#timetable-filter-clear')?.addEventListener('click',()=>{
    ['timetable-day-filter','timetable-teacher-filter','timetable-course-filter','timetable-class-filter','timetable-room-filter','timetable-time-filter','timetable-status-filter'].forEach(id=>{const input=$(`#${id}`);if(input)input.value='';});
    applyFilters();
  });
  bindWeekControls();
  // The shared data table fills its rows in a microtask. Delegate actions from
  // the screen container so buttons work in both the weekly grid and table,
  // regardless of when the rows are materialized.
  el.onclick=e=>{
    const edit=e.target.closest('.timetable-edit');
    const students=e.target.closest('.timetable-students');
    const cancel=e.target.closest('.timetable-cancel');
    if(edit) timetableEditModal(edit.dataset.id);
    else if(students) timetableStudentsModal(students.dataset.id);
    else if(cancel) timetableCancel(cancel.dataset.id);
  };
}
async function evaluations(el){
  const [list,classesList]=await Promise.all([load('/api/evaluations','evaluations'),load('/api/classes','classes')]);
  const canCreate=['ADMIN','STAFF','TEACHER'].includes(state.user.role);
  el.innerHTML=head('Đánh giá hàng ngày','Theo dõi nhận xét và điểm theo buổi học.',canCreate?'<button class="primary" id="add-evaluation">Ghi đánh giá</button>':'')+`<div class="filter-strip"><label>Lớp<select id="evaluation-class-filter"><option value="">Tất cả</option>${classesList.map(x=>`<option value="${x.code}">${esc(x.code)} — ${esc(x.course_name)}</option>`).join('')}</select></label><label>Trạng thái<select id="evaluation-status-filter"><option value="">Tất cả</option>${['DRAFT','PUBLISHED'].map(x=>`<option value="${x}">${x}</option>`).join('')}</select></label><label>Từ ngày<input id="evaluation-date-from" type="text" inputmode="numeric" placeholder="dd/mm/yyyy" data-date-input></label><label>Đến ngày<input id="evaluation-date-to" type="text" inputmode="numeric" placeholder="dd/mm/yyyy" data-date-input></label><button class="ghost" id="evaluation-filter-clear" type="button">Xóa lọc</button></div>`+dataTable('đánh giá',[{label:'Ngày',key:'session_date'},{label:'Lớp',key:'class_code'},{label:'Học viên',render:x=>`${esc(x.student_code)} — ${esc(x.full_name)}`},{label:'Điểm',key:'score'},{label:'Trạng thái',key:'status'},{label:'Ghi chú',key:'note'}],list);
  $('#add-evaluation')?.addEventListener('click',()=>evaluationModal());
  const tableId=el.querySelector('[data-table-card]')?.dataset.tableCard;
  attachServerTableFilters(el,tableId,['evaluation-class-filter','evaluation-status-filter','evaluation-date-from','evaluation-date-to','evaluation-filter-clear'],'/api/evaluations',v=>{const q=new URLSearchParams();if(v['evaluation-class-filter'])q.set('class',v['evaluation-class-filter']);if(v['evaluation-status-filter'])q.set('status',v['evaluation-status-filter']);if(v['evaluation-date-from'])q.set('date_from',v['evaluation-date-from']);if(v['evaluation-date-to'])q.set('date_to',v['evaluation-date-to']);return q;},'evaluations');
}
async function tests(el){
  const [list,classesList]=await Promise.all([load('/api/tests','tests'),load('/api/classes','classes')]);
  const canCreate=['ADMIN','STAFF','TEACHER'].includes(state.user.role);
  const testColumns=[{label:'Ngày',key:'test_date'},{label:'Tên',key:'name'},{label:'Lớp',key:'class_code'},{label:'Điểm tối đa',key:'max_score'},{label:'Trạng thái',key:'status'},{label:'Kết quả',key:'result_count'},{label:'Thao tác',render:x=>`<button class="small-action test-results" data-id="${x.id}">${canCreate?'Nhập / xem':'Xem kết quả'}</button>`}];
  el.innerHTML=head('Kiểm tra','Bài kiểm tra và số kết quả đã nhập.',canCreate?'<button class="primary" id="add-test">Tạo bài kiểm tra</button>':'')+`<div class="filter-strip"><label>Lớp<select id="test-class-filter"><option value="">Tất cả</option>${classesList.map(x=>`<option value="${x.code}">${esc(x.code)} — ${esc(x.course_name)}</option>`).join('')}</select></label><label>Trạng thái<select id="test-status-filter"><option value="">Tất cả</option>${['DRAFT','OPEN','CLOSED'].map(x=>`<option value="${x}">${x}</option>`).join('')}</select></label><label>Từ ngày<input id="test-date-from" type="text" inputmode="numeric" placeholder="dd/mm/yyyy" data-date-input></label><label>Đến ngày<input id="test-date-to" type="text" inputmode="numeric" placeholder="dd/mm/yyyy" data-date-input></label><button class="ghost" id="test-filter-clear" type="button">Xóa lọc</button></div>`+dataTable('bài kiểm tra',testColumns,list);
  $('#add-test')?.addEventListener('click',()=>testModal());
  const tableId=el.querySelector('[data-table-card]')?.dataset.tableCard;
  attachServerTableFilters(el,tableId,['test-class-filter','test-status-filter','test-date-from','test-date-to','test-filter-clear'],'/api/tests',v=>{const q=new URLSearchParams();if(v['test-class-filter'])q.set('class',v['test-class-filter']);if(v['test-status-filter'])q.set('status',v['test-status-filter']);if(v['test-date-from'])q.set('date_from',v['test-date-from']);if(v['test-date-to'])q.set('date_to',v['test-date-to']);return q;},'tests');
  el.onclick=e=>{const result=e.target.closest('.test-results');if(result)testResultsModal(result.dataset.id,canCreate);};
}
async function homework(el){
  const [list,classesList]=await Promise.all([load('/api/homework','homework'),load('/api/classes','classes')]);
  const canCreate=['ADMIN','STAFF','TEACHER'].includes(state.user.role);
  el.innerHTML=head('Bài tập về nhà','Bài tập theo lớp và hạn nộp.',canCreate?'<button class="primary" id="add-homework">Tạo bài tập</button>':'')+`<div class="filter-strip"><label>Lớp<select id="homework-class-filter"><option value="">Tất cả</option>${classesList.map(x=>`<option value="${x.code}">${esc(x.code)} — ${esc(x.course_name)}</option>`).join('')}</select></label><label>Trạng thái<select id="homework-status-filter"><option value="">Tất cả</option>${['DRAFT','OPEN','CLOSED'].map(x=>`<option value="${x}">${x}</option>`).join('')}</select></label><label>Hạn từ<input id="homework-date-from" type="text" inputmode="numeric" placeholder="dd/mm/yyyy" data-date-input></label><label>Hạn đến<input id="homework-date-to" type="text" inputmode="numeric" placeholder="dd/mm/yyyy" data-date-input></label><button class="ghost" id="homework-filter-clear" type="button">Xóa lọc</button></div>`+dataTable('bài tập',[{label:'Hạn nộp',key:'due_date'},{label:'Tiêu đề',key:'title'},{label:'Lớp',key:'class_code'},{label:'Người tạo',key:'created_by_name'},{label:'Trạng thái',key:'status'}],list);
  $('#add-homework')?.addEventListener('click',()=>homeworkModal());
  const tableId=el.querySelector('[data-table-card]')?.dataset.tableCard;
  attachServerTableFilters(el,tableId,['homework-class-filter','homework-status-filter','homework-date-from','homework-date-to','homework-filter-clear'],'/api/homework',v=>{const q=new URLSearchParams();if(v['homework-class-filter'])q.set('class',v['homework-class-filter']);if(v['homework-status-filter'])q.set('status',v['homework-status-filter']);if(v['homework-date-from'])q.set('date_from',v['homework-date-from']);if(v['homework-date-to'])q.set('date_to',v['homework-date-to']);return q;},'homework');
}
async function trials(el){
  const list=await load('/api/trial-registrations','trials');
  const canEdit=['ADMIN','STAFF'].includes(state.user.role);
  const actions=canEdit?'<button class="primary" id="add-trial">Tạo đăng ký</button>':'';
  el.innerHTML=head('Đăng ký học thử','Danh sách khách hàng đăng ký học thử.',actions)+`<div class="filter-strip"><label>Trạng thái<select id="trial-status-filter"><option value="">Tất cả</option>${['NEW','CONFIRMED','CANCELLED'].map(x=>`<option value="${x}">${x}</option>`).join('')}</select></label><label>Từ ngày<input id="trial-date-from" type="text" inputmode="numeric" placeholder="dd/mm/yyyy" data-date-input></label><label>Đến ngày<input id="trial-date-to" type="text" inputmode="numeric" placeholder="dd/mm/yyyy" data-date-input></label><button class="ghost" id="trial-filter-clear" type="button">Xóa lọc</button></div>`+dataTable('đăng ký',[{label:'Ngày học thử',key:'trial_date'},{label:'Họ tên',key:'full_name'},{label:'Người giám hộ',key:'guardian_name'},{label:'Điện thoại',key:'phone'},{label:'Trạng thái',key:'status'}],list);
  $('#add-trial')?.addEventListener('click',()=>trialModal());
  const tableId=el.querySelector('[data-table-card]')?.dataset.tableCard;
  attachServerTableFilters(el,tableId,['trial-status-filter','trial-date-from','trial-date-to','trial-filter-clear'],'/api/trial-registrations',v=>{const q=new URLSearchParams();if(v['trial-status-filter'])q.set('status',v['trial-status-filter']);if(v['trial-date-from'])q.set('date_from',v['trial-date-from']);if(v['trial-date-to'])q.set('date_to',v['trial-date-to']);return q;},'trials');
}
async function confirmations(el){
  const list=await load('/api/enrollment-confirmations','confirmations');
  const canEdit=['ADMIN','STAFF'].includes(state.user.role);
  const cols=[{label:'Mã hợp đồng',render:x=>`<button class="link-button confirmation-detail" data-id="${x.id}">${esc(x.contract_code)}</button>`},{label:'Học viên',render:x=>`${esc(x.student_code)} — ${esc(x.full_name)}`},{label:'Lớp',key:'class_code'},{label:'Khóa học',key:'course_name'},{label:'Trạng thái',key:'status'},{label:'Thao tác',render:x=>canEdit?`<button class="small-action confirmation-status" data-id="${x.id}" data-status="${esc(statusLabel(x.status))}">Cập nhật</button>`:'—'}];
  el.innerHTML=head('Xác nhận ghi danh','Theo dõi trạng thái hợp đồng và phê duyệt.')+`<div class="filter-strip"><label>Trạng thái<select id="confirmation-status-filter"><option value="">Tất cả</option>${['PENDING','APPROVED','REJECTED'].map(x=>`<option value="${x}">${x}</option>`).join('')}</select></label><label>Lớp<input id="confirmation-class-filter" placeholder="Mã lớp"></label><button class="ghost" id="confirmation-filter-clear" type="button">Xóa lọc</button></div>`+dataTable('xác nhận',cols,list);
  const tableId=el.querySelector('[data-table-card]')?.dataset.tableCard;
  attachServerTableFilters(el,tableId,['confirmation-status-filter','confirmation-class-filter','confirmation-filter-clear'],'/api/enrollment-confirmations',v=>{const q=new URLSearchParams();if(v['confirmation-status-filter'])q.set('status',v['confirmation-status-filter']);if(v['confirmation-class-filter'])q.set('class',v['confirmation-class-filter']);return q;},'confirmations');
  el.onclick=e=>{const detail=e.target.closest('.confirmation-detail'),status=e.target.closest('.confirmation-status');if(detail)confirmationDetailModal(detail.dataset.id);else if(status)confirmationStatusModal(status.dataset.id,status.dataset.status);};
}
async function customerTests(el){
  const saleRoute=state.route==='/sale/customer_test', crmRoute=state.route==='/crm/customer_test';
  const list=await load('/api/customer-tests','customer-tests');
  const canEdit=['ADMIN','STAFF'].includes(state.user.role);
  const cols=saleRoute?[
    {label:'No.',render:(x,i)=>String(i+1)},{label:'Khách hàng',key:'customer_name'},{label:'Phụ huynh',key:'parent_name'},{label:'Ngày hẹn test',render:x=>formatDateValue(x.test_date)},{label:'Điểm test',render:x=>x.score==null?'—':esc(x.score)},{label:'Nhân viên sale',key:'sales_owner'},{label:'Ghi chú',render:x=>esc(x.note||'—')},{label:'Hoạt động',render:x=>esc(x.activity_label||'—')}]
    :crmRoute?[
    {label:'No.',render:(x,i)=>String(i+1)},{label:'Khách hàng',key:'customer_name'},{label:'Phụ huynh',key:'parent_name'},{label:'Ngày hẹn test',render:x=>formatDateValue(x.test_date)},{label:'Điểm test',render:x=>x.score==null?'—':esc(x.score)},{label:'Nhân viên sale',key:'sales_owner'},{label:'Thời gian',render:x=>fmt(x.appointment_time)},{label:'Công cụ',render:x=>canEdit?`<button class="small-action customer-test-edit" data-id="${x.id}">Sửa</button>`:'—'}]
    :[
    {label:'STT',render:(x,i)=>String(i+1)},{label:'Khách hàng',key:'customer_name'},{label:'Phụ huynh',key:'parent_name'},{label:'Ngày hẹn test',render:x=>formatDateValue(x.test_date)},{label:'Điểm test',render:x=>x.score==null?'—':esc(x.score)},{label:'Nhân viên sale',key:'sales_owner'},{label:'Ghi chú',render:x=>esc(x.note||'—')}];
  const actions=(canEdit?'<button class="primary" id="add-customer-test">Tạo lịch hẹn</button>':'')+'<button class="ghost" id="export-customer-tests">Excel</button>';
  const saleOwners=[...new Set(list.map(x=>x.sales_owner).filter(Boolean))];
  const pageSize=`<label class="customer-test-page-size">Hiển thị<select id="customer-test-page-size"><option>10</option><option>25</option><option>50</option><option value="all">All</option></select> bản ghi</label>`;
  el.innerHTML=head('Danh sách test / hẹn test','',actions)+`<div class="filter-strip"><label><input id="customer-test-query" placeholder="Tìm trong bảng..."></label><label><input id="customer-test-date-from" type="text" inputmode="numeric" placeholder="Từ ngày" data-date-input></label><label><input id="customer-test-date-to" type="text" inputmode="numeric" placeholder="Đến ngày" data-date-input></label>${saleRoute?'':`<label><select id="customer-test-sale-filter"><option value="">Tất cả</option>${saleOwners.map(x=>`<option value="${esc(x)}">${esc(x)}</option>`).join('')}</select></label>`}${pageSize}<button class="ghost" id="customer-test-filter-clear" type="button">Xóa lọc</button></div>`+dataTable('lịch hẹn test',cols,list);
  $('#add-customer-test')?.addEventListener('click',()=>customerTestModal());
  $('#export-customer-tests')?.addEventListener('click',()=>{const q=new URLSearchParams();if($('#customer-test-query')?.value)q.set('q',$('#customer-test-query').value);if($('#customer-test-sale-filter')?.value)q.set('sales_owner',$('#customer-test-sale-filter').value);if($('#customer-test-date-from')?.value)q.set('date_from',parseDisplayDate($('#customer-test-date-from').value));if($('#customer-test-date-to')?.value)q.set('date_to',parseDisplayDate($('#customer-test-date-to').value));downloadCsv('/api/export/customer-tests'+(q.toString()?'?'+q.toString():''),'customer-tests.csv');});
  const tableId=el.querySelector('[data-table-card]')?.dataset.tableCard;
  const ids=['customer-test-query','customer-test-sale-filter','customer-test-date-from','customer-test-date-to','customer-test-filter-clear'];
  attachServerTableFilters(el,tableId,ids,'/api/customer-tests',v=>{const q=new URLSearchParams();if(v['customer-test-query'])q.set('q',v['customer-test-query']);if(v['customer-test-sale-filter'])q.set('sales_owner',v['customer-test-sale-filter']);if(v['customer-test-date-from'])q.set('date_from',parseDisplayDate(v['customer-test-date-from']));if(v['customer-test-date-to'])q.set('date_to',parseDisplayDate(v['customer-test-date-to']));return q;},'customer-tests');
  const size=$('#customer-test-page-size'); if(size){const card=el.querySelector(`[data-table-card="${tableId}"]`); size.addEventListener('change',()=>{if(card){card.dataset.pageSize=size.value==='all'?'1000':size.value;card.dataset.page='0';bindDataTable(tableId);}});}
  el.onclick=e=>{const edit=e.target.closest('.customer-test-edit');if(edit)customerTestEditModal(edit.dataset.id);};
}
async function pending(el){
  const list=await load('/api/pending-enrollments','pending');
  const canEdit=['ADMIN','STAFF'].includes(state.user.role);
  const cols=[{label:'Họ tên',key:'customer_name'},{label:'Điện thoại',key:'phone'},{label:'Khóa học',key:'course_name'},{label:'Ngày mong muốn',key:'preferred_day'},{label:'Ca mong muốn',key:'preferred_session'},{label:'Trạng thái',key:'status'},{label:'Thao tác',render:x=>canEdit?`<button class="small-action pending-edit" data-id="${x.id}">Sửa</button><button class="small-action pending-cancel" data-id="${x.id}" ${x.status==='CANCELLED'?'disabled':''}>Hủy</button>`:'—'}];
  const actions=canEdit?'<button class="primary" id="add-pending">Tạo đăng ký</button><button class="ghost" id="export-pending">Xuất CSV</button>':'';
  el.innerHTML=head('Đăng ký chờ lớp','Danh sách học viên chờ xếp lớp.',actions)+`<div class="filter-strip"><label>Trạng thái<select id="pending-status-filter"><option value="">Tất cả</option>${['WAITING','ASSIGNED','CANCELLED'].map(x=>`<option value="${x}">${x}</option>`).join('')}</select></label><label>Khóa học<input id="pending-course-filter" placeholder="Mã hoặc tên khóa"></label><label>Ngày mong muốn<input id="pending-day-filter" placeholder="Ví dụ: Thứ 2"></label><button class="ghost" id="pending-filter-clear" type="button">Xóa lọc</button></div>`+dataTable('đăng ký chờ',cols,list);
  $('#add-pending')?.addEventListener('click',()=>pendingModal());
  $('#export-pending')?.addEventListener('click',()=>{
    const params=new URLSearchParams();
    const status=$('#pending-status-filter')?.value||'', course=$('#pending-course-filter')?.value||'', day=$('#pending-day-filter')?.value||'';
    if(status)params.set('status',status); if(course)params.set('course',course); if(day)params.set('preferred_day',day);
    downloadCsv('/api/export/pending-enrollments'+(params.toString()?'?'+params.toString():''),'pending-enrollments.csv');
  });
  const tableId=el.querySelector('[data-table-card]')?.dataset.tableCard;
  attachServerTableFilters(el,tableId,['pending-status-filter','pending-course-filter','pending-day-filter','pending-filter-clear'],'/api/pending-enrollments',v=>{const q=new URLSearchParams();if(v['pending-status-filter'])q.set('status',v['pending-status-filter']);if(v['pending-course-filter'])q.set('course',v['pending-course-filter']);if(v['pending-day-filter'])q.set('preferred_day',v['pending-day-filter']);return q;},'pending');
  el.onclick=e=>{const edit=e.target.closest('.pending-edit'),cancel=e.target.closest('.pending-cancel');if(edit)pendingEditModal(edit.dataset.id);else if(cancel)pendingCancel(cancel.dataset.id);};
}
async function confirmationDetailModal(id){try{const d=await api(`/api/enrollment-confirmations/${id}`);const x=d.data;const wrap=document.createElement('div');wrap.className='modal-backdrop';wrap.innerHTML=`<div class="modal"><h2>Chi tiết hợp đồng</h2><div class="detail-grid"><span>Mã hợp đồng</span><b>${esc(x.contract_code)}</b><span>Học viên</span><b>${esc(x.student_code)} — ${esc(x.full_name)}</b><span>Email</span><b>${esc(x.email||'—')}</b><span>Lớp</span><b>${esc(x.class_code)}</b><span>Khóa học</span><b>${esc(x.course_code)} — ${esc(x.course_name)}</b><span>Trạng thái</span><b>${esc(statusLabel(x.status))}</b><span>Người duyệt</span><b>${esc(x.confirmed_by_name||'—')}</b></div><div class="form-actions"><button class="ghost close-modal">Đóng</button></div></div>`;document.body.append(wrap);wrap.querySelector('.close-modal').onclick=()=>wrap.remove();}catch(err){toast(err.message);}}
async function confirmationStatusModal(id,current){const wrap=document.createElement('div');wrap.className='modal-backdrop';wrap.innerHTML=`<div class="modal"><h2>Cập nhật xác nhận</h2><form><label>Trạng thái<select name="status">${['PENDING','APPROVED','REJECTED'].map(s=>`<option ${s===current?'selected':''}>${s}</option>`).join('')}</select></label><div class="form-actions"><button type="button" class="ghost close-modal">Hủy</button><button class="primary">Lưu</button></div><p class="error modal-error"></p></form></div>`;document.body.append(wrap);wrap.querySelector('.close-modal').onclick=()=>wrap.remove();wrap.querySelector('form').onsubmit=async e=>{e.preventDefault();try{await api('/api/enrollment-confirmations',{method:'POST',body:{id,status:new FormData(e.currentTarget).get('status')}});wrap.remove();toast('Đã cập nhật xác nhận');render();}catch(err){wrap.querySelector('.modal-error').textContent=err.message;}};}
function attendanceModal(classesList,studentsList){const wrap=document.createElement('div');wrap.className='modal-backdrop';wrap.innerHTML=`<div class="modal"><h2>Ghi điểm danh</h2><form id="attendance-form"><div class="form-grid"><label>Lớp<select name="class_id">${classesList.map(x=>`<option value="${x.id}">${esc(x.code)} — ${esc(x.course_name)}</option>`).join('')}</select></label><label>Học viên<select name="student_id">${studentsList.map(x=>`<option value="${x.id}">${esc(x.student_code)} — ${esc(x.full_name)}</option>`).join('')}</select></label><label>Ngày<input name="session_date" type="text" inputmode="numeric" placeholder="dd/mm/yyyy" data-date-input required></label><label>Trạng thái<select name="status"><option>PRESENT</option><option>ABSENT</option><option>LATE</option><option>EXCUSED</option></select></label><label class="wide">Ghi chú<input name="note"></label></div><div class="form-actions"><button type="button" class="ghost" id="close-modal">Hủy</button><button class="primary">Lưu</button></div><p class="error" id="modal-error"></p></form></div>`;document.body.append(wrap);$('#close-modal').onclick=()=>wrap.remove();$('#attendance-form').onsubmit=async(e)=>{e.preventDefault();try{await api('/api/attendance',{method:'POST',body:Object.fromEntries(new FormData(e.currentTarget))});wrap.remove();toast('Đã lưu điểm danh');render();}catch(err){$('#modal-error').textContent=err.message;}};}
function fieldHtml(field){const required=field.required===false?'':' required';if(field.options)return `<label>${esc(field.label)}<select name="${esc(field.name)}"${required}>${field.options.map(x=>`<option value="${esc(x.value)}"${field.value!==undefined&&String(x.value)===String(field.value)?' selected':''}>${esc(x.label||statusLabel(x.value))}</option>`).join('')}</select></label>`;const dateAttrs=field.dateInput?' type="text" inputmode="numeric" placeholder="dd/mm/yyyy" data-date-input':'';return `<label class="${field.wide?'wide':''}">${esc(field.label)}<input name="${esc(field.name)}"${dateAttrs||` type="${field.type||'text'}"`}${field.value!==undefined?` value="${esc(field.value)}"`:''}${required}></label>`;}
function formModal(title, endpoint, fields, success){const wrap=document.createElement('div');wrap.className='modal-backdrop';wrap.innerHTML=`<div class="modal"><h2>${esc(title)}</h2><form><div class="form-grid">${fields.map(fieldHtml).join('')}</div><div class="form-actions"><button type="button" class="ghost close-modal">Hủy</button><button class="primary">Lưu</button></div><p class="error modal-error"></p></form></div>`;document.body.append(wrap);wrap.querySelector('.close-modal').onclick=()=>wrap.remove();wrap.querySelector('form').onsubmit=async(e)=>{e.preventDefault();try{await api(endpoint,{method:'POST',body:Object.fromEntries(new FormData(e.currentTarget))});wrap.remove();toast(success);render();}catch(err){wrap.querySelector('.modal-error').textContent=err.message;}};return wrap;}
function openJsonForm(title, endpoint, fields, onSaved, transform=(value)=>value){
  const wrap=document.createElement('div');wrap.className='modal-backdrop';
  wrap.innerHTML=`<div class="modal modal-wide"><h2>${esc(title)}</h2><form><div class="form-grid">${fields.map(fieldHtml).join('')}</div><div class="form-actions"><button type="button" class="ghost close-modal">Hủy</button><button class="primary">Lưu</button></div><p class="error modal-error"></p></form></div>`;
  document.body.append(wrap);wrap.querySelector('.close-modal').onclick=()=>wrap.remove();
  wrap.querySelector('form').onsubmit=async e=>{e.preventDefault();try{const result=await api(endpoint,{method:'POST',body:transform(Object.fromEntries(new FormData(e.currentTarget)))});wrap.remove();toast('Đã lưu thay đổi');if(onSaved)onSaved(result.data);else render();}catch(err){wrap.querySelector('.modal-error').textContent=err.message;}};
}
function financeContractFields(x={}, catalog=[], students=[]){
  const accountOptions=students.map(s=>({value:s.id,label:`${s.student_code||''} — ${s.full_name||''}`.trim()}));
  const itemOptions=catalog.map(item=>({value:item.id,label:`${item.name} · ${Number(item.unit_price||0).toLocaleString('vi-VN')} VND`}));
  return [
    {name:'contract_code',label:'Mã hợp đồng',value:x.contract_code||''},
    {name:'created_date',label:'Ngày tạo',type:'text',inputmode:'numeric',placeholder:'dd/mm/yyyy',dateInput:true,value:x.created_date||''},
    {name:'customer_type',label:'Khách hàng',value:x.customer_type||'STUDENT',options:[{value:'LEAD',label:'Khách hàng tiềm năng'},{value:'STUDENT',label:'Học viên đang học'}]},
    {name:'expiry_date',label:'Ngày hết hạn',type:'text',inputmode:'numeric',placeholder:'dd/mm/yyyy',dateInput:true,value:x.expiry_date||'',required:false},
    {name:'account_id',label:'Tài khoản',value:x.account_id??x.student_id??'',options:[{value:'',label:'Tìm kiếm khách hàng'},...accountOptions],required:false},
    {name:'note',label:'Ghi chú',value:x.note||'',required:false},
    {name:'item_id',label:'Khóa/gói khóa học/Vật phẩm/Khoản thu',value:x.item_id||'',options:[{value:'',label:'Chọn khóa/gói khóa học/Vật phẩm/Khoản thu'},...itemOptions],required:false,wide:true},
    {name:'payment_due_date',label:'Ngày hẹn đóng tiền',type:'text',inputmode:'numeric',placeholder:'dd/mm/yyyy',dateInput:true,value:x.payment_due_date||'',required:false},
    {name:'payment_due_amount',label:'Số tiền hẹn đóng',type:'number',value:x.payment_due_amount??'',required:false},
    {name:'payment_note',label:'Ghi chú hẹn đóng tiền',value:x.payment_note||'',required:false},
    {name:'discount_code',label:'Ưu đãi cho toàn bộ hợp đồng',value:x.discount_code||'',required:false},
    {name:'direct_discount',label:'Giảm giá trực tiếp (VND)',type:'number',value:x.direct_discount??0,required:false},
    {name:'total_amount',label:'Tổng tiền',type:'number',value:x.total_amount??0},
    {name:'paid_amount',label:'Đã thanh toán',type:'number',value:x.paid_amount??0,required:false}
  ];
}
async function financeContractContext(){
  const [catalog, students]=await Promise.all([
    api('/api/finance/contract-catalog').then(x=>x.data||[]),
    api('/api/students').then(x=>x.data||[])
  ]);
  return {catalog,students};
}
async function financeContractModal(){try{const c=await financeContractContext();openJsonForm('Tạo hợp đồng','/api/finance/contracts',financeContractFields({},c.catalog,c.students),()=>render());}catch(err){toast(err.message);}}
async function financeContractEditModal(id){try{const [x,c]=await Promise.all([api(`/api/finance/contracts/${id}`).then(r=>r.data),financeContractContext()]);openJsonForm('Sửa hợp đồng',`/api/finance/contracts/${id}`,financeContractFields(x,c.catalog,c.students),()=>render());}catch(err){toast(err.message);}}
function financeContractFilterMarkup(route, courseOptions){
  const input=(id,placeholder,date=false)=>`<label><input id="${id}" data-finance-contract-filter="${id}"${date?' type="text" inputmode="numeric" data-date-input data-date-text="1"':' type="text"'} placeholder="${esc(placeholder)}"></label>`;
  const select=(id,first,options,{multiple=false}={})=>{const seenFirst=String(first||'').trim();const rows=options.filter(([,label])=>String(label||'').trim()!==seenFirst);return `<label><select id="${id}" data-finance-contract-filter="${id}"${multiple?' multiple':''}><option value="">${esc(first)}</option>${rows.map(([value,label])=>`<option value="${esc(value)}">${esc(label)}</option>`).join('')}</select></label>`;};
  const lifecycle=[['ALL','Tất cả'],['CANCELLED','Hủy'],['WAITING','Chờ lớp'],['ASSIGNED','Chưa thực hiện-Đã xếp lớp'],['ACTIVE','Đang thực hiện'],['COMPLETED','Hoàn thành'],['REFUNDED','Hoàn trả'],['PAUSED','Bảo lưu'],['PENDING_APPROVAL','Đã ghi danh - Chờ Phê Duyệt'],['TRANSFERRED','Chuyển nhượng']];
  const courseStatus=[['PAUSED','Bảo lưu'],['ACTIVE','Đang học'],['TRANSFERRED','Đã chuyển lớp'],['COMPLETED','Hoàn thành'],['DROPPED','Nghỉ học'],['ASSIGNED','Chưa thực hiện-Đã xếp lớp'],['WAITING','Chờ lớp'],['PENDING_APPROVAL','Đã ghi danh - Chờ Phê Duyệt']];
  const discounts=[['DISC_FALL','Ưu đãi nhập học kỳ thu 2026'],['DISC_SUMMER','Chào hè 2026'],['DISC_SIBLINGS','Anh chị em ruột']];
  const courseChoices=courseOptions.map(c=>[c.id,c.name||c.code]);
  const controls=[input('finance-contract-query','Tìm trong bảng...'),input('finance-contract-date-from','Từ ngày tạo',true),input('finance-contract-date-to','Đến ngày tạo',true),input('finance-contract-expiry-from','Từ ngày hết hạn',true),input('finance-contract-expiry-to','Đến ngày hết hạn',true)];
  const lifecycleSelect=select('finance-contract-status-select','Tất cả',lifecycle,{multiple:true});
  const courseSelect=select('finance-contract-course-select',courseChoices[0]?.[1]||'Tiếng anh cơ bản 1',courseChoices,{multiple:true});
  const courseStatusSelect=select('finance-contract-course-status-select','Bảo lưu',courseStatus,{multiple:true});
  const discountSelect=select('finance-contract-discount-select','Ưu đãi nhập học kỳ thu 2026',discounts,{multiple:true});
  const centerSelect=select('finance-contract-center-select','Trung tâm CenterOnline - Demo',[['demo','Trung tâm CenterOnline - Demo']],{multiple:true});
  const paymentSelect=select('finance-contract-payment-select','Chưa đóng tiền',[['PENDING','Chưa đóng tiền'],['PARTIAL','Còn nợ'],['PAID','Đóng đủ'],['CANCELLED','Đã hủy']],{multiple:true});
  const expiredSelect=select('finance-contract-expired-filter','Tất cả',[['EXPIRED','Hợp đồng hết hạn'],['DUE_SOON','Hợp đồng sắp hết hạn']]);
  if(route==='/finance/contract'){
    // Observed Finance order: contract status, course, course status,
    // discount, center, payment, sale, creator, expiry status.
    controls.push(lifecycleSelect,input('finance-contract-status-search','Trạng thái hợp đồng'));
    controls.push(courseSelect,input('finance-contract-course-search','Chọn khóa học'));
    controls.push(courseStatusSelect,input('finance-contract-course-status-search','Trạng thái khóa học'));
    controls.push(discountSelect,input('finance-contract-discount-search','Chọn ưu đãi'));
    controls.push(centerSelect,input('finance-contract-branch-filter','Chi nhánh'));
    controls.push(paymentSelect,input('finance-contract-payment-search','Trạng thái đóng tiền'));
    controls.push(select('finance-contract-sale-select','Chọn sale',[],{multiple:true}),input('finance-contract-sale-search','Sale'));
    controls.push(select('finance-contract-creator-select','Nguyễn Minh Vũ',[],{multiple:true}),input('finance-contract-creator-search','Người tạo'));
    controls.push(expiredSelect);
  } else {
    // Observed Sale order omits sale/creator controls and starts with course.
    controls.push(courseSelect,input('finance-contract-course-search','Chọn khóa học'));
    controls.push(expiredSelect);
    controls.push(centerSelect,input('finance-contract-branch-filter','Chi nhánh'));
    controls.push(paymentSelect,input('finance-contract-payment-search','Trạng thái đóng tiền'));
    controls.push(lifecycleSelect,input('finance-contract-status-search','Trạng thái hợp đồng'));
    controls.push(courseStatusSelect,input('finance-contract-course-status-search','Trạng thái khóa học'));
    controls.push(discountSelect,input('finance-contract-discount-search','Chọn ưu đãi'));
  }
  return controls.join('');
}
async function financeContracts(el){
  const canEdit=['ADMIN','STAFF'].includes(state.user.role);
  const [list, summary] = await Promise.all([
    load('/api/finance/contracts','finance-contracts'),
    api('/api/finance/contracts/summary').then(x=>x.data||{}),
  ]);
  const cols=[
    {label:'No.',render:(_x,i)=>esc(i+1)},
    {label:'Mã hợp đồng',render:x=>`<button class="link-button finance-contract-edit" data-id="${x.id}">${esc(x.contract_code)}</button>`},
    {label:'Khách hàng',render:x=>`<span class="contract-customer"><b>${esc(x.student_name||'')}</b><small>${esc(x.student_code||'')}</small><small>${esc(x.student_phone||'')}</small></span>`},
    {label:'Ngày tạo/Hết hạn',render:x=>`<span class="contract-dates"><span>Tạo: ${esc(formatDateValue(x.created_date))}</span><span>HH: ${esc(formatDateValue(x.expiry_date))}</span></span>`},
    {label:'Khóa học đăng kí',render:x=>`<span class="contract-course"><b>${esc(x.package_name||x.course_name||'')}</b><small>${esc(statusLabel(x.contract_status))}</small></span>`},
    {label:'Thanh toán/Còn nợ',render:x=>`<span class="contract-money"><span class="paid">${Number(x.paid_amount||0).toLocaleString('vi-VN')} VND</span><span class="debt">${Number(x.debt_amount||0).toLocaleString('vi-VN')} VND</span></span>`},
    {label:'Nhân viên sale',render:x=>`<span class="contract-person">${esc(x.sales_owner||'')}</span>`},
    {label:'Người tạo',render:x=>`<span class="contract-person">${esc(x.created_by_name||'')}</span>`},
    {label:'Trạng thái đóng tiền',render:x=>statusBadge(x.payment_status,x.payment_status==='PAID'?'green':x.payment_status==='OVERDUE'?'red':'')},
    {label:'Trạng thái hợp đồng',render:x=>statusBadge(x.contract_status,x.contract_status==='ACTIVE'?'green':'')},
    {label:'Ghi chú',render:x=>`<span class="contract-note">${esc(x.note||'')}</span>`},
    {label:'Công cụ',render:x=>canEdit?`<button class="small-action finance-contract-edit" data-id="${x.id}" title="Sửa">✎</button><button class="small-action" title="Thêm thao tác">…⌄</button>`:'—'}
  ];
  const money=v=>Number(v||0).toLocaleString('vi-VN')+' VND';
  const route=state.route;
  const actions=route==='/finance/contract'
    ? (canEdit?'<button class="primary" id="renew-finance-contracts">Gia hạn nhiều HĐ</button><button class="primary" id="add-finance-contract">Tạo mới</button><button class="upload-action" id="upload-finance-contracts">Upload</button><button class="ghost" id="export-finance-contracts">Excel</button>':'<button class="ghost" id="export-finance-contracts">Excel</button>')
    : (canEdit?'<button class="primary" id="add-finance-contract">Tạo mới</button>':'');
  const summaryMarkup=`<div class="finance-summary contract-summary"><div><b>Số hợp đồng</b><strong>${esc(summary.contract_count||0)}</strong></div><div><b>Tạm tính</b><strong>${money(summary.subtotal)}</strong></div><div><b>Đã thanh toán</b><strong>${money(summary.paid)}</strong></div><div><b>Còn nợ</b><strong>${money(summary.debt)}</strong></div><div><b>Hoàn trả</b><strong>${money(summary.refund)}</strong></div><div><b>Nợ xấu</b><strong>${money(summary.bad_debt)}</strong></div><div><b>Ví CO</b><strong>${money(summary.co_wallet)}</strong></div></div>`;
  const courseOptions=(await api('/api/courses').then(x=>x.data||[]).catch(()=>[]));
  const filterActions=route==='/finance/contract'||route==='/sale/contract'?'<button class="filter-apply" id="finance-contract-filter-apply" type="button">Lọc</button><button class="ghost" id="finance-contract-filter-clear" type="button">Xóa lọc</button>':'<button class="filter-apply" id="finance-contract-filter-apply" type="button">Lọc</button>';
  el.innerHTML=head(route==='/finance/contract'?'Hợp đồng khóa học':'Hợp đồng','',actions)+(route==='/finance/contract'?summaryMarkup:'')+`<div class="filter-strip">${financeContractFilterMarkup(route,courseOptions)}${filterActions}</div>`+dataTable('hợp đồng',cols,list);
  $('#add-finance-contract')?.addEventListener('click',financeContractModal);
  // Keep the observed contract actions connected to their owned child routes.
  // Upload and renewal remain local contracts; the child screens enforce
  // their own validation and do not claim private reference semantics.
  $('#upload-finance-contracts')?.addEventListener('click',()=>navigate('/finance/contract/upload'));
  $('#renew-finance-contracts')?.addEventListener('click',()=>navigate('/finance/contract/get_extension_contract'));
  const filterIds=[...el.querySelectorAll('[data-finance-contract-filter]')].map(x=>x.id);
  const build=v=>{const q=new URLSearchParams();const map=[['q','finance-contract-query'],['date_from','finance-contract-date-from'],['date_to','finance-contract-date-to'],['expiry_from','finance-contract-expiry-from'],['expiry_to','finance-contract-expiry-to'],['contract_status','finance-contract-status-select'],['course_id','finance-contract-course-select'],['branch','finance-contract-branch-filter'],['payment_status','finance-contract-payment-select'],['sales_owner','finance-contract-sale-search'],['creator','finance-contract-creator-search'],['discount','finance-contract-discount-search'],['expired_date_status','finance-contract-expired-filter']];map.forEach(([k,id])=>{if(v[id])q.set(k,/date/.test(k)?parseDisplayDate(v[id]):v[id]);});return q;};
  $('#export-finance-contracts')?.addEventListener('click',()=>{const q=build(Object.fromEntries(filterIds.map(id=>[id,$(`#${id}`)?.value||''])));downloadCsv('/api/export/finance-contracts?'+q.toString(),'finance-contracts.csv');});
  const tableId=el.querySelector('[data-table-card]')?.dataset.tableCard;
  attachServerTableFilters(el,tableId,[...filterIds,'finance-contract-filter-clear','finance-contract-filter-apply'],'/api/finance/contracts',build,'finance-contracts');
  el.onclick=e=>{const b=e.target.closest('.finance-contract-edit');if(b&&canEdit)financeContractEditModal(b.dataset.id);};
}
async function financeTransfers(el){
  const list=await load('/api/finance/transfers','finance-transfers'), canEdit=['ADMIN','STAFF'].includes(state.user.role);
  const cols=[
    {label:'No.',render:x=>esc(x.id)},
    {label:'Mã chuyển nhượng',key:'transfer_code'},
    {label:'Ngày chuyển nhượng',render:x=>formatDateValue(x.transfer_date)},
    {label:'Học viên chuyển',render:x=>`${esc(x.from_student_code||'')}<small>${esc(x.from_student_name||'')}</small>`},
    {label:'Hợp đồng',key:'contract_code'},
    {label:'Khóa học',render:x=>esc(x.course_name||x.course_code||'—')},
    {label:'Học viên nhận',render:x=>`${esc(x.to_student_code||'')}<small>${esc(x.to_student_name||'')}</small>`},
    {label:'Số tiền nhận',render:x=>Number(x.amount_received||0).toLocaleString('vi-VN')+' VND'},
    {label:'Ghi chú',key:'note'},
    {label:'Trạng thái',render:x=>statusBadge(x.status,x.status==='PROCESSED'?'green':x.status==='CANCELLED'?'red':'')},
    {label:'Action',render:()=>canEdit?'—':'—'}
  ];
  const actions=canEdit?'<button class="primary" id="add-finance-transfer">Tạo mới</button><button class="ghost" id="export-finance-transfers">Xuất Excel</button>':'<button class="ghost" id="export-finance-transfers">Xuất Excel</button>';
  el.innerHTML=head('Chuyển nhượng hợp đồng','Theo dõi chuyển nhượng hợp đồng giữa học viên.',actions)+referenceTabs([{label:'Chuyển nhượng hợp đồng'},{label:'Chuyển nhượng khoản thu vật phẩm'},{label:'Danh sách hợp đồng chênh lệch phí khi chuyển lớp'}])+`<div class="filter-strip"><label><input id="finance-transfer-query" placeholder="Tìm trong bảng…"></label><label>Trạng thái<select id="finance-transfer-status"><option value="">Tất cả</option><option value="PENDING">Chưa xử lý</option><option value="PROCESSED">Đã xử lý</option><option value="CANCELLED">Đã hủy</option></select></label><button class="ghost" id="finance-transfer-filter-clear" type="button">Xóa lọc</button></div>`+dataTable('chuyển nhượng',cols,list);
  $('#add-finance-transfer')?.addEventListener('click',async()=>{
    try{
      const [students,contracts]=await Promise.all([api('/api/students').then(x=>x.data||[]),api('/api/finance/contracts').then(x=>x.data||[])]);
      openJsonForm('Tạo chuyển nhượng','/api/finance/transfers',[
        {name:'transfer_code',label:'Mã chuyển nhượng'},
        {name:'transfer_date',label:'Ngày chuyển nhượng',type:'text',dateInput:true,value:new Date().toISOString().slice(0,10)},
        {name:'from_student_id',label:'Học viên chuyển',options:students.map(x=>({value:x.id,label:`${x.student_code} — ${x.full_name}`}))},
        {name:'to_student_id',label:'Học viên nhận',options:students.map(x=>({value:x.id,label:`${x.student_code} — ${x.full_name}`}))},
        {name:'contract_id',label:'Hợp đồng',options:[{value:'',label:'Không chọn'},...contracts.map(x=>({value:x.id,label:`${x.contract_code} — ${x.student_name||''}`}))],required:false},
        {name:'amount_received',label:'Số tiền nhận',type:'number',value:0,required:false},
        {name:'status',label:'Trạng thái',options:[{value:'PENDING',label:'Chưa xử lý'},{value:'PROCESSED',label:'Đã xử lý'},{value:'CANCELLED',label:'Đã hủy'}]},
        {name:'note',label:'Ghi chú',required:false,wide:true}
      ],()=>render());
    }catch(err){toast(err.message);}
  });
  const build=v=>{const q=new URLSearchParams();if(v['finance-transfer-query'])q.set('q',v['finance-transfer-query']);if(v['finance-transfer-status'])q.set('status',v['finance-transfer-status']);return q;};
  $('#export-finance-transfers')?.addEventListener('click',()=>{const v=Object.fromEntries(['finance-transfer-query','finance-transfer-status'].map(id=>[id,$(`#${id}`)?.value||'']));const q=build(v);downloadCsv('/api/export/finance-transfers'+(q.toString()?'?'+q:''),'finance-transfers.csv');});
  const tableId=el.querySelector('[data-table-card]')?.dataset.tableCard;attachServerTableFilters(el,tableId,['finance-transfer-query','finance-transfer-status','finance-transfer-filter-clear'],'/api/finance/transfers',build,'finance-transfers');
}
function financeBillFields(x={}){return [
  {name:'invoice_code',label:'Mã hóa đơn',value:x.invoice_code||''},{name:'contract_code',label:'Mã hợp đồng',value:x.contract_code||'',required:false},
  {name:'class_code',label:'Lớp học',value:x.class_code||'',required:false},{name:'subject',label:'Đối tượng',value:x.subject||'',required:false},
  {name:'customer_name',label:'Khách hàng',value:x.customer_name||'',required:false},{name:'payment_amount',label:'Thanh toán',type:'number',value:x.payment_amount??'',required:false},
  {name:'sales_owner',label:'Nhân viên sale',value:x.sales_owner||'',required:false},{name:'center',label:'Trung tâm',value:x.center||'',required:false},
  {name:'branch',label:'Chi nhánh',value:x.branch||'',required:false},{name:'employee',label:'Nhân viên',value:x.employee||'',required:false},
  {name:'confirmation_status',label:'Trạng thái xác nhận',value:x.confirmation_status||'PENDING',options:['PENDING','CONFIRMED','REJECTED'].map(v=>({value:v,label:v}))},
  {name:'payment_method',label:'Hình thức thanh toán',value:x.payment_method||'',required:false},{name:'invoice_date',label:'Ngày hóa đơn',type:'text',inputmode:'numeric',placeholder:'dd/mm/yyyy',dateInput:true,value:x.invoice_date||'',required:false},
  {name:'note',label:'Ghi chú',value:x.note||'',required:false,wide:true}
];}
function financeSpendFields(x={}){return [
  {name:'code',label:'Mã phiếu chi',value:x.code||''},
  {name:'spend_date',label:'Ngày lập phiếu',type:'text',inputmode:'numeric',placeholder:'dd/mm/yyyy',dateInput:true,value:x.spend_date||''},
  {name:'center_id',label:'Mã trung tâm',value:x.center_id||'demo'},
  {name:'center_name',label:'Trung tâm áp dụng',value:x.center_name||'Trung tâm CenterOnline - Demo'},
  {name:'content',label:'Nội dung',value:x.content||''},
  {name:'note',label:'Ghi chú',value:x.note||'',required:false},
  {name:'category',label:'Danh mục',value:x.category||'Vận hành',options:['CSVC','Lương','Marketing','Vận hành','Khác'].map(v=>({value:v,label:v}))},
  {name:'amount_vnd',label:'Số tiền',type:'number',value:x.amount_vnd??0},
  {name:'payment_method',label:'Phương thức thanh toán',value:x.payment_method||'cash',options:[['cash','Tiền mặt'],['bank_transfer','Chuyển khoản'],['card','Thẻ']].map(([value,label])=>({value,label}))}
];}
async function financeSpendEditModal(id){try{const x=(await api(`/api/finance/spends/${id}`)).data;openJsonForm('Sửa phiếu chi',`/api/finance/spends/${id}`,financeSpendFields(x),()=>render());}catch(err){toast(err.message);}}
async function financeSpends(el){
  const payload=await load('/api/finance/spends','finance-spends'); const list=payload.items||[], canEdit=['ADMIN','STAFF'].includes(state.user.role);
  const cols=[
    {label:'No.',render:(x,i)=>esc(i+1)}, {label:'Mã phiếu chi',render:x=>`<button class="link-button finance-spend-edit" data-id="${x.id}">${esc(x.code)}</button>`},
    {label:'Ngày lập phiếu',render:x=>formatDateValue(x.spend_date)}, {label:'Trung tâm áp dụng',key:'center_name'}, {label:'Nội dung',key:'content'},
    {label:'Ghi chú',render:x=>esc(x.note||'')}, {label:'Danh mục',key:'category'}, {label:'Số tiền',render:x=>`${Number(x.amount_vnd||0).toLocaleString('vi-VN')} VND`},
    {label:'Phương thức thanh toán',render:x=>x.payment_method==='cash'?'Tiền mặt':x.payment_method==='bank_transfer'?'Chuyển khoản':'Thẻ'}, {label:'Người lập phiếu',key:'created_by'},
    {label:'Công cụ',render:x=>canEdit?`<button class="small-action finance-spend-edit" data-id="${x.id}">Sửa</button>`:'—'}
  ];
  const actions=canEdit?'<button class="primary" id="add-finance-spend">+ Thêm phiếu chi</button><button class="ghost" id="export-finance-spends">Xuất Excel</button>':'<button class="ghost" id="export-finance-spends">Xuất Excel</button>';
  el.innerHTML=head('Phiếu chi','Quản lý các khoản chi theo trung tâm.',actions)+referenceTabs([{label:'Danh mục'},{label:'Khoản chi tài chính'}])+`<div class="filter-strip"><label>Trung tâm<input id="finance-spend-center" placeholder="Chọn trung tâm"></label><label>Danh mục<select id="finance-spend-category"><option value="">Tất cả</option>${['CSVC','Lương','Marketing','Vận hành','Khác'].map(v=>`<option value="${v}">${v}</option>`).join('')}</select></label><label>Tìm trong bảng<input id="finance-spend-query" placeholder="Tìm trong bảng…"></label><label>Từ ngày<input id="finance-spend-from" type="text" placeholder="dd/mm/yyyy" data-date-input></label><label>Đến ngày<input id="finance-spend-to" type="text" placeholder="dd/mm/yyyy" data-date-input></label><button class="ghost" id="finance-spend-filter-clear" type="button">Xóa lọc</button></div>`+dataTable('phiếu chi',cols,list);
  // The reference spend screen exposes only its five server filters.  Hide the
  // generic client-side table search and page-size controls on this route so
  // structural comparison does not count controls absent from the reference.
  queueMicrotask(() => {
    const card = el.querySelector('[data-table-card]');
    card?.querySelector('.table-toolbar .table-search')?.remove();
    card?.querySelector('.table-page-size')?.remove();
  });
  $('#add-finance-spend')?.addEventListener('click',()=>openJsonForm('Tạo phiếu chi','/api/finance/spends',financeSpendFields(),()=>render()));
  $('#export-finance-spends')?.addEventListener('click',()=>{const v=Object.fromEntries(['finance-spend-center','finance-spend-category','finance-spend-query','finance-spend-from','finance-spend-to'].map(id=>[id,$(`#${id}`)?.value||'']));const q=new URLSearchParams();[['center_id','finance-spend-center'],['category','finance-spend-category'],['q','finance-spend-query'],['from_date','finance-spend-from'],['to_date','finance-spend-to']].forEach(([k,id])=>{if(v[id])q.set(k,/date/.test(k)?parseDisplayDate(v[id]):v[id]);});downloadCsv('/api/export/finance-spends?'+q.toString(),'finance-spends.csv');});
  const build=v=>{const q=new URLSearchParams();[['center_id','finance-spend-center'],['category','finance-spend-category'],['q','finance-spend-query'],['from_date','finance-spend-from'],['to_date','finance-spend-to']].forEach(([k,id])=>{if(v[id])q.set(k,/date/.test(k)?parseDisplayDate(v[id]):v[id]);});return q;};
  const tableId=el.querySelector('[data-table-card]')?.dataset.tableCard;attachServerTableFilters(el,tableId,['finance-spend-center','finance-spend-category','finance-spend-query','finance-spend-from','finance-spend-to','finance-spend-filter-clear'],'/api/finance/spends',build,'finance-spends');
  el.onclick=e=>{const b=e.target.closest('.finance-spend-edit');if(b&&canEdit)financeSpendEditModal(b.dataset.id);};
}
function financeAppointmentFields(x={}){return [
  {name:'student_name',label:'Học viên',value:x.student_name||''},
  {name:'parent_name',label:'Phụ huynh',value:x.parent_name||'',required:false},
  {name:'appointment_date',label:'Ngày hẹn',type:'text',placeholder:'dd/mm/yyyy',dateInput:true,value:x.appointment_date||''},
  {name:'amount',label:'Số tiền',type:'number',value:x.amount??0,required:false},
  {name:'appointment_type',label:'Kiểu hẹn',value:x.appointment_type||'Theo hóa đơn',options:['Theo hóa đơn','Theo hợp đồng'].map(v=>({value:v,label:v}))},
  {name:'reference_code',label:'Mã tham chiếu',value:x.reference_code||''},
  {name:'contract_code',label:'Hợp đồng liên quan',value:x.contract_code||'',required:false},
  {name:'status',label:'Trạng thái',value:x.status||'Chưa xử lý',options:['Chưa xử lý','Đã xử lý','Đã hủy'].map(v=>({value:v,label:v})),required:false},
  {name:'note',label:'Ghi chú',value:x.note||'',required:false,wide:true}
];}
async function financeAppointmentEditModal(id){try{const x=(await api(`/api/finance/appointments/${id}`)).data;openJsonForm('Sửa lịch hẹn đóng tiền',`/api/finance/appointments/${id}`,financeAppointmentFields(x),()=>render());}catch(err){toast(err.message);}}
async function financeAppointments(el){
  const payload=await load('/api/finance/appointments','finance-appointments'), list=payload.items||[], canEdit=['ADMIN','STAFF'].includes(state.user.role);
  const saleRoute = state.route === '/sale/appointment_date';
  // The captured SALE screen has a duplicated "Học viên" header for its
  // second party column.  Preserve the underlying parent value while matching
  // that observed route contract; the Finance alias keeps the precise
  // "Phụ huynh" label.
  const cols=[{label:'Trạng thái',render:x=>statusBadge(x.status,x.status==='Đã xử lý'?'green':'')},{label:'Học viên',key:'student_name'},{label:saleRoute?'Học viên':'Phụ huynh',key:'parent_name'},{label:'Ngày hẹn',render:x=>formatDateValue(x.appointment_date)},{label:'Số tiền',render:x=>`${Number(x.amount||0).toLocaleString('vi-VN')} VND`},{label:'Ghi chú',key:'note'},{label:'Kiểu/Mã',render:x=>`${esc(x.appointment_type)} / ${esc(x.reference_code)}`},{label:'Hợp đồng liên quan',key:'contract_code'},{label:'Công cụ',render:x=>canEdit?`<button class="small-action finance-appointment-edit" data-id="${x.id}">Sửa</button>`:'—'}];
  const actions=canEdit?'<button class="primary" id="add-finance-appointment">+ Thêm mới</button><button class="ghost" id="export-finance-appointments">Xuất Excel</button>':'<button class="ghost" id="export-finance-appointments">Xuất Excel</button>';
  el.innerHTML=head('Hẹn đóng tiền','Theo dõi lịch hẹn thanh toán theo hóa đơn hoặc hợp đồng.',actions)+`<div class="filter-strip"><label>Tìm trong bảng<input id="finance-appointment-query" placeholder="Tìm trong bảng…"></label><label>Từ ngày<input id="finance-appointment-from" type="text" placeholder="dd/mm/yyyy" data-date-input></label><label>Đến ngày<input id="finance-appointment-to" type="text" placeholder="dd/mm/yyyy" data-date-input></label><label>Kiểu hẹn<select id="finance-appointment-type"><option value="">Tất cả</option><option value="Theo hóa đơn">Theo hóa đơn</option><option value="Theo hợp đồng">Theo hợp đồng</option></select></label><button class="ghost" id="finance-appointment-filter-clear" type="button">Xóa lọc</button></div>`+dataTable('lịch hẹn đóng tiền',cols,list);
  // The reference has one search field in the server filter row plus a page
  // size selector; remove the generic client-side table search to avoid a
  // duplicate control on both Finance and Sale aliases.
  queueMicrotask(() => el.querySelector('[data-table-card] .table-toolbar .table-search')?.remove());
  $('#add-finance-appointment')?.addEventListener('click',()=>openJsonForm('Tạo lịch hẹn đóng tiền','/api/finance/appointments',financeAppointmentFields(),()=>render()));
  const build=v=>{const q=new URLSearchParams();[['q','finance-appointment-query'],['date_from','finance-appointment-from'],['date_to','finance-appointment-to'],['appointment_type','finance-appointment-type']].forEach(([k,id])=>{if(v[id])q.set(k,/date/.test(k)?parseDisplayDate(v[id]):v[id]);});return q;};
  $('#export-finance-appointments')?.addEventListener('click',()=>{const v=Object.fromEntries(['finance-appointment-query','finance-appointment-from','finance-appointment-to','finance-appointment-type'].map(id=>[id,$(`#${id}`)?.value||'']));downloadCsv('/api/export/finance-appointments?'+build(v).toString(),'finance-appointments.csv');});
  const tableId=el.querySelector('[data-table-card]')?.dataset.tableCard;attachServerTableFilters(el,tableId,['finance-appointment-query','finance-appointment-from','finance-appointment-to','finance-appointment-type','finance-appointment-filter-clear'],'/api/finance/appointments',build,'finance-appointments');
  el.onclick=e=>{const b=e.target.closest('.finance-appointment-edit');if(b&&canEdit)financeAppointmentEditModal(b.dataset.id);};
}
function financeAssessmentFields(x={}){return [
  {name:'assessment_code',label:'Mã định giá',value:x.assessment_code||'',required:false},
  {name:'name',label:'Nhập tên định giá',value:x.name||x.assessment_name||''},
  {name:'date_apply',label:'Chọn ngày áp dụng',type:'text',placeholder:'dd/mm/yyyy',dateInput:true,value:x.date_apply||''},
  {name:'course_name',label:'Khóa học liên quan',value:x.course_name||'',required:false},
  {name:'old_price',label:'Giá cũ',type:'number',value:x.old_price??'',required:false},
  {name:'new_price',label:'Giá mới',type:'number',value:x.new_price??'',required:false},
  {name:'status',label:'Trạng thái',value:x.status||'ACTIVE',options:[['ACTIVE','Hoạt động'],['INACTIVE','Tạm khóa']].map(([value,label])=>({value,label}))}
];}
async function financeAssessmentEditModal(id){try{const x=(await api(`/api/finance/assessments/${id}`)).data;openJsonForm('Sửa định giá',`/api/finance/assessments/${id}`,financeAssessmentFields(x),()=>render());}catch(err){toast(err.message);}}
async function financeAssessments(el){
  const payload=await load('/api/finance/assessments','finance-assessments'), list=payload.items||[], canEdit=['ADMIN','STAFF'].includes(state.user.role);
  const cols=[{label:'No.',render:(_x,i)=>esc(i+1)},{label:'Tên',render:x=>`<button class="link-button finance-assessment-edit" data-id="${x.id}">${esc(x.name)}</button>`},{label:'Ngày áp dụng',render:x=>formatDateValue(x.date_apply)},{label:'Nhân viên định giá',key:'pricing_staff'},{label:'Khóa học liên quan',key:'course_name'}];
  const actions=canEdit?'<button class="primary" id="add-finance-assessment">Tạo định giá</button>':'', tabs=referenceTabs([{label:'Ưu đãi - Khuyến mãi'},{label:'Gói học phí'},{label:'Định giá'},{label:'Định giá gói học phí'}]);
  // Reference exposes only the DataTable search and page-size controls here;
  // status remains a persisted/API filter without adding a third visible
  // control that would change the observed screen shape.
  el.innerHTML=head('Định giá','Thiết lập giá áp dụng cho khóa học.',actions)+tabs+dataTable('định giá',cols,list);
  $('#add-finance-assessment')?.addEventListener('click',()=>openJsonForm('Tạo định giá','/api/finance/assessments',financeAssessmentFields(),()=>render()));
  const tableId=el.querySelector('[data-table-card]')?.dataset.tableCard;
  el.onclick=e=>{const b=e.target.closest('.finance-assessment-edit');if(b&&canEdit)financeAssessmentEditModal(b.dataset.id);};
}
function financeReserveFields(x={}){return [
  {name:'reserve_code',label:'Mã bảo lưu',value:x.reserve_code||'',required:false},
  {name:'student_name',label:'Học viên',value:x.student_name||''},
  {name:'reserve_date',label:'Ngày bảo lưu',type:'text',placeholder:'dd/mm/yyyy',dateInput:true,value:x.reserve_date||''},
  {name:'amount_or_days',label:'Số tiền/Số ngày bảo lưu',type:'number',value:x.amount_or_days??0},
  {name:'contract_code',label:'Hợp đồng bảo lưu',value:x.contract_code||'',required:false},
  {name:'course_name',label:'Khóa học',value:x.course_name||'',required:false},
  {name:'status',label:'Trạng thái',value:x.status||'Chờ xử lý',options:['Chờ xử lý','Đã cộng vào ví','Đã hoàn trả'].map(v=>({value:v,label:v}))},
  {name:'note',label:'Ghi chú',value:x.note||'',required:false,wide:true}
];}
async function financeReserveEditModal(id){try{const x=(await api(`/api/finance/reserves/${id}`)).data;openJsonForm('Sửa bảo lưu',`/api/finance/reserves/${id}`,financeReserveFields(x),()=>render());}catch(err){toast(err.message);}}
async function financeReserves(el){
  const payload=await load('/api/finance/reserves','finance-reserves'), list=payload.items||[], canEdit=['ADMIN','STAFF'].includes(state.user.role);
  const cols=[{label:'Mã bảo lưu',render:x=>`<button class="link-button finance-reserve-edit" data-id="${x.id}">${esc(x.reserve_code)}</button>`},{label:'Học viên',key:'student_name'},{label:'Ngày bảo lưu',render:x=>formatDateValue(x.reserve_date)},{label:'Số tiền/Số ngày bảo lưu',render:x=>`${Number(x.amount_or_days||0).toLocaleString('vi-VN')} VND`},{label:'Hợp đồng bảo lưu',render:x=>esc(x.contract_code||x.course_name||'—')},{label:'Người tạo',key:'created_by'},{label:'Trạng thái',render:x=>statusBadge(x.status,x.status==='Đã cộng vào ví'?'green':'')},{label:'Công cụ',render:x=>canEdit?`<button class="small-action finance-reserve-edit" data-id="${x.id}">Sửa</button>`:'—'}];
  const actions=canEdit?'<button class="primary" id="add-finance-reserve">Bảo lưu</button><button class="ghost" id="export-finance-reserves">Xuất Excel</button>':'<button class="ghost" id="export-finance-reserves">Xuất Excel</button>';
  el.innerHTML=head('Bảo lưu','Theo dõi các khoản bảo lưu của học viên.',actions)+referenceTabs([{label:'Hoàn trả'},{label:'Bảo lưu'}])+`<div class="filter-strip"><label><input id="finance-reserve-query" placeholder="Tìm trong bảng…"></label><label><select id="finance-reserve-mode"><option value="">Tất cả</option><option value="Theo hợp đồng">Theo hợp đồng</option><option value="Theo khóa học">Theo khóa học</option></select></label><button class="ghost" id="finance-reserve-clear" type="button">Xóa lọc</button></div>`+dataTable('bảo lưu',cols,list);
  $('#add-finance-reserve')?.addEventListener('click',()=>openJsonForm('Tạo bảo lưu','/api/finance/reserves',financeReserveFields(),()=>render()));
  $('#export-finance-reserves')?.addEventListener('click',()=>{const q=new URLSearchParams();if($('#finance-reserve-query')?.value)q.set('q',$('#finance-reserve-query').value);if($('#finance-reserve-mode')?.value)q.set('mode',$('#finance-reserve-mode').value);downloadCsv('/api/export/finance-reserves?'+q,'finance-reserves.csv');});
  const build=v=>{const q=new URLSearchParams();if(v['finance-reserve-query'])q.set('q',v['finance-reserve-query']);if(v['finance-reserve-mode'])q.set('mode',v['finance-reserve-mode']);return q;};
  const tableId=el.querySelector('[data-table-card]')?.dataset.tableCard;attachServerTableFilters(el,tableId,['finance-reserve-query','finance-reserve-mode','finance-reserve-clear'],'/api/finance/reserves',build,'finance-reserves');
  el.onclick=e=>{const b=e.target.closest('.finance-reserve-edit');if(b&&canEdit)financeReserveEditModal(b.dataset.id);};
}
function financePointFields(x={}){return [
  {name:'code',label:'Mã tích điểm',value:x.code||''},
  {name:'name',label:'Tên',value:x.name||''},
  {name:'status',label:'Trạng thái',value:x.status||'active',options:[{value:'active',label:'Hoạt động'},{value:'inactive',label:'Ngừng hoạt động'}]},
  {name:'amount_per_point',label:'Số tiền tích 1 điểm',type:'number',value:x.amount_per_point??''},
  {name:'conversion_rate',label:'Tỉ lệ quy đổi',type:'number',value:x.conversion_rate??''},
  {name:'center_id',label:'Mã trung tâm',value:x.center_id||'demo'},
  {name:'center_name',label:'Trung tâm áp dụng',value:x.center_name||'Trung tâm CenterOnline - Demo'}
];}
async function financePointEditModal(id){try{const x=(await api(`/api/finance/point-rules/${id}`)).data;openJsonForm('Sửa mã tích điểm',`/api/finance/point-rules/${id}`,financePointFields(x),()=>render());}catch(err){toast(err.message);}}
async function financePoints(el){
  const payload=await load('/api/finance/point-rules','finance-points'), list=payload.items||[], canEdit=['ADMIN','STAFF'].includes(state.user.role);
  const cols=[
    {label:'No.',render:(_x,i)=>esc(i+1)},
    {label:'Mã tích điểm',render:x=>`<button class="link-button finance-point-edit" data-id="${x.id}">${esc(x.code)}</button>`},
    {label:'Tên',key:'name'},
    {label:'Trạng thái',render:x=>statusBadge(x.status,x.status==='active'?'green':'')},
    {label:'Số tiền tích 1 điểm',render:x=>`${Number(x.amount_per_point||0).toLocaleString('vi-VN')} VND`},
    {label:'Tỉ lệ quy đổi',render:x=>`${Number(x.conversion_rate||0).toLocaleString('vi-VN')} VND`},
    {label:'Trung tâm áp dụng',key:'center_name'},
    {label:'Công cụ',render:x=>canEdit?`<button class="small-action finance-point-edit" data-id="${x.id}">Sửa</button>`:'—'}
  ];
  const actions=canEdit?'<button class="primary" id="add-finance-point">Tạo mã tích điểm</button><button class="ghost" id="export-finance-points">Xuất Excel</button>':'<button class="ghost" id="export-finance-points">Xuất Excel</button>';
  el.innerHTML=head('Thiết lập tích điểm','Quản lý mã và quy tắc tích điểm.',actions)+referenceTabs([{label:'Thiết lập tích điểm'},{label:'Thống kê tích điểm'}])+`<div class="filter-strip"><label><input id="finance-point-query" placeholder="Tìm trong bảng..."></label><label>Trạng thái<select id="finance-point-status"><option value="">Tất cả</option><option value="active">Hoạt động</option><option value="inactive">Ngừng hoạt động</option></select></label><label>Hiển thị<select id="finance-point-page-size"><option>5</option><option selected>10</option><option>25</option><option>50</option></select></label><button class="ghost" id="finance-point-filter-clear" type="button">Xóa lọc</button></div>`+dataTable('mã tích điểm',cols,list);
  $('#add-finance-point')?.addEventListener('click',()=>openJsonForm('Tạo mã tích điểm','/api/finance/point-rules',financePointFields(),()=>render()));
  $('#export-finance-points')?.addEventListener('click',()=>{const q=new URLSearchParams();if($('#finance-point-query')?.value)q.set('q',$('#finance-point-query').value);if($('#finance-point-status')?.value)q.set('status',$('#finance-point-status').value);downloadCsv('/api/export/finance-point-rules'+(q.toString()?`?${q}`:''),'finance-point-rules.csv');});
  const tableId=el.querySelector('[data-table-card]')?.dataset.tableCard;
  const build=v=>{const q=new URLSearchParams();if(v['finance-point-query'])q.set('q',v['finance-point-query']);if(v['finance-point-status'])q.set('status',v['finance-point-status']);if(v['finance-point-page-size'])q.set('page_size',v['finance-point-page-size']);return q;};
  attachServerTableFilters(el,tableId,['finance-point-query','finance-point-status','finance-point-page-size','finance-point-filter-clear'],'/api/finance/point-rules',build,'finance-points');
  el.onclick=e=>{const b=e.target.closest('.finance-point-edit');if(b&&canEdit)financePointEditModal(b.dataset.id);};
}
function financeItemFields(x={}){return [
  {name:'code',label:'Mã vật phẩm',value:x.code||''}, {name:'fullname',label:'Tên vật phẩm',value:x.fullname||''},
  {name:'category',label:'Danh mục',value:x.category||''}, {name:'description',label:'Màu sắc, kích cỡ, mô tả',value:x.description||'',required:false,wide:true},
  {name:'unit',label:'Đơn vị tính',value:x.unit||'cái'}, {name:'course_ids',label:'Khóa học áp dụng',value:x.course_ids||'',required:false},
  {name:'branch',label:'Trung tâm áp dụng',value:x.branch||'Trung tâm Demo',required:false}, {name:'quantity',label:'Số lượng còn',type:'number',value:x.quantity??0},
  {name:'sale_price',label:'Giá bán',type:'number',value:x.sale_price??0}, {name:'price_adjustment',label:'Điều chỉnh giá',type:'number',value:x.price_adjustment??0,required:false},
  {name:'status',label:'Trạng thái',value:x.status||'Hoạt động',options:[{value:'Hoạt động',label:'Hoạt động'},{value:'Tạm khóa',label:'Tạm khóa'}]},
  {name:'start_date',label:'Ngày bắt đầu',type:'text',placeholder:'dd/mm/yyyy',dateInput:true,value:x.start_date||'',required:false}
];}
async function financeItemEditModal(id){try{const x=(await api(`/api/finance/items/${id}`)).data;openJsonForm('Sửa vật phẩm',`/api/finance/items/${id}`,financeItemFields(x),()=>render());}catch(err){toast(err.message);}}
async function financeItems(el){
  const list=await load('/api/finance/items','finance-items'), canEdit=['ADMIN','STAFF'].includes(state.user.role);
  const cols=[{label:'No.',render:(_x,i)=>esc(i+1)},{label:'Mã vật phẩm',render:x=>`<button class="link-button finance-item-edit" data-id="${x.id}">${esc(x.code)}</button>`},{label:'Danh mục',key:'category'},{label:'Tên vật phẩm',key:'fullname'},{label:'Khóa học áp dụng',key:'course_ids'},{label:'Đơn vị tính',key:'unit'},{label:'Trung tâm áp dụng',key:'branch'},{label:'Số lượng còn',key:'quantity'},{label:'Giá bán',render:x=>`${Number(x.sale_price||0).toLocaleString('vi-VN')} VND`},{label:'Điều chỉnh giá',key:'price_adjustment'},{label:'Trạng thái',render:x=>statusBadge(x.status,x.status==='Hoạt động'?'green':'')},{label:'Công cụ',render:x=>canEdit?`<button class="small-action finance-item-edit" data-id="${x.id}">Sửa</button>`:'—'}];
  const actions=canEdit?'<button class="primary" id="add-finance-item">Thêm vật phẩm</button><button class="ghost" id="export-finance-items">Xuất Excel</button>':'<button class="ghost" id="export-finance-items">Xuất Excel</button>';
  el.innerHTML=head('Vật phẩm','Danh mục vật phẩm và tồn kho.',actions)+referenceTabs([{label:'Danh mục vật phẩm'},{label:'Vật phẩm'},{label:'Phiếu nhập kho'},{label:'Phiếu xuất kho'}])+`<div class="filter-strip"><label><input id="finance-item-query" placeholder="Tìm trong bảng..."></label><label>Trạng thái<select id="finance-item-status"><option value="">Tất cả</option><option>Hoạt động</option><option>Tạm khóa</option></select></label><button class="ghost" id="finance-item-filter-clear" type="button">Xóa lọc</button></div>`+dataTable('vật phẩm',cols,list);
  $('#add-finance-item')?.addEventListener('click',()=>openJsonForm('Tạo vật phẩm','/api/finance/items',financeItemFields(),()=>render()));
  $('#export-finance-items')?.addEventListener('click',()=>{const q=new URLSearchParams();if($('#finance-item-query')?.value)q.set('q',$('#finance-item-query').value);if($('#finance-item-status')?.value)q.set('status',$('#finance-item-status').value);downloadCsv('/api/export/finance-items'+(q.toString()?`?${q}`:''),'finance-items.csv');});
  const tableId=el.querySelector('[data-table-card]')?.dataset.tableCard;const build=v=>{const q=new URLSearchParams();if(v['finance-item-query'])q.set('q',v['finance-item-query']);if(v['finance-item-status'])q.set('status',v['finance-item-status']);return q;};attachServerTableFilters(el,tableId,['finance-item-query','finance-item-status','finance-item-filter-clear'],'/api/finance/items',build,'finance-items');el.onclick=e=>{const b=e.target.closest('.finance-item-edit');if(b&&canEdit)financeItemEditModal(b.dataset.id);};
}
function financeDebitItemFields(x={}){return [{name:'invoice_code',label:'Hóa đơn',value:x.invoice_code||''},{name:'invoice_date',label:'Ngày xuất HĐ',type:'text',placeholder:'dd/mm/yyyy',dateInput:true,value:x.invoice_date||''},{name:'customer_name',label:'Khách hàng',value:x.customer_name||''},{name:'item_name',label:'Vật phẩm nợ',value:x.item_name||''},{name:'quantity',label:'Số lượng',type:'number',value:x.quantity??1},{name:'total_amount',label:'Tổng tiền',type:'number',value:x.total_amount??0},{name:'status',label:'Trạng thái',value:x.status||'Chưa trả',options:[{value:'Chưa trả',label:'Chưa trả'},{value:'Đã trả',label:'Đã trả'}]}];}
async function financeDebitItemEditModal(id){try{const x=(await api(`/api/finance/debit-items/${id}`)).data;openJsonForm('Sửa vật phẩm nợ',`/api/finance/debit-items/${id}`,financeDebitItemFields(x),()=>render());}catch(err){toast(err.message);}}
async function financeDebitItems(el){
  const payload=await load('/api/finance/debit-items','finance-debit-items'), list=payload.items||[], canEdit=['ADMIN','STAFF'].includes(state.user.role);
  const cols=[{label:'No.',render:(_x,i)=>esc(i+1)},{label:'Hóa đơn',render:x=>`<button class="link-button finance-debit-item-edit" data-id="${x.id}">${esc(x.invoice_code)}</button>`},{label:'Ngày xuất HĐ',render:x=>formatDateValue(x.invoice_date)},{label:'Khách hàng',key:'customer_name'},{label:'Vật phẩm nợ',key:'item_name'},{label:'Số lượng',key:'quantity'},{label:'Tổng tiền',render:x=>`${Number(x.total_amount||0).toLocaleString('vi-VN')} VND`},{label:'Trạng thái',render:x=>statusBadge(x.status,x.status==='Đã trả'?'green':'')},{label:'Action',render:x=>canEdit?`<button class="small-action finance-debit-item-edit" data-id="${x.id}">Sửa</button>`:'—'}];
  const actions=canEdit?'<button class="primary" id="add-finance-debit-item">Tạo vật phẩm nợ</button><button class="ghost" id="export-finance-debit-items">Xuất Excel</button>':'<button class="ghost" id="export-finance-debit-items">Xuất Excel</button>';
  el.innerHTML=head('Vật phẩm nợ','Theo dõi vật phẩm còn nợ theo hóa đơn.',actions)+referenceTabs([{label:'Vật phẩm nợ'}])+`<div class="filter-strip"><label><input id="finance-debit-item-query" placeholder="Tìm trong bảng..."></label><label>Trạng thái<select id="finance-debit-item-status"><option>Tất cả</option><option>Chưa trả</option><option>Đã trả</option></select></label><label>Từ ngày<input id="finance-debit-item-from" type="text" placeholder="dd/mm/yyyy" data-date-input></label><label>Đến ngày<input id="finance-debit-item-to" type="text" placeholder="dd/mm/yyyy" data-date-input></label><button class="ghost" id="finance-debit-item-filter-clear" type="button">Xóa lọc</button></div>`+dataTable('vật phẩm nợ',cols,list);
  $('#add-finance-debit-item')?.addEventListener('click',()=>openJsonForm('Tạo vật phẩm nợ','/api/finance/debit-items',financeDebitItemFields(),()=>render()));
  $('#export-finance-debit-items')?.addEventListener('click',()=>{const q=new URLSearchParams();[['q','finance-debit-item-query'],['status','finance-debit-item-status'],['from_date','finance-debit-item-from'],['to_date','finance-debit-item-to']].forEach(([k,id])=>{if($(`#${id}`)?.value)q.set(k,/date/.test(k)?parseDisplayDate($(`#${id}`).value):$(`#${id}`).value);});downloadCsv('/api/export/finance-debit-items?'+q,'finance-debit-items.csv');});
  const tableId=el.querySelector('[data-table-card]')?.dataset.tableCard;const build=v=>{const q=new URLSearchParams();[['q','finance-debit-item-query'],['status','finance-debit-item-status'],['from_date','finance-debit-item-from'],['to_date','finance-debit-item-to']].forEach(([k,id])=>{if(v[id])q.set(k,/date/.test(k)?parseDisplayDate(v[id]):v[id]);});return q;};attachServerTableFilters(el,tableId,['finance-debit-item-query','finance-debit-item-status','finance-debit-item-from','finance-debit-item-to','finance-debit-item-filter-clear'],'/api/finance/debit-items',build,'finance-debit-items');el.onclick=e=>{const b=e.target.closest('.finance-debit-item-edit');if(b&&canEdit)financeDebitItemEditModal(b.dataset.id);};
}
async function financeWallets(el){
  const payload=await load('/api/finance/wallets','finance-wallets'), list=payload.items||[];
  const cols=[
    {label:'No.',render:(_x,i)=>esc(i+1)}, {label:'Tên học viên',key:'student_name'},
    {label:'Trung tâm/chi nhánh',key:'branch'},
    {label:'Tổng tiền',render:x=>`${Number(x.total_amount||0).toLocaleString('vi-VN')} VND`},
    {label:'Đã dùng',render:x=>`${Number(x.used_amount||0).toLocaleString('vi-VN')} VND`},
    {label:'Chưa dùng',render:x=>`${Number(x.unused_amount||0).toLocaleString('vi-VN')} VND`},
    {label:'Trạng thái',render:x=>statusBadge(x.status,x.status==='Kích hoạt'?'green':'')},
    {label:'Công cụ',render:()=>'<span class="small-action" aria-label="Xem">⋯</span>'}
  ];
  el.innerHTML=head('Ví CO','Quản lý số dư ví của học viên.','<button class="ghost" id="export-finance-wallets">Excel</button>')+referenceTabs([{label:'Ví CO'}])+`<div class="filter-strip"><label><input id="finance-wallet-query" placeholder="Tìm trong bảng..."></label><label><select id="finance-wallet-status"><option value="">Tất cả</option><option>Kích hoạt</option><option>Tạm khóa</option></select></label><button class="ghost" id="finance-wallet-filter-clear" type="button">Xóa lọc</button></div>`+dataTable('ví CO',cols,list);
  const build=v=>{const q=new URLSearchParams();if(v['finance-wallet-query'])q.set('q',v['finance-wallet-query']);if(v['finance-wallet-status'])q.set('status',v['finance-wallet-status']);return q;};
  $('#export-finance-wallets')?.addEventListener('click',()=>{const q=build({'finance-wallet-query':$('#finance-wallet-query')?.value||'','finance-wallet-status':$('#finance-wallet-status')?.value||''});downloadCsv('/api/export/finance-wallets'+(q.toString()?'?'+q:''),'finance-wallets.csv');});
  const tableId=el.querySelector('[data-table-card]')?.dataset.tableCard;
  attachServerTableFilters(el,tableId,['finance-wallet-query','finance-wallet-status','finance-wallet-filter-clear'],'/api/finance/wallets',build,'finance-wallets');
}
function financeBillModal(){openJsonForm('Tạo hóa đơn','/api/finance/bills',financeBillFields(),()=>render());}
async function financeBillEditModal(id){try{const x=(await api(`/api/finance/bills/${id}`)).data;openJsonForm('Sửa hóa đơn',`/api/finance/bills/${id}`,financeBillFields(x),()=>render());}catch(err){toast(err.message);}}
async function financeBills(el){
  const list=await load('/api/finance/bills','finance-bills'), canEdit=['ADMIN','STAFF'].includes(state.user.role);
  const cols=[{label:'No.',render:x=>esc(x.id)},{label:'Mã hóa đơn',render:x=>`<button class="link-button finance-bill-edit" data-id="${x.id}">${esc(x.invoice_code)}</button>`},{label:'Mã hợp đồng',key:'contract_code'},{label:'Lớp học',key:'class_code'},{label:'Đối tượng',key:'subject'},{label:'Khách hàng',key:'customer_name'},{label:'Thanh toán',render:x=>x.payment_amount==null?'—':Number(x.payment_amount).toLocaleString('vi-VN')},{label:'Nhân viên sale',key:'sales_owner'},{label:'Người tạo',render:x=>esc(x.created_by_name||'—')},{label:'Trạng thái xác nhận',render:x=>`<span class="badge ${x.confirmation_status==='CONFIRMED'?'green':x.confirmation_status==='REJECTED'?'red':''}">${esc(x.confirmation_status)}</span>`},{label:'Hình thức thanh toán',key:'payment_method'},{label:'Ghi chú',key:'note'},{label:'Công cụ',render:x=>canEdit?`${x.confirmation_status==='PENDING'?`<button class="small-action finance-bill-confirm" data-id="${x.id}">Xác nhận</button>`:''}<button class="small-action finance-bill-edit" data-id="${x.id}">Sửa</button>`:'—'}];
  const actions=canEdit?'<button class="primary" id="add-finance-bill">Tạo hóa đơn</button><button class="ghost" id="export-finance-bills">Xuất Excel</button>':'';
  const confirmed=list.filter(x=>x.confirmation_status==='CONFIRMED'), totalPaid=confirmed.reduce((sum,x)=>sum+(Number(x.payment_amount)||0),0);
  el.innerHTML=head('Hóa đơn','Theo dõi hóa đơn, xác nhận và thu tiền.',actions)+referenceTabs([{label:'Hóa đơn đóng tiền'},{label:'Hóa đơn đóng tiền trước'},{label:'Hóa đơn online'}])+`<div class="filter-strip"><label>Tìm kiếm<input id="finance-bill-query" placeholder="Tìm trong bảng…"></label><label>Người tạo<input id="finance-bill-creator" placeholder="Người tạo"></label><label>Từ ngày<input id="finance-bill-date-from" type="text" inputmode="numeric" placeholder="dd/mm/yyyy" data-date-input></label><label>Đến ngày<input id="finance-bill-date-to" type="text" inputmode="numeric" placeholder="dd/mm/yyyy" data-date-input></label><label>Chi nhánh<input id="finance-bill-branch" placeholder="Chi nhánh"></label><label>Nhân viên<input id="finance-bill-employee" placeholder="Nhân viên"></label><label>Xác nhận<select id="finance-bill-status-filter"><option value="">Trạng thái xác nhận</option>${['PENDING','CONFIRMED','REJECTED'].map(v=>`<option>${v}</option>`).join('')}</select></label><button class="ghost" id="finance-bill-filter-clear" type="button">Xóa lọc</button></div><div class="finance-summary"><div><b>Số hóa đơn:</b> ${list.length}</div><div><b>Tiền thu được:</b> ${totalPaid.toLocaleString('vi-VN')} VND</div><div><b>Tiền hợp đồng:</b> —</div><div><b>Số tiền hoàn trả:</b> —</div><div><b>Số tiền vật phẩm:</b> —</div><div><b>Phụ thu:</b> —</div><div><b>Ví tiền CO:</b> —</div></div>`+dataTable('hóa đơn',cols,list);
  $('#add-finance-bill')?.addEventListener('click',financeBillModal);
  const build=v=>{const q=new URLSearchParams();[['q','finance-bill-query'],['creator','finance-bill-creator'],['date_from','finance-bill-date-from'],['date_to','finance-bill-date-to'],['center','finance-bill-center'],['branch','finance-bill-branch'],['employee','finance-bill-employee'],['confirmation_status','finance-bill-status-filter']].forEach(([key,id])=>{if(v[id])q.set(key,v[id]);});return q;};
  $('#export-finance-bills')?.addEventListener('click',()=>downloadCsv('/api/export/finance-bills'+(build(Object.fromEntries(['finance-bill-query','finance-bill-creator','finance-bill-date-from','finance-bill-date-to','finance-bill-center','finance-bill-branch','finance-bill-employee','finance-bill-status-filter'].map(id=>[id,$(`#${id}`)?.value||'']))).toString()?'?'+build(Object.fromEntries(['finance-bill-query','finance-bill-creator','finance-bill-date-from','finance-bill-date-to','finance-bill-center','finance-bill-branch','finance-bill-employee','finance-bill-status-filter'].map(id=>[id,$(`#${id}`)?.value||'']))).toString():''),'finance-bills.csv'));
  const tableId=el.querySelector('[data-table-card]')?.dataset.tableCard;attachServerTableFilters(el,tableId,['finance-bill-query','finance-bill-creator','finance-bill-date-from','finance-bill-date-to','finance-bill-center','finance-bill-branch','finance-bill-employee','finance-bill-status-filter','finance-bill-filter-clear'],'/api/finance/bills',build,'finance-bills');
  el.onclick=e=>{const confirm=e.target.closest('.finance-bill-confirm'),button=e.target.closest('.finance-bill-edit');if(confirm&&canEdit){api(`/api/finance/bills/${confirm.dataset.id}/confirm`,{method:'POST',body:{}}).then(()=>{toast('Đã xác nhận hóa đơn');render();}).catch(err=>toast(err.message));}else if(button&&canEdit)financeBillEditModal(button.dataset.id);};
}
function financeRevenueFields(x={}){return [{name:'code',label:'Mã',value:x.code||''},{name:'name',label:'Tên',value:x.name||''},{name:'status',label:'Trạng thái',value:x.status||'ACTIVE',options:['ACTIVE','INACTIVE'].map(v=>({value:v,label:v}))},{name:'price',label:'Giá',type:'number',value:x.price??'',required:false},{name:'discount_type',label:'Kiểu giảm',value:x.discount_type||'',required:false,options:[{value:'',label:'Không giảm'},{value:'FIXED',label:'Số tiền'},{value:'PERCENT',label:'Phần trăm'}]},{name:'discount_value',label:'Giá trị giảm',type:'number',value:x.discount_value??'',required:false},{name:'amount_due',label:'Giá phải thu',type:'number',value:x.amount_due??'',required:false},{name:'center',label:'Trung tâm',value:x.center||'',required:false},{name:'note',label:'Ghi chú',value:x.note||'',required:false,wide:true}];}
function financeRevenueModal(){openJsonForm('Tạo doanh thu','/api/finance/revenues',financeRevenueFields(),()=>render());}
async function financeRevenueEditModal(id){try{const x=(await api(`/api/finance/revenues/${id}`)).data;openJsonForm('Sửa doanh thu',`/api/finance/revenues/${id}`,financeRevenueFields(x),()=>render());}catch(err){toast(err.message);}}
async function financeRevenues(el){
  const list=await load('/api/finance/revenues','finance-revenues'), canEdit=['ADMIN','STAFF'].includes(state.user.role);
  const discountLabel=value=>value==='PERCENT'?'%':value==='FIXED'?'Theo tiền':(value||'—');
  const cols=[
    {label:'No.',render:(_x,index)=>esc(index+1)},
    {label:'Mã',render:x=>`<button class="link-button finance-revenue-edit" data-id="${x.id}">${esc(x.code)}</button>`},
    {label:'Tên',key:'name'},
    {label:'Trạng thái',render:x=>`<span class="badge ${x.status==='ACTIVE'?'green':'red'}">${esc(({ACTIVE:'Kích hoạt',INACTIVE:'Tạm khóa'})[x.status]||x.status)}</span>`},
    {label:'Giá',render:x=>x.price==null?'—':`${Number(x.price).toLocaleString('vi-VN')} VND`},
    {label:'Kiểu giảm',render:x=>esc(discountLabel(x.discount_type))},
    {label:'Giá trị giảm',render:x=>x.discount_value==null?'—':`${Number(x.discount_value).toLocaleString('vi-VN')} ${x.discount_type==='PERCENT'?'%':'VND'}`},
    {label:'Giá phải thu',render:x=>x.amount_due==null?'—':`${Number(x.amount_due).toLocaleString('vi-VN')} VND`},
    {label:'Trung tâm',key:'center'},
    {label:'Ghi chú',key:'note'},
    {label:'Công cụ',render:x=>canEdit?`<button class="small-action finance-revenue-edit" data-id="${x.id}" title="Sửa">…</button>`:'—'}
  ];
  // Reference /finance/revenue exposes search plus the shared 10/25/50/100
  // pager. Status/center filters and Excel are absent from the pinned screen.
  const actions=canEdit?'<button class="primary" id="add-finance-revenue">Tạo mới</button>':'';
  const filterMarkup='<div class="filter-strip finance-revenue-filters"><label><input id="finance-revenue-query" placeholder="Tìm trong bảng..." aria-label="Tìm trong bảng..."></label><button class="ghost" id="finance-revenue-filter-clear" type="button">Xóa lọc</button></div>';
  el.innerHTML=head('Khoản thu tài chính','',actions)+filterMarkup+dataTable('bản ghi',cols,list,{includeSearch:false,pageSizes:[10,25,50,100]});
  $('#add-finance-revenue')?.addEventListener('click',financeRevenueModal);
  const build=v=>{const q=new URLSearchParams();if(v['finance-revenue-query'])q.set('q',v['finance-revenue-query']);return q;};
  const tableId=el.querySelector('[data-table-card]')?.dataset.tableCard;
  const card=el.querySelector('[data-table-card]');
  const updateRevenueCount=()=>{const footer=card?.querySelector('.table-footer');if(!footer)return;let count=footer.querySelector('.finance-revenue-page-count');if(!count){count=document.createElement('span');count.className='finance-revenue-page-count';footer.prepend(count);}const registry=state.tableRegistry[tableId];const total=registry?.rows?.length||0;const size=Number(card.dataset.pageSize||10),page=Number(card.dataset.page||0);count.textContent=`Hiển thị ${total?page*size+1:0} đến ${Math.min((page+1)*size,total)} của ${total} bản ghi`;};
  queueMicrotask(()=>{updateRevenueCount();const footer=card?.querySelector('.table-footer');if(footer)new MutationObserver(updateRevenueCount).observe(footer,{childList:true});});
  attachServerTableFilters(el,tableId,['finance-revenue-query','finance-revenue-filter-clear'],'/api/finance/revenues',build,'finance-revenues');
  el.onclick=e=>{const b=e.target.closest('.finance-revenue-edit');if(b&&canEdit)financeRevenueEditModal(b.dataset.id);};
}
function surveyFields(x={}){return [{name:'name',label:'Tên khảo sát',value:x.name||''},{name:'due_date',label:'Hạn làm',type:'text',inputmode:'numeric',placeholder:'dd/mm/yyyy',dateInput:true,value:x.due_date||'',required:false},{name:'status',label:'Trạng thái',value:x.status||'DRAFT',options:['DRAFT','PUBLISHED','CLOSED'].map(v=>({value:v,label:v}))},{name:'description',label:'Mô tả',value:x.description||'',required:false,wide:true}];}
function surveyModal(){openJsonForm('Tạo khảo sát','/api/surveys',surveyFields(),data=>surveyBuilderModal(data.id));}
async function surveyEditModal(id,onSaved){try{const x=(await api(`/api/surveys/${id}`)).data;openJsonForm('Thiết lập khảo sát',`/api/surveys/${id}`,surveyFields(x),onSaved||(()=>render()));}catch(err){toast(err.message);}}
function surveyQuestionForm(survey,page,question,onSaved){const x=question||{};openJsonForm(question?'Sửa câu hỏi':'Thêm câu hỏi',question?`/api/survey-questions/${question.id}`:`/api/survey-pages/${page.id}/questions`,[{name:'kind',label:'Loại câu hỏi',value:x.kind||'INPUT',options:[['INPUT','Một đầu vào'],['CHECKBOX','Checkbox'],['DROPDOWN','Thả xuống'],['COMMENT','Bình luận'],['RATING','Xếp hạng'],['IMAGE','Hình ảnh']].map(([value,label])=>({value,label}))},{name:'label',label:'Nội dung câu hỏi',value:x.label||''},{name:'options',label:'Các lựa chọn (mỗi dòng một mục)',value:(x.options||[]).join('\n'),required:false,wide:true},{name:'position',label:'Vị trí',type:'number',value:x.position??(page.questions?.length||0)},{name:'required',label:'Bắt buộc',value:x.required?'true':'false',options:[{value:'false',label:'Không'},{value:'true',label:'Có'}]}],onSaved,(v)=>{v.options=v.options?String(v.options).split(/\r?\n/).map(s=>s.trim()).filter(Boolean):[];v.position=Number(v.position||0);});}
async function surveyBuilderModal(id){
  try{let model=JSON.parse(JSON.stringify((await api(`/api/surveys/${id}`)).data));let selected=0,history=[JSON.stringify(model)],cursor=0;const wrap=document.createElement('div');wrap.className='modal-backdrop';wrap.innerHTML=`<div class="modal modal-wide"><div class="screen-head"><div><p class="eyebrow">SURVEY BUILDER</p><h2 id="survey-builder-title"></h2></div><div class="form-actions"><button type="button" class="ghost" id="survey-undo">Hoàn tác</button><button type="button" class="ghost" id="survey-redo">Làm lại</button><button type="button" class="ghost" id="survey-settings">Thiết lập khảo sát</button><button type="button" class="ghost close-modal">Đóng</button></div></div><div class="tab-strip"><button type="button" class="ghost active" data-survey-tab="design">Thiết kế khảo sát</button><button type="button" class="ghost" data-survey-tab="test">Kiểm-tra-khảo-sát</button></div><div id="survey-builder-panel"></div></div>`;document.body.append(wrap);wrap.querySelector('.close-modal').onclick=()=>wrap.remove();
    const panel=wrap.querySelector('#survey-builder-panel');const push=next=>{model=JSON.parse(JSON.stringify(next));history=history.slice(0,cursor+1);history.push(JSON.stringify(model));cursor++;};const refresh=data=>{push(data);renderDesign();};
    const renderDesign=()=>{wrap.querySelector('#survey-builder-title').textContent=model.name;const page=model.pages[selected]||{title:'Trang mới',description:'',questions:[]};panel.innerHTML=`<div class="filter-strip"><label>Trang<select id="survey-page-select">${model.pages.map((p,i)=>`<option value="${i}" ${i===selected?'selected':''}>${i+1}. ${esc(p.title||'Trang '+(i+1))}</option>`).join('')}</select></label><button class="primary" id="survey-add-page">+ Trang</button><button class="ghost" id="survey-add-question">+ Câu hỏi</button><button class="ghost" id="survey-edit-page">Sửa trang</button></div><div class="card" style="padding:18px"><h3>${esc(page.title||'Trang chưa đặt tên')}</h3><p class="muted">${esc(page.description||'')}</p>${page.questions.length?page.questions.map((q,i)=>`<div class="activity-row"><span><b>${i+1}. ${esc(q.label)}</b><small> · ${esc(q.kind)}${q.required?' · bắt buộc':''}</small></span><button class="small-action survey-question-edit" data-id="${q.id}">Sửa</button></div>`).join(''):'<div class="empty">Chưa có câu hỏi.</div>'}</div>`;
      $('#survey-page-select')?.addEventListener('change',e=>{selected=Number(e.target.value);renderDesign();});$('#survey-add-page')?.addEventListener('click',()=>openJsonForm('Thêm trang khảo sát',`/api/surveys/${id}/pages`,[{name:'title',label:'Tiêu đề trang',value:'Trang '+(model.pages.length+1),required:false},{name:'description',label:'Mô tả',required:false,wide:true},{name:'position',label:'Vị trí',type:'number',value:model.pages.length}],refresh));$('#survey-edit-page')?.addEventListener('click',()=>openJsonForm('Sửa trang',`/api/survey-pages/${page.id}`,[{name:'title',label:'Tiêu đề trang',value:page.title,required:false},{name:'description',label:'Mô tả',value:page.description,required:false,wide:true},{name:'position',label:'Vị trí',type:'number',value:page.position}],refresh));$('#survey-add-question')?.addEventListener('click',()=>surveyQuestionForm(model,page,null,refresh));panel.querySelectorAll('.survey-question-edit').forEach(b=>b.onclick=()=>surveyQuestionForm(model,page,page.questions.find(q=>String(q.id)===String(b.dataset.id)),refresh));};
    const renderTest=async()=>{const pageQuestions=model.pages.flatMap(p=>p.questions.map(q=>({...q,page_title:p.title})));const responses=(await api(`/api/surveys/${id}/responses`)).data||[];panel.innerHTML=`<div class="card" style="padding:18px"><h3>Thử khảo sát</h3><form id="survey-response-form"><label>Người trả lời<input name="respondent_name" value="${esc(state.user.full_name)}"></label>${pageQuestions.map(q=>`<label>${esc(q.label)}${q.kind==='COMMENT'?`<textarea name="answer_${q.id}" rows="3"></textarea>`:q.kind==='CHECKBOX'?`<input name="answer_${q.id}" placeholder="Các lựa chọn, phân tách dấu phẩy">`:q.kind==='DROPDOWN'?`<select name="answer_${q.id}">${(q.options||[]).map(o=>`<option>${esc(o)}</option>`).join('')}</select>`:q.kind==='RATING'?`<input name="answer_${q.id}" type="number" min="1" max="5">`:q.kind==='IMAGE'?`<input name="answer_${q.id}" type="url" placeholder="URL hình ảnh">`:`<input name="answer_${q.id}">`}</label>`).join('')}<div class="form-actions"><button class="primary">Lưu phản hồi</button></div><p class="error modal-error"></p></form></div><div class="card" style="padding:18px;margin-top:14px"><h3>Kết quả (${responses.length})</h3>${responses.length?responses.map(r=>`<div class="activity-row"><span>${esc(r.respondent_name)} · ${esc(r.respondent_role)}</span><small>${fmt(r.submitted_at)}</small></div>`).join(''):'<div class="empty">Chưa có phản hồi.</div>'}</div>`;panel.querySelector('form').onsubmit=async e=>{e.preventDefault();const f=new FormData(e.currentTarget),answers={};pageQuestions.forEach(q=>{answers[String(q.id)]=f.get(`answer_${q.id}`)||'';});try{await api(`/api/surveys/${id}/responses`,{method:'POST',body:{respondent_name:f.get('respondent_name'),answers}});toast('Đã lưu phản hồi');renderTest();}catch(err){panel.querySelector('.modal-error').textContent=err.message;}};};
    wrap.querySelectorAll('[data-survey-tab]').forEach(tab=>tab.onclick=()=>{wrap.querySelectorAll('[data-survey-tab]').forEach(x=>x.classList.toggle('active',x===tab));tab.dataset.surveyTab==='design'?renderDesign():renderTest();});wrap.querySelector('#survey-settings').onclick=()=>surveyEditModal(id,data=>{model=data;wrap.querySelector('#survey-builder-title').textContent=model.name;renderDesign();});wrap.querySelector('#survey-undo').onclick=()=>{if(cursor>0){cursor--;model=JSON.parse(history[cursor]);renderDesign();}};wrap.querySelector('#survey-redo').onclick=()=>{if(cursor<history.length-1){cursor++;model=JSON.parse(history[cursor]);renderDesign();}};renderDesign();
  }catch(err){toast(err.message);}
}
async function surveys(el){const list=await load('/api/surveys','surveys'),canEdit=['ADMIN','STAFF'].includes(state.user.role);const cols=[{label:'No.',render:x=>esc(x.id)},{label:'Tên khảo sát',render:x=>`<button class="link-button survey-open" data-id="${x.id}">${esc(x.name)}</button>`},{label:'Hạn làm',render:x=>esc(x.due_date||'—')},{label:'Đã làm / Đã gửi / Người nhận',render:x=>`${esc(x.completed_count)} / ${esc(x.sent_count)} / ${esc(x.recipient_count)}`},{label:'Người tạo',render:x=>esc(x.created_by_name||'—')},{label:'Thống kê / Kết quả',render:x=>esc(x.response_count??x.completed_count??0)},{label:'Hành động',render:x=>canEdit?`<button class="small-action survey-open" data-id="${x.id}">Mở</button>`:'—'}];const actions=canEdit?'<button class="primary" id="add-survey">Tạo khảo sát</button><button class="ghost" id="export-surveys">Xuất CSV</button>':'';el.innerHTML=head('Khảo sát','Thiết kế, kiểm tra và xem kết quả khảo sát.',actions)+`<div class="filter-strip"><label>Tìm kiếm<input id="survey-query" placeholder="Tên hoặc mô tả"></label><label>Trạng thái<select id="survey-status-filter"><option value="">Tất cả</option>${['DRAFT','PUBLISHED','CLOSED'].map(v=>`<option>${v}</option>`).join('')}</select></label><button class="ghost" id="survey-filter-clear" type="button">Xóa lọc</button></div>`+dataTable('khảo sát',cols,list);$('#add-survey')?.addEventListener('click',surveyModal);$('#export-surveys')?.addEventListener('click',()=>{const q=new URLSearchParams();if($('#survey-query')?.value)q.set('q',$('#survey-query').value);if($('#survey-status-filter')?.value)q.set('status',$('#survey-status-filter').value);downloadCsv('/api/export/surveys'+(q.toString()?'?'+q:''),'surveys.csv');});const tableId=el.querySelector('[data-table-card]')?.dataset.tableCard;attachServerTableFilters(el,tableId,['survey-query','survey-status-filter','survey-filter-clear'],'/api/surveys',v=>{const q=new URLSearchParams();if(v['survey-query'])q.set('q',v['survey-query']);if(v['survey-status-filter'])q.set('status',v['survey-status-filter']);return q;},'surveys');el.onclick=e=>{const b=e.target.closest('.survey-open');if(b)surveyBuilderModal(b.dataset.id);};}
async function callRecordFields(x={}){const [studentsList,customersList]=await Promise.all([load('/api/students','call-students'),load('/api/potential-customers','call-customers')]);return [{name:'phone',label:'Số điện thoại',value:x.phone||'',required:false},{name:'full_name',label:'Họ tên',value:x.full_name||''},{name:'student_id',label:'Học viên liên kết',value:x.student_id||'',required:false,options:[{value:'',label:'Không liên kết'},...studentsList.map(s=>({value:s.id,label:`${s.student_code} — ${s.full_name}`}))]},{name:'potential_customer_id',label:'Khách tiềm năng liên kết',value:x.potential_customer_id||'',required:false,options:[{value:'',label:'Không liên kết'},...customersList.map(c=>({value:c.id,label:`${c.customer_code} — ${c.full_name}`}))]},{name:'party_role',label:'Quyền',value:x.party_role||'',required:false},{name:'call_type',label:'Loại cuộc gọi',value:x.call_type||'',required:false},{name:'staff_name',label:'Nhân viên',value:x.staff_name||'',required:false},{name:'note',label:'Ghi chú',value:x.note||'',required:false,wide:true},{name:'status',label:'Trạng thái',value:x.status||'',required:false},{name:'duration_seconds',label:'Thời lượng (giây)',type:'number',value:x.duration_seconds??'',required:false},{name:'recording_ref',label:'Ghi âm',value:x.recording_ref||'',required:false},{name:'called_at',label:'Thời gian',value:x.called_at||'',required:false}];}
async function callHistoryModal(){openJsonForm('Ghi log cuộc gọi','/api/call-history',await callRecordFields(),()=>render());}
async function callHistoryEditModal(id){try{const rows=(await api('/api/call-history')).data||[],row=rows.find(x=>String(x.id)===String(id));if(!row)throw new Error('Không tìm thấy log cuộc gọi');openJsonForm('Sửa log cuộc gọi',`/api/call-history/${id}`,await callRecordFields(row),()=>render());}catch(err){toast(err.message);}}
async function callHistory(el){const list=await load('/api/call-history','call-history'),canEdit=['ADMIN','STAFF'].includes(state.user.role);const cols=[{label:'No.',render:x=>esc(x.id)},{label:'Số điện thoại',key:'phone'},{label:'Họ tên',key:'full_name'},{label:'Liên kết',render:x=>esc(x.linked_student_name?`HV: ${x.linked_student_code} — ${x.linked_student_name}`:x.linked_customer_name?`KH: ${x.linked_customer_code} — ${x.linked_customer_name}`:'—')},{label:'Quyền',key:'party_role'},{label:'Loại cuộc gọi',key:'call_type'},{label:'Nhân viên',key:'staff_name'},{label:'Ghi chú',key:'note'},{label:'Trạng thái',key:'status'},{label:'Thời lượng cuộc gọi',render:x=>x.duration_seconds==null?'—':`${esc(x.duration_seconds)}s`},{label:'Ghi âm',key:'recording_ref'},{label:'Thời gian',render:x=>esc(x.called_at||x.created_at||'—')},{label:'Công cụ',render:x=>canEdit?`<button class="small-action call-history-edit" data-id="${x.id}">Sửa</button>`:'—'}];const actions=canEdit?'<button class="primary" id="add-call-history">Ghi log cuộc gọi</button><button class="ghost" id="export-call-history">Xuất CSV</button>':'';el.innerHTML=head('Lịch sử cuộc gọi','Theo dõi cuộc gọi gắn với học viên và khách hàng.',actions)+`<div class="filter-strip"><label>Tất cả / trạng thái<select id="call-status-filter"><option value="">Tất cả</option><option>CONNECTED</option><option>MISSED</option><option>FOLLOW_UP</option></select></label><label>Từ ngày<input id="call-date-from" type="text" inputmode="numeric" placeholder="dd/mm/yyyy" data-date-input></label><label>Đến ngày<input id="call-date-to" type="text" inputmode="numeric" placeholder="dd/mm/yyyy" data-date-input></label><label>Tìm kiếm<input id="call-query" placeholder="Số điện thoại, họ tên, hồ sơ…"></label><button class="ghost" id="call-filter-clear" type="button">Xóa lọc</button></div>`+dataTable('lịch sử cuộc gọi',cols,list);$('#add-call-history')?.addEventListener('click',callHistoryModal);const build=v=>{const q=new URLSearchParams();if(v['call-query'])q.set('q',v['call-query']);if(v['call-status-filter'])q.set('status',v['call-status-filter']);if(v['call-date-from'])q.set('date_from',v['call-date-from']);if(v['call-date-to'])q.set('date_to',v['call-date-to']);return q;};$('#export-call-history')?.addEventListener('click',()=>{const v=Object.fromEntries(['call-query','call-status-filter','call-date-from','call-date-to'].map(id=>[id,$(`#${id}`)?.value||'']));const q=build(v);downloadCsv('/api/export/call-history'+(q.toString()?'?'+q:''),'call-history.csv');});const tableId=el.querySelector('[data-table-card]')?.dataset.tableCard;attachServerTableFilters(el,tableId,['call-query','call-status-filter','call-date-from','call-date-to','call-filter-clear'],'/api/call-history',build,'call-history');el.onclick=e=>{const b=e.target.closest('.call-history-edit');if(b&&canEdit)callHistoryEditModal(b.dataset.id);};}
async function timetableModal(){const [classesList,slotsList]=await Promise.all([state.data.classes?Promise.resolve(state.data.classes):load('/api/classes','classes'),load('/api/session-slots','session-slots')]);const wrap=formModal('Thêm buổi học','/api/timetable',[{name:'class_id',label:'Lớp',options:classesList.map(x=>({value:x.id,label:`${x.code} — ${x.course_name}`}))},{name:'session_slot_id',label:'Ca học',required:false,options:[{value:'',label:'Không chọn ca'},...slotsList.filter(x=>x.status==='ACTIVE').map(x=>({value:x.id,label:`${x.code} — ${x.name} (${x.start_time}–${x.end_time})`,slot:x}))]},{name:'session_date',label:'Ngày',type:'text',inputmode:'numeric',placeholder:'dd/mm/yyyy',dateInput:true},{name:'start_time',label:'Bắt đầu',type:'time'},{name:'end_time',label:'Kết thúc',type:'time'},{name:'room',label:'Phòng',required:false}], 'Đã tạo buổi học');const slotSelect=wrap.querySelector('[name="session_slot_id"]');slotSelect?.addEventListener('change',()=>{const slot=slotsList.find(x=>String(x.id)===String(slotSelect.value));if(!slot)return;wrap.querySelector('[name="start_time"]').value=slot.start_time;wrap.querySelector('[name="end_time"]').value=slot.end_time;});}
async function timetableEditModal(id){const [list,slotsList]=await Promise.all([state.data.timetable?Promise.resolve(state.data.timetable):load('/api/timetable','timetable'),load('/api/session-slots','session-slots')]);const x=list.find(row=>String(row.id)===String(id));if(!x){toast('Không tìm thấy buổi học');return;}const wrap=document.createElement('div');wrap.className='modal-backdrop';wrap.innerHTML=`<div class="modal"><h2>Sửa buổi học</h2><form><div class="form-grid"><label>Ca học<select name="session_slot_id"><option value="">Không chọn ca</option>${slotsList.map(s=>`<option value="${esc(s.id)}" ${String(s.id)===String(x.session_slot_id||'')?'selected':''}>${esc(s.code)} — ${esc(s.name)} (${esc(s.start_time)}–${esc(s.end_time)})${s.status==='INACTIVE'?' · INACTIVE':''}</option>`).join('')}</select></label><label>Ngày<input name="session_date" type="text" inputmode="numeric" placeholder="dd/mm/yyyy" data-date-input value="${esc(x.session_date)}" required></label><label>Phòng<input name="room" value="${esc(x.room||'')}"></label><label>Bắt đầu<input name="start_time" type="time" value="${esc(x.start_time)}" required></label><label>Kết thúc<input name="end_time" type="time" value="${esc(x.end_time)}" required></label><label>Trạng thái<select name="status">${['SCHEDULED','COMPLETED','CANCELLED'].map(s=>`<option ${s===x.status?'selected':''}>${s}</option>`).join('')}</select></label></div><div class="form-actions"><button type="button" class="ghost close-modal">Hủy</button><button class="primary">Lưu</button></div><p class="error modal-error"></p></form></div>`;document.body.append(wrap);wrap.querySelector('.close-modal').onclick=()=>wrap.remove();wrap.querySelector('form').onsubmit=async e=>{e.preventDefault();try{await api(`/api/timetable/${id}`,{method:'POST',body:Object.fromEntries(new FormData(e.currentTarget))});wrap.remove();toast('Đã cập nhật buổi học');render();}catch(err){wrap.querySelector('.modal-error').textContent=err.message;}};}
async function timetableStudentsModal(id){try{const d=await api(`/api/timetable/${id}/students`);const rows=d.data||[];const wrap=document.createElement('div');wrap.className='modal-backdrop';wrap.innerHTML=`<div class="modal modal-wide"><h2>Danh sách học viên</h2><p class="muted">${rows.length} học viên đã ghi danh cho buổi học này.</p>${rows.length?`<div class="table-wrap"><table><thead><tr><th>Mã</th><th>Họ tên</th><th>Email</th><th>Điện thoại</th><th>Trạng thái</th></tr></thead><tbody>${rows.map(x=>`<tr><td>${esc(x.student_code)}</td><td>${esc(x.full_name)}</td><td>${esc(x.email||'—')}</td><td>${esc(x.phone||'—')}</td><td><span class="badge green">${esc(statusLabel(x.enrollment_status))}</span></td></tr>`).join('')}</tbody></table></div>`:'<div class="empty">Chưa có học viên ghi danh.</div>'}<div class="form-actions"><button class="ghost close-modal">Đóng</button></div></div>`;document.body.append(wrap);wrap.querySelector('.close-modal').onclick=()=>wrap.remove();}catch(err){toast(err.message);}}
async function timetableCancel(id){confirmDeleteModal({title:'Xác nhận hủy buổi học',message:'Buổi học sẽ chuyển sang trạng thái đã hủy.',onConfirm:async()=>{await api(`/api/timetable/${id}/cancel`,{method:'POST',body:{}});toast('Đã hủy buổi học');render();}});}
async function evaluationModal(){const [classesList,studentsList]=await Promise.all([load('/api/classes','classes'),load('/api/students','students')]);formModal('Ghi đánh giá','/api/evaluations',[{name:'class_id',label:'Lớp',options:classesList.map(x=>({value:x.id,label:`${x.code} — ${x.course_name}`}))},{name:'student_id',label:'Học viên',options:studentsList.map(x=>({value:x.id,label:`${x.student_code} — ${x.full_name}`}))},{name:'session_date',label:'Ngày',type:'text',inputmode:'numeric',placeholder:'dd/mm/yyyy',dateInput:true},{name:'score',label:'Điểm (0–10)',type:'number',required:false},{name:'status',label:'Trạng thái',options:[{value:'DRAFT',label:'Nháp'},{value:'PUBLISHED',label:'Đã công bố'}]},{name:'note',label:'Ghi chú',required:false,wide:true}], 'Đã lưu đánh giá');}
async function testModal(){const classesList=state.data.classes||await load('/api/classes','classes');formModal('Tạo bài kiểm tra','/api/tests',[{name:'class_id',label:'Lớp',options:classesList.map(x=>({value:x.id,label:`${x.code} — ${x.course_name}`}))},{name:'name',label:'Tên bài kiểm tra'},{name:'test_date',label:'Ngày',type:'text',inputmode:'numeric',placeholder:'dd/mm/yyyy',dateInput:true},{name:'max_score',label:'Điểm tối đa',type:'number',value:'10'}], 'Đã tạo bài kiểm tra');}
async function testResultsModal(id,canEdit){
  try {
    const payload=(await api(`/api/tests/${id}/results`)).data;
    const x=payload.test, rows=payload.results||[], wrap=document.createElement('div');
    wrap.className='modal-backdrop';
    const roster=rows.length?rows.map(row=>`<div class="result-row"><div><b>${esc(row.student_code)} — ${esc(row.full_name)}</b><small>${esc(row.email||'')}</small></div><label>Điểm<input name="score_${row.student_id}" type="number" min="0" max="${esc(x.max_score)}" step="0.1" value="${row.score==null?'':esc(row.score)}" ${canEdit?'':'disabled'}></label><label>Ghi chú<input name="note_${row.student_id}" value="${esc(row.note||'')}" ${canEdit?'':'disabled'}></label></div>`).join(''):'<div class="empty">Chưa có học viên ghi danh.</div>';
    wrap.innerHTML=`<div class="modal modal-wide"><h2>${esc(x.name)} · kết quả</h2><p class="muted">${esc(x.class_code)} · ${esc(x.test_date)} · tối đa ${esc(x.max_score)}</p><form>${roster}<div class="form-actions"><button type="button" class="ghost close-modal">Đóng</button>${canEdit&&rows.length?'<button class="primary">Lưu kết quả</button>':''}</div><p class="error modal-error"></p></form></div>`;
    document.body.append(wrap);
    wrap.querySelector('.close-modal').onclick=()=>wrap.remove();
    if(canEdit&&rows.length) wrap.querySelector('form').onsubmit=async e=>{
      e.preventDefault();
      const values=new FormData(e.currentTarget);
      try {
        for(const row of rows){
          const raw=values.get(`score_${row.student_id}`), note=values.get(`note_${row.student_id}`)||'';
          if(raw==='' && !note && !row.result_id) continue;
          await api('/api/test-results',{method:'POST',body:{test_id:id,student_id:row.student_id,score:raw===''?null:raw,note}});
        }
        wrap.remove(); toast('Đã lưu kết quả kiểm tra'); render();
      } catch(err){wrap.querySelector('.modal-error').textContent=err.message;}
    };
  } catch(err){toast(err.message);}
}
async function homeworkModal(){const classesList=state.data.classes||await load('/api/classes','classes');formModal('Tạo bài tập','/api/homework',[{name:'class_id',label:'Lớp',options:classesList.map(x=>({value:x.id,label:`${x.code} — ${x.course_name}`}))},{name:'title',label:'Tiêu đề'},{name:'due_date',label:'Hạn nộp',type:'text',inputmode:'numeric',placeholder:'dd/mm/yyyy',dateInput:true},{name:'status',label:'Trạng thái',options:[{value:'OPEN',label:'Đang mở'},{value:'DRAFT',label:'Nháp'},{value:'CLOSED',label:'Đã đóng'}]},{name:'description',label:'Mô tả',required:false,wide:true}], 'Đã tạo bài tập');}
function trialModal(){formModal('Tạo đăng ký học thử','/api/trial-registrations',[{name:'full_name',label:'Họ tên'},{name:'guardian_name',label:'Người giám hộ',required:false},{name:'phone',label:'Điện thoại',required:false},{name:'trial_date',label:'Ngày học thử',type:'text',inputmode:'numeric',placeholder:'dd/mm/yyyy',dateInput:true},{name:'notes',label:'Ghi chú',required:false,wide:true}], 'Đã tạo đăng ký học thử');}
function customerTestModal(){formModal('Tạo lịch hẹn test','/api/customer-tests',[{name:'customer_name',label:'Họ tên'},{name:'parent_name',label:'Phụ huynh',required:false},{name:'test_date',label:'Ngày hẹn',type:'text',inputmode:'numeric',placeholder:'dd/mm/yyyy',dateInput:true},{name:'score',label:'Điểm (nếu có)',type:'number',required:false},{name:'sales_owner',label:'Phụ trách',required:false},{name:'note',label:'Ghi chú',required:false,wide:true}], 'Đã tạo lịch hẹn');}
async function customerTestEditModal(id){const d=await api(`/api/customer-tests/${id}`);const x=d.data;const wrap=document.createElement('div');wrap.className='modal-backdrop';wrap.innerHTML=`<div class="modal"><h2>Cập nhật điểm test</h2><form><div class="form-grid"><label>Họ tên<input name="customer_name" value="${esc(x.customer_name)}" required></label><label>Phụ huynh<input name="parent_name" value="${esc(x.parent_name||'')}"></label><label>Ngày hẹn<input name="test_date" type="text" inputmode="numeric" placeholder="dd/mm/yyyy" data-date-input value="${esc(x.test_date)}" required></label><label>Điểm (0–10)<input name="score" type="number" min="0" max="10" step="0.1" value="${x.score===null?'':esc(x.score)}"></label><label>Phụ trách<input name="sales_owner" value="${esc(x.sales_owner||'')}"></label><label>Trạng thái<select name="status">${['BOOKED','SCORED','CANCELLED'].map(s=>`<option ${s===x.status?'selected':''}>${s}</option>`).join('')}</select></label><label class="wide">Ghi chú<input name="note" value="${esc(x.note||'')}"></label></div><div class="form-actions"><button type="button" class="ghost close-modal">Hủy</button><button class="primary">Lưu</button></div><p class="error modal-error"></p></form></div>`;document.body.append(wrap);wrap.querySelector('.close-modal').onclick=()=>wrap.remove();wrap.querySelector('form').onsubmit=async e=>{e.preventDefault();try{await api(`/api/customer-tests/${id}`,{method:'POST',body:Object.fromEntries(new FormData(e.currentTarget))});wrap.remove();toast('Đã cập nhật điểm test');render();}catch(err){wrap.querySelector('.modal-error').textContent=err.message;}};}
async function pendingModal(){const coursesList=state.data.courses||await load('/api/courses','courses');formModal('Tạo đăng ký chờ lớp','/api/pending-enrollments',[{name:'customer_name',label:'Họ tên'},{name:'phone',label:'Điện thoại',required:false},{name:'course_id',label:'Khóa học',required:false,options:[{value:'',label:'Chưa chọn'},...coursesList.map(x=>({value:x.id,label:`${x.code} — ${x.name}`}))]},{name:'preferred_day',label:'Ngày mong muốn',required:false},{name:'preferred_session',label:'Ca mong muốn',required:false},{name:'notes',label:'Ghi chú',required:false,wide:true}], 'Đã tạo đăng ký chờ lớp');}
async function pendingEditModal(id){const [d,coursesList]=await Promise.all([api(`/api/pending-enrollments/${id}`),state.data.courses?Promise.resolve(state.data.courses):load('/api/courses','courses')]);const x=d.data;const wrap=document.createElement('div');wrap.className='modal-backdrop';wrap.innerHTML=`<div class="modal"><h2>Sửa đăng ký chờ lớp</h2><form><div class="form-grid"><label>Họ tên<input name="customer_name" value="${esc(x.customer_name)}" required></label><label>Điện thoại<input name="phone" value="${esc(x.phone||'')}"></label><label>Khóa học<select name="course_id"><option value="">Chưa chọn</option>${coursesList.map(c=>`<option value="${c.id}" ${String(c.id)===String(x.course_id)?'selected':''}>${esc(c.code)} — ${esc(c.name)}</option>`).join('')}</select></label><label>Trạng thái<select name="status">${['WAITING','ASSIGNED','CANCELLED'].map(s=>`<option ${s===x.status?'selected':''}>${s}</option>`).join('')}</select></label><label>Ngày mong muốn<input name="preferred_day" value="${esc(x.preferred_day||'')}"></label><label>Ca mong muốn<input name="preferred_session" value="${esc(x.preferred_session||'')}"></label><label class="wide">Ghi chú<input name="notes" value="${esc(x.notes||'')}"></label></div><div class="form-actions"><button type="button" class="ghost close-modal">Hủy</button><button class="primary">Lưu</button></div><p class="error modal-error"></p></form></div>`;document.body.append(wrap);wrap.querySelector('.close-modal').onclick=()=>wrap.remove();wrap.querySelector('form').onsubmit=async e=>{e.preventDefault();try{await api(`/api/pending-enrollments/${id}`,{method:'POST',body:Object.fromEntries(new FormData(e.currentTarget))});wrap.remove();toast('Đã cập nhật đăng ký chờ');render();}catch(err){wrap.querySelector('.modal-error').textContent=err.message;}};}
async function pendingCancel(id){confirmDeleteModal({title:'Xác nhận hủy đăng ký',message:'Đăng ký chờ lớp sẽ chuyển sang trạng thái đã hủy.',onConfirm:async()=>{await api(`/api/pending-enrollments/${id}/cancel`,{method:'POST',body:{}});toast('Đã hủy đăng ký chờ');render();}});}
async function potentialCustomers(el){
  const saleRoute=state.route==='/sale/potential/index';
  const scopeQuery=saleRoute?'?scope=sale':'';
  const payload=await api('/api/potential-customers'+scopeQuery);
  const list=payload.data||[]; state.data['potential-customers']=list;
  const summary=payload.summary||{};
  const canEdit=['ADMIN','STAFF'].includes(state.user.role);
  const saleOwners=[...new Set(list.map(x=>x.sale_owner).filter(Boolean))];
  const saleAssistants=[...new Set(list.map(x=>x.sale_assistant).filter(Boolean))];
  const statusSummary=`<div class="potential-status-summary" role="tab"><span class="is-new">Mới ${esc(summary.new??0)}</span><span class="is-contacted">Đang chăm sóc ${esc(summary.contacted??0)}</span><span class="is-success">Chăm sóc thành công ${esc(summary.successful??0)}</span><span class="is-lost">Đã hủy tư vấn ${esc(summary.cancelled??0)}</span></div>`;
  const tabs=referenceTabs(saleRoute?[{label:'Khách hàng tiềm năng'},{label:'Lịch sử chăm sóc'}]:[{label:'Khách hàng tiềm năng'},{label:'Khách hàng thô'},{label:'Lịch sử chăm sóc'}]);
  const cols=[
    {label:'No.',render:(_x,index)=>esc(index+1)},
    {label:'Khách hàng',render:x=>`<button class="link-button potential-detail potential-customer-cell" data-id="${esc(x.id)}"><b>${esc(x.full_name)}</b><small>${esc(formatDisplayDate(x.date_of_birth)||'—')} · ${esc(x.customer_code)} · ${esc(x.phone||'—')}</small><small>${esc(formatDisplayDate(x.created_at)||'—')} · ${esc(x.branch||'—')}</small></button>`},
    {label:state.route==='/sale/potential/index'?'Sales rep':'Nhân viên sale',render:x=>`<span class="class-multiline"><b>${esc(x.sale_owner||'—')}</b><small>${esc(x.branch||'—')}</small></span>`},
    {label:'Sale phụ',render:x=>esc(x.sale_assistant||'—')},
    {label:'Tag',render:x=>`<span class="potential-tag">${esc(x.tag||'')}</span>`},
    {label:'Khóa học chăm sóc',render:x=>esc(x.care_course||'0 Khóa học')},
    {label:'Khóa học quan tâm',render:x=>esc(x.interested_course||x.interest||'0 Khóa học')},
    {label:'Trạng thái',render:x=>potentialStatusBadge(x.status,x.status==='CONVERTED'?'green':x.status==='LOST'?'red':x.status==='CONTACTED'?'orange':'')},
    {label:'Hẹn test',render:x=>x.test_appointment?esc(formatDisplayDate(x.test_appointment)):'Chưa test'},
    {label:'Điểm test',render:x=>x.test_score==null?'Chưa test':esc(Number(x.test_score).toLocaleString('vi-VN'))},
    {label:'Học thử',render:x=>esc(x.trial_status||'Chưa đăng ký')},
    {label:'Ghi chú',render:x=>esc(x.note||'—')},
    {label:'Chăm sóc',render:x=>{const progress=String(x.care_progress||'0/5');const m=progress.match(/(\d+)\s*\/\s*(\d+)/);const done=m?Number(m[1]):0,total=m?Number(m[2]):5;return `<div class="care-progress" aria-label="${esc(progress)}"><span>${esc(progress)}</span><i><b style="width:${Math.min(100,Math.round(done/Math.max(1,total)*100))}%"></b></i></div>`;}},
  ];
  const actions=canEdit?`${saleRoute?'':'<button class="primary transfer-potential" type="button">Chuyển khách hàng</button>'}<button class="upload-action" type="button">Tải lên</button><button class="primary" id="add-potential">Tạo khách hàng</button>`:'';
  const ownerFilter=saleRoute?'':`<label><select id="potential-owner-filter"><option value="">Tất cả</option>${saleOwners.map(x=>`<option value="${esc(x)}">${esc(x)}</option>`).join('')}</select></label>`;
  const excelButton=saleRoute?'':'<button class="ghost" id="export-potential" type="button">Excel</button>';
  const queryPlaceholder=saleRoute?'Tìm kiếm khách hàng':'Tìm kiếm...';
  el.innerHTML=head('Khách hàng tiềm năng','',actions)+statusSummary+tabs+`<div class="potential-total">Tổng số khách hàng <b>${esc(summary.total??list.length)}</b></div><div class="filter-strip potential-filters"><label><input id="potential-query" placeholder="${queryPlaceholder}"></label>${ownerFilter}<label><select id="potential-assistant-filter"><option value="">Sale phụ</option>${saleAssistants.map(x=>`<option value="${esc(x)}">${esc(x)}</option>`).join('')}</select></label><button class="filter-apply" id="potential-filter-apply" type="button"><span aria-hidden="true">⌕</span> Lọc</button>${excelButton}<button class="ghost" id="potential-filter-clear" type="button">Xóa lọc</button></div>`+dataTable('khách hàng',cols,list,{pageSizes:[10,20],pageSizeLabel:'10 20'});
  $('#add-potential')?.addEventListener('click',()=>potentialCustomerModal());
  $('#export-potential')?.addEventListener('click',()=>{const q=new URLSearchParams();const values={q:$('#potential-query')?.value||'',sale_owner:$('#potential-owner-filter')?.value||'',sale_assistant:$('#potential-assistant-filter')?.value||''};Object.entries(values).forEach(([k,v])=>{if(v)q.set(k,v);});if(saleRoute)q.set('scope','sale');downloadCsv('/api/export/potential-customers'+(q.toString()?'?'+q.toString():''),'potential-customers.csv');});
  const tableId=el.querySelector('[data-table-card]')?.dataset.tableCard;
  queueMicrotask(()=>el.querySelector('.table-toolbar .table-search')?.remove());
  // The observed potential screens expose one page-size selector (10/20).
  // The shell's generic normalizer may add a second copy to the filter strip;
  // keep the table footer selector as the single interactive control.
  const removeDuplicatePotentialPageSize = () => {
    el.querySelectorAll('.w3-reference-page-size').forEach((node) => node.remove());
    el.querySelectorAll('.potential-filters select').forEach((select) => {
      const values = [...select.options].map((option) => option.textContent.trim());
      if (values.length === 2 && values[0] === '10' && values[1] === '20') select.closest('label')?.remove();
    });
  };
  [500, 900, 1600].forEach((delay) => setTimeout(removeDuplicatePotentialPageSize, delay));
  attachServerTableFilters(el,tableId,['potential-query','potential-owner-filter','potential-assistant-filter','potential-filter-apply','potential-filter-clear'],'/api/potential-customers',v=>{const q=new URLSearchParams();if(saleRoute)q.set('scope','sale');if(v['potential-query'])q.set('q',v['potential-query']);if(v['potential-owner-filter'])q.set('sale_owner',v['potential-owner-filter']);if(v['potential-assistant-filter'])q.set('sale_assistant',v['potential-assistant-filter']);return q;},'potential-customers');
  el.onclick=e=>{const detail=e.target.closest('.potential-detail'),edit=e.target.closest('.potential-edit'),follow=e.target.closest('.potential-followup'),remove=e.target.closest('.potential-delete');if(detail)potentialCustomerDetailModal(detail.dataset.id);else if(edit)potentialCustomerEditModal(edit.dataset.id);else if(follow)potentialFollowupModal(follow.dataset.id);else if(remove)confirmDeleteModal({title:'Xác nhận xóa khách hàng tiềm năng',message:'Khách hàng sẽ được xóa khỏi danh sách hiện tại.',onConfirm:async()=>{await api(`/api/potential-customers/${encodeURIComponent(remove.dataset.id)}`,{method:'DELETE'});toast('Đã xóa khách hàng');render();}});};
}
function potentialFields(x={}){return [{name:'customer_code',label:'Mã khách hàng',value:x.customer_code||'',required:false},{name:'full_name',label:'Họ tên',value:x.full_name||''},{name:'date_of_birth',label:'Ngày sinh',value:x.date_of_birth||'',required:false,dateInput:true},{name:'phone',label:'Điện thoại',value:x.phone||'',required:false},{name:'email',label:'Email',type:'email',value:x.email||'',required:false},{name:'branch',label:'Chi nhánh',value:x.branch||'',required:false},{name:'source',label:'Nguồn',value:x.source||'',required:false},{name:'sale_owner',label:'Nhân viên sale',value:x.sale_owner||'',required:false},{name:'sale_assistant',label:'Sale phụ',value:x.sale_assistant||'',required:false},{name:'tag',label:'Tag',value:x.tag||'',required:false},{name:'care_course',label:'Khóa học chăm sóc',value:x.care_course||'',required:false},{name:'interested_course',label:'Khóa học quan tâm',value:x.interested_course||x.interest||'',required:false},{name:'status',label:'Trạng thái',value:x.status||'NEW',options:['NEW','CONTACTED','QUALIFIED','CONVERTED','LOST'].map(s=>({value:s,label:statusLabel(s)}))},{name:'test_appointment',label:'Hẹn test',value:x.test_appointment||'',required:false,dateInput:true},{name:'test_score',label:'Điểm test',type:'number',value:x.test_score??'',required:false},{name:'trial_status',label:'Học thử',value:x.trial_status||'',required:false},{name:'care_progress',label:'Tiến độ chăm sóc',value:x.care_progress||'',required:false},{name:'next_follow_up_at',label:'Lịch chăm sóc tiếp theo',value:x.next_follow_up_at||'',required:false},{name:'note',label:'Ghi chú',value:x.note||'',required:false,wide:true}];}
function potentialCustomerModal(){formModal('Tạo khách hàng tiềm năng','/api/potential-customers',potentialFields(),'Đã tạo khách hàng');}
async function potentialCustomerEditModal(id){try{const x=(await api(`/api/potential-customers/${id}`)).data;const wrap=document.createElement('div');wrap.className='modal-backdrop';wrap.innerHTML=`<div class="modal modal-wide"><h2>Sửa khách hàng tiềm năng</h2><form><div class="form-grid">${potentialFields(x).map(fieldHtml).join('')}</div><div class="form-actions"><button type="button" class="ghost close-modal">Hủy</button><button class="primary">Lưu</button></div><p class="error modal-error"></p></form></div>`;document.body.append(wrap);wrap.querySelector('.close-modal').onclick=()=>wrap.remove();wrap.querySelector('form').onsubmit=async e=>{e.preventDefault();try{await api(`/api/potential-customers/${id}`,{method:'POST',body:Object.fromEntries(new FormData(e.currentTarget))});wrap.remove();toast('Đã cập nhật khách hàng');render();}catch(err){wrap.querySelector('.modal-error').textContent=err.message;}};}catch(err){toast(err.message);}}
async function potentialCustomerDetailModal(id){try{const x=(await api(`/api/potential-customers/${id}`)).data;const rows=x.followups||[];const wrap=document.createElement('div');wrap.className='modal-backdrop';wrap.innerHTML=`<div class="modal modal-wide"><h2>${esc(x.full_name)}</h2><div class="detail-grid"><span>Mã khách hàng</span><b>${esc(x.customer_code)}</b><span>Điện thoại</span><b>${esc(x.phone||'—')}</b><span>Email</span><b>${esc(x.email||'—')}</b><span>Nguồn</span><b>${esc(x.source||'—')}</b><span>Sale</span><b>${esc(x.sale_owner||'—')} · ${esc(x.sale_assistant||'—')}</b><span>Trạng thái</span><b>${esc(statusLabel(x.status))}</b><span>Nhu cầu</span><b>${esc(x.interest||'—')}</b></div><h3>Lịch sử chăm sóc</h3>${rows.length?`<div class="activity">${rows.map(r=>`<div class="activity-row"><span><b>${esc(r.action_type)}</b> · ${esc(r.note)}</span><small>${esc(r.outcome||'')} · ${fmt(r.created_at)}</small></div>`).join('')}</div>`:'<div class="empty">Chưa có lịch sử chăm sóc.</div>'}<div class="form-actions"><button class="ghost close-modal">Đóng</button></div></div>`;document.body.append(wrap);wrap.querySelector('.close-modal').onclick=()=>wrap.remove();}catch(err){toast(err.message);}}
async function potentialFollowupModal(id){const wrap=document.createElement('div');wrap.className='modal-backdrop';wrap.innerHTML=`<div class="modal"><h2>Ghi nhận chăm sóc</h2><form><div class="form-grid"><label>Hình thức<select name="action_type"><option>CALL</option><option>MESSAGE</option><option>NOTE</option><option>APPOINTMENT</option></select></label><label>Kết quả<input name="outcome"></label><label>Lịch tiếp theo<input name="next_follow_up_at" placeholder="YYYY-MM-DD HH:MM"></label><label class="wide">Nội dung<textarea name="note" required rows="4"></textarea></label></div><div class="form-actions"><button type="button" class="ghost close-modal">Hủy</button><button class="primary">Lưu</button></div><p class="error modal-error"></p></form></div>`;document.body.append(wrap);wrap.querySelector('.close-modal').onclick=()=>wrap.remove();wrap.querySelector('form').onsubmit=async e=>{e.preventDefault();try{await api(`/api/potential-customers/${id}/followups`,{method:'POST',body:Object.fromEntries(new FormData(e.currentTarget))});wrap.remove();toast('Đã ghi nhận chăm sóc');render();}catch(err){wrap.querySelector('.modal-error').textContent=err.message;}};}
async function careAppointments(el){
  const saleRoute=state.route==='/sale/potential/appointment';
  const scope=saleRoute?'sale':'crm';
  const endpoint=`/api/care-appointments?scope=${scope}`;
  const list=await load(endpoint,'care-appointments');
  const cols=[
    {label:'No.',render:(x,i)=>String(i+1)},
    {label:'Học viên',render:x=>`<button class="link-button care-customer-detail" data-id="${x.potential_customer_id}"><b>${esc(x.student_name||x.full_name)}</b><small>${esc(x.customer_code||'')}</small></button>`},
    {label:'Nhân viên sale',render:x=>esc(x.sale_name||x.sale_owner||'—')},
    {label:'Ngày hẹn',render:x=>formatDateValue(x.appointment_date)},
    {label:'Hành động',render:x=>esc(x.action_label||'—')},
    {label:'Ghi chú',render:x=>esc(x.note||'—')},
    {label:'Trạng thái',render:x=>`<span class="badge ${x.appointment_status==='APPOINTMENT_PROCESSED'?'green':x.appointment_status==='APPOINTMENT_CANCELLED'?'red':''}">${esc(x.appointment_status_label||'—')}</span>`}
  ];
  const actions=saleRoute?'':'<button class="ghost" id="export-care-appointments">Excel</button>';
  const statusOptions=[['','Trạng thái'],['PENDING','Chưa xử lý'],['PROCESSED','Đã xử lý'],['CANCELLED','Đã hủy cuộc hẹn']];
  const actionOptions=[['','Hành động'],['CALL','Gọi'],['MESSAGE','Nhắn tin'],['APPOINTMENT','Gặp trực tiếp']];
  // The reference exposes a sale-owner selector. Build its values from the
  // persisted rows returned by this route so the filter is actionable without
  // inventing staff names or making a second authority call.
  const saleOwners=[...new Set(list.map(x=>String(x.sale_name||x.sale_owner||'').trim()).filter(Boolean))].sort((a,b)=>a.localeCompare(b,'vi'));
  const ownerOptions=[['','Nhân viên'],['','Tất cả'],...saleOwners.map(owner=>[owner,owner])];
  const pageSize=saleRoute?'<label class="care-page-size">Hiển thị<select id="care-page-size"><option>10</option><option>25</option><option>50</option><option>100</option></select> bản ghi</label>':'';
  el.innerHTML=head('Lịch hẹn khách hàng','',actions)+
    `<div class="filter-strip"><label><input id="care-query" placeholder="Tìm kiếm..."></label><label><input id="care-date-from" type="text" inputmode="numeric" placeholder="Từ ngày" data-date-input></label><label><input id="care-date-to" type="text" inputmode="numeric" placeholder="Đến ngày" data-date-input></label><label><select id="care-status-filter">${statusOptions.map(([v,l])=>`<option value="${v}">${l}</option>`).join('')}</select></label>${saleRoute?'':`<label><select id="care-owner-filter">${ownerOptions.map(([v,l])=>`<option value="${esc(v)}">${esc(l)}</option>`).join('')}</select></label>`}<label><select id="care-action-filter">${actionOptions.map(([v,l])=>`<option value="${v}">${l}</option>`).join('')}</select></label><button class="ghost" id="care-filter-clear" type="button">Xóa lọc</button>${pageSize}</div>`+
    dataTable('lịch hẹn khách hàng',cols,list);
  // The observed appointment routes own their filter search. Remove the
  // shared table search and footer page-size so the DOM has one control per
  // reference contract; Sale keeps its explicit filter-strip page-size.
  queueMicrotask(() => {
    const card = el.querySelector('[data-table-card]');
    card?.querySelector('.table-toolbar .table-search')?.remove();
    card?.querySelector('.table-footer .table-page-size')?.remove();
  });
  const build=values=>{const q=new URLSearchParams({scope});if(values['care-query'])q.set('q',values['care-query']);if(values['care-status-filter'])q.set('status',values['care-status-filter']);if(values['care-action-filter'])q.set('action_type',values['care-action-filter']);if(values['care-owner-filter'])q.set('sale_owner',values['care-owner-filter']);if(values['care-date-from'])q.set('date_from',parseDisplayDate(values['care-date-from']));if(values['care-date-to'])q.set('date_to',parseDisplayDate(values['care-date-to']));return q;};
  const values=()=>Object.fromEntries(['care-query','care-status-filter','care-action-filter','care-owner-filter','care-date-from','care-date-to'].map(id=>[id,$(`#${id}`)?.value||'']));
  $('#export-care-appointments')?.addEventListener('click',()=>downloadCsv('/api/export/care-appointments?'+build(values()).toString(),'care-appointments.csv'));
  const tableId=el.querySelector('[data-table-card]')?.dataset.tableCard;
  attachServerTableFilters(el,tableId,['care-query','care-status-filter','care-action-filter','care-owner-filter','care-date-from','care-date-to','care-filter-clear'],'/api/care-appointments',build,'care-appointments');
  const size=$('#care-page-size'); if(size){const card=el.querySelector(`[data-table-card="${tableId}"]`); size.value='10'; size.addEventListener('change',()=>{if(card){card.dataset.pageSize=size.value;card.dataset.page='0';bindDataTable(tableId);}});}
  el.onclick=e=>{const detail=e.target.closest('.care-customer-detail');if(detail)potentialCustomerDetailModal(detail.dataset.id);};
}
async function reports(el){
  const route=state.route||'/report/training/attendance';
  const payload=(await api('/api/reports/run?route='+encodeURIComponent(route))).data||{};
  const list=payload.rows||[];
  const definitions=(payload.columns||[]);
  const columns=definitions.length?definitions.map(col=>({label:col.label||col.key,render:x=>{const value=x[col.key];return /trạng thái|status/i.test(String(col.label||col.key))?statusBadge(value):esc(displayValue(value));}})):Object.keys(list[0]||{}).map(key=>({label:key,render:x=>esc(displayValue(x[key]))}));
  const filters=(payload.filters||[]).filter(f=>f && (f.name||f.label||f.placeholder || f.options?.length)).map((f,i)=>{const id=`report-filter-${i}`;const label=f.label||f.placeholder||'Lọc';if(Array.isArray(f.options)&&f.options.length)return `<label>${esc(label)}<select id="${id}"><option value="">Tất cả</option>${f.options.map(v=>`<option value="${esc(v)}">${esc(v)}</option>`).join('')}</select></label>`;return `<label><input id="${id}" placeholder="${esc(f.placeholder||label)}"></label>`;}).join('');
  const attendanceNote=route==='/report/training/attendance'?'<p class="report-attendance-note">Ghi chú: Đúng giờ ✓, Đi muộn M, Vắng có phép CP, Vắng không phép KP, Chưa điểm danh -, Chưa vào lớp/Đã ra khỏi lớp</p>':'';
  el.innerHTML=head(payload.title||'Báo cáo','', '<button class="primary" id="export-report">Excel</button>')+`<div class="filter-strip">${filters}<button class="ghost" id="report-filter-clear" type="button">Xóa lọc</button></div>`+attendanceNote+dataTable('báo cáo '+route,columns,list);
  if(route==='/report/training/attendance'){
    const now=new Date();
    const today=`${String(now.getDate()).padStart(2,'0')}/${String(now.getMonth()+1).padStart(2,'0')}/${now.getFullYear()}`;
    el.querySelectorAll('.filter-strip input').forEach(input=>{
      const placeholder=String(input.placeholder||'').toLocaleLowerCase();
      if(/từ ngày|đến ngày/.test(placeholder) && !input.value) input.value=today;
    });
  }
  if(!list.length) el.querySelector('.table-card tbody')?.insertAdjacentHTML('beforeend',`<tr><td colspan="${Math.max(1,columns.length)}" class="empty">Chưa có dữ liệu.</td></tr>`);
  const queryFromFilters=()=>{const q=new URLSearchParams({route});el.querySelectorAll('.filter-strip input,.filter-strip select').forEach((node,i)=>{if(node.value)q.set(i===0?'q':`filter_${i}`,node.value);});return q;};
  $('#export-report')?.addEventListener('click',()=>downloadCsv('/api/reports/export?'+queryFromFilters().toString(),'report.csv'));
  const tableId=el.querySelector('[data-table-card]')?.dataset.tableCard;
  const ids=[...el.querySelectorAll('.filter-strip input,.filter-strip select')].map(x=>x.id).concat('report-filter-clear');
  attachServerTableFilters(el,tableId,ids,'/api/reports/run',v=>{const q=queryFromFilters();return q;},'reports');
}
async function audit(el){
  const list=await load('/api/audit','audit');
  const columns=[{label:'Thời gian',render:x=>fmt(x.created_at)},{label:'Actor',render:x=>esc(x.actor_id||'system')},{label:'Action',key:'action'},{label:'Entity',key:'entity'},{label:'ID',render:x=>esc(x.entity_id||'—')}];
  el.innerHTML=head('Nhật ký hệ thống','Các thay đổi được ghi nhận để truy vết.')+dataTable('nhật ký',columns,list);
}
bootstrap();

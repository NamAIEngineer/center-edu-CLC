export const POTENTIAL_PERIOD_TABS = ['Tất cả', 'Hôm nay', 'Tuần này', 'Tháng này', 'Chưa xử lý'];
const potentialDate = value => {
  const match = String(value || '').match(/^(\d{4})-(\d{2})-(\d{2})/);
  return match ? new Date(`${match[1]}-${match[2]}-${match[3]}T00:00:00`) : null;
};
export const potentialPeriodMatch = (row, period, referenceDate = new Date()) => {
  if (period === 'all') return true;
  // NEW is the only unprocessed lifecycle state. CONTACTED and QUALIFIED have
  // already moved into active follow-up, so they must not appear here.
  if (period === 'pending') return String(row?.status || '').toUpperCase() === 'NEW';
  const date = potentialDate(row?.created_at || row?.created_date);
  if (!date || Number.isNaN(date.getTime())) return false;
  const now = new Date(referenceDate); now.setHours(0, 0, 0, 0);
  if (period === 'today') return date.getTime() === now.getTime();
  if (period === 'month') return date.getFullYear() === now.getFullYear() && date.getMonth() === now.getMonth();
  const start = new Date(now); start.setDate(now.getDate() - ((now.getDay() + 6) % 7));
  const end = new Date(start); end.setDate(start.getDate() + 7);
  return date >= start && date < end;
};

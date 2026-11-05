/* Loaded after every other browser module. Applies the finance DOM seam after
 * the shared renderer and observed-control normalizer have both completed. */
import { patchFinanceControls } from './finance_parity.js';

const ROUTES = [
  '/finance/contract', '/sale/contract', '/finance/bill/index', '/finance/revenue',
  '/finance/spend/index', '/finance/appointment_date', '/finance/assessment',
  '/finance/reserve', '/finance/history_move_student', '/finance/accumulate_points',
  '/finance/item', '/finance/bill/debit_item/index', '/finance/wallet_co/index',
];

export function register(global) {
  const host = global || window.CenterEdu || {};
  const registry = host.screenRenderers;
  if (!registry || typeof host.registerScreen !== 'function') return false;
  ROUTES.forEach(route => {
    const previous = registry.get(route);
    if (typeof previous !== 'function' || previous.__financeParityWrapped) return;
    const wrapped = async (screen, context) => {
      const result = await previous(screen, context);
      // The shell's finally block starts an async normalizer without awaiting
      // it. Reapply after each possible completion window so the observed
      // controls cannot overwrite this route-specific shape.
      for (let delay = 0; delay <= 5000; delay += 250) setTimeout(() => patchFinanceControls(route, screen), delay);
      return result;
    };
    wrapped.__financeParityWrapped = true;
    host.registerScreen(route, wrapped);
  });
  return true;
}

import './styles.css';
import { h, clear } from './ui/dom';
import { currentRoute, navigate, onRouteChange } from './ui/router';
import type { Screen } from './ui/screens';
import { getSettings } from './db/db';

// Screens are loaded lazily so a broken screen cannot take the whole app down.
const screens: Record<string, () => Promise<Screen>> = {
  today: () => import('./ui/today').then((m) => m.todayScreen),
  session: () => import('./ui/session').then((m) => m.sessionScreen),
  daily: () => import('./ui/daily').then((m) => m.dailyScreen),
  map: () => import('./ui/map').then((m) => m.mapScreen),
  node: () => import('./ui/node').then((m) => m.nodeScreen),
  progress: () => import('./ui/progress').then((m) => m.progressScreen),
  settings: () => import('./ui/settings').then((m) => m.settingsScreen),
  placement: () => import('./ui/placement').then((m) => m.placementScreen),
};

const NAV: { route: string; label: string; icon: string }[] = [
  { route: 'today', label: 'Today', icon: '◎' },
  { route: 'daily', label: 'Integral', icon: '∫' },
  { route: 'map', label: 'Map', icon: '⋯' },
  { route: 'progress', label: 'Progress', icon: '▲' },
  { route: 'settings', label: 'Settings', icon: '⚙' },
];

let active: Screen | null = null;
let renderSeq = 0;

async function applyTheme() {
  const s = await getSettings();
  document.documentElement.dataset.theme = s.theme;
}

async function route() {
  const seq = ++renderSeq;
  const r = currentRoute();
  const main = document.getElementById('main')!;
  const loader = screens[r.name] ?? screens.today;
  for (const b of document.querySelectorAll<HTMLButtonElement>('nav button')) {
    const isActive = b.dataset.route === r.name || (r.name === 'session' && b.dataset.route === 'today') || (r.name === 'node' && b.dataset.route === 'map');
    b.classList.toggle('active', isActive);
  }
  active?.unmount?.();
  clear(main);
  try {
    const screen = await loader();
    if (seq !== renderSeq) return; // a newer navigation superseded this render
    active = screen;
    clear(main);
    await screen.render(main, r.params);
    main.scrollTop = 0; window.scrollTo(0, 0);
  } catch (err) {
    console.error(err);
    main.appendChild(h('div', { class: 'card error' }, h('h3', null, 'Something went wrong'), h('pre', null, String((err as Error)?.stack ?? err))));
  }
}

function shell() {
  const app = document.getElementById('app')!;
  clear(app);
  app.append(
    h('header', { class: 'topbar' }, h('div', { class: 'brand', onclick: () => navigate('today') }, h('span', { class: 'brand-int' }, '∫'), ' Integrand')),
    h('main', { id: 'main' }),
    h('nav', { class: 'tabbar' }, ...NAV.map((n) => h('button', { 'data-route': n.route, onclick: () => navigate(n.route) }, h('span', { class: 'icon' }, n.icon), h('span', { class: 'label' }, n.label)))),
  );
}

async function boot() {
  shell();
  await applyTheme();
  window.addEventListener('settings-changed', applyTheme);
  onRouteChange(route);
  if (!location.hash) navigate('today'); else await route();
  if ('serviceWorker' in navigator && import.meta.env.PROD) {
    navigator.serviceWorker.register(`${import.meta.env.BASE_URL}sw.js`).catch(() => {});
  }
}

boot();

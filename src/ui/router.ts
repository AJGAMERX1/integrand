// Hash router: #/today, #/daily, #/daily/2026-10-01, #/map, #/node/limits-intro, #/progress, #/settings, #/placement, #/session
export interface Route { name: string; params: string[]; }

export function currentRoute(): Route {
  const hash = location.hash.replace(/^#\/?/, '');
  const [name, ...params] = hash.split('/').filter(Boolean);
  return { name: name || 'today', params: params.map(decodeURIComponent) };
}

export function navigate(path: string) {
  location.hash = path.startsWith('#') ? path : '#/' + path.replace(/^\/+/, '');
}

export function onRouteChange(fn: (r: Route) => void) {
  window.addEventListener('hashchange', () => fn(currentRoute()));
}

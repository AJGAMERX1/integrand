import { h } from './dom';
import type { Screen } from './screens';
export const settingsScreen: Screen = {
  render(c) { c.appendChild(h('div', { class: 'card' }, h('h2', null, 'settings'), h('p', { class: 'muted' }, 'Screen not built yet.'))); },
};

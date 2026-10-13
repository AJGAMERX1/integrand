// Curriculum map: every node grouped by chapter, with mastery, lock state, and Daily Integral tier badges.
import { h, clear } from './dom';
import { navigate } from './router';
import type { Screen } from './screens';
import { curriculum, getNode } from '../data/load';
import { loadSkillStates } from '../db/state';
import { CONFIG } from '../lib/config';
import { today } from '../lib/date';
import { currentIntegralTier, isUnlocked, masteryLabel, unlockedNodes } from '../engine';
import type { CurriculumNode, SkillState } from '../types';

/** ---------- Shared helpers (also used by node.ts and progress.ts) ---------- */

export type NodeStatus = 'locked' | 'available' | 'in progress' | 'mastered' | 'due for review';

/** "2.2 · pp. 83-94" or "App. D · pp. A24-A33"; empty string for nodes without a Stewart ref. */
export function stewartLabel(node: CurriculumNode): string {
  const s = node.stewart;
  if (!s) return '';
  const p = s.pagePrefix ?? '';
  const [a, b] = s.printedPages;
  const pages = a === b ? `p. ${p}${a}` : `pp. ${p}${a}-${p}${b}`;
  return `${s.section} · ${pages}`;
}

/** Mastered per SPEC 4: mastery at/above the node's threshold with the minimum attempts. */
export function isNodeMastered(node: CurriculumNode, state: SkillState | undefined): boolean {
  if (!state) return false;
  const threshold = node.unlockThreshold ?? CONFIG.unlock.defaultThreshold;
  return state.mastery >= threshold && state.attempts >= CONFIG.unlock.minAttempts;
}

export function nodeStatus(node: CurriculumNode, states: Map<string, SkillState>, date: string): NodeStatus {
  const st = states.get(node.id);
  if (!isUnlocked(node.id, states, curriculum)) return 'locked';
  if (st?.dueDate && st.dueDate <= date) return 'due for review';
  if (isNodeMastered(node, st)) return 'mastered';
  if (st && st.attempts > 0) return 'in progress';
  return 'available';
}

export function statusChip(status: NodeStatus): HTMLElement {
  const cls = status === 'mastered' ? 'good' : status === 'due for review' ? 'warn' : status === 'in progress' ? 'accent' : status === 'locked' ? '' : 'accent';
  const text = status === 'locked' ? '🔒 locked' : status;
  return h('span', { class: `chip status-chip ${cls}`.trim() }, text);
}

/** A thin mastery bar with the engine's label beside it. */
export function masteryBar(mastery: number, opts: { label?: boolean; small?: boolean } = {}): HTMLElement {
  const pct = Math.round(Math.max(0, Math.min(1, mastery)) * 100);
  const label = masteryLabel(mastery);
  const bar = h('div', { class: `progressbar mastery-bar mastery-${label} ${opts.small ? 'small' : ''}`.trim(), title: `${pct}%` }, h('div', { style: { width: `${pct}%` } }));
  if (opts.label === false) return bar;
  return h('div', { class: 'mastery-row' }, bar, h('span', { class: 'mastery-label small muted' }, `${label} · ${pct}%`));
}

export function tierBadge(tier: number | null): HTMLElement | null {
  if (tier === null || tier === undefined) return null;
  return h('span', { class: 'chip int tier-badge' }, `∫ tier ${tier}`);
}

export function missingPrereqs(node: CurriculumNode, states: Map<string, SkillState>): CurriculumNode[] {
  return node.prereqs.map((id) => getNode(id)).filter((p): p is CurriculumNode => !!p && !isNodeMastered(p, states.get(p.id)));
}

/** ---------- Map screen ---------- */

type Filter = 'all' | 'ramp' | 'stewart' | 'due';

const FILTERS: { id: Filter; label: string }[] = [
  { id: 'all', label: 'All' }, { id: 'ramp', label: 'Ramp' }, { id: 'stewart', label: 'Stewart' }, { id: 'due', label: 'Due' },
];

let activeFilter: Filter = 'all';

function nodeRow(node: CurriculumNode, states: Map<string, SkillState>, date: string): HTMLElement {
  const st = states.get(node.id);
  const status = nodeStatus(node, states, date);
  const mastery = st?.mastery ?? 0;
  const ref = stewartLabel(node);

  const row = h('div', { class: `listitem maprow ${status === 'locked' ? 'locked' : ''}`.trim(), role: 'button', tabindex: 0 },
    h('div', { class: 'maprow-main' },
      h('div', { class: 'maprow-title' }, node.title),
      ref ? h('div', { class: 'small muted maprow-ref' }, ref) : h('div', { class: 'small muted maprow-ref' }, 'Concept page only'),
      masteryBar(mastery),
    ),
    h('div', { class: 'maprow-side' }, statusChip(status), tierBadge(node.integralTier)),
  );

  const wrap = h('div', { class: 'maprow-wrap' }, row);

  if (status === 'locked') {
    const missing = missingPrereqs(node, states);
    const detail = h('div', { class: 'maprow-detail hidden' },
      h('div', { class: 'small muted' }, missing.length ? 'Needs first:' : 'Prerequisites not yet mastered.'),
      h('div', { class: 'row' }, ...missing.map((p) => {
        const pst = states.get(p.id);
        const chip = h('span', { class: 'chip prereq-chip', role: 'button', tabindex: 0 }, p.title, h('span', { class: 'muted' }, ` · ${masteryLabel(pst?.mastery ?? 0)}`));
        chip.addEventListener('click', (e) => { e.stopPropagation(); navigate(`node/${p.id}`); });
        return chip;
      })),
    );
    wrap.appendChild(detail);
    const toggle = () => detail.classList.toggle('hidden');
    row.addEventListener('click', toggle);
    row.addEventListener('keydown', (e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); toggle(); } });
  } else {
    const go = () => navigate(`node/${node.id}`);
    row.addEventListener('click', go);
    row.addEventListener('keydown', (e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); go(); } });
  }
  return wrap;
}

function headerCard(states: Map<string, SkillState>, date: string): HTMLElement {
  const nodes = curriculum.nodes;
  const unlocked = unlockedNodes(states, curriculum);
  const mastered = nodes.filter((n) => isNodeMastered(n, states.get(n.id))).length;
  const inProgress = nodes.filter((n) => { const s = states.get(n.id); return s && s.attempts > 0 && !isNodeMastered(n, s); }).length;
  const tier = currentIntegralTier(states, curriculum);
  const nextUp = unlocked.find((n) => !isNodeMastered(n, states.get(n.id))) ?? null;
  const due = nodes.filter((n) => nodeStatus(n, states, date) === 'due for review').length;

  return h('div', { class: 'card map-header' },
    h('div', { class: 'bigstat map-stats' },
      h('div', null, h('div', { class: 'n' }, String(mastered)), h('div', { class: 'l' }, 'mastered')),
      h('div', null, h('div', { class: 'n' }, String(inProgress)), h('div', { class: 'l' }, 'in progress')),
      h('div', null, h('div', { class: 'n' }, `${unlocked.length}`, h('span', { class: 'muted small' }, `/${nodes.length}`)), h('div', { class: 'l' }, 'unlocked')),
    ),
    h('div', { class: 'row spread map-meta' },
      h('span', { class: 'chip int' }, `∫ current tier ${tier}`),
      due > 0 ? h('span', { class: 'chip warn' }, `${due} due for review`) : h('span', { class: 'chip' }, 'nothing due'),
    ),
    nextUp
      ? h('div', { class: 'map-next', role: 'button', tabindex: 0, onclick: () => navigate(`node/${nextUp.id}`) },
        h('div', { class: 'small muted' }, 'Next up'),
        h('div', { class: 'map-next-title' }, nextUp.title),
        h('div', { class: 'small muted' }, [nextUp.group, stewartLabel(nextUp)].filter(Boolean).join(' · ')),
      )
      : h('div', { class: 'map-next' }, h('div', { class: 'small muted' }, 'Next up'), h('div', { class: 'map-next-title' }, 'Everything unlocked is mastered. Nice.')),
  );
}

function filterRow(onChange: (f: Filter) => void): HTMLElement {
  const row = h('div', { class: 'segmented map-filter', role: 'tablist' });
  for (const f of FILTERS) {
    const b = h('button', { type: 'button', class: `seg ${activeFilter === f.id ? 'active' : ''}`.trim(), role: 'tab', 'aria-selected': String(activeFilter === f.id) }, f.label);
    b.addEventListener('click', () => {
      activeFilter = f.id;
      for (const x of row.querySelectorAll('button')) { x.classList.toggle('active', x === b); x.setAttribute('aria-selected', String(x === b)); }
      onChange(f.id);
    });
    row.appendChild(b);
  }
  return row;
}

function matchesFilter(node: CurriculumNode, f: Filter, states: Map<string, SkillState>, date: string): boolean {
  if (f === 'all') return true;
  if (f === 'ramp') return node.track === 0;
  if (f === 'stewart') return node.track === 1;
  return nodeStatus(node, states, date) === 'due for review';
}

function groupList(states: Map<string, SkillState>, date: string, f: Filter): HTMLElement {
  const container = h('div', { class: 'map-groups' });
  const groups: { name: string; nodes: CurriculumNode[] }[] = [];
  for (const n of curriculum.nodes) {
    if (!matchesFilter(n, f, states, date)) continue;
    let g = groups[groups.length - 1];
    if (!g || g.name !== n.group) { g = { name: n.group, nodes: [] }; groups.push(g); }
    g.nodes.push(n);
  }
  if (groups.length === 0) {
    container.appendChild(h('div', { class: 'card' }, h('p', { class: 'muted' }, f === 'due' ? 'Nothing is due for review today.' : 'No nodes match this filter.')));
    return container;
  }
  for (const g of groups) {
    const masteredCount = g.nodes.filter((n) => isNodeMastered(n, states.get(n.id))).length;
    const unlockedCount = g.nodes.filter((n) => isUnlocked(n.id, states, curriculum)).length;
    container.appendChild(h('section', { class: 'map-group' },
      h('div', { class: 'row spread map-group-head' },
        h('h3', { class: 'map-group-title' }, g.name),
        h('span', { class: 'small muted' }, `${masteredCount}/${g.nodes.length} mastered · ${unlockedCount} unlocked`),
      ),
      h('div', { class: 'list' }, ...g.nodes.map((n) => nodeRow(n, states, date))),
    ));
  }
  return container;
}

export const mapScreen: Screen = {
  async render(container) {
    const states = await loadSkillStates();
    const date = today();
    container.appendChild(h('h1', null, 'Map'));
    container.appendChild(headerCard(states, date));
    const listHost = h('div');
    container.appendChild(filterRow((f) => { clear(listHost); listHost.appendChild(groupList(states, date, f)); }));
    container.appendChild(listHost);
    listHost.appendChild(groupList(states, date, activeFilter));
  },
};

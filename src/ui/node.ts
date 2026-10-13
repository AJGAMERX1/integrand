// Node detail page (#/node/<id>): header with mastery and prerequisites, then Explain / Practice / History tabs.
import { h, append, clear, toast } from './dom';
import { navigate } from './router';
import type { Screen } from './screens';
import { renderConcept } from './concept';
import { renderProblem } from './problemCard';
import { isNodeMastered, masteryBar, missingPrereqs, nodeStatus, statusChip, stewartLabel, tierBadge } from './map';
import { conceptFor, curriculum, getNode, problemsFor } from '../data/load';
import { loadAttempts, loadSkillStates, saveSkillState, seenProblemIds } from '../db/state';
import { prettyDate, today } from '../lib/date';
import { applyAttempt, initialSkillState, isUnlocked, masteryLabel, pickProblems } from '../engine';
import type { AttemptRecord, CurriculumNode, SkillState } from '../types';

type Tab = 'explain' | 'practice' | 'history';

let currentDestroy: (() => void) | null = null;

function prereqChip(p: CurriculumNode, states: Map<string, SkillState>): HTMLElement {
  const st = states.get(p.id);
  const mastered = isNodeMastered(p, st);
  const chip = h('a', { class: `chip prereq-chip ${mastered ? 'good' : ''}`.trim(), href: `#/node/${p.id}` },
    p.title, h('span', { class: 'muted' }, ` · ${masteryLabel(st?.mastery ?? 0)}`));
  return chip;
}

function header(node: CurriculumNode, states: Map<string, SkillState>, date: string): HTMLElement {
  const st = states.get(node.id);
  const status = nodeStatus(node, states, date);
  const prereqs = node.prereqs.map((id) => getNode(id)).filter((n): n is CurriculumNode => !!n);
  const unlocks = curriculum.nodes.filter((n) => n.prereqs.includes(node.id));
  const ref = stewartLabel(node);
  const missing = missingPrereqs(node, states);

  const facts = h('div', { class: 'node-facts small muted' },
    h('span', null, `${st?.attempts ?? 0} attempt${(st?.attempts ?? 0) === 1 ? '' : 's'}`),
    st?.lastPracticed ? h('span', null, `last ${prettyDate(st.lastPracticed)}`) : null,
    st?.dueDate ? h('span', { class: st.dueDate <= date ? 'warn-text' : '' }, st.dueDate <= date ? `review due (${prettyDate(st.dueDate)})` : `next review ${prettyDate(st.dueDate)}`) : null,
    st ? h('span', null, `difficulty ${st.difficulty}`) : null,
  );

  return h('div', { class: 'card node-header' },
    h('div', { class: 'small muted' }, node.group),
    h('h1', { class: 'node-title' }, node.title),
    h('div', { class: 'row node-chips' },
      ref ? h('span', { class: 'chip' }, ref) : h('span', { class: 'chip' }, 'Concept page only'),
      statusChip(status),
      tierBadge(node.integralTier),
    ),
    h('p', { class: 'node-summary' }, node.summary),
    masteryBar(st?.mastery ?? 0),
    facts,
    status === 'locked'
      ? h('div', { class: 'node-locked-note small' }, `Locked. Master ${missing.length ? missing.map((m) => m.title).join(', ') : 'the prerequisites'} first (${Math.round((node.unlockThreshold ?? 0.7) * 100)}% mastery with at least 5 attempts). You can still read the explanation.`)
      : null,
    prereqs.length
      ? h('div', { class: 'node-rel' }, h('div', { class: 'small muted' }, 'Prerequisites'), h('div', { class: 'row' }, ...prereqs.map((p) => prereqChip(p, states))))
      : h('div', { class: 'node-rel small muted' }, 'No prerequisites: a starting point.'),
    unlocks.length
      ? h('div', { class: 'node-rel' }, h('div', { class: 'small muted' }, 'Unlocks'), h('div', { class: 'row' }, ...unlocks.map((u) => h('a', { class: `chip ${isUnlocked(u.id, states, curriculum) ? 'accent' : ''}`.trim(), href: `#/node/${u.id}` }, u.title))))
      : null,
  );
}

function tabs(active: Tab, onChange: (t: Tab) => void): HTMLElement {
  const items: { id: Tab; label: string }[] = [{ id: 'explain', label: 'Explain' }, { id: 'practice', label: 'Practice' }, { id: 'history', label: 'History' }];
  const row = h('div', { class: 'segmented node-tabs', role: 'tablist' });
  for (const t of items) {
    const b = h('button', { type: 'button', class: `seg ${active === t.id ? 'active' : ''}`.trim(), role: 'tab', 'aria-selected': String(active === t.id) }, t.label);
    b.addEventListener('click', () => {
      for (const x of row.querySelectorAll('button')) { x.classList.toggle('active', x === b); x.setAttribute('aria-selected', String(x === b)); }
      onChange(t.id);
    });
    row.appendChild(b);
  }
  return row;
}

/** ---------- Explain ---------- */

function explainTab(node: CurriculumNode): HTMLElement {
  const host = h('div', { class: 'card node-explain' });
  const concept = conceptFor(node.id);
  if (!concept) {
    append(host, [
      h('h3', null, 'Explanation coming soon'),
      h('p', { class: 'muted' }, `There is no written explanation for ${node.title} yet.`),
      node.stewart ? h('p', null, `Read ${stewartLabel(node)} in the book; the summary above tells you what to look for.`) : null,
    ]);
    return host;
  }
  renderConcept(host, concept);
  return host;
}

/** ---------- Practice ---------- */

function practiceTab(node: CurriculumNode, states: Map<string, SkillState>, seen: Set<string>): HTMLElement {
  const host = h('div', { class: 'card node-practice' });
  const bank = problemsFor(node.id);
  if (bank.length === 0) {
    host.append(h('h3', null, 'No problems yet'), h('p', { class: 'muted' }, `The problem bank for ${node.title} has not been generated yet. Check back after the next update.`));
    return host;
  }
  if (!isUnlocked(node.id, states, curriculum)) {
    host.append(
      h('h3', null, 'Locked'),
      h('p', { class: 'muted' }, 'Practice opens once the prerequisites are mastered. Until then, read the explanation and work on the prerequisites.'),
      h('div', { class: 'row' }, ...missingPrereqs(node, states).map((p) => h('a', { class: 'chip', href: `#/node/${p.id}` }, p.title))),
    );
    return host;
  }

  let state: SkillState = states.get(node.id) ?? initialSkillState(node.id);
  let correct = 0, total = 0;
  const localSeen = new Set(seen);
  const rng = () => Math.random();

  const score = h('div', { class: 'row spread practice-score' },
    h('span', { class: 'small muted' }, 'Free practice counts toward mastery.'),
    h('span', { class: 'chip' }, '0 / 0'),
  );
  const scoreChip = score.lastElementChild as HTMLElement;
  const masteryHost = h('div', { class: 'practice-mastery' }, masteryBar(state.mastery));
  const problemHost = h('div', { class: 'practice-problem' });
  host.append(score, masteryHost, problemHost);

  let card: { destroy(): void } | null = null;

  const showProblem = () => {
    card?.destroy();
    card = null;
    clear(problemHost);
    const [problem] = pickProblems(bank, state, localSeen, 1, rng);
    if (!problem) { problemHost.appendChild(h('p', { class: 'muted' }, 'No more problems available right now.')); return; }
    localSeen.add(problem.id);
    // The card records the AttemptRecord itself (context 'practice'); we own the skill-state update.
    card = renderProblem(problemHost, problem, {
      context: 'practice',
      heading: `Practice · ${node.title}`,
      explainLink: false,
      continueLabel: 'Next problem',
      onContinue: showProblem,
      onDone: (r) => {
        total += 1; if (r.correct && !r.revealed) correct += 1;
        scoreChip.textContent = `${correct} / ${total}`;
        state = applyAttempt(state, { correct: r.correct, hintsUsed: r.hintsUsed, revealed: r.revealed }, today());
        states.set(node.id, state);
        clear(masteryHost); masteryHost.appendChild(masteryBar(state.mastery));
        saveSkillState(state).catch((err) => { console.error(err); toast('Could not save your progress.'); });
      },
    });
  };
  currentDestroy = () => { card?.destroy(); card = null; };
  showProblem();
  return host;
}

/** ---------- History ---------- */

function historyTab(node: CurriculumNode, attempts: AttemptRecord[]): HTMLElement {
  const host = h('div', { class: 'card node-history' });
  const mine = attempts.filter((a) => a.nodeId === node.id).sort((a, b) => b.timestamp - a.timestamp).slice(0, 20);
  if (mine.length === 0) {
    host.append(h('h3', null, 'No attempts yet'), h('p', { class: 'muted' }, 'Problems you work on this node will show up here.'));
    return host;
  }
  const all = attempts.filter((a) => a.nodeId === node.id);
  const c = all.filter((a) => a.correct && !a.revealed).length;
  host.append(
    h('div', { class: 'row spread' }, h('h3', null, 'Recent attempts'), h('span', { class: 'small muted' }, `${c}/${all.length} correct all-time`)),
    h('div', { class: 'list history-list' }, ...mine.map((a) => {
      const miss = !a.correct || a.revealed;
      const time = new Date(a.timestamp).toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' });
      return h('div', { class: 'history-row' },
        h('span', { class: `history-mark ${miss ? 'bad' : 'good'}` }, miss ? '✕' : '✓'),
        h('div', { class: 'history-main' },
          h('div', null, `${prettyDate(a.date)} · ${time}`),
          h('div', { class: 'small muted' }, [
            a.revealed ? 'revealed' : a.correct ? 'correct' : 'miss',
            a.hintsUsed > 0 ? `${a.hintsUsed} hint${a.hintsUsed === 1 ? '' : 's'}` : 'no hints',
            a.context,
          ].join(' · ')),
        ),
      );
    })),
  );
  return host;
}

/** ---------- Screen ---------- */

export const nodeScreen: Screen = {
  async render(container, params) {
    const id = params[0] ?? '';
    const node = getNode(id);
    if (!node) {
      container.appendChild(h('div', { class: 'card' },
        h('h2', null, 'Unknown node'),
        h('p', { class: 'muted' }, `There is no node called "${id}" in the curriculum.`),
        h('a', { class: 'btn ghost', href: '#/map' }, 'Back to the map'),
      ));
      return;
    }
    const [states, attempts, seen] = await Promise.all([loadSkillStates(), loadAttempts(), seenProblemIds()]);
    const date = today();

    container.appendChild(h('a', { class: 'backlink small', href: '#/map' }, '← Map'));
    container.appendChild(header(node, states, date));

    const body = h('div', { class: 'node-body' });
    const initial: Tab = isUnlocked(node.id, states, curriculum) && (states.get(node.id)?.attempts ?? 0) > 0 ? 'practice' : 'explain';
    const show = (t: Tab) => {
      currentDestroy?.(); currentDestroy = null;
      clear(body);
      if (t === 'explain') body.appendChild(explainTab(node));
      else if (t === 'practice') body.appendChild(practiceTab(node, states, seen));
      else body.appendChild(historyTab(node, attempts));
    };
    container.appendChild(tabs(initial, show));
    container.appendChild(body);
    show(initial);
  },
  unmount() { currentDestroy?.(); currentDestroy = null; },
};

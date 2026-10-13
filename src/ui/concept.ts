// Concept explanation component: renders a data/concepts/<node-id>.json entry for reading on a phone.
// Used by the node page ("Explain" tab) and available to the session flow after a miss.
import { h, clear } from './dom';
import { richText } from './math';
import type { Concept, WorkedExample } from '../types';

export interface ConceptOptions {
  /** Compact: shorter headings, examples and reading guide collapsed, no "why it matters" paragraph. */
  compact?: boolean;
}

function section(title: string, ...body: (Node | null | false | undefined)[]): HTMLElement {
  return h('section', { class: 'concept-section' }, h('h3', { class: 'concept-h' }, title), ...body);
}

function bulletList(items: string[], cls = ''): HTMLElement {
  return h('ul', { class: `concept-list ${cls}`.trim() }, ...items.map((t) => h('li', null, richText(t))));
}

function workedExample(ex: WorkedExample, index: number, open: boolean): HTMLElement {
  const steps = h('ol', { class: 'concept-steps' }, ...ex.steps.map((s) => h('li', null, richText(s))));
  return h('details', { class: 'concept-example', open: open || undefined },
    h('summary', null, h('span', { class: 'concept-example-n' }, `Example ${index + 1}`), h('span', { class: 'concept-example-t' }, ex.title)),
    h('div', { class: 'concept-example-body' },
      h('div', { class: 'concept-problem' }, richText(ex.problem)),
      steps,
    ),
  );
}

function checkYourself(items: { q: string; a: string }[]): HTMLElement {
  return h('div', { class: 'concept-checks' }, ...items.map((item, i) => {
    const answer = h('div', { class: 'concept-answer hidden' }, h('span', { class: 'muted small' }, 'Answer'), richText(item.a));
    const btn = h('button', { class: 'btn ghost small', type: 'button' }, 'Show answer');
    btn.addEventListener('click', () => {
      const show = answer.classList.toggle('hidden');
      btn.textContent = show ? 'Show answer' : 'Hide answer';
    });
    return h('div', { class: 'concept-check' },
      h('div', { class: 'concept-check-q' }, h('span', { class: 'concept-check-n' }, `${i + 1}.`), richText(item.q)),
      btn,
      answer,
    );
  }));
}

/** Render a concept into `container` (clears it first). Returns the root element. */
export function renderConcept(container: HTMLElement, concept: Concept, opts: ConceptOptions = {}): HTMLElement {
  const compact = !!opts.compact;
  clear(container);
  const root = h('article', { class: `concept ${compact ? 'concept-compact' : ''}`.trim() });

  root.appendChild(h('div', { class: 'concept-overview' }, richText(concept.overview)));

  if (concept.keyIdeas?.length) {
    root.appendChild(section('Key ideas', bulletList(concept.keyIdeas, 'concept-ideas')));
  }

  if (concept.workedExamples?.length) {
    const examples = concept.workedExamples.map((ex, i) => workedExample(ex, i, !compact && i === 0));
    root.appendChild(section('Worked examples', h('div', { class: 'stack' }, ...examples)));
  }

  if (concept.commonMistakes?.length) {
    root.appendChild(section('Common mistakes', bulletList(concept.commonMistakes, 'concept-mistakes')));
  }

  if (!compact && concept.whyItMatters) {
    root.appendChild(section('Why it matters', h('div', { class: 'concept-why' }, richText(concept.whyItMatters))));
  }

  if (concept.checkYourself?.length) {
    root.appendChild(section('Check yourself', checkYourself(concept.checkYourself)));
  }

  if (concept.readingGuide?.length) {
    const guide = bulletList(concept.readingGuide, 'concept-guide');
    if (compact) {
      root.appendChild(h('details', { class: 'guide concept-guide-details' }, h('summary', null, 'Reading guide'), guide));
    } else {
      root.appendChild(section('Reading guide', h('p', { class: 'muted small' }, 'What to look for while reading the book pages.'), guide));
    }
  }

  container.appendChild(root);
  return root;
}

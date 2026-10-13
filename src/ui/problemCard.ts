// Reusable problem component: statement, math/choice input, Check, hint ladder (Hint 1, Hint 2, Reveal),
// worked solution, "Explain this concept" link and an optional Continue button.
// Used by the session, Daily Integral, placement and the node practice tab.
import type { AttemptContext, Problem } from '../types';
import { h, clear } from './dom';
import { tex, richText, mathInput, statement as renderStatement, type MathInput } from './math';
import { grade, type GradeResult } from '../grader';
import { recordAttempt } from '../db/state';

export interface ProblemResult {
  /** Answered correctly (never true when revealed). */
  correct: boolean;
  hintsUsed: number;
  /** The solution was shown without a correct answer (explicit reveal, attempts exhausted, or gave up with reveal). */
  revealed: boolean;
  /** Last submitted answer (LaTeX, or the chosen index for choice problems). */
  answer: string;
  attempts: number;
  /** The learner pressed the give-up button (e.g. "I don't know"). */
  gaveUp: boolean;
}

export interface ProblemCardOptions {
  context: AttemptContext;
  /** Fires once, as soon as the problem resolves (correct, attempts exhausted, revealed or gave up). */
  onDone(result: ProblemResult): void;
  /** When given, a Continue button is shown after the problem resolves and this fires when it is tapped. */
  onContinue?(result: ProblemResult): void;
  /** Default 3. */
  maxAttempts?: number;
  /** Show the Reveal step of the hint ladder (default true). */
  allowReveal?: boolean;
  /** Show hints at all (default true). */
  allowHints?: boolean;
  /** Show the worked solution after the problem resolves (default true). */
  showSolution?: boolean;
  /** Record an AttemptRecord via recordAttempt() when the problem resolves (default true). */
  record?: boolean;
  /** Show the "Explain this concept" link to #/node/<skill> (default true). */
  explainLink?: boolean;
  continueLabel?: string;
  /** When set, shows a button with this label that resolves the problem as a miss (used by placement: "I don't know"). */
  giveUpLabel?: string;
  /** Small label above the statement, e.g. "Review · Limits". */
  heading?: string;
}

export interface ProblemCardHandle {
  el: HTMLElement;
  /** True once the problem has resolved. */
  readonly done: boolean;
  destroy(): void;
}

const ATTEMPT_WORD = (n: number) => (n === 1 ? '1 attempt' : `${n} attempts`);

export function renderProblem(container: HTMLElement, problem: Problem, opts: ProblemCardOptions): ProblemCardHandle {
  const maxAttempts = Math.max(1, opts.maxAttempts ?? 3);
  const allowReveal = opts.allowReveal ?? true;
  const allowHints = opts.allowHints ?? true;
  const showSolution = opts.showSolution ?? true;
  const record = opts.record ?? true;
  const hints = allowHints ? (problem.hints ?? []) : [];
  const isChoice = problem.checker === 'choice';

  let attempts = 0;
  let hintsUsed = 0;
  let finished = false;
  let lastAnswer = '';
  let choiceIdx: number | null = null;
  let input: MathInput | null = null;
  const choiceButtons: HTMLButtonElement[] = [];

  const card = h('div', { class: 'card problem' });
  const head = h('div', { class: 'row spread problem-head' });
  const attemptsChip = h('span', { class: 'chip small' });
  if (opts.heading) head.appendChild(h('span', { class: 'small muted' }, opts.heading));
  head.appendChild(attemptsChip);

  const statement = h('div', { class: 'problem-statement' }, renderStatement(problem.statement));
  const inputArea = h('div', { class: 'problem-input' });
  const feedback = h('div', { class: 'problem-feedback hidden' });
  const hintsArea = h('div', { class: 'problem-hints' });
  const actions = h('div', { class: 'problem-actions' });
  const resultArea = h('div', { class: 'problem-result hidden' });

  // ----- input -----
  if (isChoice) {
    const choices = problem.choices ?? [];
    if (choices.length === 0) {
      inputArea.appendChild(h('p', { class: 'muted small' }, 'This problem has no answer choices.'));
    }
    choices.forEach((c, i) => {
      const b = h('button', {
        type: 'button', class: 'choice',
        onclick: () => {
          if (finished) return;
          choiceIdx = i;
          for (const cb of choiceButtons) cb.classList.toggle('selected', cb === b);
        },
      }, h('span', { class: 'choice-letter' }, String.fromCharCode(65 + i)), tex(c));
      choiceButtons.push(b);
      inputArea.appendChild(b);
    });
  } else {
    input = mathInput('Your answer');
    input.onEnter(() => check());
    inputArea.appendChild(input.el);
    if (problem.checker === 'equiv_plus_c') inputArea.appendChild(h('p', { class: 'small muted input-note' }, 'Antiderivative: + C is optional.'));
    if (problem.checker === 'interval') inputArea.appendChild(h('p', { class: 'small muted input-note' }, 'Write an interval like (-∞, 3] or [0, 2).'));
  }

  // ----- actions -----
  const checkBtn = h('button', { type: 'button', class: 'btn block', onclick: () => check() }, 'Check');
  const hintBtn = h('button', { type: 'button', class: 'btn ghost', onclick: () => ladder() }, 'Hint 1');
  const giveUpBtn = opts.giveUpLabel
    ? h('button', { type: 'button', class: 'btn ghost', onclick: () => giveUp() }, opts.giveUpLabel)
    : null;
  actions.append(checkBtn, h('div', { class: 'row problem-secondary' }, hintBtn, giveUpBtn));

  card.append(head, statement, inputArea, feedback, hintsArea, actions, resultArea);
  container.appendChild(card);
  updateChips();
  updateLadder();

  function updateChips() {
    const left = maxAttempts - attempts;
    attemptsChip.textContent = finished ? (attempts === 0 ? '' : `${attempts} ${attempts === 1 ? 'attempt' : 'attempts'}`) : `${ATTEMPT_WORD(left)} left`;
    attemptsChip.classList.toggle('hidden', finished && attempts === 0);
  }

  /** Decide what the ladder button says next: Hint n, Reveal, or hidden. */
  function updateLadder() {
    if (finished) { hintBtn.classList.add('hidden'); return; }
    if (hintsUsed < hints.length) { hintBtn.textContent = `Hint ${hintsUsed + 1}`; hintBtn.classList.remove('hidden'); return; }
    if (allowReveal) { hintBtn.textContent = 'Reveal solution'; hintBtn.classList.remove('hidden'); return; }
    hintBtn.classList.add('hidden');
  }

  function setFeedback(msg: string, tone: 'bad' | 'muted' | 'good') {
    feedback.className = `problem-feedback ${tone}`;
    feedback.textContent = msg;
  }

  function ladder() {
    if (finished) return;
    if (hintsUsed < hints.length) {
      const text = hints[hintsUsed];
      hintsUsed++;
      hintsArea.appendChild(h('div', { class: 'hint' }, h('div', { class: 'hint-label' }, `Hint ${hintsUsed}`), richText(text)));
      updateLadder();
      return;
    }
    if (allowReveal) finish(false, true, false);
  }

  function giveUp() {
    if (finished) return;
    finish(false, allowReveal && showSolution, true);
  }

  function currentAnswer(): string {
    if (isChoice) return choiceIdx === null ? '' : String(choiceIdx);
    return (input?.latex() ?? '').trim();
  }

  function check() {
    if (finished) return;
    const answer = currentAnswer();
    if (!answer) { setFeedback(isChoice ? 'Pick an answer first.' : 'Enter an answer first.', 'muted'); return; }
    let res: GradeResult;
    try {
      res = grade(problem, answer);
    } catch (err) {
      console.error(err);
      setFeedback('Could not check that answer. Try writing it differently.', 'muted');
      return;
    }
    attempts++;
    lastAnswer = answer;
    if (res.correct) { finish(true, false, false); return; }
    const left = maxAttempts - attempts;
    const reason = res.reason ? res.reason.trim().replace(/\.?$/, '.') : 'That is not equivalent to the answer.';
    if (left <= 0) {
      setFeedback(`Not quite. ${reason}`, 'bad');
      finish(false, true, false);
    } else {
      setFeedback(`Not quite. ${reason} ${ATTEMPT_WORD(left)} left.`, 'bad');
      updateChips();
      if (input) input.focus();
    }
  }

  function finish(correct: boolean, revealed: boolean, gaveUp: boolean) {
    if (finished) return;
    finished = true;
    if (gaveUp) attempts = Math.max(attempts, maxAttempts);
    const result: ProblemResult = { correct, hintsUsed, revealed: !correct && revealed, answer: lastAnswer, attempts, gaveUp };

    // Lock the input.
    if (input) { input.el.readOnly = true; }
    for (const b of choiceButtons) b.disabled = true;
    if (isChoice) {
      const key = Number(problem.answer);
      choiceButtons.forEach((b, i) => {
        if (i === key && (correct || showSolution || revealed)) b.classList.add('correct');
        if (i === choiceIdx && !correct) b.classList.add('wrong');
      });
    }
    actions.classList.add('hidden');
    updateChips();
    updateLadder();

    // Result banner.
    let banner: string;
    let tone: 'good' | 'bad' | 'warn';
    if (correct) {
      banner = attempts === 1 && hintsUsed === 0 ? 'Correct, first try.' : hintsUsed > 0 ? 'Correct (with a hint).' : 'Correct.';
      tone = 'good';
      feedback.classList.add('hidden');
    } else if (gaveUp) {
      banner = revealed ? 'No problem. Here is how it goes.' : 'Marked as not known.';
      tone = 'warn';
    } else if (revealed && attempts === 0) {
      banner = 'Solution revealed.';
      tone = 'warn';
    } else {
      banner = 'Out of attempts. Here is the solution.';
      tone = 'bad';
    }
    resultArea.classList.remove('hidden');
    resultArea.appendChild(h('div', { class: `result-banner ${tone}` }, banner));

    if (showSolution && (revealed || correct)) resultArea.appendChild(solutionBlock(problem));

    const footer = h('div', { class: 'problem-footer' });
    if (opts.explainLink ?? true) {
      footer.appendChild(h('a', { class: 'btn ghost small', href: `#/node/${encodeURIComponent(problem.skill)}` }, 'Explain this concept'));
    }
    if (opts.onContinue) {
      footer.appendChild(h('button', {
        type: 'button', class: 'btn block',
        onclick: (e: Event) => { (e.currentTarget as HTMLButtonElement).disabled = true; opts.onContinue?.(result); },
      }, opts.continueLabel ?? 'Continue'));
    }
    resultArea.appendChild(footer);

    if (record) {
      recordAttempt({
        problemId: problem.id, nodeId: problem.skill, answer: lastAnswer,
        correct, hintsUsed, revealed: result.revealed, context: opts.context,
      }).catch((err) => console.error('recordAttempt failed', err));
    }
    try { opts.onDone(result); } catch (err) { console.error(err); }
    resultArea.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  }

  return {
    el: card,
    get done() { return finished; },
    destroy() {
      try { input?.el.blur(); } catch { /* ignore */ }
      clear(card);
      card.remove();
    },
  };
}

/** Worked solution block: numbered steps rendered with richText. Falls back to showing the answer key. */
export function solutionBlock(problem: Problem): HTMLElement {
  const wrap = h('div', { class: 'solution' }, h('h3', null, 'Worked solution'));
  const steps = problem.solution ?? [];
  if (steps.length > 0) {
    wrap.appendChild(h('ol', { class: 'solution-steps' }, ...steps.map((s) => h('li', null, richText(s)))));
  }
  if (problem.checker === 'choice') {
    const key = Number(problem.answer);
    const c = problem.choices?.[key];
    if (c !== undefined) wrap.appendChild(h('p', { class: 'answer-line' }, 'Answer: ', h('strong', null, String.fromCharCode(65 + key)), ' ', tex(c)));
  } else if (steps.length === 0) {
    wrap.appendChild(h('p', { class: 'answer-line' }, 'Answer: ', h('code', { class: 'mono' }, problem.answer)));
  }
  return wrap;
}

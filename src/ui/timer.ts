// Timers. flowTimer(): Flowmodoro (tap to focus, counts up; tap to end, break = elapsed / ratio counts down).
// blockTimer(): simple countdown for a session block. Both persist their running state in localStorage so that
// switching apps or reloading does not lose the clock.
import { h, clear, toast } from './dom';

const FLOW_KEY = 'integrand.flow';

type FlowPhase = 'idle' | 'focus' | 'break';
interface FlowState { phase: 'focus' | 'break'; startedAt: number; breakMs?: number }

function readJSON<T>(key: string): T | null {
  try { const raw = localStorage.getItem(key); return raw ? (JSON.parse(raw) as T) : null; } catch { return null; }
}
function writeJSON(key: string, value: unknown) { try { localStorage.setItem(key, JSON.stringify(value)); } catch { /* ignore */ } }
function remove(key: string) { try { localStorage.removeItem(key); } catch { /* ignore */ } }

export function fmtClock(totalSec: number): string {
  const s = Math.max(0, Math.floor(totalSec));
  const hh = Math.floor(s / 3600), mm = Math.floor((s % 3600) / 60), ss = s % 60;
  return hh > 0 ? `${hh}:${String(mm).padStart(2, '0')}:${String(ss).padStart(2, '0')}` : `${String(mm).padStart(2, '0')}:${String(ss).padStart(2, '0')}`;
}

export interface FlowTimerOptions {
  /** focus minutes / breakRatio = break minutes (settings.flowBreakRatio, default 5). */
  breakRatio: number;
  /** Called when a focus period ends, with whole minutes (rounded) and exact seconds. Callers log study time. */
  onFocusEnd(minutes: number, seconds: number): void;
  title?: string;
  /** Shown under the clock while idle, e.g. "Logs to: Limits". */
  note?: string;
}

export interface FlowTimerHandle { el: HTMLElement; phase(): FlowPhase; destroy(): void }

/** Renders a Flowmodoro card into container. State survives reloads via localStorage. */
export function flowTimer(container: HTMLElement, opts: FlowTimerOptions): FlowTimerHandle {
  const ratio = Math.max(1, opts.breakRatio || 5);
  let state: FlowState | null = readJSON<FlowState>(FLOW_KEY);
  if (state && (state.phase !== 'focus' && state.phase !== 'break')) state = null;

  const card = h('div', { class: 'card flow' });
  const label = h('div', { class: 'flow-phase muted small' });
  const clock = h('div', { class: 'timer-big' }, '00:00');
  const mainBtn = h('button', { type: 'button', class: 'btn block', onclick: () => onMain() });
  const skipBtn = h('button', { type: 'button', class: 'btn ghost small hidden', onclick: () => endBreak(true) }, 'Skip break');
  const note = h('div', { class: 'small muted flow-note' }, opts.note ?? '');
  card.append(
    h('div', { class: 'row spread' }, h('h3', null, opts.title ?? 'Focus timer'), label),
    clock, mainBtn, h('div', { class: 'row flow-row' }, skipBtn), note,
  );
  container.appendChild(card);

  function phase(): FlowPhase { return state?.phase ?? 'idle'; }

  function render() {
    const now = Date.now();
    const p = phase();
    if (p === 'idle') {
      label.textContent = 'Ready';
      clock.textContent = '00:00';
      clock.classList.remove('focus', 'break');
      mainBtn.textContent = 'Start focus';
      mainBtn.className = 'btn block';
      skipBtn.classList.add('hidden');
      note.textContent = opts.note ?? 'Tap to start. Tap again when you stop; the break is a fifth of your focus time.';
    } else if (p === 'focus' && state) {
      const sec = (now - state.startedAt) / 1000;
      label.textContent = 'Focusing';
      clock.textContent = fmtClock(sec);
      clock.classList.add('focus'); clock.classList.remove('break');
      mainBtn.textContent = 'End focus';
      mainBtn.className = 'btn block good';
      skipBtn.classList.add('hidden');
      note.textContent = `Break will be ${fmtClock(sec / ratio)}`;
    } else if (p === 'break' && state) {
      const remainingMs = (state.breakMs ?? 0) - (now - state.startedAt);
      if (remainingMs <= 0) { endBreak(false); return; }
      label.textContent = 'Break';
      clock.textContent = fmtClock(remainingMs / 1000);
      clock.classList.add('break'); clock.classList.remove('focus');
      mainBtn.textContent = 'Start focus';
      mainBtn.className = 'btn block';
      skipBtn.classList.remove('hidden');
      note.textContent = 'Step away. Focus starts again when you tap.';
    }
  }

  function onMain() {
    const p = phase();
    if (p === 'focus') { endFocus(); return; }
    // idle or break -> start focus (starting during a break just ends the break)
    state = { phase: 'focus', startedAt: Date.now() };
    writeJSON(FLOW_KEY, state);
    render();
  }

  function endFocus() {
    if (!state || state.phase !== 'focus') return;
    const seconds = (Date.now() - state.startedAt) / 1000;
    const minutes = Math.round(seconds / 60);
    try { opts.onFocusEnd(minutes, seconds); } catch (err) { console.error(err); }
    const breakMs = Math.round((seconds / ratio) * 1000);
    if (seconds >= 60) {
      state = { phase: 'break', startedAt: Date.now(), breakMs };
      writeJSON(FLOW_KEY, state);
    } else {
      state = null; remove(FLOW_KEY);
    }
    render();
  }

  function endBreak(skipped: boolean) {
    state = null; remove(FLOW_KEY);
    if (!skipped) toast('Break over. Ready when you are.');
    render();
  }

  render();
  const iv = window.setInterval(render, 500);
  const onVis = () => render();
  document.addEventListener('visibilitychange', onVis);

  return {
    el: card,
    phase,
    destroy() {
      window.clearInterval(iv);
      document.removeEventListener('visibilitychange', onVis);
      clear(card); card.remove();
    },
  };
}

/** ---------- Block countdown timer ---------- */

export interface BlockTimer {
  el: HTMLElement;
  start(): void;
  stop(): void;
  running(): boolean;
  elapsedSeconds(): number;
  /** Whole minutes spent, rounded; at least 1 once 30 s have passed. */
  elapsedMinutes(): number;
  remainingSeconds(): number;
  /** Stops the clock and removes it from the DOM and localStorage. */
  destroy(): void;
}

export interface BlockTimerOptions {
  /** When set, the start time is persisted under this key so a reload resumes the same clock. */
  persistKey?: string;
  /** Start immediately (default true). */
  autoStart?: boolean;
}

/**
 * Countdown from `minutes` to zero. Calls onTick(remainingSec, elapsedSec) every second and onEnd() once when it hits zero;
 * afterwards it keeps counting overtime ("+01:12") so the caller can still log real minutes.
 */
export function blockTimer(minutes: number, onTick: (remainingSec: number, elapsedSec: number) => void, onEnd: () => void, opts: BlockTimerOptions = {}): BlockTimer {
  const totalSec = Math.max(0, Math.round(minutes * 60));
  const el = h('div', { class: 'blocktimer mono' }, fmtClock(totalSec));
  let startedAt: number | null = null;
  let iv: number | null = null;
  let ended = false;

  if (opts.persistKey) {
    const saved = readJSON<{ startedAt: number }>(opts.persistKey);
    if (saved && typeof saved.startedAt === 'number' && saved.startedAt <= Date.now()) startedAt = saved.startedAt;
  }

  function elapsedSeconds() { return startedAt === null ? 0 : (Date.now() - startedAt) / 1000; }
  function remainingSeconds() { return totalSec - elapsedSeconds(); }

  function tick() {
    const elapsed = elapsedSeconds();
    const remaining = totalSec - elapsed;
    if (remaining >= 0) {
      el.textContent = fmtClock(remaining);
      el.classList.remove('over');
    } else {
      el.textContent = `+${fmtClock(-remaining)}`;
      el.classList.add('over');
      if (!ended) { ended = true; try { onEnd(); } catch (err) { console.error(err); } }
    }
    try { onTick(Math.max(0, remaining), elapsed); } catch (err) { console.error(err); }
  }

  function start() {
    if (iv !== null) return;
    if (startedAt === null) {
      startedAt = Date.now();
      if (opts.persistKey) writeJSON(opts.persistKey, { startedAt });
    }
    tick();
    iv = window.setInterval(tick, 1000);
  }
  function stop() { if (iv !== null) { window.clearInterval(iv); iv = null; } }

  if (opts.autoStart ?? true) start();

  return {
    el, start, stop,
    running: () => iv !== null,
    elapsedSeconds,
    elapsedMinutes: () => { const s = elapsedSeconds(); return s >= 30 ? Math.max(1, Math.round(s / 60)) : 0; },
    remainingSeconds,
    destroy() { stop(); if (opts.persistKey) remove(opts.persistKey); el.remove(); },
  };
}

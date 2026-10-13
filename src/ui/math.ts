// KaTeX rendering + MathLive input wrapper. Import this instead of touching katex/mathlive directly.
import katex from 'katex';
import 'katex/dist/katex.min.css';
import { MathfieldElement } from 'mathlive';
import { h } from './dom';

/** Render a LaTeX string into an element (display or inline). Never throws; falls back to plain text. */
export function tex(latex: string, display = false): HTMLElement {
  const el = h('span', { class: display ? 'tex tex-display' : 'tex' });
  try { katex.render(latex, el, { displayMode: display, throwOnError: false, strict: 'ignore' }); }
  catch { el.textContent = latex; }
  return el;
}

/** Render "markdown-lite" text: paragraphs split by blank lines, $...$ inline math, $$...$$ display math, **bold**. */
export function richText(text: string): HTMLElement {
  const wrap = h('div', { class: 'rich' });
  for (const para of text.split(/\n\s*\n/)) {
    const p = h('p');
    const parts = para.split(/(\$\$[\s\S]+?\$\$|\$[^$]+?\$)/g);
    for (const part of parts) {
      if (!part) continue;
      if (part.startsWith('$$')) p.appendChild(tex(part.slice(2, -2), true));
      else if (part.startsWith('$')) p.appendChild(tex(part.slice(1, -1)));
      else {
        const bold = part.split(/(\*\*[^*]+\*\*)/g);
        for (const b of bold) {
          if (!b) continue;
          if (b.startsWith('**')) p.appendChild(h('strong', null, b.slice(2, -2)));
          else p.appendChild(document.createTextNode(b));
        }
      }
    }
    wrap.appendChild(p);
  }
  return wrap;
}

let mathliveConfigured = false;
function configureMathlive() {
  if (mathliveConfigured) return;
  mathliveConfigured = true;
  // Fonts/sounds are served from the package; disable sounds and keep everything local (no CDN).
  MathfieldElement.soundsDirectory = null;
  MathfieldElement.fontsDirectory = new URL('../../node_modules/mathlive/fonts/', import.meta.url).href;
}

export interface MathInput {
  el: MathfieldElement;
  /** LaTeX value as typed */
  latex(): string;
  /** ASCIIMath-ish plain value (what the grader parses) */
  ascii(): string;
  clear(): void;
  focus(): void;
  onEnter(fn: () => void): void;
}

/** Creates a MathLive field tuned for a phone: virtual keyboard on focus, large text. */
export function mathInput(placeholder = 'Your answer'): MathInput {
  configureMathlive();
  const el = new MathfieldElement();
  el.setAttribute('placeholder', placeholder);
  el.classList.add('math-input');
  el.mathVirtualKeyboardPolicy = 'auto';
  el.smartFence = true;
  el.smartSuperscript = true;
  let enterFn: (() => void) | null = null;
  el.addEventListener('keydown', (e) => { if (e.key === 'Enter') { e.preventDefault(); enterFn?.(); } });
  return {
    el,
    latex: () => el.getValue('latex'),
    ascii: () => el.getValue('ascii-math'),
    clear: () => el.setValue(''),
    focus: () => el.focus(),
    onEnter: (fn) => { enterFn = fn; },
  };
}

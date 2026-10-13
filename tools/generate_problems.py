#!/usr/bin/env python
"""
Generate SymPy-verified problem banks for Integrand.

    tools/.venv/bin/python tools/generate_problems.py                 # full run: every template module, every skill
    tools/.venv/bin/python tools/generate_problems.py --only sigma-notation
    tools/.venv/bin/python tools/generate_problems.py --only tier0     # or daily-tier-0
    tools/.venv/bin/python tools/generate_problems.py --list
    tools/.venv/bin/python tools/generate_problems.py --claude [DRAFT_DIR]   # also ask Claude for extra drafts (needs ANTHROPIC_API_KEY)

Every module in tools/templates/ (except names starting with "_") must expose `build() -> dict[str, list[problem]]`.
Keys are skill ids, or "daily-tier-<n>" for Daily Integral tiers, which are written to data/problems/daily-tier-<n>.json
with `skill` set to the node that owns that tier. Everything goes through problemkit.write_bank, which verifies each
problem with SymPy, dedupes, drops private `_verify` fields, and appends rejections to tools/rejected.log.
"""
from __future__ import annotations
import argparse, glob, importlib.util, json, os, re, sys, collections

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, 'templates'))
import problemkit
from problemkit import ROOT, REJECT_LOG, dedupe, write_bank, make_problem

TIER_OWNER = {0: 'area-by-geometry', 1: 'areas-and-distances', 2: 'definite-integral', 3: 'antiderivatives',
              4: 'substitution', 5: 'transcendental-integrals', 6: 'integration-by-parts'}
TIER_RE = re.compile(r'^(?:daily-)?tier-?(\d)$')


def load_templates() -> dict[str, object]:
    mods = {}
    for path in sorted(glob.glob(os.path.join(HERE, 'templates', '*.py'))):
        name = os.path.splitext(os.path.basename(path))[0]
        if name.startswith('_'):
            continue
        spec = importlib.util.spec_from_file_location(f'templates.{name}', path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        if hasattr(mod, 'build'):
            mods[name] = mod
    return mods


def curriculum_ids() -> set[str]:
    try:
        c = json.load(open(os.path.join(ROOT, 'data', 'curriculum.json')))
        return {n['id'] for n in c['nodes']}
    except Exception:
        return set()


def bank_target(key: str) -> tuple[str, str]:
    """(skill, filename) for a build() key."""
    m = TIER_RE.match(key)
    if m:
        n = int(m.group(1))
        return TIER_OWNER[n], f'daily-tier-{n}'
    return key, key


def normalize_only(only: str | None) -> str | None:
    if only is None:
        return None
    m = TIER_RE.match(only)
    return f'daily-tier-{m.group(1)}' if m else only


# ---------------------------------------------------------------- optional Claude drafting

CLAUDE_MODEL = 'claude-opus-5-5'

def claude_drafts(skill: str, summary: str, n: int, draft_dir: str | None) -> list[dict]:
    """Ask Claude for `n` extra problems for `skill` as JSON. Returns template-shaped problems (with _verify) or [].
    Degrades to [] with a clear message when the SDK or key is missing. The key is read by the SDK from the environment
    and is never written anywhere."""
    try:
        import anthropic
    except ImportError:
        print('  [claude] the anthropic package is not installed (tools/.venv/bin/pip install -r tools/requirements.txt); skipping drafts')
        return []
    if not os.environ.get('ANTHROPIC_API_KEY'):
        print('  [claude] ANTHROPIC_API_KEY is not set in the environment; skipping drafts')
        return []
    client = anthropic.Anthropic()
    schema = r'''
Return ONLY a JSON array. Each element:
{
 "statement": "prose with $...$ LaTeX math",
 "checker": "equiv" | "numeric" | "choice" | "interval",
 "answer": "<plain syntax: + - * / ^ ( ) sin cos tan sec csc cot asin acos atan exp ln sqrt abs pi e; numeric answers like 3, -1/3, sqrt(3)/2; choice answers are the 0-based index as a string; intervals like (-inf,3] or [0,6)>",
 "difficulty": 1 | 2 | 3,
 "hints": ["hint 1", "hint 2"],                 (exactly two)
 "solution": ["step", "step", ...],              (2-6 steps, $...$ allowed)
 "choices": ["LaTeX option", ...],               (choice only, 4 options)
 "variable": "x", "domain": [lo, hi],            (equiv only)
 "_verify": one of
    {"kind": "equiv", "expected": "<sympy expression equivalent to the answer, e.g. the UNSIMPLIFIED original>"}
    {"kind": "numeric", "value": "<sympy expression that evaluates to the answer, derived from the problem data not the answer>"}
    {"kind": "solve", "lhs": "<sympy>", "rhs": "<sympy>", "pick": "<optional root to select>"}
    {"kind": "evaluate", "expr": "<sympy>", "at": "<value>"}
    {"kind": "definite", "integrand": "<sympy>", "a": "<lo>", "b": "<hi>"}
    {"kind": "interval", "expected": "<sympy condition in x, e.g. 3*x+2<11 or (x>=0)&(x<6)>"}
    {"kind": "choice", "expected": "<sympy expr>", "choices_plain": ["plain form of each option in the same order as choices"]}
}
Rules: original problems only (never from any textbook); precise statements; sympy strings use ** for powers and * for products; the _verify
spec must let SymPy re-derive the key independently of how you computed the answer.'''
    prompt = (f"Write {n} original practice problems for a learner who has not finished algebra 2, for the skill '{skill}': {summary}. "
              f"Mix difficulties 1-3 and checker types.\n{schema}")
    try:
        with client.messages.stream(model=CLAUDE_MODEL, max_tokens=16000, output_config={'effort': 'high'},
                                    messages=[{'role': 'user', 'content': prompt}]) as stream:
            msg = stream.get_final_message()
    except anthropic.AuthenticationError:
        print('  [claude] authentication failed (check ANTHROPIC_API_KEY); skipping drafts')
        return []
    except anthropic.RateLimitError:
        print('  [claude] rate limited; skipping drafts for this skill')
        return []
    except anthropic.APIStatusError as ex:
        print(f'  [claude] API error {ex.status_code}: {ex.message}; skipping drafts')
        return []
    except anthropic.APIConnectionError:
        print('  [claude] network error; skipping drafts')
        return []
    if msg.stop_reason == 'refusal':
        print('  [claude] request was declined by the model; skipping drafts')
        return []
    text = ''.join(b.text for b in msg.content if b.type == 'text')
    m = re.search(r'\[.*\]', text, re.S)
    if not m:
        print('  [claude] no JSON array in the response; skipping drafts')
        return []
    try:
        raw = json.loads(m.group(0))
    except json.JSONDecodeError as ex:
        print(f'  [claude] could not parse JSON ({ex}); skipping drafts')
        return []
    if draft_dir:
        os.makedirs(draft_dir, exist_ok=True)
        with open(os.path.join(draft_dir, f'{skill}.json'), 'w') as f:
            json.dump(raw, f, indent=1)
    out = []
    for r in raw:
        try:
            p = make_problem(skill, r['statement'], r['checker'], str(r['answer']), difficulty=int(r.get('difficulty', 2)),
                             hints=list(r['hints']), solution=list(r['solution']), verify=r['_verify'],
                             variable=r.get('variable', 'x'), domain=tuple(r['domain']) if r.get('domain') else None,
                             choices=r.get('choices'), tier=r.get('tier'), tags=['claude'] + list(r.get('tags', [])))
            out.append(p)
        except Exception as ex:
            problemkit.log_reject({'id': None, 'skill': skill, 'statement': r.get('statement'), 'answer': r.get('answer')}, f'claude draft malformed: {ex!r}')
    print(f'  [claude] {len(out)} drafts accepted for verification')
    return out


# ---------------------------------------------------------------- main

def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--only', help='skill id or tier name (e.g. sigma-notation, daily-tier-0, tier0)')
    ap.add_argument('--list', action='store_true', help='list template modules and the skills they build, then exit')
    ap.add_argument('--claude', nargs='?', const=os.path.join(HERE, 'claude_drafts'), default=None, metavar='DRAFT_DIR',
                    help='also draft extra problems with the Anthropic API (raw drafts saved to DRAFT_DIR for audit)')
    ap.add_argument('--claude-count', type=int, default=8, help='drafts to request per skill with --claude')
    args = ap.parse_args(argv)

    mods = load_templates()
    only = normalize_only(args.only)
    if args.list:
        for name, mod in mods.items():
            try:
                keys = list(mod.build().keys())
            except Exception as ex:
                keys = [f'(build() failed: {ex!r})']
            print(f'{name}: ' + ', '.join(keys))
        return 0

    ids = curriculum_ids()
    node_summary = {}
    try:
        node_summary = {n['id']: n.get('summary', '') for n in json.load(open(os.path.join(ROOT, 'data', 'curriculum.json')))['nodes']}
    except Exception:
        pass

    if only is None:
        open(REJECT_LOG, 'w').close()  # full run starts a fresh rejection log
    before = sum(1 for _ in open(REJECT_LOG)) if os.path.exists(REJECT_LOG) else 0

    rows, matched, failed = [], False, []
    for name, mod in mods.items():
        try:
            built = mod.build()
        except Exception as ex:  # one broken template module must not take the whole run down
            print(f'error: templates/{name}.py build() failed: {ex!r}; skipping that module')
            failed.append(name)
            continue
        for key, problems in built.items():
            if only is not None and normalize_only(key) != only:
                continue
            matched = True
            skill, filename = bank_target(key)
            if ids and skill not in ids:
                print(f'warning: {name}.{key}: skill {skill!r} is not in data/curriculum.json')
            if args.claude:
                problems = list(problems) + claude_drafts(skill, node_summary.get(skill, ''), args.claude_count, args.claude)
            generated = len(problems)
            cands = dedupe(problems)
            rej_before = sum(1 for _ in open(REJECT_LOG))
            written = write_bank(skill, cands, filename)
            rej_after = sum(1 for _ in open(REJECT_LOG))
            rows.append((filename, generated, generated - len(cands), written, rej_after - rej_before))
    if not matched:
        print(f'no template builds {args.only!r}; use --list to see what is available')
        return 1
    if failed:
        print(f'warning: {len(failed)} template module(s) failed and were skipped: {", ".join(failed)}')

    print(f"\n{'bank':34} {'generated':>9} {'deduped':>8} {'verified':>8} {'rejected':>8}")
    for fn, gen, dd, ok, rej in rows:
        flag = '' if ok >= 40 else '  <-- fewer than 40'
        print(f'{fn:34} {gen:9} {dd:8} {ok:8} {rej:8}{flag}')
    print(f'{"total":34} {sum(r[1] for r in rows):9} {sum(r[2] for r in rows):8} {sum(r[3] for r in rows):8} {sum(r[4] for r in rows):8}')

    reasons = collections.Counter()
    for line in open(REJECT_LOG):
        try:
            reasons[json.loads(line)['reason'][:60]] += 1
        except Exception:
            pass
    if reasons:
        print('\ntop rejection reasons (tools/rejected.log):')
        for reason, n in reasons.most_common(8):
            print(f'  {n:4}  {reason}')
    else:
        print('\nno rejections logged')
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main())

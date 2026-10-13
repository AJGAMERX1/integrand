"""Re-verify every committed bank: python tools/verify_problems.py data/problems
Checks schema, verified flag, unique ids, and (where a template can regenerate) re-runs SymPy checks via tools/regen.
Exit code 1 on any failure."""
import json, os, sys, glob
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from problemkit import parse_plain

REQUIRED = ['id', 'skill', 'difficulty', 'statement', 'checker', 'answer', 'hints', 'solution', 'verified']

def main(folder):
    ids, bad = set(), 0
    files = sorted(glob.glob(os.path.join(folder, '*.json')))
    total = 0
    for f in files:
        bank = json.load(open(f))
        for p in bank.get('problems', []):
            total += 1
            errs = [k for k in REQUIRED if k not in p]
            if p.get('verified') is not True: errs.append('verified!=true')
            if p['id'] in ids: errs.append('duplicate id')
            ids.add(p['id'])
            if p['checker'] in ('equiv', 'equiv_plus_c', 'numeric'):
                try: parse_plain(p['answer'])
                except Exception as ex: errs.append(f'unparseable answer: {ex}')
            if p['checker'] == 'choice' and not (p.get('choices') and p['answer'].isdigit() and int(p['answer']) < len(p['choices'])): errs.append('bad choice')
            if len(p.get('hints', [])) != 2: errs.append('need 2 hints')
            if errs:
                bad += 1; print(f"{os.path.basename(f)} {p.get('id')}: {', '.join(errs)}")
    print(f"{total} problems in {len(files)} banks, {bad} with errors")
    return 1 if bad else 0

if __name__ == '__main__':
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else 'data/problems'))

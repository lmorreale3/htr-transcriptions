#!/usr/bin/env python3
"""Score transcriptions against ground truth (character and word error rate).

Usage: python3 scripts/score_cer.py <Collection_Name>
Compares transcriptions/<C>/<name>.txt (body after the '---' header line,
before any 'NOTES:' block) with ground_truth/<C>/<name>.gt.txt.
Writes transcriptions/<C>/_scores.csv and prints a summary.

Metrics
  CER strict   : every character counts (spacing, line breaks, symbols)
  CER relaxed  : lowercase, whitespace/underscores/line breaks removed,
                 bracket markup like [?] removed  -> "did it read the letters?"
  CER conv.    : relaxed + ꝑ=ꝓ, i=j, °=º=ª, lb=℔, macrons/tildes and . - / ignored
                 -> differences of reading only, not of transcription convention
  WER          : word error rate on whitespace-split tokens
"""
import sys, os, re, csv, unicodedata

def lev(a, b):
    if len(a) < len(b): a, b = b, a
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]

def body(path):
    t = unicodedata.normalize('NFC', open(path, encoding='utf-8').read())
    if '\n---\n' in t: t = t.split('\n---\n', 1)[1]
    t = re.split(r'^NOTES:', t, flags=re.M)[0]
    return '\n'.join(l.rstrip() for l in t.strip().split('\n'))

CONV = [('ꝑ','ꝓ'),('°','º'),('j','i'),('lb','℔'),('ª','º'),('chontanti','chontāti'),('cōtanti','cōtāti')]
def conventions(t):
    """Strip differences of transcription convention, keep differences of reading."""
    t = relaxed(t)
    for a, b in CONV: t = t.replace(a, b)
    t = unicodedata.normalize('NFD', t)
    t = ''.join(ch for ch in t if unicodedata.category(ch) != 'Mn')  # drop macrons/tildes
    return re.sub(r'[.\-/]', '', t)

def relaxed(t):
    t = re.sub(r'\[(\?|\.\.\.[^\]]*)\]', '', t)
    return re.sub(r'[\s_]+', '', t.lower())

c = sys.argv[1]
tdir, gdir = f'transcriptions/{c}', f'ground_truth/{c}'
rows = []
for f in sorted(os.listdir(tdir)):
    if not f.endswith('.txt') or f.startswith('_') or f.endswith('.prev.txt'): continue
    g = f'{gdir}/{f[:-4]}.gt.txt'
    if not os.path.exists(g): continue
    h, r = body(g), body(f'{tdir}/{f}')
    hw, rw = h.split(), r.split()
    rows.append(dict(page=f[:-4], gt_lines=h.count('\n') + 1, hyp_lines=r.count('\n') + 1,
        gt_chars=len(h),
        cer_strict=round(lev(h, r) / max(1, len(h)), 3),
        cer_relaxed=round(lev(relaxed(h), relaxed(r)) / max(1, len(relaxed(h))), 3),
        cer_conventions=round(lev(conventions(h), conventions(r)) / max(1, len(conventions(h))), 3),
        wer=round(lev(hw, rw) / max(1, len(hw)), 3)))
if not rows: sys.exit('no transcription/ground-truth pairs found')
with open(f'{tdir}/_scores.csv', 'w', newline='', encoding='utf-8') as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
for r in rows: print(r)
n = sum(r['gt_chars'] for r in rows)
print('weighted CER strict  :', round(sum(r['cer_strict'] * r['gt_chars'] for r in rows) / n, 3))
print('weighted CER relaxed :', round(sum(r['cer_relaxed'] * r['gt_chars'] for r in rows) / n, 3))
print('weighted CER conv.   :', round(sum(r['cer_conventions'] * r['gt_chars'] for r in rows) / n, 3))

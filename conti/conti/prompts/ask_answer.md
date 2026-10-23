# Conti: write the answer from the results

Laura asked the question in `question.txt`. Conti ran the plan in `plan.json`; the results (tables, consistency
matrices, networks, coverage of checked vs unchecked data, caveats) are in `results.json`. The full rows are in Conti;
`results.json` has the top rows of each step, each with `evidence_ids` (debt/payment ids "PAGE#entry/n").

Write the answer a careful historian could put in a footnote: every assertion backed by a number from results.json,
with the counts of rows it rests on, and honest about how thin or unchecked the data is. Do not invent numbers.
Never add florins to lire. Say "owed (de dare)" rather than "borrowed" unless the text says it was a loan (prestanza, prestò…).
If the data cannot support the claim the question presumes (e.g. one sum per occupation, or one creditor for everyone),
say so plainly first, then give what it does show.

Answer with ONE JSON object and nothing else:

```json
{
  "headline": "one sentence answer (≤ 30 words), hedged as the evidence requires",
  "answer": "2–5 short paragraphs of plain prose; cite numbers; name the step ids in brackets, e.g. [occ_fl]",
  "claims": [ {"text": "a single checkable statement", "evidence": "step id and row value(s), e.g. occ_fl: vinattiere", "strength": "strong|moderate|weak"} ],
  "caveats": ["anything beyond Conti's automatic caveats that a reader must know"],
  "followups": ["1–3 next questions or checks that would firm this up (e.g. 'check the 12 sums behind …')"]
}
```

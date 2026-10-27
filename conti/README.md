# Conti

Queries and charts over Leggio's transcriptions of account books. **Conti only reads Leggio's files**
(`workspace/<manuscript>/pages`, `reading/`) and never changes them; it can run while Leggio is open.

Start: double-click `conti/Start Conti.command` → http://127.0.0.1:8771 (Leggio stays on 8770).

## What it finds (step 1)
- **Sums** in the sums column (or at the end of an entry whose sum was never cut off), read as
  florins (kept apart) and lire · soldi · denari (12 𝒹 = 1 ß, 20 ß = 1 lira), with pc̄ / a fiorino marks.
  Each sum shows the image of its line; you mark it **Right**, **Correct** it, or **Not a sum** (e.g. ℔ as weight).
- **Dates** ("di xii di maggio 389"): day, month, the **year as written** and the **modern year**
  (Florentine style by default: 1 Jan–24 Mar → +1). Missing years are carried forward and marked.
- **Cross-references** ("ac̄ 41", "a libro giallo acār 312") with the book they point to.
- **Kind of entry**: de dare / de avere, anno dato / resta a dare.

## Tags, holdings, queries, networks (steps 2–3)
- **Tags** (per manuscript): people, places, occupations/roles, institutions, goods. Claude suggests (dashed, "?"), you check.
- **Holdings** (per manuscript): properties with owner, former owners, occupants and contract, location, and confini 1º–4º.
- **Query**: lines / entries / tags across manuscripts; count by name, year, book…; export .xlsx/.csv; save as datasets
  (growing or fixed). **Names**: merge spellings of the same person across manuscripts.
- **Network**: people & things named together (from any query or dataset), holdings & owners, cross-references;
  export for Gephi. **Neighbourhoods**: a relational (not to-scale) map of holdings by popolo / luogo / via:
  squares with their four confini, pulled together around shared neighbours. Sides = order written, not compass points.

- **Map**: holdings tethered to the most specific place with known coordinates (street, parish church, village), coloured
  by owner at the slider date. **Places**: the gazetteer (conti_data/_places.json) with confidence (secure / approximate /
  uncertain), basis and source for every coordinate; approve, change, or click the map to place a lane yourself.
  The street map underneath is OpenStreetMap (needs internet); everything else works offline.

## Ask (plain-language questions)
- **Ask** tab: type a question in ordinary language ("Which occupation consistently borrowed the largest sums?",
  "a network of the top 50 borrowers and lenders"). Claude turns it into a **plan** (a few steps); **Conti computes every number**
  and shows the rows behind it, with links to the line in Leggio and its image, what share rests on sums and tags you checked,
  and caveats. Downloads: evidence .xlsx (answer, every table, every row, coverage, plan), Gephi .zip for networks; query steps can
  be saved as datasets. **↻ Re-run** repeats the plan on today's data without Claude (the answer grows with the edition).
- Two ways to answer, no paid API: **✦ Ask Claude** runs Claude Code on this Mac (like Leggio's ✦ Refine; two short calls: plan,
  then wording), or **Save for a chat** and ask Claude in a Cowork chat to "answer the Conti questions waiting in the Ask tab".
- Debts (`ledger.py`): a *de dare* line starts a debt, its sum is the first one before the payments; *anno dato / a me dato*
  lines are payments; debtors = tags with role debtor; creditor = a tag with role creditor, else the manuscript's **account holder**
  (Settings; MPAP 4 = Heirs of Deo di Vanni), always marked "assumed". Florins and lire never added together; ƒ ß 𝒹 a fiorino at
  29 soldi to the florin; joint debts shared equally (or in full, if a plan says so).
- Code: `ledger.py` (debts), `analyze.py` (plan steps: transactions, aggregate with year-by-year consistency, network, query),
  `ask.py` (questions in `conti_data/_questions/`, Claude Code calls, CLI `python3 -m conti.ask …`), `prompts/`, `static/ask.js`.

## Catasto 1427 (who in the books appears in the Catasto)
- **Catasto 1427** tab: every person tagged in the books, with households of the Florentine Catasto of 1427 (city of Florence;
  `reference/catasto_1427/`, Brown's Online Catasto) that may be the same person or a relative. Code: `catasto.py`, `static/catasto.js`.
- Names are compared in the Catasto's spelling (upper case, 10 letters, Jacopo → IACOPO, Paolo → PAGOLO, ser/messer dropped);
  short forms (Nanni/Vanni = Giovanni, Meo = Bartolomeo, Cecco = Francesco…) count as weaker.
- **Same person**: first name + father's name (+ family name when both have one; a different one rules it out). **Relative**: the
  head's father (or a widow's late husband) has the person's name and family name. Common names are marked; the Catasto age in 1427
  is turned back to the year of the entry (a child then = probably a son or heir); the occupation tag is compared with the trade code.
- Each candidate shows gonfalone, trade, age, bocche, total / deductions / taxable (florins), ASF Campioni volume and page, and the
  reasons. You decide: **Same person / Relative / Not this one**; also a search by hand. Decisions: `conti_data/_catasto.json`.
  **⬇ Confirmed links .xlsx** lists them.

## Where things are
- Code: `conti/conti/` (`money.py`, `dates.py`, `refs.py`, `extract.py`, `app.py`, `static/`). Tests: `conti/tests/`.
- Your decisions: `conti_data/<manuscript>/tags.json`, `holdings.json`, `sums_review.json`; datasets in `conti_data/_datasets/`;
  merged names in `conti_data/_names.json`;, settings in `settings.json` (previous version kept as `.bak`).
  A decision is tied to the sum as written: if you later change that sum in Leggio, Conti shows
  "changed since checked" and stops counting the old decision.

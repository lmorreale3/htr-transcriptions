# Conti: plain-language questions (22–23 October 2026)

Follows `SESSION_SUMMARY_2026-10-22.md` (Conti section 5). Everything lives in `/Users/Shared/HTR_exploration`.
Goal: ask Conti questions in ordinary language and get an answer **with its evidence**.

**Before using it: restart Conti** (`conti/Start Conti.command`), then reload the page with Cmd-Shift-R. **Commit** `conti/`,
`conti_data/` and `CLAUDE.md` to GitHub as usual (the device shell cannot commit).

## Decisions taken with Laura
- **Both ways of answering, no paid API**: an **Ask** tab that runs Claude Code on the Mac (like ✦ Refine), and questions
  saved for a Cowork chat, answered there with the same code.
- **Creditor when none is written**: the manuscript's **account holder** (new Settings field; MPAP 4 = *Heirs of Deo di Vanni*),
  always shown as "assumed" and never confused with a tagged creditor.
- Standing rules kept: florins and lire never added together (no exchange rate); every number comes from Conti, never from Claude.

## 1. The Ask tab
- Type a question → Claude writes a **plan** (a few steps) → **Conti computes every count and sum** → Claude words the answer
  from Conti's results.
- Each answer shows: a one-line headline, a short written answer, **claims with their evidence** (strong / moderate / weak),
  "how the question was read" and "what the data cannot say yet", **what it rests on** (pages included and tagged, tags approved,
  sums checked, assumed creditor) and automatic caveats.
- Then one panel per step: bar charts, tables, a **year-by-year consistency grid**, a **directed network** (debtor → creditor;
  dashed = assumed creditor), and the **rows behind every number** (links to the line in Leggio, 🖼 picture of the line).
- Buttons: **⬇ Evidence .xlsx** (answer, every table, every row, coverage, plan), **Export for Gephi (.zip)**, **Save as dataset**
  (query steps), **↻ Re-run on today's data** (same plan, no Claude: answers grow with the edition; the text is flagged if it was
  written on older data), **Ask Claude again**, **Save for a chat**.
- Questions are stored in `conti_data/_questions/<id>.json`; working files in `.work/ask/<id>/`.

## 2. How debts are read (`conti/conti/ledger.py`)
- A **debt** starts on a *de dare / deono dare* line (or one naming a tagged debtor with "dare"); its sum is the first sum before
  the payments. A **payment** is an *anno dato / a me dato / a mone dato* line; payments belong to the debt above them.
- Debtors = tags with role *debtor*; occupation = occupation tag whose "of" names the debtor (same entry, else elsewhere).
- Creditor = tag with role *creditor*, else the account holder (assumed), else unknown.
- ƒ ß 𝒹 a fiorino counted at 29 soldi to the florin; joint debts shared equally among debtors (or in full if a plan says so).
- Payments are counted apart in networks, never added to what is owed.
- Caveat stated in every answer: *de dare* = owed the estate (rent, purchase or loan; the book rarely says which).

## 3. The plan language (`conti/conti/analyze.py`)
- `transactions` (debts / payments / all, with filters: occupation, debtor, creditor, year, currency, checked sums only,
  approved tags only, leave out flagged sums…)
- `aggregate` (by occupation / debtor / creditor / year / page; rank by median, total, mean, max or count; per currency;
  `over: year` = does the ranking hold in each period)
- `network` (top N parties + everyone they owed or who owed them)
- `query` (any existing Conti query, with counts)

## 4. The first two questions (MPAP 4, 10 tagged pages)
**"Which occupation consistently borrowed the largest sums?"** — not yet answerable with confidence.
- 63 debts with a tagged debtor; 26 name an occupation; 47 have a sum, **0 checked**, 17 flagged; **only 8 dated** (1388–1389),
  so "consistently" cannot be tested.
- Largest single debt: **Bartolo di Nese, vinattiere**, ƒ 176 ℔ 79 ß 16 𝒹 2 (RS1123; the sum has a plain-d warning).
  Lire: vinattiere ℔ 79.81, lavoratore ℔ 64.88 (Domenicuccio d'Andrea), tessitore di drappi ℔ 23.23.
- Every occupation rests on 1–3 sums. Leaving out flagged sums, the albergatore leads in florins (ƒ 14.34).

**"Network of the top 50 borrowers and lenders"** — the network is a star.
- 83 debts and payments, 76 parties; no entry names a creditor, so all 75 links run to the heirs of Deo di Vanni (assumed):
  ƒ 335.66 and ℔ 342.17 owed.
- Largest debtors: Bartolo di Nese (ƒ 176 / ℔ 79.81), Leonardo di Donato (ƒ 25.69), Pagolo di Jacopo dell'Aressa (ƒ 24),
  Compagnia di Santa Maria da Carraia (ƒ 19.03). Pagolo, the Compagnia di Carraia, the Opera di San Barnaba and Francesco di
  Detto made 3–4 payments each, received by Miniato di messer Arrigo (the heirs' attore).

## 5. Answering questions saved for a chat
Ask Claude in Cowork: *"Answer the Conti questions waiting in the Ask tab."* Claude runs, in the device shell from `conti/`:
`python3 -m conti.ask pending` → `packet <id>` → writes a plan → `run <id> --plan plan.json` → reads `results.json` →
writes the answer → `answer <id> answer.json`. (Also recorded in `CLAUDE.md`.)

## 6. Files
- New: `conti/conti/ledger.py`, `analyze.py`, `ask.py`, `prompts/ask_plan.md`, `prompts/ask_answer.md`, `static/ask.js`,
  `tests/test_ask.py` (26 tests passing in all).
- Changed: `app.py` (endpoints `/api/ask…`), `data.py` + `static/app.js` (account holder setting; Ask in the top bar),
  `static/style.css`, `static/index.html` (v=6), `pyproject.toml` (prompts packaged), `conti/README.md`, `CLAUDE.md`.
- Data: `conti_data/MPAP_4/settings.json` (account_holder), `conti_data/_questions/` (the two answered questions).
- Not yet tried in the browser by Laura.

## 7. Next
- **Laura**: check the sums behind the debts (Sums tab; start with Bartolo di Nese RS1123 and Domenicuccio d'Andrea RS1126);
  approve the occupation tags on the 10 pilot pages.
- **Claude**: tag more MPAP 4 pages (RS1124–RS1145); tag creditors where an entry names one; Deo's own books (libro giallo / rosso)
  would give real lender networks; add a "recipient / agent" layer (Miniato) to the network.
- Carried over: RS1135–RS1144 sums boxes still to fit; RS1145 Latin hallucinations; training-page flag clean-up; CER of the 17b model.

## 8. Leggio: folio numbers instead of image numbers (23 October, later)
- **Already in Leggio**: collection page → **Renumber folios…** (start page id, its folio, r/v) fills 1r, 1v, 2r… from that page
  to the end; the page editor's **folio box** takes any label by hand. Once set, the folio replaces the image id in lists,
  breadcrumbs, Flags and all exports. Code: `app.py` `/api/collections/{cid}/folios`, `importers.folio_label`, `static/app.js` "renum".
- **Status**: no folios set yet in MPAP_4 (0/593), Princeton_MS_131 or UPenn_1321; Baker_MS_493 and UPenn_1435 have them.
- **To do for MPAP 4**: run Renumber once from the first page, then again from each page where the foliation jumps.
- **Possible improvements (not built; Laura: "fine for now")**: "↓ Fill from here" button beside the folio box; hand-entered folios
  as fixed points (fill only between them, never overwrite); skip blank/cover pages; numbering by opening (*carta*: left/right share a
  number), which would let Conti's folio references link to pages. Open question: is MPAP 4 foliated r/v or by opening?

## 9. Catasto of 1427 (23 October, evening)
- Downloaded Brown's Online Catasto (city of Florence) through its search form: 10,004 households, all 25 fields →
  `reference/catasto_1427/` (data, codebook, decoded copy, README with source and citation).
- **Conti → Catasto 1427 tab**: for each tagged person, possible Catasto households (same person, or son / daughter / widow),
  with reasons, warnings (common name, age in 1427 vs the year of the entry, trade agrees/differs) and the household's gonfalone,
  trade, age, bocche, wealth, Campioni vol./page. Laura decides; decisions in `conti_data/_catasto.json`; xlsx of confirmed links.
- First run on MPAP 4: 132 people, 45 with possible households. Best so far: Michele di Fazio, notaio = Michele di Fazio, judge and
  notary, S. Giovanni – Chiavi, age 74 (strong); Salvestro di ser Bartolomeo (possible); Andrea di Pagolo dell'Aressa, Leon Bianco,
  perhaps son of Pagolo di Jacopo dell'Aressa. MPAP 4 is c. 1386–1391, ~40 years before the Catasto: most matches will be heirs.
- Noticed: RS1154 line 5 "28 di genaio 288" is read as 1288/1289; probably 388 (check the transcription).
- Needs: restart Conti; commit to GitHub (steps given in the chat).

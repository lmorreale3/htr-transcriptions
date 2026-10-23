# HTR exploration: summary of work with Claude (22 October 2026\)

Follows `SESSION_SUMMARY_2026-10-18.md`. Everything lives in `/Users/Shared/HTR_exploration`. Plan for the day: (1) fix problems in Leggio, (2) export the data, (3) a new "financial records data visualizer". Tasks 1 and 2 are done; task 3 starts in a new chat.

**Before using Leggio: restart it** (server code changed; the first start installs two small libraries), then reload the browser page with Cmd-Shift-R. **Commit both folders** to GitHub as usual (the device shell cannot commit).

## 1\. Cursor jumped to the start of the line (fixed)

- Cause: every 5 s Leggio checks for new Claude suggestions. On a page whose last history event was a Claude refinement, each of Laura's own saves looked like "new suggestions", so the page reloaded and the cursor went to position 0\. That is why it happened after accepting suggestions.  
- Now only a genuinely new refinement reloads the page, and never while typing (a "Load them" button appears instead). After any reload the cursor returns where it was. Special-character buttons can no longer write into an outdated line box.  
- File: `leggio/leggio/static/app.js`. Backup: `.work/app.js.bak_before_caretfix_20261022`.

## 2\. Sums shown under their entries (built)

- Cause: Kraken usually draws ONE line straight across an entry and its sum (the ruled dash joins them), so the sum stays at the end of the entry's text. Regrouping only works when a sum is a line of its own. Examples: RS1128 had 27 such lines; ms1435\_img040/041/047/048/049 had 5–15 each.  
- **Cutting at the red line** (new `leggio/leggio/tidy.py`): a line that crosses the sums boundary is cut there; the left part stays the entry, the right part becomes a ↳ sum line under it. Text is cut at the money sign (ƒ ℔ ⫳ 𝓎 pc̄) nearest the boundary; with no sign, at the nearest space and the sum is flagged "Check where the sum begins". Claude suggestions and Kraken readings are cut the same way. Lines not yet edited are re-read by Kraken in both halves.  
- Where: ⫼ Sums column → "Apply, keep my text"; the page button **✂ Tidy lines**; line ⋯ → "✂ Cut the sum off this line". A bar reports what changed, with **Undo** (`page.before_tidy`).  
- **Picture of the sum**: each sum/date sub-line shows a small crop of the page image beside its box.  
- **Margin years no longer take sums**: `layout.apply` prefers full-width entry lines on the same row, so "1468." / "1466" in the MS 1435 margin stop capturing the sum (9 attachments improved on existing pages, none worse).  
- **Automatic tidy after every machine reading** (Settings checkbox, on by default): removes empty slivers and true duplicate lines, and joins tiny cut-off pieces (an initial, a sign) to their line. It never touches edited, flagged, or sums/dates-box lines. Tested on all 694 pages: rules tightened after image checks (a first version would have removed \~2,900 lines and merged margin words such as "venduti" into entries).  
- Backups: `.work/*.bak_before_tidy_20261022` (app.js, style.css, layout.py, app.py, pipeline.py).

## 3\. Segmentation quality (advice; deferred)

- Kraken's default line finder was not trained on account books (ruled dashes, sums columns, marginal figures).  
- Short term: the tidy-up above. Real fix, later: train a segmentation model (`ketos segtrain`) on \~30–50 pages with clean layouts (sums as separate lines), added to Leggio's training page with the same crash/resume protection.

## 4\. Export (built)

- One menu item: collection → **More ▾ → Export (spreadsheet, Word, PDF)…** (replaces "Export finished pages as text"). Dialog: format; statuses (default Finished \+ Sent to training); From/To range or only ticked pages; for editions, text \= semi-diplomatic / expanded / both, and include translation. Remembers the last choices.  
- **Spreadsheet (.xlsx / .csv)**: one row per line of text, numbered as in the editor. Columns: manuscript, page, folio, status, line, column, text, sum (as written), date (as written), expanded, translation, translation draft/reviewed, flag, note, image file, line ids. Sums stay as written (no numeric conversion, by Laura's choice). The .xlsx also has "Pages" and "About" sheets.  
- **Reading edition (Word)**: page by page, table № · transcription · sum · translation; header row repeats; draft translations grey; † \= line not yet expanded.  
- **Reading edition (PDF)**: same layout as a print-ready page in a new tab → Save as PDF (the browser finds fonts for 𝒹 ⫳ ꝓ…).  
- Files go to `exports/<manuscript>/` and are also downloaded. Code: `leggio/leggio/export_data.py`; endpoints `POST /api/collections/{cid}/export`, `GET /api/exports/{cid}/{name}`. New dependencies: openpyxl, python-docx.  
- Backups: `.work/*.bak_before_export_20261022`. Test files in `.work/export_test/` and `.work/tidy_check/` can be deleted.

## 5\. Next: the financial records data visualizer (new chat)

- Input: the Leggio spreadsheet export (Lines sheet: one row per line, sums and dates in their own columns).  
- To decide at the start: what questions to ask of the data (people, places, dates, amounts, folio cross-references "a c. 39"), whether it reads exports or Leggio's workspace directly, whether sums need converting to numbers there (ƒ / ℔ / ⫳ / ß / 𝒹 per manuscript), and where it lives (a page in Leggio, a separate local app, or a published page).  
- Open items carried over: RS1135–RS1144 sums boxes copied from RS1134 still need fitting; RS1145 marked Finished but still has Kraken Latin hallucinations; training-page clean-up flags before retraining; CER of the 17b model on held-out pages.

# Conti: the financial records data visualizer (22 October 2026, second chat)

Built a new local app, **Conti**, in `conti/` (start: double-click `conti/Start Conti.command` → http://127.0.0.1:8771; Leggio stays on 8770 and both can run together). **Conti only reads Leggio's workspace and never writes it**; it uses Leggio's own export code (`export_data.page_rows`, read-only) so lines, sums and dates group exactly as in Leggio's spreadsheet export. Laura's decisions and Claude's suggestions live in `conti_data/` (plain JSON, previous version kept as `.bak`). **Restart Conti after each code update.** Commit `conti/` and `conti_data/` with the main project (`.gitignore` now excludes `conti/.venv`, `conti/conti.egg-info`, `conti_data/**/*.bak`, `conti_data/_exports/`). Tests: `conti/tests/` (20 passing). Code updates were delivered via `.work/conti_step*.tgz`; Claude's raw suggestion files are in `.work/conti_pilot_tags/`, `.work/conti_holdings/`, `.work/conti_geo/`.

Decisions taken with Laura: separate app (Leggio untouched); rules + Claude suggestions + Laura approves; dates stored in **both** Florentine (as written) and modern reckoning; data other than sums is the priority (sums need careful editing first); maps are **relational** (who holds next to whom), anchored to topography only where coordinates are secure.

## 1\. Rules (automatic, every page)

- **Sums** (`money.py`): ƒ kept apart from ℔/⫳/𝓎 · ß/β · 𝒹 (12 𝒹 = 1 ß, 20 ß = 1 lira), pc̄ and a fiorino marks; ƒ ß 𝒹 without lire = parts of the florin (soldi a fiorino, flagged at ≥ 29). Problems flagged (no sign, twice, order, ß ≥ 20, words). A sum never cut off its line is read from the end of the entry. **Sums tab**: image of line and sum, Right / Correct / Not a sum (e.g. ℔ as weight); decisions tied to the sum as written ("changed since checked" if edited later in Leggio).
- **Dates** (`dates.py`): "di xii di maggio 389", "dt̄oƀre", "di cēƀre" → day, month, **year as written** and **modern year** (Florentine style default: 1 Jan–24 Mar = +1; Pisan and modern selectable per manuscript in Settings). Missing years carried forward and marked.
- **Cross-references** (`refs.py`): ac̄ / acār / a carte / c̄ + folio lists (72/⁊/73/74), with the book named before ("libro detto" → last book of that kind; none → "(this book)"). **Entry kind**: de dare / de avere, anno dato, resta a dare. **Entries**: lines grouped into accounts/items (heuristic).
- MPAP 4 (38 Finished/Sent pages): 1,645 lines, 620 entries, 124 dates, 282 references, 318 sums (1 checked by Laura).

## 2\. Tags, query, datasets

- **Tags** (`tags.py`, `conti_data/<ms>/tags.json`): person (title, role, relation), place (kind, origin/residence/location), occupation/role, institution, goods. Claude tagged 10 pilot pages (RS1108, 1110, 1118, 1120–1123, 1126, 1128, 1138): **459 suggestions**, all still "?" to check in the **Tags** tab (click to approve/edit/reject; select words to add a tag). Guide: `.work/conti_pilot_tags/GUIDE.md`.
- **Names** tab: merge spellings of the same person across manuscripts (`conti_data/_names.json`; tags unchanged, merges reversible).
- **Query** tab (`query.py`): manuscripts × lines / entries / tags; conditions on person/place/occupation/institution/goods (contains/is/exists, role, same line or same entry), text (abbreviation marks ignored), kind, year (modern or as written), date, month, pages, book, folio, sums; "only tags I have checked"; **count by** name/role/year/book with first–last dates; export .xlsx / .csv (`conti_data/_exports/`).
- **Datasets** (`conti_data/_datasets/`): saved queries, **growing** (re-run, cumulative across manuscripts) or **fixed snapshot**; rows can be taken out by hand.

## 3\. Networks, holdings, neighbourhoods, map

- **Holdings** (`holdings.py`, `conti_data/<ms>/holdings.json`): kind, location (popolo / luogo / via / comune), owner, former owners, occupants + contract (pigione, affitto, mezzadria) + rent, **confini 1º–4º** (= order written, not compass points), related holdings, and a **timeline** of owners and occupants (modern dates; basis stated / inferred / unknown / open). Claude extracted **56 holdings** from RS1108, RS1110–1113, RS1158, RS1195, with timelines (guides `GUIDE.md`, `TIMELINE.md` in `.work/conti_holdings/`). All "?" — check in the **Holdings** tab (edit form covers every field incl. timeline). Key inference: Deo → heirs at the inventory date 12 Jun 1387 (death between testament 5 Nov 1386 and inventory).
- **Network** tab (`network.py`, d3 vendored): people & things named in the same entry (from any query or dataset), holdings & owners (owns / formerly / occupies / borders), cross-references (page → book/folio); click a node for connections, hide hubs; **Export for Gephi** (nodes.csv + edges.csv).
- **Neighbourhoods** tab: relational map per place — each holding a square with its four confini on its sides (grey bands = street fronts), pulled towards shared neighbours (Deo, Francesco Marchi, the Agli, Lapo Mazzuoli's heirs…); dashed = linked in the text. **Time slider + play**: squares coloured by owner at that date (colour changes when ownership passes), panel shows a Gantt of owners and tenants with the evidence.
- **Map** tab (Leaflet vendored; OpenStreetMap underneath optional, needs internet): holdings tethered to the most specific **located** place (street → parish church → village → city), same slider and owner colours; 51 of 56 placed. **Places** tab: gazetteer `conti_data/_places.json`, 35 places (12 secure, 9 approximate, 14 uncertain), each with basis and source URL; approve, change confidence, or **Place on map** by clicking (e.g. from Buonsignori). Barberino identified as **Val d'Elsa** (Spoiano, San Jacopo a Magliano); modern Via de' Fossi doubtful (outside San Lorenzo parish).
- External data: Florence As It Was offers no downloadable data (ArcGIS app of ~20 buildings on Buonsignori; host not reachable from Claude). Worth contacting: Niall Atkinson's **CATASTO 1427** project (UChicago/OCHRE: relational property location from neighbours, "openly accessible data"), Litchfield's **Online Gazetteer** (Brown; Buonsignori grid, parish churches), **DECIMA** (Toronto; 1561 census on Buonsignori).

## 4\. To do in Conti

- Laura: review the 459 tags and 56 holdings/timelines (doubts listed by Claude: RS1108 legacy to the Capitolo di S. Maria Maggiore treated as ownership; RS1110-h3 struck lease; RS1112 Vanni del Fede lease "1388"; RS1195 "viii di marzo 1380" read as 8 Mar 1381; unnamed RS1158 testator; Santa Lucia / Sant'Antonino / Spoiano unplaced); approve/place Places.
- Claude: tag + extract holdings for all Finished MPAP 4 pages (and other manuscripts) so networks and neighbourhoods fill in; entry grouping is heuristic.

## 5\. Next: plain-language questions (new chat)

Goal: ask Conti questions in ordinary language, e.g. *"Which occupation consistently borrowed the largest sums, with data to back up this assertion"*, or *"Create a network analysis of the top 50 borrowers and lenders, and who they were borrowing from or lending to"*, and get an answer **with its evidence** (the query used, the rows, a chart/network, and an export).

Points to settle at the start:
- **How it runs without a paid API**: Claude in a session (like the refinement pass) translates the question into Conti's existing query/network JSON, runs it through Conti's code, and writes the answer + evidence (dataset saved in Conti, .xlsx, chart). Options: a Claude skill that knows Conti's query language, or an "Ask" page in Conti that stores questions for Claude to answer.
- **What the data can support today**: "borrowed / lent" needs (a) amounts → only 1 of 318 sums checked so far; answers must say whether they rest on checked or machine-read sums, and keep florins and lire apart (no exchange rate); (b) who owes whom → in MPAP 4 most debtors owe the heirs of Deo di Vanni, so lender–borrower networks need the counterparty recorded per entry (person roles debtor/creditor exist in tags; an explicit "owes to" link may be needed); (c) occupation per person → from occupation tags linked by "of".
- **Answer standard**: every assertion backed by numbers and the rows behind them, with counts of checked vs unchecked data, and caveats (Florentine dating, partial transcription).

## 6\. Leggio: ⚑ Flags button (end of day)

- New **⚑ Flags** button in Leggio's top bar → list of every line flagged for recheck across all collections (filter by manuscript), grouped by page, each with its line number (sum/date sub-lines say "sum of line N"), text and note, plus pages marked "Needs recheck". Click a row → the page opens **at that line** (new deep link `#/p/<collection>/<page>/<line id>`, the line is outlined briefly).
- To share with a colleague: **Copy list** (Markdown with links, to paste in an e-mail or shared doc), **Download .md** / **.csv** (also saved in `exports/_flags/`). Each entry also gives the file path and line id, so it can be found without Leggio. Links point to http://127.0.0.1:8770, i.e. they work on any computer running Leggio on the same project.
- Files: new `leggio/leggio/flags.py`; endpoints `GET /api/flags`, `GET /api/flags/export?format=md|csv[&cid=]` in `app.py`; `static/app.js` (viewFlags, line deep link), `index.html`, `style.css`. Backups: `.work/*.bak_before_flags_20261022`. **Restart Leggio** and reload with Cmd-Shift-R. Currently 5 flagged lines (Baker MS 493 f. 7r; UPenn 1435 ff. 2r and img034) and 2 pages "Needs recheck".

# HTR Exploration Project

## Project Overview
This project resides at `/Users/Shared/HTR_exploration` and focuses on Handwritten Text Recognition (HTR), data extraction, and document processing workflows.

## Environment & Tooling
- Primary languages: Python, Shell scripting
- Data formats: IIIF manifests, ALTO XML, PAGE XML, TEI/XML, JSON
- Tools & Frameworks: eScriptorium, OpenCV, PyTorch / Kraken, FromThePage integrations

## Code Guidelines
- Keep scripts modular and well-documented.
- Retain character encoding integrity (UTF-8) across all XML/JSON parsing tasks.
- Avoid modifying source manifest or transcription files directly without creating a backup.

## Manuscript image transcription workflow
- Drop images into `images/<Collection_Name>/` (copies; originals stay where they are).
- Transcriptions go to `transcriptions/<Collection_Name>/<image-basename>.txt`, one per image.
- Follow `TRANSCRIPTION_CONVENTIONS.md` (strictly diplomatic). Skip images that already have a transcription unless asked to redo them.

## Leggio (transcription app)
- App code lives in `leggio/` (its own git repo). Start with `leggio/Start Leggio.command`.
- Leggio data: `workspace/<collection>/pages/*.json`; models in `models/`; training packages in `training/`.
- See `leggio/README.md` and `leggio/docs/GITHUB.md`.

## Reference material for the Claude refinement pass
- `reference/glossary/`: Edler (de Roover), *Glossary of Mediaeval Terms of Business* (1934), searchable PDF + text.
  - `edler_headwords.tsv` (headword → printed page), `edler_wordbank.tsv` (11k period word forms from her quotations),
    `edler_formulas.tsv` (recurring 3–4-word phrases), `edler_quotations.tsv` (1,442 dated quotations with sources).
  - `edler_ms493_quotes.json`: Edler's quotations from Medici MS 493 (= images/Baker_MS_493) with folio → image numbers.
  - Edler's text is normalised (word division, some expansions): use it to identify words, then render them diplomatically.
- Baker volume = Medici MS 493 (Baker Library, HBS). Images `images/Baker_MS_493/ms493_imgNNN.jpg`; folio n recto = img 2n−4.

## Status 2026-10-14 (MS 493 retraining push)
- Goal: finish 7r (img010), 14r (img024), 21r (img038), 21v (img039), then train an MS 493 model
  (Training → Pages from: Baker MS 493 → Build training set → Train; start from catmus_secondtraining_v2_4).
- 7r: corrected by Laura. 14r: 37 Claude suggestions; segmentation needs merges/deletes (fragments, sums column).
- 21r: 34 suggestions; Laura correcting. 21v: machine-read in cloud + 23 suggestions (Edler p.189 passage).
- Leggio v0.2.5 added "Merge with line above/below" in the line ⋯ menu.
- Suggestion files: .work/claude_suggestions/<page>.json
- 2026-10-15: Leggio 0.2.6: rows in amounts/labels boxes found by ink profile (leggio/rows.py, pipeline.reread_row_boxes,
  POST /api/read/{cid}/{pid}/rows); manual sub-lines via line field `sub` (amounts|labels|none) + `attached_to`
  (layout.sub_type). Untested in the browser yet. Full summary: SESSION_SUMMARY_2026-10-14.md; MPAP 4 + training: SESSION_SUMMARY_2026-10-16.md
- 2026-10-15: New manuscript ASF MPAP 4 (Balduccii): 593 JPEGs in images/MPAP_4/ (RSnnnn_DSCnnnnn-scr.jpg), model v3_0
  (v3 was trained on these images). eScriptorium ALTO export (doc112, RS1108–RS1158, 51 pages) unzipped in
  ground_truth/MPAP_4/alto_doc112/; its 21 pages with text were imported, judged poor, and reset (backup .work/backup_MPAP4_bad_alto_20261016).
  Training pages instead: second export (…013701.zip) = first 13 folios RS1108–RS1120, 665 lines, in ground_truth/MPAP_4/alto_first13/.
  attach_alto now skips ALTO files with no text. TEI files (RS1510–1514) in ground_truth/MPAP_4/ have no coordinates.
- 2026-10-15 (later): Claude refined all 13 MPAP 4 training pages (513 line suggestions, files in .work/claude_suggestions/RS11*.json;
  pre-suggestion backup .work/backup_MPAP4_before_claude_20261016). Pages set to "Needs recheck": Laura reviews, marks Finished, then trains.
  MPAP hand: ʒ-shaped figure = 3. 2026-10-16 Laura: do NOT change roman numerals; keep each manuscript's pound sign
  (MPAP ℔, MS 493 ⫳). Rules in transcriptions/MPAP_4/CONVENTIONS.md. Laura then rejected the rest: 13 pages Finished, ready to train.
- 2026-10-16 13:14: MPAP 4 fine-tune (training/20261016_124903, from v3_0, 13 pages) ran only 3 epochs (val acc 0.869 → 0.865 → 0.881,
  word acc 0.613) then ketos exited with no traceback (early stopping was 0/10, so not a normal stop; likely killed). Leggio converted
  the best checkpoint (checkpoint_02-0.8809) anyway. Renamed to models/catmus_secondtraining_v3_wleggio_2026-10-16.mlmodel (Laura's name).
  Next: read RS1121–RS1140 with it in Leggio, then Claude refines those 20 pages.
- 2026-10-16 afternoon: MPAP_4 collection model switched to catmus_secondtraining_v3_wleggio_2026-10-16; RS1122–RS1136 and RS1138–RS1140
  re-read with it (RS1137 still v3_0; RS1121 has Laura's layout edits, untouched). Claude suggestions written into readings.claude:
  RS1138–1140 (66) and RS1122–1136 (375; done by parallel subagents from 4-line image strips). Records in .work/claude_suggestions/.
  Backups: .work/backup_MPAP4_before_claude_RS1121-1140_20261016, .work/backup_MPAP4_before_claude_RS1122-1136_reread_20261016.
  Open question for Laura: one subagent read the looped ꝗ-shaped figure as 4 and the hooked ϛ-shaped figure as 5 (checked against sums in words on RS1134).
  2026-10-16 Laura: it is "Anno dato" (hanno), not "Anne dato" — all suggestions corrected.
- 2026-10-17: Leggio editor: two markup buttons at the start of the special-character bar — "del" wraps the selection as [del: …], "‸ ins" as [ins: …] (cursor lands inside if nothing is selected). Front-end only (app.js, style.css); backups in .work/*.bak_before_delins_20261017.

## Roadmap (Laura, 17 Oct 2026)
1. NOW: finish correcting the RS1121–RS1140 batch → mark Finished → train (all 16+ finished MPAP 4 pages, from v3_0, Leggio left open) →
   measure the new model against v3_wleggio (CER on a few held-out corrected pages; scripts/score_cer.py).
2. LATER (Laura will ask): (a) save the refinement procedure as a Claude skill (line-strip image check, amounts column,
   transcriptions/MPAP_4/CONVENTIONS.md, never overwrite Laura's edits, back up first); (b) a scheduled task that refines
   newly machine-read pages automatically and flags when enough Finished pages exist to retrain. No paid API.
3. ULTIMATELY: a reading page per manuscript with three side-by-side panes — page image · diplomatic transcription ·
   English translation — line/entry aligned. (Likely a Leggio "Reading view" fed from workspace/<collection>/pages.)
   Transcription pane has TWO modes (toggle): (i) semi-diplomatic = the text as Laura transcribes it in Leggio;
   (ii) expanded = every abbreviation expanded (an̄o→anno, cōt→cont-, ꝑ→per, ꝓ→pro, ac̄/acār→a carte, Giovan̄i→Giovanni, mãzo→marzo…)
   EXCEPT currency signs, which stay as symbols: ƒ ℔ ß 𝒹 pc̄ (and the sum layout). Expansion rules to be kept in a
   per-manuscript table so they can be reviewed; Claude drafts expansions, Laura approves.
   Expanded text is CLEAN (no brackets/italics marking supplied letters) — the semi-diplomatic toggle is the check (Laura, 17 Oct).
- 2026-10-17: reference/MPAP4_vocabulary.md built from verified pages (regenerate after each batch). Vocabulary pass on RS1128, RS1134–RS1137.
- 2026-10-17: Training run 2 (training/20261017_142953, 29 MPAP 4 pages, from v3_0, ~1,350 lines): ketos ran ONE epoch
  (val acc 0.884, word acc 0.537) then exited silently at 14:41 (same pattern as 16 Oct: no traceback, "23 leaked semaphore" warning →
  process killed, probably macOS memory pressure on MPS). Leggio converted checkpoint_00 → renamed
  models/catmus_secondtraining_v3_wleggio_2026-10-17.mlmodel. Earlier the Mac froze when two trainings ran at once (old set re-run + new set).
  Next: make training survive (e.g. ketos --workers 0 / smaller memory, or resume from checkpoint epoch by epoch).
- 2026-10-17: leggio/exporters.run_ketos now (a) refuses a second run on the same set (.training.lock), (b) moves old checkpoints to checkpoints/old_<time>/ before a run, (c) if ketos is killed, auto-resumes from the newest checkpoint with ketos --resume (up to 40 restarts). Needs Leggio restart. Backup .work/exporters.py.bak_before_resume_20261017.
- 2026-10-17 evening: Training run 3 (same 29-page set, from v3_0) COMPLETED with auto-resume: 13 epochs, 2 crashes (exit -6/-11,
  MPS) resumed automatically, early stopping ended it normally. Best = epoch 2, val acc 0.9047 → models/catmus_secondtraining_v3_wleggio_2026-10-17b.mlmodel
  (vs 0.881 on 16 Oct, 0.884 earlier today). Use this one for MPAP_4.
- 2026-10-17: Reading view built into Leggio: #/r/<cid>/<pid> (📖 Reading view button in page editor); server endpoint
  GET /api/reading/{cid}/{pid} (needs Leggio restart). Data: workspace/<cid>/reading/<pid>.json {lines:{lid:{expanded,translation}}}.
  Drafts generated by Claude for all 29 Finished MPAP_4 pages (unreviewed). Expanded = clean, currency glyphs kept.
- Session summary for 16–17 Oct: SESSION_SUMMARY_2026-10-17.md

## Status 2026-10-18 (full summary: SESSION_SUMMARY_2026-10-18.md)
- MPAP_4 model is now catmus_secondtraining_v3_wleggio_2026-10-17b. Re-read RS1142, RS1144–1146 (read with 16 Oct model) before refining.
  A re-read drops Claude suggestions: re-read first, refine second.
- CONVENTIONS CHECKER in Leggio (⚠ per line, Fix / Ignore → line.conv_ignore, "Fix all automatic"); engines leggio/leggio/conventions.py
  + static/app.js (parity 0/4206); CLI scripts/check_conventions.py; apply_suggestions.py refuses rule-breaking suggestions (--force).
- CONVENTIONS LIBRARY: conventions/sets/*.json (shared, with origin) + workspace/<cid>/conventions.json (use/level/params/promote/disable/
  own rules/prose/references). Nothing applies unless a manuscript adopts it; borrowed sets start "check-only". Leggio: collection → Conventions.
- "✦ REFINE WITH CLAUDE" (page button; "Refine selected" on collection page): leggio/leggio/refine.py runs Claude Code headless on the Mac
  (Laura's Harvard account, ~/.local/bin/claude, no API key) in .work/refine/<page>_<time>/ with conventions/refine_prompt.md.
  RS1141 test: Kraken CER 39.4% → 13.0% (default model; Opus 15.4%, no better). Setup: leggio/docs/CLAUDE_REFINE.md.
- NEW MPAP 4 CONVENTIONS (rules + CONVENTIONS.md): camãlingo/camãlingho (tilde over a, no macron on m); aꝓile/daꝓile; florin = ƒ alone
  (never ƒi). Training/finished pages corrected (5 + 1 + 19 lines; backups .work/backup_MPAP4_before_*_fix_20261018).
- OPEN: ƒa (a part of the symbol?); RS1127 l5 "ƒ ō" (ƒiō?); clean training-page flags (RS1124 l1/l13 Latin junk, RS1125 l15 "[", aentrata/alibro/
  auscita/pē leftovers, ƀ→𝒹 RS1122 l34, RS1133 l4) before retraining; CER of 17b on held-out pages (roadmap 1); RS1144 = DSC00654 like RS1138?
- Device shell is UTC: run scripts with TZ=America/New_York. Never `uv run` from the device shell. Bump app.js?v= in index.html after front-end edits.
- TRANSLATION DRAFTS: leggio/leggio/translate.py + conventions/translate_prompt.md (Claude Code, like refine). Runs automatically when a page is
  marked Finished (Settings → Claude checkbox, default on) and from the Reading view's "✦ Draft translation" button. Writes
  workspace/<cid>/reading/<pid>.json lines {expanded, translation, src, draft}; redrafts only new/changed lines; never replaces "reviewed": true.
  RS1141 drafted (24 lines, 39 s). RS1145 is marked Finished but still has Latin Kraken hallucinations: recheck before training/translating.
- SUMS COLUMN PER PAGE: page editor → "⫼ Sums column" (leggio/leggio/sums.py; GET/POST /api/pages/{cid}/{pid}/sums). Red line = where the
  sums begin, suggested from: this page (page.sums_boundary) → previous page set → ink detector (right on RS1133/1134/1145, wrong on RS1136/
  RS1121, false column on RS1141 = suggestion only). Apply refits column + amounts boxes to the page's writing area and either re-reads the
  page (unedited pages: sums become ↳ child lines of their entries) or only regroups (keeps text). "No sums column" removes the boxes.
  Pages RS1135–RS1144 still carry the box copied from RS1134: fit each.
  BENT BOUNDARY (Laura: hand-ruled column is not straight): sums_boundary is now a list of [x,y] points; handles on the red line
  (drag = tilt/bend, double-click line = add, double-click handle = remove). Regions carry "poly" (layout.in_region; pipeline crops
  and rows.find_rows white out what lies outside the polygon). Detector suggests 4 band points; previous page's line is reused. Next steps: B (Claude proposes sum→entry attachments), C (ketos
  segtrain with line types once ~30–50 pages have clean layout).
- COMMA-QWEN OFF by default (leggio_settings.json comma_enabled=false; Laura found it unhelpful): reads are Kraken only (was 2.1–2.4 min/page
  with comma x6). On demand: page editor "+ comma-qwen readings" (POST /api/read/{cid}/{pid}/comma, pipeline.comma_page) adds readings.comma
  + agreement to existing lines, never changes text. Remaining MPAP 4: 554 unread ≈ 385 account pages + ≈162 inventories + 7 blank/slips
  (visual guess: .work/contact/MPAP4_layout_guess_20261018.json).
- BAKER MS 493 CONVENTIONS (18 Oct): workspace/Baker_MS_493/conventions.json (pound ⫳; shared sets CHECK-ONLY except kraken-hygiene;
  numeral-j and lira-sign disabled: Baker writes final j (xij, xxvij) and uses ℔ for the weight pound on 21r) + prose
  transcriptions/Baker_MS_493/CONVENTIONS.md (vocab/usage transfer from MPAP 4, hand does not). References for Claude: Edler MS 493
  quotes, wordbank, formulas, MPAP4_vocabulary. Laura: ℔ = weight pound (libbra), lira = ⫳; rule lira-is-not-libbra (check).
- MS 1435 conventions set up (workspace/UPenn_1435/conventions.json, transcriptions/UPenn_1435/CONVENTIONS.md: 𝓎 lira, β/ß soldi?, strike-
  through chars vs [del:] = open questions). MS 1321 = images/UPenn_Fellowship (305 images + index.csv), not yet a Leggio collection.
- PROGRESS WORKBOOK: HTR_progress_2026-10-18.xlsx (Overview formulas over Pages; Next steps with Status column; Done log). Regenerate
  from workspace/*/pages on request (generator: collect .work/progress_data.json, then openpyxl).
- Roadmap 2(a) partly done (procedure now lives in refine.py + refine_prompt.md + conventions); 2(b) can now be a scheduled task calling the same code.
- 2026-10-18: Archived on GitHub (private): github.com/lmorreale3/htr-transcriptions (project, ~1,130 files) and github.com/lmorreale3/leggio (app). After each session: git add -A && git commit -m "…" && git push in both folders (Laura runs it in Terminal; the device shell cannot commit).

## Status 2026-10-22 (full summary: SESSION_SUMMARY_2026-10-22.md; needs Leggio restart)
- CARET BUG fixed (app.js): the 5-s "new Claude suggestions?" poll treated your own saves as new suggestions on pages whose last
  history event was a Claude refinement → reloaded the page, caret to position 0. Now only a NEW refinement event reloads, never while
  typing ("Load them" button instead); caret restored after any reload; char buttons never write into a stale line box.
- SUMS UNDER ENTRIES: leggio/leggio/tidy.py. split_sums cuts lines that cross the red sums boundary (text cut at the money sign nearest
  it, else nearest space + flag); sum becomes a ↳ sub-line; unedited halves re-read by Kraken. Runs on "Apply, keep my text" in
  ⫼ Sums column, on page button "✂ Tidy lines", on line ⋯ → "✂ Cut the sum off this line", and after every machine reading
  (Settings: tidy_after_read). tidy(): removes empty slivers + true duplicates, merges tiny same-row pieces; never touches edited,
  flagged or sums/dates-box lines. Undo: page["before_tidy"], POST /api/pages/{cid}/{pid}/tidy/undo (tidy bar → Undo).
  layout.apply: a margin year/mark on the same row no longer takes a sum (full-width lines preferred).
  Sum/date sub-lines show a picture of the sum cut from the page beside the box.
  Backups: .work/*.bak_before_caretfix_20261022, .work/*.bak_before_tidy_20261022.
- Segmentation training (ketos segtrain on clean layouts): deferred by Laura.
- EXPORT (task 2, done): collection → More ▾ → "Export (spreadsheet, Word, PDF)…" (one dialog, replaces the old text-export item;
  plain text is still a format in it). leggio/leggio/export_data.py + POST /api/collections/{cid}/export, GET /api/exports/{cid}/{name}.
  Formats: .xlsx (sheets Lines / Pages / About) and .csv = one row per line of text, numbered as in the editor, sums/dates (↳ sub-lines)
  in Sum / Date columns AS WRITTEN (Laura: no numeric conversion), expanded + translation from reading/<pid>.json;
  .docx reading edition (table № · transcription · sum · translation, header row repeats); PDF = print-ready HTML that opens in a new tab
  (browser Save as PDF, so every special glyph finds a font). Edition text: semi / expanded († = not expanded yet) / both.
  Files land in ROOT/exports/<cid>/ and are downloaded. New deps in pyproject: openpyxl, python-docx (uv installs them on next start).
  Backups .work/*.bak_before_export_20261022. Test files in .work/export_test/ (can be deleted).
- Next: (3) new app "financial records data visualizer" — should read the .xlsx/.csv export (Lines sheet).

## Conti (financial records visualizer), started 2026-10-22
- Separate app in `conti/` (port 8771, `conti/Start Conti.command`); READS Leggio's workspace only, never writes it.
  Imports leggio/leggio/export_data.page_rows read-only so lines/sums group exactly as in Leggio's export.
- Laura's data: `conti_data/<collection>/settings.json`, `sums_review.json` (decisions keyed "<page>|<line ids>", tied to the
  sum as written; a later edit in Leggio shows "changed since checked").
- Rules (conti/conti/): money.py (ƒ kept apart from ℔·ß·𝒹; ƒ ß 𝒹 without ℔ = parts of the florin a fiorino),
  dates.py (year_written + year_modern; Florentine style default = 25 March), refs.py (ac̄/acār/c̄ folio refs + book; kind de dare/de avere/resta).
- 2026-10-22 step 2 done: tags (conti/tags.py; conti_data/<ms>/tags.json, names merged across manuscripts in conti_data/_names.json),
  entries (account/item grouping, heuristic), query builder (conti/query.py: lines/entries/tags, count-by, xlsx/csv), datasets
  (conti_data/_datasets/, growing or snapshot). Claude pilot tags: 459 suggestions on 10 MPAP 4 pages (guide + raw files in
  .work/conti_pilot_tags/). Laura: data other than sums is the priority.
- 2026-10-22 step 3a done: holdings (conti/holdings.py; conti_data/<ms>/holdings.json: owner, former owners, occupants+contract,
  location, confini 1º–4º = ORDER WRITTEN not compass), networks (conti/network.py, static/network.js, d3 vendored: people named
  together, holdings & owners, cross-references; Gephi zip) and relational Neighbourhood map (squares with 4 confini, pulled to
  shared neighbours). Claude extracted 56 holdings (suggestions) from RS1108, RS1110–1113, RS1158, RS1195 (.work/conti_holdings/).
  Laura wants relational, not terrestrial, maps (coordinates only if secure).
- 2026-10-22 step 3b: holding timelines (holding.timeline: owner/occupant periods, modern dates, basis stated/inferred/unknown/open;
  Claude suggestions in .work/conti_holdings/timeline_*.json, guide TIMELINE.md). Neighbourhoods has a time slider + play: squares
  coloured by owner at that date (colour changes when ownership passes), panel shows a Gantt of owners/occupants.
- 2026-10-22 step 3c: Map tab (Leaflet vendored, OSM tiles optional): holdings tethered to the most specific LOCATED place
  (conti/places.py, gazetteer conti_data/_places.json: 35 places, 12 secure / 9 approximate / 14 uncertain, each with basis +
  source; Barberino = Val d'Elsa). Places tab: approve, change confidence, click map to place a lane. Florence As It Was has no
  downloadable data (ArcGIS app only); candidates to ask: Atkinson's CATASTO 1427 (UChicago/OCHRE), Litchfield gazetteer (Brown).
- Plan: 1 rules + sums review (done) · 2 query builder + saved/growing datasets + xlsx/csv · 3 views (amounts, people/places,
  timeline, cross-ref network) · 4 Claude tagging pass for people/places/occupations/goods (suggestions, Laura approves).
- Next (Laura, 22 Oct): plain-language questions for Conti (answers with evidence); see SESSION_SUMMARY_2026-10-22.md, Conti section 5.
- 2026-10-22: Leggio ⚑ Flags button: list of flagged lines (all collections) with links to the line (#/p/<c>/<p>/<line id>), Copy / .md / .csv for colleagues (leggio/leggio/flags.py; exports/_flags/). Backups .work/*.bak_before_flags_20261022.

## Conti Ask tab (plain-language questions), 2026-10-23
- conti/conti/ledger.py (debts/payments with debtor, occupation via occupation tag "of", creditor tagged or ASSUMED = settings
  account_holder; MPAP_4 = "Heirs of Deo di Vanni"), analyze.py (plan runner: transactions · aggregate [by occupation/debtor/creditor/
  year/page, rank_by median|total|count, over=year → consistency] · network [debtor → creditor, payments counted apart] · query;
  coverage + caveats; xlsx + Gephi), ask.py (conti_data/_questions/<id>.json; Claude Code headless via leggio.refine.claude_path,
  prompts in conti/conti/prompts/), static/ask.js. Tests: conti/tests/test_ask.py (26 passing in all).
- ANSWERING QUESTIONS SAVED FOR A CHAT (Laura: "answer the Conti questions waiting"): in the device shell, from conti/:
  `python3 -m conti.ask pending` → `python3 -m conti.ask packet <id>` (read .work/ask/<id>/profile.json + PLAN_LANGUAGE.md +
  INSTRUCTIONS.md) → write plan.json ({title, understood, limits, plan}) → `python3 -m conti.ask run <id> --plan plan.json`
  → read .work/ask/<id>/results.json, write answer.json per ANSWER_INSTRUCTIONS.md → `python3 -m conti.ask answer <id> answer.json`.
  Never invent numbers: every figure must come from results.json. Run with TZ=America/New_York.
- First two questions answered (20261023-102408-a225 occupations; -307d network). Findings: 63 debts with a tagged debtor on the
  10 tagged pages, 26 with an occupation, 0 sums checked, 8 dated → "consistently" untestable; largest debt Bartolo di Nese
  vinattiere ƒ 176 ℔ 79 (RS1123, plain-d warning). Network = star: no entry names a creditor, all 75 links to the heirs (assumed).
- Next: tag creditors where named; Deo's own books (libro giallo/rosso) for lender networks; a "recipient/agent" layer (Miniato).

- 2026-10-23: CATASTO 1427 (city of Florence, Brown Online Catasto) downloaded to reference/catasto_1427/ (10,004 households, codebook, decoded copy; README there). For cross-referencing contemporary account books.
- 2026-10-23: Conti CATASTO 1427 tab (#/catasto): conti/conti/catasto.py + static/catasto.js; proposes Catasto households for tagged people (same person / relative), Laura decides → conti_data/_catasto.json; xlsx export. Needs Conti restart (index.html v=7). Backups .work/*.bak_before_catasto_20261023. Tests conti/tests/test_catasto.py.

## TEI import, MPAP 4 inventories (23 Oct 2026, evening)
- Source: Laura's TEI files, /Users/lauramorreale/Applications, job, grant, etc./Upenn fellowship/MPAP4/Transcriptions (559 xml, named
  "ASF MPAP 4 (<family>)_<folio>_RS<n>.xml"; ~280 with text, the rest description only / <mute>). No coordinates; abbreviations expanded.
- scripts/tei_import.py (device shell: python3 -B scripts/tei_import.py <folder> RS… | --all [--dry-run]; run in chunks of ~35 pages,
  background runs stall). Per page: readings.tei, readings.tei_expanded, an open suggestion in readings.claude (TEI letters + Kraken's
  abbreviation signs), Reading-view expanded text (from:"TEI"), page note from <quote>, page.tei_unmatched; boxes widened left to take
  in item numbers (old box in line.polygon_before_tei / baseline_before_tei). Skips finished / in_progress / sent_to_training pages.
  Run 23 Oct: 184 pages, 14,912 of 15,686 TEI lines matched, 13,991 suggestions, 10,166 boxes widened. Log .work/tei_import_run_20261023.txt.
  Backup before: .work/backup_MPAP4_before_tei_20261023_1717.
- Laura's decisions: braccia = ƀ; word division as in the TEI; item numbers part of the line. Shared rule bstroke-pound disabled for MPAP_4,
  replaced by check rule bstroke-pound-sum (ƀ before a sum ending in ß/𝒹).
- FOLIOS reset from the TEI file names (560 pages); 33 pages without a file got an estimated folio ending in "?"
  (RS1153–1173, RS1175–1183, RS1490–1493). Old Leggio numbering was wrong (RS1152 was 42r, really 27r).
- No image in Leggio for RS1326, RS1334, RS1554, RS1668 (TEI exists).

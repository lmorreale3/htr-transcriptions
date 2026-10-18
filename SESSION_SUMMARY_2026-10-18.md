# HTR exploration: summary of work with Claude (18 October 2026)

Follows `SESSION_SUMMARY_2026-10-17.md`. Everything lives in `/Users/Shared/HTR_exploration`.

## 1. RS1141 and the model setting
- RS1141 had been read with the **16 Oct** model: `workspace/MPAP_4/collection.json` still named
  `catmus_secondtraining_v3_wleggio_2026-10-16`. **Switched to `…_2026-10-17b`** (best model, val acc 0.905).
  Pages read before the switch (RS1142, RS1144–RS1146) should be re-read before refining.
- RS1141's layout was copied from RS1134: its amounts box cut line ends into fragments (l22–l26, l30) and some
  line tails lay outside any box. Claude wrote 23 suggestions; Laura then corrected and finished the page.
- A re-read replaces the lines and **drops Claude's suggestions**: always re-read first, refine second.
- RS1144_DSC00654 has the same camera number as RS1138_DSC00654 (possibly a duplicate photo): check.

## 2. Conventions checker (in Leggio)
- Every line is checked against the manuscript's rules. A ⚠ appears under the line, with **Fix** for mechanical rules
  ("fix") and a reminder to look at the image for the rest ("check"). **Ignore** silences one rule on one line
  (`line.conv_ignore`). A bar offers "Next ⚠" and "Fix all automatic". Claude's suggestions show ⚠ too.
- The same rules run in the browser (`static/app.js`) and in Python (`leggio/leggio/conventions.py`); they gave
  identical results on all 4,206 lines tested.
- Command line (read-only): `python3 scripts/check_conventions.py MPAP_4 [pages] [--status …] [--suggestions] [--file x.json]`.
- `leggio/scripts/apply_suggestions.py` now refuses suggestions that break a rule (`--force` overrides).

## 3. Shared conventions library
- `conventions/sets/*.json`: rule sets grouped by subject, each recording where it was established:
  kraken-hygiene, roman-numerals-i-final, florentine-money (lira sign is a parameter), carta-references,
  account-formulae, tilde-for-r.
- `workspace/<collection>/conventions.json`: what each manuscript **uses** (nothing applies unless listed), at what
  level ("as-written", or "check-only" for a set borrowed from another manuscript until confirmed), its parameters
  (MPAP 4: `pound` = ℔), its own rules, and the prose/reference files Claude reads.
- In Leggio: collection page → **Conventions**. Details: `conventions/README.md`.

## 4. "✦ Refine with Claude"
- Button on each page, and "Refine selected with Claude" on the collection page (pages run one after another,
  beside the Kraken queue). Settings → **Claude** card (status, Test, model, time limit, "also suggest on corrected lines").
- Runs **Claude Code on the Mac**, signed in with Laura's Harvard Claude account (no API key; the key is removed
  from the environment so it can never bill the API). Installed at `~/.local/bin/claude` (v2.1.302); test passed.
- Each run builds a packet in `.work/refine/<page>_<time>/`: one enlarged full-width image per line with the line's
  outline in orange, the page, `packet.json`, copies of the conventions files, and `INSTRUCTIONS.md`
  (= `conventions/refine_prompt.md`). Claude reads it with read-only tools and answers in JSON.
  Leggio then applies the mechanical rules, backs up the page, and writes `readings.claude`. Lines Laura has
  corrected are skipped. Layout problems and doubts appear under **ⓘ Claude's notes**.
- Test on RS1141 (reset to raw Kraken, scored against Laura's finished text):

  | Version | CER (characters wrong) |
  |---|---|
  | Raw Kraken | 39.4% |
  | First instructions (Claude skimmed) | 35.9% |
  | **Instructions requiring every line image (default model, ~2 min)** | **13.0%** |
  | Same with Opus (~3 min, ~3× usage) | 15.4% |

  The default model stays. Setup notes: `leggio/docs/CLAUDE_REFINE.md`.

## 5. New conventions from Laura (all enforced as rules and written in `transcriptions/MPAP_4/CONVENTIONS.md`)
- **camarlingo** = camãlingo / camãlingho (tilde = r over the a after m), never cam̄alingo / camālingo.
- **aprile** = aꝓile / daꝓile (flourished p); a fully written "aprile" stays as written.
- **Florin** = ƒ alone; the i-like stroke is part of the symbol (never ƒi). Not changed: ƒiō / ƒio, ƒii, ƒi before ß/℔.
- Training/finished pages corrected to match: camarlingo 5 lines, aprile 1 line, florin 19 lines.
  Backups: `.work/backup_MPAP4_before_{camarlingo,aprile,florin}_fix_20261018`.

## 6. Open items
- **ƒa** (≈6×, e.g. RS1133 l24, RS1140): is the a part of the florin symbol? Awaiting Laura.
- RS1127 l5 now reads "…costarono ƒ ō": probably the word ƒiō; check the image.
- Still flagged in training pages: RS1124 l1 and l13 are Latin Kraken hallucinations; RS1125 l15 has a stray "[";
  leftovers of aentrata / alibro / auscita / Anne dato / pē; ƀ where 𝒹 belongs (RS1122 l34, RS1133 l4).
  Run `scripts/check_conventions.py MPAP_4 --status sent_to_training` and clean these before the next training run.
- Roadmap item 1 (CER of the 17b model on held-out pages with `scripts/score_cer.py`) not yet done.
- Pages read with the 16 Oct model (RS1142, RS1144–RS1146): re-read with 17b, then refine.

## 7. Practical notes for Claude
- The device shell is UTC: run scripts with `TZ=America/New_York` (page history uses local time).
- Never run `uv run` from the device shell (it touches `leggio/.venv`). Use `PYTHONPATH=leggio LEGGIO_ROOT=$PWD python3 …`.
- `index.html` loads `app.js?v=…` / `style.css?v=…`: bump the tag after front-end changes, or browsers keep the old script.
- Backups of every changed code file: `.work/*.bak_before_{conventions,refine,sets}_20261018`. Nothing committed to git.

## 8. Translation drafts on Finished (added late 18 Oct)
- Marking a page **Finished** now queues a Claude pass that drafts the **expanded** text and **English** translation for the
  Reading view (`leggio/leggio/translate.py`, instructions `conventions/translate_prompt.md`). Also: "✦ Draft translation"
  button in the Reading view (redrafts only lines that are new or changed since the last draft). Switch in Settings → Claude.
- Style follows the 17 Oct drafts: expanded keeps the scribe's word division and the money signs; translation keeps ƒ ℔ ß 𝒹
  amounts as written, years in full, supplied words in [ ].
- RS1141 drafted (24 lines, 39 s). RS1145 is marked Finished but still contains Latin Kraken hallucinations: recheck first.

## 9. Sums attached to their entries: "⫼ Sums column" (added late 18 Oct)
- Kraken only finds and reads lines; the sum→entry link is Leggio's layout step: lines in a page's **amounts** box are
  attached to the entry on their row (↳). It failed on recent pages because RS1134's boxes had been copied to RS1135–RS1144.
- New tool in the page editor, under the image: **⫼ Sums column**. A red line shows where the sums begin (suggested from
  the page itself, the previous page, or the ink). Drag it just left of the first ƒ/℔/ß, then:
  **Apply & re-read page** (unedited pages), **Apply, keep my text** (corrected pages: regroups only), or **No sums column**.
- The next page suggests the boundary you set on the previous one. Code: `leggio/leggio/sums.py`.
- Note: during this work a script briefly emptied `static/app.js`; it was restored from `.work/app.js.bak_before_sums_20261018`
  and the change re-applied (all features checked present).

## 10. comma-qwen on demand (added late 18 Oct)
- Automatic comma-qwen reading is now **off** (Settings → comma-qwen). Pages are read by Kraken only.
- "+ comma-qwen readings" in the page editor adds its readings to one page on request, beside Kraken's, without changing the text.
- Remaining MPAP 4: 554 unread pages ≈ 385 account pages, ≈162 inventories, 7 blank/slips (list in `.work/contact/`).
  At the old 2.1–2.4 min/page that was ~14 h for the account pages; Kraken alone should be several times faster (time one page).
- (later) The boundary can now bend to follow the hand-ruled column: drag the circular handles, double-click the line to add
  one, double-click a handle to remove it. Boxes become polygons; reading and sum-attachment follow the bent line.

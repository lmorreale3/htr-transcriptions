# HTR exploration: summary of work with Claude (16–17 October 2026)

Follows `SESSION_SUMMARY_2026-10-16.md`. Everything lives in `/Users/Shared/HTR_exploration`.

## 1. Training: three runs, and how they were made to finish

| Run | Set | Rounds | Characters correct | Model in `models/` |
|---|---|---|---|---|
| 16 Oct | 13 pages (RS1108–RS1120) from v3_0 | 3, then Kraken crashed | 88.1% | `catmus_secondtraining_v3_wleggio_2026-10-16` |
| 17 Oct, 1st | 29 pages from v3_0 | 1, then Kraken crashed | 88.4% | `catmus_secondtraining_v3_wleggio_2026-10-17` |
| **17 Oct, 2nd** | **29 pages** from v3_0 | **13, finished normally** | **90.5%** (round 3) | **`catmus_secondtraining_v3_wleggio_2026-10-17b`** ← use this |

- **Training set:** `training/20261017_142953`. It holds 29 MPAP 4 pages (RS1108–RS1127, RS1129–RS1134, RS1138–RS1140), about 1,350 lines.
- **Why the runs stopped:** Kraken crashes on the Mac's built-in GPU (exit codes −6 and −11, no error message). Separately, the Mac froze once because two trainings were running at the same time. The first one had been started by mistake on the old 13-page set.
- **Leggio changes** (`leggio/leggio/exporters.py`):
  - a run that crashes restarts automatically from its newest checkpoint with `ketos --resume`, up to 40 restarts;
  - a second training run on the same set is refused while one is running (a `.training.lock` file);
  - old checkpoints are moved to `checkpoints/old_*` before a new run, so they can't be picked as "best".
- **Training steps in Leggio:**
  1. Set **Pages from: MPAP 4**, not "all". The first attempt also picked up a Baker MS 493 page.
  2. Build the training set, then pick that set and click **Train once**.
  3. Leave the Mac plugged in and alone.
- **Outside servers, if needed:**
  - Harvard FASRC (Cannon cluster): billed at school level; needs a sponsoring PI account.
  - A rented cloud GPU (e.g. RunPod): about $0.27–0.90 an hour, so a run would cost under $2.
  - eScriptorium, if that instance has GPU training enabled.

## 2. The batch RS1121–RS1140

- **Reading:** MPAP_4's model was switched to the new one, and the pages were re-read. **Don't re-read pages that have suggestions**: a re-read wipes them, which happened once and had to be repaired.
- **Claude's suggestions** were written into `readings.claude` on every page, then refined over several passes:
  - **Line check:** each line was compared with a crop of the image.
  - **Amounts:** the right-hand money column was checked line by line, across 519 lines.
  - **Lira sign:** a separate check for ℔, using reference glyphs.
  - **Vocabulary:** garbled words were predicted from the formulas they sit in and from the word lists.
  - **Your rules** (section 3) were applied everywhere.
- **Status:** RS1121–RS1127, RS1129–RS1134 and RS1138–RS1140 are Finished and were used in training. RS1128 (Needs recheck) and RS1135–RS1137 are still open. They're kept out of training so they can be used to test the new model.
- **Kraken junk lines:** five Latin lines on Finished pages were blanked before training. The old text is kept in `readings.before`.
- **Records:** every suggestion batch is saved in `.work/claude_suggestions/`, and every pass has a backup in `.work/backup_MPAP4_*`.

## 3. Transcription rules (all in `transcriptions/MPAP_4/CONVENTIONS.md`)

- **Anno dato** (= hanno dato), not "Anne dato". **rede**, not "bede": in this hand capital R looks like B.
- **E a libro** / **a libro**, **a entrata**, **a uscita**. These are the only word-division changes allowed.
- **Sums:**
  - order: **ƒ (fiorini) · ℔ (lire) · ß (soldi) · 𝒹 (denari) · pc̄**;
  - denari are always 𝒹, never plain d;
  - a 𝒹 standing in the lire position is a misread ℔;
  - ℔ is the wide knotted loop with cross-bars (see `reference/MPAP4_money_glyphs.jpg`).
- **Model line:** `E a libro rosso di deo acār 72/⁊/73/74/105 ⁊ a libro giallo c̄ 316 ƒclxxviº ℔ lxxviiiiº ß xvi 𝒹 ii pc̄`
- **Numerals:**
  - º at the end of a sum = …iiii (quattro), but not for ordinals ("a iiº via");
  - a Y-shaped final stroke = ii, and j is never written;
  - ʒ = 3.
- **di vs 𝒹:** a day number followed by a month is **di**; 𝒹 is only for denari.
- **Strokes:** a **macron** = n/m (an̄o, cōt, ac̄ / c̄ = a carte); a **tilde** = r (mãzo, tẽra, quãto, attõe).
- **The dot–bar–dot sign (÷)** is written **1/1**.
- **Vocabulary:** predict garbled words from formulas, `reference/MPAP4_vocabulary.md` and Edler's word bank (e.g. "avuto ⁊ Ricevuto", "Truovo", "ꝓ resto", "monte Nuovo").

## 4. Other Leggio changes (front end)

- **Editor buttons:** **del** wraps the selected text as `[del: …]`; **‸ ins** wraps it as `[ins: …]`.
- **📖 Reading view** (`#/r/<collection>/<page>`) has three panes:
  - the page image, with the current line highlighted;
  - the transcription, with a **Semi-diplomatic | Expanded** toggle. Expanded is clean text with the abbreviations spelled out, but the money signs (ƒ ℔ ß 𝒹 pc̄ aō) stay as symbols.
  - the English translation, line by line.
- **Reading data:** stored in `workspace/MPAP_4/reading/<page>.json`. Claude wrote **unreviewed drafts for all 29 Finished pages**.
- **Restart needed:** restart Leggio once for the reading view's server part to work.
- **Backups of the old code:** in `.work/*.bak_*`.

## 5. Things to check or decide

- **Abbreviation decisions in the expanded text:**
  - ꝓ as *per* or *pr* (daꝓile → daprile);
  - ß as *ser* inside words (ßrami → serrami);
  - mō as mona, monte or monta;
  - cōꝓati as comperati;
  - vē (in inventory margins) as venduto;
  - 𝒹 in prose as denari.

  Once you've decided, Claude will turn them into a reviewed table, `workspace/MPAP_4/abbreviations.json`.
- **Reading layout:** whether to align the translation by line (as now) or by entry.
- **New model:** set MPAP_4's model to `catmus_secondtraining_v3_wleggio_2026-10-17b`.

## 6. Next steps

1. Correct RS1128 and RS1135–RS1137. Then measure the new model against the 16 Oct model on those pages (`scripts/score_cer.py`).
2. Read the next batch with v3_wleggio_2026-10-17b. Claude writes suggestions with the vocabulary list, then you correct, then retrain.
3. **When you ask:**
   - save the refinement procedure as a Claude skill;
   - set up a scheduled task that refines newly read pages automatically;
   - review the expanded texts and translations;
   - extend the reading view to other manuscripts.
4. To start a new chat: link it to this computer, then ask Claude to read `CLAUDE.md` and this file first.

# HTR exploration: summary of work with Claude (14–15 October 2026)

Everything lives in `/Users/Shared/HTR_exploration`.

## 1. What we set out to do

- Build a workflow for transcribing medieval manuscript images, following my strictly diplomatic rules in `TRANSCRIPTION_CONVENTIONS.md`.
- Marginal notes:
  - titles and rubrics go **before** their section;
  - other marginal notes go at the **end** of their section.
- Combine three kinds of reading:
  - my eScriptorium (Kraken) models;
  - Mattingly's comma-qwen model, following "where the readings disagree";
  - Claude's refinements, done progressively in chat sessions (no paid API).
- Then retrain Kraken on my corrected pages.

## 2. Manuscripts and images

| Folder (`images/`) | Manuscript | Notes |
|---|---|---|
| `UPenn_Fellowship/` | UPenn MS 1321 | Element 2 = f. 2r; foliation runs 2r, 2v, 3r… |
| `UPenn_1435/` | UPenn MS 1435 | Element 2 = f. 3r. `index.csv` uses the folio numbers read from the pages, which have jumps. |
| `Baker_MS_493/` | Baker Library (Harvard), Medici MS 493 | `ms493_img001–219`. **Folio n recto = image 2n−4** (7r = img010, 14r = img024, 21r = img038, 21v = img039). |

- Ground truth from eScriptorium/FromThePage is in `ground_truth/`.
- The draft reordered files (`*.gt.proposed.txt`) for MS 1435 are on hold.

## 3. Leggio, the transcription app we built

- **What it is:** a local web app, similar to FromThePage, in `leggio/`. The current version is **0.2.6**.
- **Start it:** double-click `leggio/Start Leggio.command`, or run in Terminal:
  ```
  cd /Users/Shared/HTR_exploration/leggio
  LEGGIO_ROOT=/Users/Shared/HTR_exploration uv run --extra comma leggio
  ```
- **Use it:** open http://127.0.0.1:8770. Stop it with **Ctrl+C** in Terminal.
- **Stop it opening a new browser tab:** put `LEGGIO_NO_BROWSER=1` in front of the command.

**Main features**

- Import images (folder, PDF or uploads) and assign a Kraken model per manuscript. MS 493, 1321 and 1435 use `catmus_secondtraining_v2_4`; v3_0 is for future images.
- Machine reading: Kraken first, then comma-qwen on whole pages and wide boxes only (it invents Latin on narrow strips). Words where the readings disagree are highlighted.
- **Columns / boxes** for ledger pages: column, dates (labels), sums (amounts), margin and heading. Dates and sums appear as ↳ sub-lines under their entry.
- **Line tools** (⋯ menu on each line):
  - Redraw outline;
  - Read this line again;
  - Insert, move or delete a line;
  - **Merge with line above/below**: joins the text, the outline and the baseline;
  - **＋ Add a sum / date line under this entry**, **↳ Make this the sum / date of the entry above**, and **⇤ Detach** (new in 0.2.6).
- **Sums and dates boxes** (new in 0.2.6): Leggio finds each row in an Amounts or Row-labels box by its ink instead of using Kraken's line finder, which broke sums into scraps. Kraken then reads all the rows in one run.
  - Automatic on new readings.
  - On a page already started: Columns → **Find rows in sums/dates boxes**. Only lines inside those boxes are replaced; the old ones are kept in the page file as `replaced_box_lines`.
- **Claude suggestions:** shown as a green/struck-through comparison with your text, with Accept, Reject, "Next suggestion" and "Accept all". Your earlier text is kept as "before".
- **Special-character keyboard:** includes ħ, ƒ, ⫳, ß, 𝒹, ꝓ, ℔ and the other glyphs, set in `leggio_settings.json`.
- **Page status:** Not started → Machine-read → In progress → Needs recheck → Finished → Sent to training.
- **Training page:** "Pages from" (choose one manuscript) → Build training set → Train. The new model is saved in `models/`.
- **GitHub instructions:** `leggio/docs/GITHUB.md`.

**Abbreviation glyphs used for MS 493**

| Glyph | Meaning |
|---|---|
| ƒ | fiorini |
| ⫳ | lire |
| ß | soldi |
| 𝒹 | denari |
| ꝓ | per/pro |
| ī | in |
| g° | grossi |
| ꝙ̄ | quattrini |
| ℔ | libbra |
| on̄ | once |

Florentine years begin on 25 March.

## 4. Reference material

- **Edler (de Roover), *Glossary of Mediaeval Terms of Business* (1934):** in `reference/glossary/`.
  - The original PDF, an OCR'd searchable PDF and the full text (`.txt`).
  - Tables of headwords, word forms, formulas and quotations (`.tsv`).
  - **`edler_ms493_quotes.json`:** Edler's quotations from MS 493, mapped to image numbers. We used them to check readings:
    - fol. 14: Oddo del Buono / Angniolo Belfredeli, p. 273;
    - fol. 21v: Il chomune di Firenze… Monte comune / Monte di Pisa, p. 189.

## 5. Where MS 493 stands (end of session)

| Folio | Image | State |
|---|---|---|
| 7r | img010 | Corrected by me. Exported to `exports/Baker_MS_493/`. Normalised + English tables made in chat. |
| 14r | img024 | 37 Claude suggestions. **Line boxes need fixing:** merge or delete fragments; rebuild the sums column. |
| 21r | img038 | 34 Claude suggestions (apothecaries' account, 1421). I'm correcting it. |
| 21v | img039 | Machine-read, with 23 Claude suggestions. Delete fragments l6, l7, l22, l25, l28; add lines for the missing sums; move l29 after l10. |

## 6. Next steps

1. Fix segmentation on 14r and 21v with Merge / Delete / Redraw. The outlines matter for training, not just the text.
2. Accept or reject the remaining suggestions and mark all four pages **Finished**.
3. Go to Training → Pages from: **Baker MS 493** → Build training set → Train, starting from `catmus_secondtraining_v2_4`.
4. Set the new model for MS 493 only, and test it on a fresh page.
5. Later:
   - a Glossary page in Leggio (my terms plus Edler);
   - a normalise-and-translate export;
   - a decision on the MS 1435 proposed ground truth.

## 7. Practical notes

- **Restarting work with Claude:** in a new chat linked to this computer, ask Claude to read `CLAUDE.md` and this summary first.
- **Getting suggestions:** ask Claude in chat to "refine" a page. The suggestions appear in Leggio automatically, or after reloading the page.
- **Network:** the network is blocked for downloads from Penn, Harvard and FromThePage, so I download images and PDFs myself and save them into `images/`.
- **Suggestion files:** saved in `.work/claude_suggestions/`.
- **Backups and earlier Leggio versions:** in `.work/`.

## 8. Update, 15 October

- **Leggio 0.2.6 is installed.** It is not yet tried in the browser: restart Leggio, then test on 14r.
  - Columns → Find rows in sums/dates boxes. On a copy of 14r it found all 10 sums and attached each to the right entry.
  - ⋯ → ＋ Add a sum line under this entry.
- **Reading quality:** Kraken still reads sums poorly. Correcting them and retraining should fix that.
- **Sums typed by hand:** they need an outline (⋯ → ✎ Redraw outline) before they can be used for training.
- **The "Invalid HTTP request received" warnings** in Terminal are harmless.

## 9. Starting a new chat

- Link the new chat to this computer.
- Ask Claude to read `CLAUDE.md` and this file first, in `/Users/Shared/HTR_exploration`.
- Leggio's source code also lives in `leggio/`. Claude edits it there and you restart Leggio for server-side changes; front-end-only changes just need a browser reload (Cmd+Shift+R).

## 10. Update, late 15 October: new manuscript ASF MPAP 4 (Balduccii)

- **Images:** 593 JPEGs in `images/MPAP_4/`. Leggio collection **MPAP_4**, model `catmus_secondtraining_v3_0`.
- **Training pages:** the first 13 folios (RS1108–RS1120), imported from eScriptorium ALTO (`ground_truth/MPAP_4/alto_first13/`).
  An earlier export (RS1108–RS1158) was poor and was removed from Leggio.
- **Claude suggestions:** 513 suggestions on those 13 pages. All 13 are set to **Needs recheck**.
- **To do next:**
  1. Review the suggestions page by page and mark each page Finished.
  2. Fix the line boxes:
     - RS1114: add the missing line between l10 and l11.
     - RS1119: redraw l14.
  3. (Decided 16 Oct: numerals stay as in the ground truth; each manuscript keeps its own pound sign. 430 suggestions left.)
  4. Training → Pages from: MPAP 4 → Build training set → Train, starting from v3_0.
- **Hand:** in MPAP 4 the ʒ-shaped figure is a 3 (so 39, not 29).

- **16 Oct:** Laura rejected the remaining suggestions; all 13 MPAP 4 pages are Finished (664 trainable lines) and ready to train.

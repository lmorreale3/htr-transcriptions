# Kraken training run, 23–24 October 2026 (MPAP 4)

## What was trained

| | |
|---|---|
| **Run folder** | `training/20261023_221332/` (pages, `train.log`, `checkpoints/`) |
| **Started** | 23 Oct, 22:13. Finished 24 Oct, 03:35 (about 5 hours on the Mac's GPU, no crash). |
| **Starting model** | `catmus_secondtraining_v3_wleggio_2026-10-17b` (the current MPAP 4 model, 90.5%) |
| **Training material** | **23 pages, 1,108 lines** of MPAP 4 |
| **Result** | **`models/catmus_secondtraining_v3_wleggio_2026-10-17b_ft_MPAP_4_20261023_221332.mlmodel`** |
| **Best score** | **92.95% characters correct** on the held-back check lines (round 6 of 17) |

**Pages used:** RS1128, RS1129, RS1138–RS1147, RS1152–RS1154, RS1158, RS1190, RS1195, RS1203–RS1206, RS1385.
Four of them (RS1129, RS1138–RS1140) were also in the 17 Oct training. These pages are now marked "Sent to training" in Leggio.

**How the run went**

- Kraken sets aside about 10% of the lines as a check (validation) set and scores the model on them after every round.
- The scores moved between 90.4% and 91.8% until round 6 reached 92.95%. Nothing beat it in the next 10 rounds, so Kraken stopped (early stopping) and kept round 6.
- Settings: `ketos train -f alto --resize union -q early --lag 10`.

## What the 92.95% means, and what it doesn't

- The check lines come from the **same pages** the model trained on, so the score flatters it a little.
- It is not directly comparable with 17b's 90.5%, which was measured on a different check set.
- The real test is a corrected page that was in **neither** training set: read it with both models and compare the error rates (CER). This has not been done yet.
- This model knows **MPAP 4's hand only**. No MS 493 pages were in this run.

## Next steps: getting the model into Leggio

1. **Nothing to copy.** The model is already in `models/`, and Leggio lists everything in that folder.
2. **Compare first (recommended):**
   - Pick one or two corrected MPAP 4 pages that were not in either training set.
   - Read them with 17b and with the new model, then compare the error rates.
   - Claude can do this: ask "compare the new MPAP 4 model with 17b".
3. **Switch MPAP 4 to the new model:**
   - Restart Leggio if it was running during training, so the model list refreshes.
   - Open the **MPAP_4** collection page and click the Kraken model button ("Kraken model for this manuscript").
   - Choose `catmus_secondtraining_v3_wleggio_2026-10-17b_ft_MPAP_4_20261023_221332.mlmodel`.
   - From then on, every reading in MPAP 4 (whole pages, "Read this line again", sums boxes) uses it. Other manuscripts keep their own models.
4. **Read the next batch:**
   - Select pages that are still "Not started" or "Machine-read" and use **Read with models**.
   - Pages you have already corrected are not overwritten. Only "Re-read anyway" would replace their lines, and that keeps a safety copy.
5. **Then the usual cycle:** Claude suggestions → your corrections → mark Finished → next training run, starting from this new model.

## Optional housekeeping

- **Shorter model name:** the name is long. It can be renamed in Finder, for example to `catmus_v3_MPAP4_2026-10-23.mlmodel`. Do it **before** step 3: a collection already set to the old name would lose its model.
- **Disk space:** each run's `checkpoints/` folder holds about a dozen copies of the model. Once the new model is in use, the older `.ckpt` files can be deleted.
- **MS 493:** it still has no model of its own (7r Finished; 14r and 21r in progress; 21v and 36v machine-read). Either finish more pages, or add the finished ones to the next MPAP 4 run.

## Comparison with 17b (24 October)

You had already renamed the new model `leggio trianing v3 10_23.mlmodel` and set it for MPAP_4.

**Fair test: your own TEI transcriptions**

- 10 MPAP 4 pages that were in no training set and that nobody has corrected: RS1192, 1257, 1327, 1431, 1483, 1567, 1605, 1645, 1689, 1719. That is 929 lines.
- Both models read the same line outlines, and their readings were compared with your TEI text for each line (`readings.tei`).
- The TEI is independent of both models, so neither has an advantage.

| | 17b | **new (10_23)** |
|---|---|---|
| Characters wrong, abbreviation signs kept (spaces and capitals ignored) | 15.7% | **14.7%** |
| Characters wrong, letters only | 14.6% | **13.4%** |
| Lines where this model did better | 194 | **318** (417 ties) |

- The new model is better on 8 of the 10 pages. On the other 2 the gap is under 1 point.
- The improvement is real but modest: about one wrong character fewer per hundred, roughly 7% fewer errors.
- The absolute rates (around 15%) look high because the TEI differs from Kraken's conventions in places (some expansions, how lines are split). They are not the true error rate of either model.

**Why not use your corrected pages for the test?**

The pages you have been correcting (RS1135, 1136, 1159, 1191, 1209 and others) start from whichever model read them. Any line you didn't change is still that model's own reading. On those pages, each model "wins" on the pages it read itself (17b on its pages, the new model on RS1171), so that test can't be trusted.

**Recommendation**

- Keep the new model for MPAP 4.
- Gains from here will come from more corrected pages per round, especially fully corrected ones.
- Results: `/tmp/claude-0/cmp/` in the Claude session; not kept on the Mac.

# HTR exploration: summary of work with Claude (15–16 October 2026)

Follows `SESSION_SUMMARY_2026-10-14.md`. Everything lives in `/Users/Shared/HTR_exploration`.

## 1. New manuscript: ASF MPAP 4 (Balduccii)

- **Images:** 593 JPEGs in `images/MPAP_4/`, named `RSnnnn_DSCnnnnn-scr.jpg` (RS1108 to RS1781), 1280 × 1920.
- **Leggio collection:** `MPAP_4`, 593 pages. Its model is set to `catmus_secondtraining_v3_0`; v3 was trained on these images in eScriptorium.
- **Ground truth** is in `ground_truth/MPAP_4/`:
  - `alto_first13/`: eScriptorium ALTO for the **first 13 folios (RS1108–RS1120)**. These are the training pages.
  - `alto_doc112/`: an earlier export (RS1108–RS1158). Its text was poor, so it was imported, rejected and removed from Leggio.
  - five TEI files (RS1510–1514). They have text only and no line positions, so they can't be used for training.
- **Leggio change:** the ALTO import now skips pages whose ALTO has no text, so it doesn't mark empty pages Finished.

## 2. Claude suggestions on the 13 training pages

- Claude read all 13 pages against the images and sent 513 suggestions to Leggio.
- On Laura's instructions, the suggestions were then revised:
  - **Roman numerals are never changed.** They stay as in the ground truth (`viii`, `iiiiº`, no final j).
  - **Each manuscript keeps its own pound sign:** MPAP 4 uses ℔ (RS1120 uses 𝓎), MS 493 uses ⫳.
- Laura accepted a few suggestions and rejected the rest. Most of them only changed word division or were Claude's misreadings.
- **Checks before training:**
  - RS1119: Laura added l14's text and fixed l16, which was a copy of l15. Claude redrew l14's outline, which had collapsed to 7 px, and removed a stray line break from its text.
  - No other problems were found. The repeated lines on RS1115 and RS1116 are real inventory entries.
- **Result:** all 13 pages are **Finished**, with **664 trainable lines**.
- The rules for future suggestions are in `transcriptions/MPAP_4/CONVENTIONS.md`:
  - suggest a change only for a clear misreading
  - no changes that only affect word division
  - keep dialect spellings as written (e.g. stiora and staiora both occur)
  - never change numerals or the pound sign
- **Palaeography:** in this hand the ʒ-shaped figure is a 3 (388, 330, 39).

## 3. Training (16 October)

- **Training set:** `training/20261016_124903` (13 MPAP 4 pages).
- **First run:** started by mistake from `catmus_secondtraining_v2_4` and stopped.
  - Leggio has no Stop button. Ctrl+C in Leggio's Terminal, then `pkill -f "ketos train"`, then check with `pgrep -fl "ketos train"`.
- **Now running:** restarted on the same set from **`catmus_secondtraining_v3_0`** (started about 13:00). The log is at `training/20261016_124903/train.log`.
- The new model will be saved in `models/`, with a name like `catmus_secondtraining_v3_0_ft_…`.
- **Starting Leggio from a new Terminal window:**
  ```
  cd /Users/Shared/HTR_exploration/leggio
  LEGGIO_ROOT=/Users/Shared/HTR_exploration uv run --extra comma leggio
  ```

## 4. Next steps

1. When training finishes, set the new model on the MPAP 4 collection (click the model name under the title).
2. Check it on a page it hasn't seen (after RS1120) against v3_0.
3. **Read all not-started pages** with Kraken (580 pages; overnight is best).
4. Then ask Claude in chat to refine MPAP 4: in batches of about 25–40 pages per session, following `transcriptions/MPAP_4/CONVENTIONS.md`.
5. Still to do on MS 493 (from 14 Oct): fix the segmentation on 14r and 21v, resolve the suggestions on 14r, 21r and 21v, and train.

## 5. Backups made this session (in `.work/`)

- `backup_MPAP4_bad_alto_20261016/`
- `backup_MPAP4_before_claude_20261016/`
- `backup_MPAP4_before_numeral_revert_20261016/`
- `backup_MPAP4_before_reject_all_20261016/`
- Suggestion files: `.work/claude_suggestions/RS11*.json`

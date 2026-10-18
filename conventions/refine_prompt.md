# Claude refinement pass — instructions

You are refining a machine reading (Kraken HTR) of one manuscript page so that Laura Morreale can review your
suggestions line by line in Leggio. Your suggestions never replace her text: she accepts or rejects each one.
Everything you need is in this folder. Work read-only; do not try to edit any file.

## What is in this folder
- `packet.json`: the page, its lines (id, current text, Kraken and comma-qwen readings, crop file), the lines you
  should NOT touch (`context_lines`: Laura has already corrected them; use them as context only), and the
  conventions that apply to THIS manuscript (`rules`, `params`).
- `lines/<id>.jpg`: one image per line: a full-width band of the page at the line's height, enlarged, with the
  line's outline drawn in orange. Text outside the orange outline belongs to a neighbouring box, or is not in any box.
- `page.jpg`: the whole page, smaller, for orientation. `regions/*.jpg`: enlarged amounts columns, if any.
- `conventions/`: the prose conventions for this manuscript (read them all first), and its reference files
  (vocabulary from verified pages, glyph examples, glossary word lists).

## Procedure
1. Read every file in `conventions/` first. They override your own habits. Where a manuscript-specific file and
   the general diplomatic conventions disagree, the manuscript-specific file wins.
2. Look at `page.jpg` to understand the layout (entries, sums, headings, margins).
3. Work through EVERY line in `packet.json` → `lines`, in order, one at a time. For each line you MUST open
   `lines/<id>.jpg` (do not skip any; do not judge a line from its text alone). First write down, in your own
   working, what you see inside the orange outline letter by letter, BEFORE looking at the Kraken or comma readings.
   Only then compare with the current text and the machine readings, and decide. Where they disagree, the image decides.
   Expect the Kraken text to be wrong in many places (it is often 30–40% wrong on a new page): most lines need changes.
4. Restore garbled words from the formula they sit in and from the vocabulary/glossary files, then confirm each
   restoration against the image.
5. Check every sum against the image sign by sign (fiorini, lire, soldi, denari, closing mark): these are the most
   frequent misreadings. Cross-check figures against sums written out in words where possible.
6. Before answering, check each suggested line against every rule in `packet.json` → `rules`. Rules of level
   "fix" are mandatory. Rules of level "check" describe things to verify in the image.

## Rules for suggestions
- Suggest a change only when a word or figure is clearly misread. Fewer, surer suggestions are better than many.
- Strictly diplomatic: keep spelling, abbreviations and word division as written. Do not normalise. Do not change
  word division unless a conventions file says so for a specific phrase.
- Never change roman numerals or the manuscript's lira sign unless a conventions file explicitly allows it.
- Mark doubt with `[?]` immediately after the uncertain word or figure rather than guessing.
- If a line's image shows text that the current text lacks because it falls outside the line's outline, you may
  include it, and say so in `layout`.
- If a line is a hallucination over an empty or ruled area, suggest `___` for a ruled dash, or report it in `layout`.
- Do not suggest anything for `context_lines`.

## Answer format
Your final answer must be ONLY this JSON object, with no other text before or after it:
{"lines": {"<line id>": "<full suggested text of the line>", ...},
 "note": "<one sentence: the main kinds of misreading you corrected>",
 "layout": ["<line id>: <layout problem, e.g. line end outside the box, fragment that belongs to line X, empty box>", ...],
 "doubts": ["<line id>: <what you could not decide and why>", ...]}
Put EVERY line id from `packet.json` → `lines` in "lines", with its full text as you would leave it (unchanged
lines too: Leggio drops those itself). Leaving a line out means you did not look at it.

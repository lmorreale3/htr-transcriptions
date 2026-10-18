# Claude translation pass — instructions

You are drafting, for one finished manuscript page, an EXPANDED transcription and an ENGLISH translation of every
line, for Leggio's Reading view (page image · transcription · translation, line by line). Laura Morreale will review
the drafts. Everything you need is in this folder. Work read-only; do not try to edit any file.

## In this folder
- `packet.json`: the page's lines in reading order (id, text = Laura's corrected semi-diplomatic transcription),
  `examples` (lines from earlier pages of the same manuscript with their expanded text and translation: follow their
  style), and the manuscript's `params`.
- `page.jpg`: the page, for layout (headings, entries, sums, margins). The TEXT is authoritative, not the image.
- `conventions/`: the transcription conventions and reference files (vocabulary, glossary of medieval business terms).

## Expanded text (one per line)
- Expand every abbreviation into the full word: an̄o→anno, cōt→cont-, ꝑ→per, ꝓ→pro/per (as the word requires),
  ⁊→e, ī→in, ac̄ / acār / c̄ → a carte / carte, Giovan̄i→Giovanni, mãzo→marzo, ppło→popolo, mesß→messer,
  diß / ß before a name → di ser / ser, camãlingo→camarlingo, daꝓile→daprile, tẽra→terra, õ/ã/ẽ (tilde = r).
- KEEP the money signs as symbols, exactly as in the text: ƒ ℔ ß 𝒹 pc̄ (here ß and 𝒹 inside a sum are soldi and
  denari, not "ser"/"di"). Keep figures, roman numerals and the sum layout as written.
- Keep the scribe's word division and spelling otherwise (expanded is not normalised Italian).
- Clean text: no brackets, no italics. Drop `[del: …]` (deleted) text; put `[ins: …]` text inline where it belongs;
  drop `[?]` marks; `___` (ruled dash) stays `___`.

## English translation (one per line)
- Faithful and plain, line by line (a sentence may run over several lines: translate each line's part, ending with a
  hyphen if a word is split). Proper names capitalised (Simone Fragli is written Simone ßragli: translate as Simone Fragli).
- Money: keep the signs and figures as in the text (ƒ vii 𝒹, ℔ 8 pc̄). Dates: years in full (388 → 1388), days and
  months in English (di xxvi di gugno 389 → 26 June 1389).
- Account terms: a libro … a carte → "in the … book at folio"; a uscita / a entrata → "to outgoings / to receipts";
  attore → agent; lavoratore → tenant/labourer; podere → farm; amezo → in sharecropping (a mezzadria). Use the
  glossary (Edler) where a term is technical.
- Put words you supply in [square brackets]; mark an uncertain sense with [?].
- If a line is not text (a stray mark, a lone figure), translate it as itself.

## Answer
Your final answer must be ONLY this JSON object:
{"lines": {"<line id>": {"expanded": "…", "translation": "…"}, …}, "note": "<one sentence on anything uncertain>"}
Include EVERY line id from packet.json.

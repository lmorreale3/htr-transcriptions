# MPAP 4 — overrides to TRANSCRIPTION_CONVENTIONS.md (Laura, 2026-10-16)

- Roman numerals: do NOT change them. Keep them exactly as in the eScriptorium ground truth
  (final stroke written as i, e.g. viii, iiiiº; no final j). Suggestions must not alter numerals.
  New numerals (e.g. a sum missing from the ground truth) follow the same style: i, not j.
- Pound / lira sign: keep the sign each manuscript uses. MPAP 4 ground truth uses ℔ (RS1120 uses 𝓎:
  keep it there). MS 493 uses ⫳. Never convert one to another.
- Other systematic glyphs as in the ground truth: ß, 𝒹, ƒ, ⁊, pē, cār / c̄, ___ for ruled dashes.
- Palaeography note: in this hand the ʒ-shaped figure is 3 (388, 330, 39).

## Lessons from the first review (16 Oct 2026) — rules for Claude's suggestions on MPAP 4
- Laura rejected almost all suggestions that only changed word division, and many "corrections" that were Claude misreadings.
- So: suggest a change only when a word or figure is clearly misread. Do NOT suggest word-division-only changes.
- Keep dialect / variant spellings as written (e.g. stiora and staiora both occur). Never normalise.
- Never change roman numerals or the pound sign (see above). Mark doubts with [?] rather than guessing.
- Fewer, surer suggestions are better than many.
- "Anno dato" (= hanno dato), NOT "Anne dato". The initial A often sits outside Kraken's line box (Kraken: "mne/nne/Ame/Amne dato").
- In this hand capital R looks like B: Kraken "bede" = "rede" (heirs).
- Money (Laura, 16 Oct): amounts, especially in the margins, run in the order fiorini ƒ · lire ℔ · soldi ß · denari 𝒹
  (12 denari = 1 soldo), often closed by pc̄ (piccioli). E.g. "ƒ 2221 ℔ 344 ß 11 𝒹 3 pc̄". Write the closing mark as pc̄ (not pē).
  ƀ is the -br- abbreviation in month names (Novēƀre, dicēƀre); before a sum it is a Kraken misreading of ℔.
- A 𝒹 that stands where lire belong in that order (after the ƒ figure, before ß) is a Kraken misreading of ℔: suggest ℔.
- "E a libro" (= and in the book) and "a libro", NOT "Ealibro / E alibro / ali bro / alibro" (Laura, 16 Oct). This overrides
  the no-word-division rule for this phrase only. Ground truth already writes "a libro".
- Macrons (Laura, 16 Oct): Claude's readings often drop the abbreviation stroke. Always check for it, e.g. ac̄ / c̄ (a carte),
  an̄o, cōt, cōtado, mōte, dan̄o, ī, Giovan̄i, van̄i, Som̄a, ꝑ/ꝓ. Before a carta number write ac̄ / c̄, never bare ac / c.
- Macron vs tilde (Laura, 16 Oct): a MACRON (combining U+0304: n̄, ā, ō, ē, ī, c̄) usually stands for a nasal n/m
  (an̄o, cōt, ī, Giovan̄i); a TILDE (combining U+0303: ã, õ, ẽ) usually stands for r (mãzo = marzo, tẽra = terra,
  quãto = quarto, attõe = attore, mãre). Look at the stroke's shape and choose accordingly. Ground-truth examples:
  mãzo, tẽra, tẽre, quãto, attõe, põtatore, pãtita, ão.

## Model line — the recurring "account reference + sum" pattern (Laura, RS1123 l28, 16 Oct)
    E a libro rosso di deo acār 72/⁊/73/74/105 ⁊ a libro giallo c̄ 316 ƒclxxviº ℔ lxxviiiiº ß xvi 𝒹 ii pc̄
- "E a libro <colour> [di deo]" = and in the <red/yellow…> book (libro rosso, libro giallo; also alibro detto, memoriale).
- acār / ac̄ / c̄ + carta number(s); several cartae are separated by "/" exactly as written (72/⁊/73/74/105), keep the slashes and ⁊.
- Then the sum in the order ƒ (fiorini) · ℔ (lire) · ß (soldi) · 𝒹 (denari — always 𝒹, never plain d) · pc̄. Roman numerals with final º as written
  (clxxviº, lxxviiiiº). Kraken typically garbles the carta list into one run of digits ("28339109") and reads ℔ as ƀ.
- Superscript º at the end of a numeral in a SUM usually means it ends in iiii (quattro): xviiiiº, lxxviiiiº, xxiiiiº, ß iiiiº.
  If Kraken shows ii º / iii º after ƒ ℔ ß 𝒹, suggest …iiiiº. Not for ordinals in boundaries ("a iº … a iiº … a iiiº via",
  "la xxviiiº prestanza"), and keep a single-i form like clxxviº when that is what is written.
- di (day) vs 𝒹 (denari) — decide by context (Laura, 16 Oct): "a di / adi / di + number + month" is a DATE → write "di"
  (Anno dato di xii di maggio 389; adi 13 di marzo). 𝒹 only for denari inside a sum (… ß xvi 𝒹 ii pc̄). Kraken often puts 𝒹 for di.
- ALWAYS check the right-hand amount column against the image, line by line (crop x≈560→edge at 3× zoom).
  Kraken splits sums into tiny boxes, reads ℔ as ƒ/ƀ/𝒹, drops ß/𝒹 signs, and hallucinates Latin on small boxes.
  Cross-check fiorini figures against sums written out in words in the entry (e.g. "centosette" = cvii).
- ℔ LOOKS LIKE THIS (see reference/MPAP4_money_glyphs.jpg, Laura's verified lines): a wide, low, knotted loop with
  cross-bars through it (like a "c"/"e"/"&" tangled with a "#"), sitting on the line BETWEEN the fiorini figure and the ß.
  ƒ = tall upright f-stroke with loop; the i-like stroke after it is PART OF THE SYMBOL: write ƒ alone, never ƒi (Laura, 18 Oct). ß = tall long-s with a big loop sweeping left below the line.
  𝒹 = small round d with its ascender curled back to the left. Kraken (and Claude) have read ℔ as c, e, 1, 𝒹, ƀ, ƀl, ƀł,
  or dropped it (RS1124 l26/l33, RS1138 l6/l8, RS1122 l9, RS1123 l28): when a figure after ƒ has no sign, look for ℔.
- Y-shaped final stroke on a numeral = TWO units, written ii (confirmed by Laura on RS1129: ℔ xxii ß vii, not ℔ xx ß vi).
  A lone 1-shaped stroke is a single i. Never write j.
- "a uscita" (= posted to the outgoings), NOT "avscita / anscita / ansata / auscita" (Laura, 16 Oct).
- "a entrata" (= posted to the receipts), NOT "aentrata" — as in the ground truth (Laura, 16 Oct).
- The dot–bar–dot sign (looks like ÷) is written 1/1 (Laura, 17 Oct; e.g. RS1133 l33 "a Gilio di lapo gili a 30 1/1 ꝓ 𝒹").
  Interest/rate phrases "a 30 ꝓ 𝒹" (per cento) recur: check each for the 1/1 sign before ꝓ. Never write ÷.
- PREDICT accounting vocabulary (Laura, 17 Oct): when Kraken garbles a word, restore it from the formula it sits in and from
  reference/MPAP4_vocabulary.md (phrases/forms from verified pages) and reference/glossary/edler_wordbank.tsv, then confirm against
  the image. E.g. "aē avuto ⁊sdicevnēo" → "aē avuto ⁊ Ricevuto"; "Truono" → "Truovo"; "besto" → "resto"; "monte Nuono" → "Nuovo".

## Machine-checked (18 Oct 2026)
The mechanical rules above are also encoded in workspace/MPAP_4/conventions.json, which Leggio checks every line against (⚠ under the line)
and which Claude's suggestions must pass before they are written. When a new rule is added here, add it there too.

## camarlingo (Laura, 18 Oct 2026)
- The abbreviation of camarlingo / camarlingho puts a TILDE (= r) over the a that follows the m: camãlingo, camãlingho.
  Never a macron on the m (not cam̄alingo / camālingo). Checked by rule "camarlingo" (set tilde-for-r).

## aprile (Laura, 18 Oct 2026)
- aprile is written with the flourished p (pr-abbreviation): aꝓile, daꝓile (= d'aprile). Kraken drops the flourish ("dapile"):
  always check for it. Checked by rule "aprile" (this manuscript's own rules). A fully written "aprile" stays as written.

## Florin sign (Laura, 18 Oct 2026)
- Write the florin as ƒ alone, also where it looks like ƒi: the i-like stroke is part of the symbol, especially in the amounts column.
  "ƒi xxvi" → "ƒ xxvi". Checked by rule "florin-sign" (set florentine-money). Not affected: ƒiō / ƒio (fiorini written as a word),
  and ƒi directly before ß/℔ (could be ƒ i = one florin: decide from the image). The reference image MPAP4_money_glyphs.jpg still
  captions "ƒi"; this rule overrides it.

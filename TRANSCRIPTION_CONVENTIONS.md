# Transcription Conventions — Strictly Diplomatic

Applies to every transcription Claude produces in this project unless a
collection folder contains its own `CONVENTIONS.md` overriding these rules.

## Reproduce exactly as written
- Original spelling, word division, capitalization, and punctuation (including
  punctus, punctus elevatus, virgula, etc., using the closest Unicode character).
- Original line breaks: one manuscript line = one line of text.
- Abbreviations are NOT expanded. Record the abbreviation mark with Unicode /
  MUFI characters where possible, e.g.:
  - nasal or general suspension: combining macron (U+0304) over the letter, e.g. `dn̄s`
  - Tironian et: `⁊`   · con-/com-: `ꝯ`   · per/par: `ꝑ`   · pro: `ꝓ`   · quod/qui: `ꝗ`
  - -rum: `ꝝ`   · -us: `ꝰ`   · superscript letters: Unicode superscripts where available (e.g. `qͥ`)
- Letter forms: keep long s `ſ`, r rotunda `ꝛ`, u/v and i/j exactly as written.
- No silent corrections of scribal errors.

## Minimal editorial markup (only where unavoidable)
- `[...]` illegible or lost text (approximate letters as `[...3...]` if countable)
- `[?]` immediately after a word whose reading is uncertain
- `[del: text]` struck-through text · `[ins: text]` interlinear/marginal insertion
- `[rubr]...[/rubr]` rubricated text · `[init: X]` decorated/historiated initial
- `[col. a]` / `[col. b]` column breaks · `[gap: illustration]` miniatures, diagrams

## Marginal notes (house rule, set 2026-10-14)
- Write each marginal note on its own line(s), exactly as written, with no
  bracket markup.
- **Titles and rubrics in the margin** (e.g. `casa`, `terre delcigna`,
  `pagamēto degliaficti`): place them **before** the section they label.
- **All other marginal notes** (later annotations such as "vendei decte terre
  a ..."): place them **at the end of the section** in which they appear,
  i.e. after the last line of that entry and its payment lines, before the
  next title, date line or entry.
- Marginal cross-reference numbers next to an entry (e.g. `85`, `69`) stay at
  the start of the line they sit beside.

## File header
Each `.txt` begins with:
```
Source image: <filename>
Collection: <folder name>
Folio/page: <as visible, or "unknown">
Script/language (best guess): <e.g. Gothic textualis, Old French>
Transcribed: <YYYY-MM-DD> by Claude — unreviewed
---
```
followed by the transcription. A short `NOTES:` block at the end may flag
problems (damage, uncertain hands, low image resolution).

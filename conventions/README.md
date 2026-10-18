# Conventions library

- `sets/*.json` — shared rule sets, grouped by subject (money, carta references, account formulae, Kraken hygiene…).
  Each records where it was established (`origin`). A set applies to NO manuscript unless that manuscript adopts it.
- `workspace/<collection>/conventions.json` — per manuscript: which sets it `use`s and at what level, its `params`
  (e.g. `"pound": "℔"`), rule ids to `promote` (to one-click fix) or `disable`, its own `rules`, and the `prose` and
  `references` files Claude reads.
  - level `as-written`: rules keep their fix/check level (for sets confirmed on this hand).
  - level `check-only`: every rule only flags ⚠ for you to look at (for a set newly borrowed from another manuscript).
- Choose sets in Leggio: collection page → "Conventions".
- `refine_prompt.md` — the instructions for "✦ Refine with Claude" (shared by all manuscripts; the manuscript's own
  conventions are added per page).
- Rule syntax: `find` is a regular expression where `\L` = any letter or mark and `{{name}}` = a manuscript parameter;
  `replace` uses `$1`… or `@NFC`. Check a manuscript: `python3 scripts/check_conventions.py <collection>`.

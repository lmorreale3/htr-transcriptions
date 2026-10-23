# Florentine Catasto of 1427 (city of Florence) — downloaded copy

Downloaded 23 October 2026 from the Online Catasto, Brown University Library (Center for Digital Scholarship),
https://cds.library.brown.edu/projects/catasto/ — data compiled by David Herlihy and Christiane Klapisch-Zuber.
Cite according to https://cds.library.brown.edu/projects/catasto/citation_instructions.html

- `catasto_1427_florence.csv` — all 10,004 records as returned by the site's search form (11 searches by record ID,
  every count matched the site). One row per household (head of household); 9,780 in series 1 (1427), 101 in series 2
  (additions 1428), 123 in series 7 (additions 1429). `volume`/`page` = ASF, Catasto, Campioni.
- `catasto_1427_codebook.csv` — codes and meanings, from the site's "Brief Codebook"
  (https://cds.library.brown.edu/projects/catasto/newsearch/catasto_codebook.html); meanings shortened, check before citing.
- `catasto_1427_florence_decoded.csv` — the same data with a readable `_label` column beside each coded field and a `quarter` column.

Money in florins. Deductions omit the 200-florin allowance per bocca. Codes not in the codebook (left blank in labels):
type_of_declaration 6 (31 households); trade 100, location 40, migration 9 (one each).
Purpose: cross-referencing people in contemporary account books (e.g. MPAP 4) with their Catasto households.

# Provenance: `lode_runner_reveng`

## Upstream project

- **Project:** lode_runner_reveng
- **Author/owner:** XekriRedmane
- **Upstream repository:** https://github.com/XekriRedmane/lode_runner_reveng
- **Upstream branch:** `main`
- **Upstream commit:** 2026-07-08T20:24:20-07:00 (`113db1c16951717259c9ae5e128958b29de0634d`)
- **Provenance record created:** 2026-09-08

The upstream project reverse engineers the Apple II version of *Lode Runner*. Its primary source is a noweb literate-programming document, `main.nw`.

The files in this directory are an unmodified snapshot of upstream files. `main.nw` is the source of truth for this project; `main.pdf` is its woven reading view.

## Imported material

| Local path  | Purpose in this project                                          |
|-------------|------------------------------------------------------------------|
| `README.md` | Overview of the upstream project and its architecture            |
| `weave.py`  | Noweb parser and chunk-graph engine, used by `scripts/nwtool.py` |
| `main.nw`   | Noweb literate source; uses LaTeX for prose chunks               |
| `main.pdf`  | `main.nw` woven into a PDF                                       |

## Relationship to other literate sources

- `reference/lode_runner_reveng/main.nw`: original source, authored by XekriRedmane (LaTeX)
- `research/main.nw.md`: created from the above `main.nw` with `make latex-to-md` (i.e. Markdown from LaTeX)
- `research/main.nw-edited.md`: basis for `research/build/index.html`, generated with `make nwhtml`

## License status

- The upstream repository is licensed under the Creative Commons Attribution-ShareAlike 4.0 International License (CC BY-SA 4.0).
- The files in this directory are used under that license, with attribution to XekriRedmane; see `LICENSE-CC-BY-SA-4.0.md`.

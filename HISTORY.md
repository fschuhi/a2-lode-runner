# a2-lode-runner -- History

(Note: "I" in the following paragraphs refer to the user, "you" to you as the AI model.)

- The resolved-work record: what was built and when (note date, or have the points in roughly reverse-chronological order).
- This is the trophy case -- kept in the repo, **out of the per-session filesdump** (so it no longer rides along every session).
- For *forward* work see `TODO.md`; for direction see `GOALS.md`; for the architecture as it stands see `README.md`.
- See "Workflow for the Whole Session (CRITICAL)" in `LLM_INSTRUCTIONS.md` for the interplay between `TODO.md` and this file. 

---

## Research

- **2026-09-04 Complete the Chapter 6 level-data investigation**: trace level selection, disk access, packed-cell decoding, board storage, drawing-time initialization, player and guard start markers, gold counting, and hidden exit ladders; distinguish normal disk levels from embedded attract-mode levels; establish the 28-by-16 board contract, low-nibble-first packing, fourteen-byte rows, 224-byte board payload, 256-byte sectors, and track/sector mapping; document source-board versus runtime-state responsibilities; define validation and visualization requirements for a future extractor; record unresolved questions without making them blockers; and create `docs/main-nw/06-levels.md` as the durable implementation-oriented result.

---

## Planning and project organization

- **2026-09-21** public on GitHub

- **2026-09-21 New direction and preparation for going public**: The Godot port is now optional; the project focuses on understanding the Apple II original and on a platform-neutral Core Game Spec (`docs/core-game-spec.md`; "The Description" during discussion), with `papple2` as a future research instrument. Rewrote `README.md` (what this is, the HTML browser pipeline as a Mermaid diagram, running, repository layout, sources and evidence, Core Game Spec scope and principles, optional Godot section with the fidelity policy, sibling projects, licensing) and `GOALS.md` (phase numbers replaced by names; Phases 4-6 collapsed into "Optional: Godot"; `papple2` section). The LaTeX -> Markdown -> HTML tooling stays in the repo as a finished subsystem; `ACTION_PLAN.md` closed, Phases 2-9 not pursued. Licensing: MIT for own code (`LICENSE`), CC BY-SA 4.0 for everything derived from XekriRedmane's work (`LICENSE-CC-BY-SA-4.0.md`); XekriRedmane confirmed by email on 2026-09-19 that `ultima1_reveng` files may be used under the same license as `lode_runner_reveng`, recorded in the new `scripts/PROVENANCE.md`. Removed `reference/ultima1_reveng/`, `reference/lode_runner_reveng/build.py`, and `chapter-3.pdf`; fixed `reference/lode_runner_reveng/PROVENANCE.md`. The disk image and the manual material are local only (`.gitignore`, `data/.gitkeep`); the README points to Xekri's repo for the disk image and to MobyGames and Macintosh Garden for cover and manual. LLM collaboration files untracked (managed by `stencil`). Fixed the `lode_runner_reveng` misspelling, the `ultima1_reveng` paths and NOTE headers, and `.PHONY`. Decided: publish from a fresh history, because the existing one contains the disk image and manuals; `research/build/` stays uncommitted, to be published later through GitHub Pages.

- **2026-09-07 HTML browser**: LaTeX -> Markdown -> HTML implemented, on the basis of `ultima1_reveng`, working off `ACTION_PLAN`. Completed Phase 0+1, documentation in `docs/reports/literate-migration`. `ACTION_PLAN` hibernated for now, focus back on chapters in (now editable) `research/main.nw-edited.md` and excerpts for the collaboration model on the basis of the original `main.nw`.

- **2026-09-06 Noweb tooling**: `scripts/nwtool.py` (`chapter N`, `index`, `chunk NAME`), a thin layer over `reference/lode_runner_reveng/weave.py`'s `Weaver.extract_chunk_info()`, woven Markdown with source-line locators (no `--numbered`; decided against per-line numbers). Real counts: 13 chapters, 181 chunk names, 337 identifiers (estimated 340 going in), 16 definitions of `<<level draw routine>>`. `tests/test_nwtool.py` covers all three commands plus a real-`main.nw` smoke test. `Makefile`: `nwchapter CHAPTER=`, `nwindex`, `nwchunk NAME="..." [MAXLINES=]`.

- **2026-09-05 nwtool checkpoint**: Compact woven Markdown chapter exporter implemented; seven fixture tests passed before the hard-break formatting adjustment. Reuses bundled weave.py; upstream files unchanged. Exports prose, fenced assembly, source ranges, continuation pointers, and identifier/chunk relationships, including external locators without copying dependencies. PDF remains the visual authority; unsupported LaTeX stays fenced. Next: validate one real chapter against the PDF and add regression tests for any problems. Index, finer selectors, and navigable HTML remain deferred. 

- **2026-09-05 Refactor the project documentation before a hiatus**: add a Noweb glossary and a chapter-neutral session workflow to the index; shrink `README.md` to charter material and point it at the index for the evidence vocabulary; turn the level extractor from three prose descriptions into one startable `TODO.md` item referenced from `GOALS.md`, `index.md`, and `06-levels.md`; add a "Noweb tooling" `TODO.md` item (`scripts/nwtool.py` reusing upstream `weave.py` to slice `main.nw` by chapter and generate a line-numbered chunk and identifier index) after measuring that `main.nw` alone is roughly 80,000 to 100,000 tokens and Chapter 8 is 23% of it; record the manual's level-validity rule (one player, one to five guards) in `06-levels.md`.

- **2026-09-04 Separate completed work from forward direction**: Updated the remaining roadmap around behavioral research, controlled level extraction, a deterministic headless gameplay core, playable integration, and later fidelity work. (The first attempt at this, in a session abandoned for hallucinations, produced `GOALS-hallucinated.md`; it was dissolved on 2026-09-05)

- **2026-09-01 Orient the project to `main.nw`**: establish `main.nw` and `main.pdf` as the primary code and navigation references; document the Noweb chunk, continuation, index, and PDF-navigation conventions; map the source chapters and top-level composition; define the research-note workflow and evidence vocabulary; select Chapter 6, covering level load, decode, and draw, as the first focused source-analysis slice; and create `docs/main-nw/index.md` as the durable navigation and handover artifact.

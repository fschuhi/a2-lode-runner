# a2-lode-runner -- TODO

(Note: "I" in the following paragraphs refer to the user, "you" to you as the AI model.)

## Charter

- Forward-looking only -- concrete, startable work: tasks specified well enough that next-session-me can begin within ten minutes, plus investigation items, test specs, and scratchpad ideas awaiting promotion or deletion.
- Items are unordered within their theme sections; open questions are marked _Needs investigation_ in the bullet.
- When an item is completed, record its durable outcome in `HISTORY.md` during the same session while the evidence and rationale are fresh, then strike it through in `TODO.md` with a concise handover note.
- Retain struck-through items through the next session because `TODO.md` is included in the standard filesdump while `HISTORY.md` normally is not; at the end of that next session, remove the already-archived items from `TODO.md`. Strategic direction, ordering, and milestones live in `GOALS.md` -- anything that needs a strategy discussion before it is actionable goes there.
- Architecture, contract, and settled decisions live in `README.md`.

---

## Publication

- **Tell XekriRedmane about the site**: Chapter 3 is converted and annotated (2026-09-22), so this is ready: write to Xekri about the published HTML edition of `lode_runner_reveng`, with the link and a short note on attribution and the annotation marker.

---

## Research

- **Chapter 8, Game play**: the next focused source-analysis slice. The bounded task definition is written at the start of the next session. Expected result: `docs/main-nw/08-game-play.md`, describing how the running game consumes and mutates the level state documented in `docs/main-nw/06-levels.md`, and naming the guard-specific behavior that is deferred to Chapter 9. The proposed outline is in `docs/main-nw/index.md` under "Recommended next focused chapter".

- ~~**Chapter 3, Apple II Graphics**: convert the leftovers in `research/main.nw-edited.md` and add the `a2-hires-lab` findings as annotations, plus a short `docs/main-nw/03-graphics.md`.~~ Done 2026-09-22: all leftovers converted, including the sprite catalog (`make sprite-catalog`); XekriRedmane's two diagrams became PNG crops from `main.pdf`, not Mermaid charts, because both are drawn by position; annotations in 3.1, 3.2 and 3.3; `docs/main-nw/03-graphics.md` written. Open questions there, none blocking. See `HISTORY.md`.

---

## Tools

- **Level extractor**: a Python script under `scripts/` that reads `data/Lode_Runner_1983_Broderbund_cr_Reset_Vector.do` and decodes the 150 disk levels (track 3 onwards, one 256-byte sector per level) using the level-data contract in `docs/main-nw/06-levels.md`. Development track: first a stable one-character ASCII rendering suitable for tests and diffs; then a controlled JSON file of all levels, in the level format the Core Game Spec will use; later a static HTML catalog with true sprite graphics. Not needed by any other item -- this is a motivation track. It has no dependency on the Chapter 8 research and can be picked up in any session. `papple2` could later cross-check the decoding (see `GOALS.md`). _Needs investigation_: whether the `.do` image uses the plain sector-offset formula `(track * 16 + sector) * 256` for all relevant tracks (`06-levels.md`, open question 6).

- **Final-LF check** (quick win): a `make` target, for example `make eol-check`, that lists every tracked text file that doesn't end with a line break. Files copied from a chat preview lose their final LF; this catches them before a commit.

---

## Refactoring

- **Smaller source for the sprite catalog** (only if the size of `research/main.nw-edited.md` starts to hurt): the catalog is about 320 KB of HTML table cells. Either a compact fenced block per sprite (one letter per pixel) that `scripts/weave_html.py` expands, as it does for `mermaid`; or keep `\input{sprite_tables.tex}` as a placeholder that the pipeline fills from `reference/lode_runner_reveng/sprite_tables.tex` at build time.

- **Hide-annotations switch** (idea): a small toggle in `scripts/web/` that collapses the `` **(`a2-lode-runner`):** `` blockquotes, so XekriRedmane's text can be read on its own.

- **`docs/main-nw/index.md` navigation**: the navigation part still treats `main.pdf` as the way into the source. Update it to the HTML research browser -- online at <https://fschuhi.github.io/a2-lode-runner/>, or built locally with `make nwhtml` and opened at `research/build/index.html` -- keeping `main.pdf` as the rendered view of `main.nw`.

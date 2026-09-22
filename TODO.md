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

- ~~**GitHub Pages for the HTML research browser**: publish the site through a GitHub Actions workflow that runs `make nwhtml` on each push to `main`, so that `research/build/` is never committed.~~ Done 2026-09-21/22: live at <https://fschuhi.github.io/a2-lode-runner/>, published by `.github/workflows/pages.yml` (tests, build, deploy on every push), with attribution on the start page and in a footer on every page, and all seven images; see `HISTORY.md`.

- **Tell XekriRedmane about the site**: once Chapter 3 is converted and annotated, write to Xekri about the published HTML edition of `lode_runner_reveng`, with the link and a short note on attribution and the annotation marker.

---

## Research

- **Chapter 8, Game play**: the next focused source-analysis slice. The bounded task definition is written at the start of the next session. Expected result: `docs/main-nw/08-game-play.md`, describing how the running game consumes and mutates the level state documented in `docs/main-nw/06-levels.md`, and naming the guard-specific behavior that is deferred to Chapter 9. The proposed outline is in `docs/main-nw/index.md` under "Recommended next focused chapter".

- **Chapter 3, Apple II Graphics**: best started in a fresh session. Decisions from 2026-09-22:
  - Convert what the converter left behind in Chapter 3 of `research/main.nw-edited.md`, comparing with `main.pdf`: six `TODO-CONVERT` blocks (four tables, two TikZ diagrams) and the colour table near the top of 3.1, which ended up garbled inside a bullet point without a marker. Xekri's two TikZ diagrams become Mermaid charts (the site renders Mermaid). These are conversions of form and get no marker.
  - Bring the findings of `a2-hires-lab` into `research/main.nw-edited.md` as annotations, i.e. blockquotes starting with `` **(`a2-lode-runner`):** ``, next to the text they refer to -- in particular the direct 1,792-byte shift table that would replace the two-stage lookup. `a2-hires-lab` already has matching Mermaid charts ("Visual Mechanics Flow" for the lookup in 3.3, "From Sprite Rows to BLOCK_DATA" for the two-into-three-bytes diagram). The start page already points to Chapter 3 as the worked example of annotations.
  - Write a short `docs/main-nw/03-graphics.md`: chapter status, evidence labels, open questions, and links to the annotations and to `a2-hires-lab`, with a header stating that this is Apple II implementation research, not an input to the Core Game Spec. The explanation itself lives in the annotations, so the two don't drift apart. Open question (_Inferred_): whether the cost of `COMPUTE_SHIFTED_SPRITE` on every sprite draw affects game speed -- to be checked when Chapter 8 shows how the game loop is timed.

---

## Tools

- **Level extractor**: a Python script under `scripts/` that reads `data/Lode_Runner_1983_Broderbund_cr_Reset_Vector.do` and decodes the 150 disk levels (track 3 onwards, one 256-byte sector per level) using the level-data contract in `docs/main-nw/06-levels.md`. Development track: first a stable one-character ASCII rendering suitable for tests and diffs; then a controlled JSON file of all levels, in the level format the Core Game Spec will use; later a static HTML catalog with true sprite graphics. Not needed by any other item -- this is a motivation track. It has no dependency on the Chapter 8 research and can be picked up in any session. `papple2` could later cross-check the decoding (see `GOALS.md`). _Needs investigation_: whether the `.do` image uses the plain sector-offset formula `(track * 16 + sector) * 256` for all relevant tracks (`06-levels.md`, open question 6).

- **Final-LF check** (quick win): a `make` target, for example `make eol-check`, that lists every tracked text file that doesn't end with a line break. Files copied from a chat preview lose their final LF; this catches them before a commit.

---

## Refactoring

- **`docs/main-nw/index.md` navigation**: the navigation part still treats `main.pdf` as the way into the source. Update it to the HTML research browser -- online at <https://fschuhi.github.io/a2-lode-runner/>, or built locally with `make nwhtml` and opened at `research/build/index.html` -- keeping `main.pdf` as the rendered view of `main.nw`.

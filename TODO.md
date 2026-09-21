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

- **Go public** (high priority): make `a2-lode-runner` public with a fresh history, because the existing history still contains the disk image and the manual material. Steps: (1) copy the whole project folder as a backup; (2) in the repo, `git checkout --orphan fresh`, `git commit -m "Initial public release"`, `git branch -D main`, `git branch -m main`; (3) check that `comm -23 <(git log --all --diff-filter=A --name-only --format= | sort -u) <(git ls-files | sort)` prints nothing and that `git ls-files` lists no game material; (4) delete the private repo on GitHub and recreate it, empty, under the same name; (5) `git push -u origin main`; (6) check that the README renders on GitHub, including the Mermaid diagram and all links, and that both licenses show; (7) switch the repo to public.

- **GitHub Pages for the HTML research browser**: publish the site through a GitHub Actions workflow that runs `make nwhtml` on each push to `main`, so that `research/build/` is never committed. Best done after the Chapter 3 tables are converted. _Needs investigation_: whether `make nwhtml` runs unchanged on the Ubuntu runner (Python version, `requirements.txt`, the `.venv` handling in the `Makefile`), and the Pages setting "Source: GitHub Actions".

---

## Research

- **Chapter 8, Game play**: the next focused source-analysis slice. The bounded task definition is written at the start of the next session. Expected result: `docs/main-nw/08-game-play.md`, describing how the running game consumes and mutates the level state documented in `docs/main-nw/06-levels.md`, and naming the guard-specific behavior that is deferred to Chapter 9. The proposed outline is in `docs/main-nw/index.md` under "Recommended next focused chapter".

- **Chapter 3, Apple II Graphics**: convert the Chapter 3 tables in `research/main.nw-edited.md`, which the converter left as `TODO-CONVERT` blocks, and compare them with `main.pdf`. Then bring the findings of `a2-hires-lab` into our notes, for example as `docs/main-nw/03-graphics.md`, in particular the direct 1,792-byte shift table that would replace the two-stage lookup. (The Excel workbench idea from the earlier version of this item became `a2-hires-lab`.)

---

## Tools

- **Level extractor**: a Python script under `scripts/` that reads `data/Lode_Runner_1983_Broderbund_cr_Reset_Vector.do` and decodes the 150 disk levels (track 3 onwards, one 256-byte sector per level) using the level-data contract in `docs/main-nw/06-levels.md`. Development track: first a stable one-character ASCII rendering suitable for tests and diffs; then a controlled JSON file of all levels, in the level format the Core Game Spec will use; later a static HTML catalog with true sprite graphics. Not needed by any other item -- this is a motivation track. It has no dependency on the Chapter 8 research and can be picked up in any session. `papple2` could later cross-check the decoding (see `GOALS.md`). _Needs investigation_: whether the `.do` image uses the plain sector-offset formula `(track * 16 + sector) * 256` for all relevant tracks (`06-levels.md`, open question 6).

- **Final-LF check** (quick win): a `make` target, for example `make eol-check`, that lists every tracked text file that doesn't end with a line break. Files copied from a chat preview lose their final LF; this catches them before a commit.

---

## Refactoring

- ~~Update `README.md` to reflect the new way of how I can do research, via HTML instead of PDF. Should also include reference to XekriRedmane. Use other project as template.~~ Done 2026-09-21: README rewritten for the Apple II focus, including the HTML browser pipeline, layout, licensing, and sibling projects; see `HISTORY.md`.

- **`docs/main-nw/index.md` navigation**: the navigation part still treats `main.pdf` as the way into the source. Update it to the HTML research browser (`make nwhtml`, then `research/build/index.html`), keeping `main.pdf` as the rendered view of `main.nw`.

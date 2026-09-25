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

- **Tell XekriRedmane about the site**: Chapter 3 is converted and annotated (2026-09-22), and Chapter 6 carries the catalog of all 150 levels as the level editor shows them (2026-09-25), so this is ready: write to Xekri about the published HTML edition of `lode_runner_reveng`, with the link, a short note on attribution and the annotation marker, and a pointer to the `a2-lode-runner` repo.

---

## Research

- **Chapter 8, Game play**: the next focused source-analysis slice. The bounded task definition is written at the start of the next session. Expected result: `docs/main-nw/08-game-play.md`, describing how the running game consumes and mutates the level state documented in `docs/main-nw/06-levels.md`, and naming the guard-specific behavior that is deferred to Chapter 9. The proposed outline is in `docs/main-nw/index.md` under "Recommended next focused chapter".

- **Which guard is dropped, confirmed in `papple2`**: in levels with six guards, the level draw routine removes the topmost guard (in level 8: row 2, column 5); Code-confirmed and Observed, see `docs/main-nw/06-levels.md`. Confirm it in `papple2` by reading `GUARD_LOCS_ROW` and `GUARD_LOCS_COL` after `DRAW_LEVEL_PAGE2` has drawn level 8.

- **Does dying reload the level from disk?** _Needs investigation_: after the player dies, is the board read from disk again, or rebuilt from the copy in memory? A breakpoint on `ACCESS_COMPRESSED_LEVEL_DATA` (AppleWin debugger or `papple2`) would show it.

- **Why did `$96 = 6` lead to level 8?** _Needs investigation_: setting `LEVELNUM` (`$A6`) only changes the number on screen; setting `DISK_LEVEL_LOC` (`$96`) to `6` while playing level 1 led to level 8, not level 7. Inferred: finishing a level increases `DISK_LEVEL_LOC` before the next level is loaded. Check in Chapter 8 where level completion updates `DISK_LEVEL_LOC` and `LEVELNUM`.

---

## Tools

- ~~**Level extractor**: a Python script under `scripts/` that reads accesses the tracks in `reference/lode_runner_reveng/disk/` using the level-data contract in `docs/main-nw/06-levels.md` and generates HTML tables like the sprites in the HTML documentation (Chapter 3). The visual catalogue of levels should be added afterwards as annotations to Chapter 6 (check if adding to `06-levels.md` would be helpful.) `papple2` will also access the disk data and emulate DOS 3.3. Note that adding the visual sprite catalogue to the literate-source consumed quite a bit of space -- are there alternatives which result in slimmer static HTML pages?~~ Done 2026-09-25: `scripts/level_extractor.py` reads the track files (`make level-ascii`, `make level-check`), `scripts/level_images.py` draws PNGs with the level-editor sprites (`make level-images`), `scripts/level_catalog.py` puts linked thumbnails into Chapter 6 (`make level-catalog`); PNG thumbnails keep the page slim. Findings, including the six-guard levels, are in `docs/main-nw/06-levels.md`. See `HISTORY.md`.

- **Level `*.do` investigation** (lower priority, since the level extractor reads the track files): access `data/Lode_Runner_1983_Broderbund_cr_Reset_Vector.do` and decode the 150 disk levels (track 3 onwards, one 256-byte sector per level). Check whether the `.do` image uses the plain sector-offset formula `(track * 16 + sector) * 256` for all relevant tracks (`06-levels.md`, open question 6). The output of `scripts/level_extractor.py` is the reference to compare against.

- **Final-LF check** (quick win): a `make` target, for example `make eol-check`, that lists every tracked text file that doesn't end with a line break. Files copied from a chat preview lose their final LF; this catches them before a commit.

---

## Refactoring

- **Smaller source for the sprite catalog** (only if the size of `research/main.nw-edited.md` starts to hurt): the catalog is about 320 KB of HTML table cells. Either a compact fenced block per sprite (one letter per pixel) that `scripts/weave_html.py` expands, as it does for `mermaid`; or keep `\input{sprite_tables.tex}` as a placeholder that the pipeline fills from `reference/lode_runner_reveng/sprite_tables.tex` at build time.

- **Hide-annotations switch** (idea): a small toggle in `scripts/web/` that collapses the `` **(`a2-lode-runner`):** `` blockquotes, so XekriRedmane's text can be read on its own.

- **`docs/main-nw/index.md` navigation**: the navigation part still treats `main.pdf` as the way into the source. Update it to the HTML research browser -- online at <https://fschuhi.github.io/a2-lode-runner/>, or built locally with `make nwhtml` and opened at `research/build/index.html` -- keeping `main.pdf` as the rendered view of `main.nw`.

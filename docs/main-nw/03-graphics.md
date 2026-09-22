# Chapter 3: Apple II Graphics

This is research on the Apple II implementation: how Lode Runner turns sprite data into bytes on the hi-res screen. It is not an input to the Core Game Spec. `README.md` defers the Apple II hi-res colour effects, and an optional Godot version would use clean pixel art instead.

The explanations live in the annotations in Chapter 3 of the HTML research browser (<https://fschuhi.github.io/a2-lode-runner/apple-ii-graphics.html>), next to the text and code they refer to. This note records status, evidence, and open questions, so that the two cannot drift apart.

## Status

- **Conversion complete.** Everything the LaTeX -> Markdown converter left behind in Chapter 3 of `research/main.nw-edited.md` is converted: the colour table and the two example tables as Markdown tables, the two example sprites as coloured HTML grids, the catalog of all 104 sprites (generated from `reference/lode_runner_reveng/sprite_tables.tex` with `make sprite-catalog`), and XekriRedmane's two diagrams as images cropped from `main.pdf`.
- **Three annotations**, marked `` **(`a2-lode-runner`):** ``:
  - [3.1 Pixels and their color](https://fschuhi.github.io/a2-lode-runner/apple-ii-graphics.html#pixels-and-their-color): the two examples are sprites 9 (the player) and 87 (the letter S); colour depends on the screen column.
  - [3.2 The sprites](https://fschuhi.github.io/a2-lode-runner/apple-ii-graphics.html#the-sprites): why the sprite bytes are stored 104 apart.
  - [3.3 Shifting sprites](https://fschuhi.github.io/a2-lode-runner/apple-ii-graphics.html#shifting-sprites): the direct 1,792-byte table that could replace the two-stage lookup, and why `main.pdf` calls both tables "never used".
- **Not researched:** section 3.4, "Memory mapped graphics", and the rest of the chapter (strings, numbers, score and status line). Graphics is deliberately not the priority; Chapter 8 comes next.

## Findings

Evidence labels as defined in `docs/main-nw/index.md`.

- **The shift lookup goes through two tables** (`PIXEL_SHIFT_TABLE`, 1,792 bytes; `PIXEL_PATTERN_TABLE`, 1,024 bytes), and one direct table of 1,792 bytes would give the same result. _Code-confirmed_: checked against direct shifting for all 896 pattern and shift combinations, and all 512 pattern entries are used; the check runs as `tests/test_shift_tables.py` in `a2-hires-lab`. The direct table has not been built or run.
- **The direct table would cut `COMPUTE_SHIFTED_SPRITE` from 1,824 to 1,208 cycles** (162 -> 106 per sprite row). _Code-confirmed_: counted from the code with the standard 6502 timings, not measured. Measuring both versions is a candidate task for `papple2`.
- **The sprite table is stored by byte position**: 22 blocks of 104 bytes, one block per byte position of the 11 rows x 2 bytes. _Code-confirmed_. That this layout exists to avoid a multiplication by 22 on every sprite draw is _Inferred_.
- **`PIXEL_SHIFT_TABLE` and `PIXEL_PATTERN_TABLE` are reached only through addresses the routine writes into its own instructions**, which is why `main.pdf` lists them as never used. _Code-confirmed_.
- **A pixel's colour depends on whether it lands on an odd or even screen column**, so a sprite moved by an odd number of columns swaps blue and orange. _Code-confirmed_ as XekriRedmane's rule in 3.1. The `a2-hires-lab` rendering is a model of the video circuit, not a run of the game; checking it against `papple2` output would make it _Observed_.

## Open questions

1. **Does the cost of `COMPUTE_SHIFTED_SPRITE` affect game speed?** _Inferred_ that it might: `DRAW_SPRITE`, `DRAW_SPRITE_AT_PIXEL_COORDS` and `ERASE_SPRITE_AT_PIXEL_COORDS` all call it, so it runs whenever one of them draws or erases a sprite. To be checked when Chapter 8 shows how the game loop is timed.
2. **Why does the game use two tables?** _Unresolved_. `a2-hires-lab` offers two hypotheses: the table generator produced the 512 unique patterns first and pointed into them, or the reduction from 896 cases to 512 patterns looked like a saving, although the two-byte pointers cost as much as the result bytes. The second is the reasoning that started the `a2-hires-lab` analysis in the first place.
3. **How does `DRAW_SPRITE` merge a shifted sprite into the screen with `PIXEL_MASK0` and `PIXEL_MASK1`?** Not researched here or in `a2-hires-lab`, whose screen placement simply overwrites.

## Links

- `a2-hires-lab` (<https://github.com/fschuhi/a2-hires-lab>), README sections:
  - [The colour model](https://github.com/fschuhi/a2-hires-lab#the-colour-model)
  - [Sprite Table Memory Layout](https://github.com/fschuhi/a2-hires-lab#sprite-table-memory-layout)
  - [The Shift Engine](https://github.com/fschuhi/a2-hires-lab#the-shift-engine)
  - [Architectural Analysis: The Indirection Mystery & Direct Table Optimization](https://github.com/fschuhi/a2-hires-lab#architectural-analysis-the-indirection-mystery--direct-table-optimization)
  - [Screen Memory and the Hires Screen](https://github.com/fschuhi/a2-hires-lab#screen-memory-and-the-hires-screen)
- Jeffrey Stanton, _Apple Graphics & Arcade Game Design_ (The Book Company, 1982), for the background on Apple II hi-res colour.

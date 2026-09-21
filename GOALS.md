# a2-lode-runner -- Goals and Roadmap

(Note: "I" in the following paragraphs refer to the user, "you" to you as the AI model.)

**Charter:** This file answers: where is the project going, in what order, and what happens next. It holds the strategic vision, the phased roadmap, and goals that need a strategy discussion before they are actionable. The _Current Session Pointer_ below is the single canonical "where we are / what's next" -- keep it to a few lines, update it, don't grow it; `FIRST_PROMPT.md` sends the reader here first. Concrete, startable work lives in `TODO.md`; the resolved-work record lives in `HISTORY.md` (on the heap, out of the per-session dump); architecture, contract, and settled decisions live in `README.md`.

---

## 📍 Current Session Pointer

### Where we are

New direction documented: the project focuses on the Apple II original and on a platform-neutral Core Game Spec, and Godot is optional. The repo is cleaned up, licensed, and ready to go public.

### What's next

- Check public repo, then the checklist in `TODO.md` under "Publication", particularly GitHub Pages.
- Then Chapter 8 (Game play): define the bounded research task; the placeholder is in `TODO.md`.

---

## 🎯 Strategic vision

Understand the original Apple II version of Lode Runner deeply enough to explain its implementation and to describe its behavior precisely, in a platform-neutral Core Game Spec.

The project has two equally legitimate outcomes:

1. A durable body of research explaining how the original program works.
2. The Core Game Spec, `docs/core-game-spec.md`: a platform-neutral description of the game mechanics, precise enough that a faithful version of the game can be implemented from it without reading the 6502 code.

The focus is the Apple II original. A Godot version is optional (see "Optional: Godot" below); the Core Game Spec is written with such an implementation in mind, so that it stays concrete and usable.

The research should preserve the distinction between understanding an Apple II implementation and reproducing its player-visible results. Hardware-specific techniques are important evidence, but a reimplementation should reproduce them only when they contribute to gameplay, timing, appearance, or another intentional project goal.

---

## Research: understand the original program

Study `main.nw` incrementally, reading it through the HTML research browser (`research/build/index.html`) and `main.pdf`, and using the original manual, the reference disk image, AppleWin, and later `papple2` where appropriate.

For each area, determine:

- What the source currently does
- Which chunks and assembly symbols own the behavior
- Which data and memory regions it relies on
- Where it sits in runtime order
- What player-visible behavior it creates
- Which Apple II constraints shaped the implementation
- Which findings affect fidelity or solvability
- Which questions remain unresolved

The analysis should build and maintain several connected views:

- Chapter and chunk map
- Identifier definition/use relationships
- Apple II memory map
- Runtime and update order
- Shared mutable state
- Level and static-data formats
- Player movement state machine
- Guard movement, chase behavior, and scheduling
- Digging, holes, regeneration, trapping, and resurrection
- Collision and interaction order
- Graphics and sprite composition
- Level progression, scoring, lives, and death
- Timing relationships that affect gameplay

Research should proceed in digestible slices. Cross-chapter conclusions should be promoted into dedicated artifacts rather than rediscovered repeatedly.

**Done when** the notes under `docs/main-nw/` document enough behavior to specify and test:

- level initialization
- player movement and collision
- climbing, falling, and rope traversal
- digging and hole regeneration
- gold collection
- hidden exit-ladder activation
- player death and level restart
- level completion and progression
- guard movement and decision-making
- guard interactions with gold, holes, and the player

Complete documentation of sound, high scores, the level editor, and Apple II disk internals is not required to finish this phase.

---

## Core Game Spec: describe the game

Turn confirmed research findings into the Core Game Spec, `docs/core-game-spec.md`.

The spec is platform-neutral. Someone implementing the game on any platform should be able to determine what the game must do without reconstructing the answer from the entire reverse-engineering narrative.

The spec should cover at least:

- The 28 by 16 logical level
- Tile and entity meanings
- Player movement and falling
- Guard movement and chase decisions
- Exact relative player and guard timing
- Digging eligibility and sequencing
- Hole lifetime and regeneration
- Gold collection, carrying, dropping, and recovery
- Player, guard, terrain, and gold interactions
- Collision and update ordering
- Death, lives, scoring, and level completion
- Level data and progression
- Known original quirks or bugs
- Fidelity decisions for behavior that is ambiguous or hardware-dependent

Important claims should retain links back to their evidence in the research notes.

To keep the spec directly usable for an implementation (Godot or otherwise), it should prefer:

- update order stated as an explicit sequence of steps per game tick, not as prose;
- timing expressed in ticks of the original game loop, not in seconds;
- state described as plain data (fields and their allowed values), not as Apple II memory addresses -- the addresses belong in the research notes;
- level data in a format that Python and Godot can both read directly, such as JSON.

---

## `papple2` as a research instrument

`papple2` is a small Apple II emulator in Python, built for stopping, inspecting, rewinding, and scripting a running program. It could take the research closer to the running code:

- letting the original routines load a level and reading the filled buffers, as a cross-check for the level extractor in `TODO.md`;
- stepping through a subroutine to confirm or refute a reading of the source;
- counting cycles where relative timing matters for the Core Game Spec.

Not started. Before it becomes a startable `TODO.md` item, it needs a strategy discussion: how to get the Lode Runner binary into `papple2`, which first question it should answer, and where the glue code lives.

---

## Supporting tools

Small Python tools may be created when they provide concrete research value. The ones in `TODO.md` under "Tools" are the approved ones.

Further tools should be proposed in response to demonstrated research friction. Possible areas include chunk graphs, identifier-use reports, memory-map extraction, call graphs, runtime traces, and comparisons between decoded artifacts. They should not be built merely because automation is possible.

---

## Optional: Godot

A Godot version of the game is not a project goal. If it is ever pursued, it builds on the finished Core Game Spec, follows the fidelity policy in `README.md`, and proceeds in this order:

1. **Deterministic prototype.** An explicit gameplay coordinator called from Godot's fixed update, preserving the ordering and timing contracts of the spec. First slices: load and display one original level, move the player, falling and climbing, digging and regenerating holes, one guard.
2. **Core game.** All original levels and the complete core interaction set as listed in `README.md`, with clean modern pixel art rather than Apple II video emulation.
3. **Deferred features.** Reassess the level editor, sound, attract mode, high scores, and the rest one by one, by player-visible value, research value, and cost.

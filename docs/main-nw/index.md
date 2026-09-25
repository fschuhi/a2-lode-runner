# `main.nw` Research Index

## Purpose and scope

This document is the navigation and research-orientation companion for:

- `reference/lode_runner_reveng/main.nw`, the canonical literate source;
- `reference/lode_runner_reveng/main.pdf`, its woven and rendered reading view.

It is not a replacement for either source artifact, a complete technical analysis, or an implementation specification.

Its purposes are to:

1. explain the Noweb conventions used by `main.nw`;
2. map the document's chapters and major composition chunks;
3. explain how to navigate the generated material in `main.pdf`;
4. record research status and planned note locations; and
5. define a practical workflow for future source analysis.

Substantive findings belong in dedicated chapter notes or cross-cutting research artifacts, not here. The "where we are / what's next" pointer lives in `GOALS.md`, not here.

---

## Source artifacts and authority

Use the source materials according to the question being answered.

| Artifact | Primary purpose |
| --- | --- |
| Original game in AppleWin | Authority for observable behavior, timing, and interaction results |
| Original manual | Authority for documented player-facing intent |
| `main.nw` | Authority for source text, named chunk structure, source ordering, and implementation evidence |
| `main.pdf` | Woven reading view, rendered diagrams, chunk continuation navigation, and generated indexes |
| Original disk image | Authority for original stored binary and level data |

The project evidence vocabulary is:

- **Manual** — directly stated in the original documentation.
- **Code-confirmed** — supported by `main.nw` or `main.pdf`.
- **Observed** — reproduced in AppleWin or another approved emulator setup.
- **Inferred** — a reasoned conclusion from incomplete evidence.
- **Unresolved** — needs more evidence.

The original game remains the final authority when source interpretation and observed behavior differ.

---

## What this index owns

This index owns:

- source-navigation conventions;
- an orientation map of the major source sections;
- research status at a high level;
- planned note paths and cross-cutting artifact candidates; and
- a practical workflow for source excerpts.

This index does **not** own:

- a full memory map;
- definitive runtime ordering;
- detailed game-mechanics findings;
- an engine-neutral behavioral specification;
- a Godot implementation plan; or
- the level extractor and catalog (see [`06-levels.md`](06-levels.md)).

Those belong in dedicated research artifacts once supported by evidence.

---

## How to read the Noweb notation used here

### Narrative text, inline code, and source references

`main.nw` is a literate-programming document: explanatory prose and assembly source are interleaved.

Its chapter order is primarily explanatory. It is not necessarily:

- execution order;
- final assembly order; or
- Apple II memory-address order.

When analyzing behavior, keep those distinct structures separate.

### Named chunk definitions

A named chunk definition has the form:

```text
<<chunk name>>=
    ... source text ...
@
```

The chunk name is a literate-programming name. It may describe:

- a routine;
- a routine fragment;
- a table;
- a group of constants;
- an assembler-layout region; or
- a high-level conceptual step.

For example, `<<load level>>` is a behavior-facing grouping, while the assembly within it contains concrete labels and instructions.

### Chunk references and nested composition

A named chunk can be included within another chunk:

```text
<<another chunk>>
```

This means that the referenced chunk's content is inserted at that point when the document is tangled into assembly source.

Chunks can nest. Therefore, reading only the visible text around one chunk definition may not reveal all code that participates in the behavior.

### Repeated definitions and chunk continuations

The same chunk name can appear in multiple definitions:

```text
<<level draw routine>>=
    ... first fragment ...
@

<<level draw routine>>=
    ... later fragment ...
@
```

These definitions are continuations. Their content is combined in source order.

**Research rule:** when studying a named chunk, identify and read all of its continuations before treating it as understood.

### The root chunk and tangling order

The root output chunk is `<<*>>`. It gives the top-level order of the final tangled assembly source:

```text
<<*>>=
    PROCESSOR 6502
    <<defines>>
    <<tables>>
    <<routines>>
    <<relocation routine>>
    <<dead code>>
    <<zeroed areas>>
    <<garbage area>>
    <<dos>>
@
```

This composition order matters for reconstructing the program, but it is not the same as runtime execution order.

### `%def` identifier declarations

Lines such as:

```text
@ %def DRAW_LEVEL_PAGE2
```

provide identifier-definition information to Noweb for the woven index.

They are not executable assembly instructions.

They are useful navigation evidence, but not a formal or necessarily exhaustive symbol table. Verify important conclusions against the actual surrounding source.

### `ORG` and the separate memory-layout view

`ORG` directives place code or data at specific Apple II memory addresses.

This creates a second important view of the program:

1. **Narrative and chunk composition:** how the document teaches and assembles the program.
2. **Memory layout:** where code, tables, graphics pages, DOS, and initialized data reside.

Do not assume that nearby prose corresponds to nearby memory or immediate runtime control flow.

---

## Noweb glossary

The words used throughout the research notes, in one place.

- **Literate program**: a document that mixes explanation for humans with source code for a machine. `main.nw` is one.
- **Chunk**: a named piece of code inside the document, written as `<<name>>=` ... `@`. The name is chosen by the author and describes what the code is for.
- **Chunk reference**: the name of a chunk written inside another chunk, as `<<name>>`. It means "insert that chunk's code here".
- **Definition**: one `<<name>>=` block. A chunk may have several.
- **Continuation**: a second or later definition of a chunk name. All definitions of one name are joined in document order to form the complete chunk.
- **Root chunk**: the chunk from which everything else is reached by references. Here it is `<<*>>`.
- **Tangle**: the step that follows the references from the root chunk and produces the plain assembly source. The result is what the assembler sees.
- **Weave**: the step that produces the human-readable document, `main.pdf`, with chunk numbers, continuation arrows, and the generated indexes.
- **`%def`**: a marker after a chunk that tells the weaver which identifiers the chunk defines, so they appear in the woven index.
- **Defined Chunks / Index**: the two generated chapters at the end of `main.pdf`. The first lists chunks, the second lists identifiers.

For more: search *noweb literate programming Ramsey* -- the original tool documentation is short.

---

## How to navigate `main.pdf`

### Woven chunk numbers and continuation markers

The PDF renders each Noweb code fragment with generated navigation information. A heading similar to:

```text
77 <<level draw routine 77>>=(278) 81a ->
```

identifies a chunk fragment and its relationship to other fragments.

A heading containing `+=`, such as:

```text
81a <<level draw routine 77>>+= (278) <- 77 81b ->
```

means that this is a continuation of the same named chunk.

The arrows identify preceding and following continuation fragments. Use them, along with the Defined Chunks index, to reconstruct distributed chunks.

### “Defines” and “Uses” footers

Many PDF code blocks include generated footers such as:

- `Defines: ...`
- `Uses: ...`

Use these as navigation aids:

- **Defines** identifies symbols associated with the current chunk.
- **Uses** identifies symbols or chunks referenced from it.

These footers do not establish semantics. In particular, they do not by themselves tell whether a symbol is read, written, compared, called, or used only indirectly.

### Chapter 14: Defined Chunks

The PDF's **Defined Chunks** chapter is the primary reverse index for named chunks.

Use it to answer questions such as:

- Where is `<<move player>>` defined?
- Does `<<level draw routine>>` have continuations?
- Which parent chunk uses `<<uncompress level data>>`?
- Where is a small helper chunk included?

### Chapter 15: Identifier index

The PDF's identifier index is the primary reverse index for assembly labels and other declared identifiers.

Use it to locate cross-cutting state and behavior, for example:

- all locations mentioning `GOLD_COUNT`;
- definitions and uses of `PLAYER_Y_ADJ`;
- references to `PTR1` and `PTR2`; or
- locations that access `GAME_MODE`.

Treat index hits as starting points for source reading, not as complete behavior analysis.

### When to use the PDF instead of the `.nw` source

Use `main.pdf` when:

- a chunk's continuation order is unclear;
- its generated `Defines` or `Uses` list is useful;
- Chapter 14 or Chapter 15 can locate a dependency;
- a diagram, figure, or rendered code layout matters;
- a durable PDF-page locator is useful in a research note.

Use `main.nw` when:

- exact source text matters;
- literal chunk boundaries or source ordering need verification;
- `%def` declarations need inspection;
- source excerpts are being prepared; or
- the relationship between prose and raw Noweb markup is relevant.

---

## Top-level assembly composition

### Root chunk

The final assembly source is composed through the root chunk:

```text
<<*>>
  PROCESSOR 6502
  <<defines>>
  <<tables>>
  <<routines>>
  <<relocation routine>>
  <<dead code>>
  <<zeroed areas>>
  <<garbage area>>
  <<dos>>
```

### Aggregator chunks

| Chunk | Role |
| --- | --- |
| `<<defines>>` | Constants, memory locations, aliases, and related assembler declarations |
| `<<tables>>` | Static data, lookup tables, sprites, level-related data, and other initialized assets |
| `<<routines>>` | Main executable assembly, collected from many explanatory chapters |
| `<<dead code>>` | Disassembled code believed not to be reachable in ordinary gameplay |

These aggregators are defined incrementally throughout the document.

### Other top-level components

| Chunk | Role |
| --- | --- |
| `<<relocation routine>>` | Code related to relocating the loaded program image |
| `<<zeroed areas>>` | Memory regions initialized or reserved as zeroed storage |
| `<<garbage area>>` | A region identified by the source as non-meaningful or unexplained data |
| `<<dos>>` | DOS-related code and data, including fixed placement in the memory image |

---

## Source chapter inventory and research status

This inventory tracks focused research into the chapters of `main.nw`. It is a navigation and prioritization aid, not a requirement to study the source strictly in chapter order.

Status meanings:

- **Complete** — a durable chapter note records the relevant behavior, evidence, conclusions, and remaining questions.
- **Partial** — the chapter has been consulted for another investigation, but has not received a complete focused pass.
- **Surveyed** — its broad purpose and location are known from the initial source orientation.
- **Queued** — selected as an upcoming focused research slice.
- **Deferred** — intentionally postponed because it is not currently on the critical path.
- **Not started** — no focused research has yet been recorded.

| Chapter | Title | Status | Durable note or current role |
|---:|---|---|---|
| 1 | Lode Runner | Surveyed | Provides the game overview and explains the purpose of the reverse-engineering document. No separate chapter note is currently needed. |
| 2 | Programming techniques | Surveyed | Introduces recurring 6502 techniques, DOS context, shared scratch storage, and source conventions. Consult as needed while studying behavioral chapters. |
| 3 | Apple II Graphics | Partial | See [`03-graphics.md`](03-graphics.md). Sections 3.1 to 3.3 carry annotations with the `a2-hires-lab` findings: sprite colours, the sprite table layout, and the two-stage shift lookup with a direct 1,792-byte alternative. Section 3.4 (memory-mapped graphics) and the rest are not researched. Apple II implementation research, not an input to the Core Game Spec; not the next priority. |
| 4 | Sound | Not started | Self-contained sound subsystem. It can be deferred until core gameplay behavior is understood. |
| 5 | Input | Partial | Level-number entry and input-related state were encountered while tracing level selection. General joystick, keyboard, and control behavior still requires focused study. |
| 6 | Levels | Complete | See [`06-levels.md`](06-levels.md). Covers board dimensions, packed sector data, cell values, disk-level addressing, attract-mode data, decoding, initialization markers, hidden ladders, validation, and the proposed portable level contract. The level catalog, all 150 levels as the level editor shows them, is at the start of Chapter 6 in the HTML research browser. |
| 7 | High scores | Deferred | Important for eventual product completeness but largely independent of the core level and gameplay model. |
| 8 | Game play | **Queued next** | Recommended next focused chapter. It contains the central game loop and player-facing mechanics that consume the level state documented in Chapter 6. |
| 9 | Guard AI | Queued after Chapter 8 | Depends on the board, movement, collision, timing, and actor-state concepts established by the level and gameplay investigations. |
| 10 | Disk routines | Partial | The interface used to read and write raw level sectors was examined for Chapter 6. A complete RWTS or DOS reconstruction is not currently required for the portable implementation. |
| 11 | Level editor | Partial | Compression and level-saving behavior were consulted while checking the level representation. The complete editor workflow is deferred until loading and gameplay are stable. |
| 12 | Extra data | Not started | Primarily preservation and reverse-engineering material. Low priority unless it becomes relevant to validation or byte-level reproduction. |
| 13 | The whole thing | Surveyed | Used to understand the top-level Noweb composition, chunk ordering, and the `<<*>>` root chunk. Revisit when mapping complete runtime control flow or build composition. |

### Generated reference chapters

The woven document also contains generated reference material:

| Generated chapter | Role | Research use |
|---|---|---|
| Defined Chunks | Lists Noweb chunks and their locations | Use to find chunk definitions, continuations, and composition relationships. |
| Index | Lists identifiers and their references | Use to trace routines, variables, constants, tables, and cross-chapter dependencies. |

These generated chapters are navigation tools rather than behavioral source chapters and therefore do not receive research-status labels.

### Recommended next focused chapter: Chapter 8, Game play

Chapter 8 should be studied next rather than continuing mechanically to Chapter 7.

Chapter 6 established the static and initialization-side level contract:

- the 28-by-16 board;
- stored cell meanings;
- source and runtime board distinctions;
- player and guard start markers;
- gold initialization;
- hidden exit-ladder locations;
- loading and restart inputs.

The next useful question is how the running game consumes and mutates that state. Chapter 8 is expected to establish the central behavioral contract for:

- the main game loop;
- frame or timer processing;
- player state and movement;
- collision and support checks;
- climbing, falling, and rope traversal;
- digging;
- holes and regeneration;
- gold collection;
- death and restart;
- level completion;
- the transition to the next level;
- the boundary between shared gameplay rules and guard-specific behavior.

This creates a natural research sequence:

1. **Chapter 6 — Levels:** establish the world and its initial state.
2. **Chapter 8 — Game play:** establish the main simulation and player interaction with that world.
3. **Chapter 9 — Guard AI:** establish guard decisions and behavior within the same simulation.
4. Revisit Chapters 3, 5, 7, 10, and 11 when their subsystems become implementation dependencies.

Chapter 7 is not being discarded. High scores are simply outside the immediate dependency chain from extracted level data to a reproducible gameplay simulation.

### Proposed Chapter 8 artifact

The focused Chapter 8 pass should produce:

```text
docs/main-nw/08-game-play.md
```

Its target is a portable behavioral specification rather than a line-by-line translation of the 6502 code.

At minimum, it should identify:

- the top-level gameplay loop and its major phases;
- persistent versus per-level versus per-life state;
- timer ownership and update order;
- player movement states and transition rules;
- collision queries against the active and background boards;
- gold-collection effects;
- digging eligibility and hole lifecycle;
- death, restart, and level-completion transitions;
- calls into guard-specific logic that should be deferred to Chapter 9;
- Apple II implementation details that need not survive in a portable version;
- unresolved questions requiring emulator observation or small experiments.

The resulting note should make it possible to design a deterministic, headless gameplay model before committing to presentation-layer or engine-specific decisions.

---

## Planned chapter notes and cross-cutting artifacts

### Chapter notes

Future chapter notes should generally record:

1. scope and source locations;
2. terminology and relevant state;
3. verified behavior and implementation findings;
4. dependencies and callers or callees;
5. evidence classification;
6. unresolved questions;
7. implications for the engine-neutral specification; and
8. implications for the Godot implementation, if appropriate.

They should not force a uniform structure where the source material does not support one. A short, evidence-focused note is preferable to a broad but speculative one.

### Cross-cutting artifacts

The following are possible future artifacts, not commitments to create every file:

| Candidate artifact | Intended purpose |
| --- | --- |
| `docs/main-nw/memory-map.md` | Memory regions, zero-page aliases, fixed addresses, and ownership questions |
| `docs/main-nw/runtime-order.md` | Verified frame/update sequencing and timing-sensitive ordering |
| `docs/main-nw/shared-state.md` | Cross-cutting global state, readers, writers, and lifecycle |
| `docs/main-nw/level-format.md` | Decoding contract for stored level data and logical board representation |
| `docs/main-nw/level-catalog.md` | Research notes and edge-case annotations for the 150 shipped levels |
| `docs/core-game-spec.md` | Engine-neutral behavioral specification for the core playable game |

Create these only when dedicated notes would reduce repeated work or make a research conclusion materially clearer.

---

## Practical workflow for source analysis

### Do not prepare manual excerpt packets

No manual extraction of Noweb chunks is expected from the project owner.

The source is large, and identifying complete chunks, continuations, nested chunks, relevant definitions, and caller context requires familiarity with the document's conventions. That is research work to be performed together, not an administrative prerequisite.

### What to upload for a focused chapter session

1. the standard `filesdump.txt` (project-control documents and this index);
2. the chapter slice, `tmp/main-chNN.nw`, produced by `scripts/nwtool.py chapter N`; and
3. the generated `docs/main-nw/main-index.md`, produced by `scripts/nwtool.py index` (once it is committed it can be added to `manifest.lst` for research sessions instead).

Upload the full `main.nw` only when a question crosses chapters, and `main.pdf` only when a rendered diagram or figure matters. Never upload `main.nw` both as a file and inside `filesdump.txt`. Until `scripts/nwtool.py` exists (see `TODO.md`, "Noweb tooling"), upload `main.nw` instead of items 2 and 3.

### How a focused chapter session proceeds

1. locate the relevant chapter sections and named chunks;
2. identify all required continuations and immediate nested chunks;
3. identify necessary constants, tables, shared state, and caller context;
4. record evidence-based findings in the chapter note;
5. update the chapter table above; and
   6. update the session pointer in `GOALS.md`.

### Source-extraction tooling

The token cost of uploading `main.nw` for every research session justified a small extraction tool; it is defined in `TODO.md` under "Tools" as "Noweb tooling". Further automation (dependency lists, `.nw` to PDF page correlation) waits for demonstrated need.

---

## Level extractor

The 150 shipped levels are a research corpus in their own right: individual layouts expose mechanics edge cases that are hard to find by ordinary play. `scripts/level_extractor.py` decodes them from the track files in `reference/lode_runner_reveng/disk/`; `scripts/level_images.py` and `scripts/level_catalog.py` show them as a catalog at the start of Chapter 6 in the HTML research browser (<https://fschuhi.github.io/a2-lode-runner/levels.html>). The decoding contract and the findings, among them the three levels with six guards, are in [`06-levels.md`](06-levels.md).

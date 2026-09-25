# Chapter 6: Levels

## Purpose

Chapter 6 describes how Lode Runner obtains, decodes, and initializes a level.

The main result needed by this project is a portable **level-data contract**: a description of the stored data and its interpretation that can later be implemented without reproducing the original Apple II disk-access or rendering code.

This document covers:

- the dimensions and coordinate system of a level;
- the meanings of the stored cell values;
- the packed level-data format;
- the relationship between levels, sectors, tracks, and the disk image;
- the distinction between disk levels and the embedded attract-mode levels;
- the logical board representation;
- initialization performed after decoding;
- important shared state associated with level loading;
- open questions that do not block extraction.

The extraction utility is `scripts/level_extractor.py`; `scripts/level_images.py` and `scripts/level_catalog.py` turn its output into the level catalog at the start of Chapter 6 in the HTML research browser. See "Level extractor and catalog" below for how they work and what they found.

## Sources and evidence

This document is based on:

- Chapter 6 of `main.nw`;
- the corresponding woven presentation in `main.pdf`;
- constants and routines referenced by the level-loading code;
- the extracted track files under `disk/`;
- `data/Lode_Runner_1983_Broderbund_cr_Reset_Vector.do`;
- comparison with the running game in normal play and attract mode.

The most important routines and chunks examined were:

- `LOAD_LEVEL`;
- `ACCESS_COMPRESSED_LEVEL_DATA`;
- `DRAW_LEVEL_PAGE2`;
- `ENABLE_NEXT_LEVEL_LADDERS`;
- `<<load level>>`;
- `<<uncompress level data>>`;
- `<<uncompress row data>>`;
- `<<next compressed row for row_loop>>`;
- `<<load compressed level data 108>>`.

The Noweb source is organized as named chunks. A chunk may contain references to other chunks, so the complete routine is assembled hierarchically. The generated assembler source is the **tangled** form of those chunks. This terminology should also be introduced in the general explanation of Noweb in `index.md`.

## Terminology

This document distinguishes three related concepts:

- A **stored level** is the packed representation found in a disk sector or embedded data page.
- A **logical board** is the decoded 28-by-16 grid of cell values.
- A **runtime level** is the logical board plus derived state such as the player position, guard positions, gold count, and hidden exit-ladder locations.

The stored data should not be treated as a direct image of everything that is rendered during play. Some stored values are initialization markers rather than persistent terrain.

## Board dimensions and coordinates

A level contains:

- **28 columns**;
- **16 rows**;
- zero-based columns `0` through `27`;
- zero-based rows `0` through `15`;
- an origin at the upper-left corner;
- rows ordered from top to bottom;
- cells ordered from left to right within each row.

The corresponding maximum-coordinate constants in the original program are equivalent to:

```asm
MAX_GAME_COL EQU #27
MAX_GAME_ROW EQU #15
```

The maximum values are inclusive, so the board dimensions are 28 by 16.

A complete board therefore contains:

```text
28 columns × 16 rows = 448 cells
```

Coordinates in this documentation are written as `(row, column)` unless stated otherwise. For example, `(0, 0)` is the upper-left cell.

## Stored cell values

Each stored cell is represented by a four-bit value. Values `0` through `9` are used as entries in the game's sprite or object table.

| Value | Suggested portable name | Meaning |
|---:|---|---|
| `0` | `EMPTY` | Empty space |
| `1` | `BRICK` | Diggable brick |
| `2` | `SOLID` | Indestructible block |
| `3` | `LADDER` | Permanently visible ladder |
| `4` | `BAR` | Hand-to-hand bar |
| `5` | `TRAP` | False brick or trap |
| `6` | `EXIT_LADDER` | Initially hidden ladder revealed after all gold is collected |
| `7` | `GOLD` | Gold collectible |
| `8` | `GUARD` | Guard starting position |
| `9` | `PLAYER` | Player starting position |

There are nine non-empty stored object types in addition to empty space.

The names above are portable names for the extraction and later implementation work. They do not need to reproduce every original assembler symbol exactly.

### Invalid values

Four bits can represent values `0` through `15`, but only `0` through `9` are valid level values.

The original decoding code checks the value against 10. Values at or above 10 are converted to empty:

```asm
CMP #10
BCC .valid
LDA #SPRITE_EMPTY
```

A new extraction utility should preferably distinguish between:

1. the original runtime behavior, which treats invalid values as empty; and
2. validation behavior, which reports invalid values as malformed source data.

The default extractor should report invalid values with their level, row, column, source byte, and nibble. It may still provide a compatibility option that replaces them with `EMPTY`.

## Packed board representation

Two horizontally adjacent cells are packed into each byte:

- the **low nibble** contains the left cell;
- the **high nibble** contains the right cell.

For a packed byte `b`:

```text
left_cell  = b & 0x0f
right_cell = (b >> 4) & 0x0f
```

The low nibble must therefore be decoded first.

For example:

```text
packed byte: $06

low nibble:  $6 -> first column
high nibble: $0 -> second column
```

Although the hexadecimal byte is written as `06`, its spatial interpretation is `6, 0`, not `0, 6`.

In the original routine, `LEVEL_DATA_INDEX` identifies the current packed source byte. The index advances only after the high nibble has been used. Conceptually, the decoder behaves as follows:

```python
for packed_byte in packed_row:
    output.append(packed_byte & 0x0f)
    output.append((packed_byte >> 4) & 0x0f)
```

The original code obtains the high nibble by shifting the byte right four times. This moves bits 4–7 into bits 0–3 so the result can be used as a value in the `0`–`9` object table.

## Row and board sizes

Each row contains 28 cells. Since each byte contains two cells, one packed row occupies:

```text
28 cells / 2 cells per byte = 14 bytes
```

The complete packed board occupies:

```text
14 bytes per row × 16 rows = 224 bytes
```

The decoder must treat the source bytes as one continuous sequence and divide them into groups of 14 bytes per logical row.

The formatting in files such as `disk/track_03.asm` is not the logical row format. Those files display 16 bytes on each `HEX` line for readability. Logical level rows therefore cross the displayed line boundaries.

The correct procedure is:

1. concatenate all bytes belonging to the sector;
2. take the first 224 bytes;
3. divide those bytes into 16 groups of 14;
4. decode each group into 28 cells.

## Sector representation

A disk level occupies one 256-byte sector.

Only the first 224 bytes are consumed by the board decoder:

```text
bytes   0–223: packed 28 × 16 board
bytes 224–255: not consumed by the board decoder
```

The final 32 bytes vary in the extracted data. Some sectors contain zeroes there, while others contain values such as `$FF`. They must not automatically be described as meaningful level cells.

Their original purpose is not required for level extraction and remains an open question. A conservative extractor should preserve them as unparsed trailing data in case they are useful later.

A suitable extracted record may therefore contain both:

```text
board_data:    224 bytes
trailing_data:  32 bytes
```

Only `board_data` participates in the 28-by-16 cell decoding contract.

## Disk levels and disk locations

`DISK_LEVEL_LOC` is a variable stored at memory address `$96`.

The instruction:

```asm
LDA DISK_LEVEL_LOC
```

loads the value currently stored in that variable. It does not load the literal number `$96`.

The value is a zero-based disk-level location:

| Player-facing level | `DISK_LEVEL_LOC` |
|---:|---:|
| 1 | 0 |
| 2 | 1 |
| 16 | 15 |
| 17 | 16 |

Normal levels begin on track 3. There are 16 sectors per track and one level per sector.

The mapping shown by `ACCESS_COMPRESSED_LEVEL_DATA` is:

```text
track  = 3 + floor(DISK_LEVEL_LOC / 16)
sector = DISK_LEVEL_LOC modulo 16
```

Equivalent Python is:

```python
track = 3 + level_index // 16
sector = level_index % 16
```

Examples:

| Player-facing level | Zero-based index | Track | Sector |
|---:|---:|---:|---:|
| 1 | 0 | `$03` | `$0` |
| 16 | 15 | `$03` | `$F` |
| 17 | 16 | `$04` | `$0` |

Only one track number and one sector number are supplied to the disk-reading code because each selected level occupies exactly one sector.

The level number is selected elsewhere. `ACCESS_COMPRESSED_LEVEL_DATA` receives the already selected zero-based location through `DISK_LEVEL_LOC` and translates it into a track and sector.

## Extracted track files

The repository contains files such as:

```text
disk/track_03.asm
```

`track_03.asm` is identified as containing levels 0 through 15. It contains one labeled section for each sector:

```asm
; Track $03, sector $0
    HEX ...

; Track $03, sector $1
    HEX ...
```

Each sector contains 256 bytes, formatted as sixteen `HEX` lines of sixteen bytes each.

For example, sector `$0` is the stored data for player-facing level 1. Once its first 224 bytes are regrouped into fourteen-byte rows and nibble-decoded, recognizable features correspond to the normal first level. This includes a gold value at the expected board position.

The track files are convenient human-readable evidence and can be used to validate an extractor.

They are the extractor's input. They are committed to the repository, so the GitHub Pages build can regenerate the level catalog, while the `.do` image is local only. The parser needed is small: a sector label, followed by `HEX` lines.

The file header of `track_0c.asm` names a second kind of content: "levels 144-149 and leftover mastering data". See "Level extractor and catalog" below.

## Direct disk-image extraction

Reading the `.do` image directly is a separate, lower-priority investigation (`TODO.md`). Its input would be:

```text
data/Lode_Runner_1983_Broderbund_cr_Reset_Vector.do
```

The `.do` image contains fixed-size tracks and sectors:

```text
16 sectors per track
256 bytes per sector
4096 bytes per track
```

For a DOS-order image, the candidate byte offset for a track and sector is:

```text
offset = (track * 16 + sector) * 256
```

The extractor must not rely on this formula without validation. It should first compare the bytes obtained for track `$03`, sector `$0` with the bytes listed under the corresponding label in `disk/track_03.asm`.

Once this comparison succeeds, the `.do` image and the track files can be checked against each other; the output of `scripts/level_extractor.py` is the reference.

If the comparison fails, the script must investigate sector ordering rather than silently producing levels from the wrong offsets.

## Disk levels versus embedded attract-mode levels

The program supports two different sources of compressed level data:

1. normal levels read from disk;
2. levels embedded in the program image for attract-mode demonstrations.

`ACCESS_COMPRESSED_LEVEL_DATA` selects the source according to `GAME_MODE`.

The embedded data is associated with labels such as:

```asm
LEVEL1_DATA
LEVEL2_DATA
LEVEL3_DATA
```

These names refer to embedded demonstration levels. They do not necessarily correspond to player-facing disk levels 1, 2, and 3.

This distinction was verified by observing the game:

- normal disk level 1 matches track `$03`, sector `$0`;
- attract-mode “level 1” has a different layout;
- the embedded level begins with packed byte `$06`;
- its value `6` at `(0, 0)` becomes an exit ladder after all gold is collected.

It is therefore incorrect to validate `LEVEL1_DATA` by comparing it with normal disk level 1.

Documentation and tools should use explicit names such as:

- `disk_level_001`;
- `attract_level_1`;

rather than assuming that both uses of “level 1” identify the same board.

## Logical board representation

A portable representation should first decode the stored data into a plain 16-by-28 matrix of integer values:

```python
board[row][column]
```

Required invariants are:

```text
len(board) == 16
len(board[row]) == 28
0 <= board[row][column] <= 9
```

The matrix should preserve the stored values before runtime interpretation. In particular:

- `EXIT_LADDER` should remain distinguishable from `EMPTY`;
- `PLAYER` should remain present as a start marker;
- `GUARD` should remain present as a start marker;
- `TRAP` should remain distinguishable from an ordinary brick.

This source board is useful for:

- validation;
- documentation;
- map visualization;
- comparing the extracted data with the original;
- later construction of a runtime board;
- preserving enough information to reproduce initialization.

A future implementation should not be forced to recover start markers from already initialized runtime state.

## Source board and runtime board

It is useful to separate immutable source data from mutable game state.

A portable design can use:

```text
LevelDefinition
    source cells
    level identity
    source track and sector
    unparsed trailing bytes

LevelState
    mutable terrain or cells
    player state
    guard states
    remaining gold
    hidden exit-ladder positions
    other transient gameplay state
```

`LevelDefinition` represents what was extracted from the disk. `LevelState` is created whenever the level begins or restarts.

This separation avoids modifying the canonical extracted level when:

- gold is collected;
- bricks are dug;
- holes regenerate;
- guards move;
- hidden ladders are revealed;
- the player dies and the level is restarted.

## Initialization behavior

Decoding the packed nibbles is only the first part of loading a playable level. The original code subsequently scans or draws the decoded board and derives runtime state from special values.

At a behavioral level, initialization must account for the following.

### Empty space

`EMPTY` remains an unoccupied board cell.

### Permanent terrain

The following values create persistent terrain:

- `BRICK`;
- `SOLID`;
- `LADDER`;
- `BAR`;
- `TRAP`.

A trap may initially be drawn like an ordinary brick, but its logical identity must remain available for collision and falling behavior.

### Gold

Each `GOLD` value creates a collectible and contributes to the count of gold remaining in the level.

The exit condition depends on all required gold having been collected. The initial gold count should therefore be derived from the source board rather than hard-coded.

### Hidden exit ladders

`EXIT_LADDER` marks a ladder segment that is unavailable or invisible when the level begins.

During initialization, the runtime system must retain the positions of these cells while treating them as initially hidden. After all gold has been collected, `ENABLE_NEXT_LEVEL_LADDERS` changes the corresponding runtime cells into usable, visible ladders.

This explains packed byte `$06` at the beginning of an embedded attract-mode level:

```text
row 0, column 0 = hidden exit ladder
row 0, column 1 = empty
```

The ladder is not visible at the beginning of play, but it appears at the upper-left after the gold condition is satisfied.

The portable source representation should retain value `6`. Converting it permanently to `EMPTY` during extraction would lose required information.

### Player start

`PLAYER` is a starting-position marker rather than permanent terrain.

Initialization must:

1. record the player's starting row and column;
2. create or position the player there;
3. ensure that the underlying runtime board cell has the appropriate non-player terrain state, normally empty.

A valid playable level has exactly one player start and one to five guards. The manual states this as the level editor's rule: a level with no player, more than one player, or more than five guards is rejected and the game returns to demo mode (Manual). The original loading code nevertheless contains handling for a missing player, so an extraction validator should report the number of player markers and guard markers rather than assume the rule holds, and treat any shipped level that breaks it as a finding worth recording.

For the shipped levels, the expected validation rule is normally:

```text
exactly one player start
```

Any exception should be reported and checked against the original behavior.

### Guard starts

Each `GUARD` value is a guard starting-position marker rather than permanent terrain.

Initialization must:

1. record the guard's starting row and column;
2. create a guard state for that position;
3. remove the marker from the mutable terrain representation.

There may be multiple guards, but the game places at most five. Levels 8, 80 and 113 have six guard markers on the disk, one more than the level editor allows (Manual). For every guard marker, `DRAW_LEVEL_PAGE2` compares `GUARD_COUNT` with 5 (`CPX #5`) and, once five guards are placed, draws an empty cell instead (`BCS .remove_sprite`) (Code-confirmed).

The routine scans the board backwards: from row 15 up to row 0, and in each row from column 27 to column 0. The guard it removes is therefore the topmost one, or the leftmost one if the topmost row has several. In level 8 that is the guard at row 2, column 5 (Observed in AppleWin, and on the in-game screenshots of the level collection at vgmaps.com). The same order decides the guards' slots: the first guard met, the one nearest the bottom-right corner, is stored at index 1 of `GUARD_LOCS_ROW` and `GUARD_LOCS_COL` (Code-confirmed). Whether the slot order matters during play belongs to Chapter 9.

A portable implementation that wants the original behavior must apply the same limit in the same scan order. The order in which guard markers are encountered may also matter if it determines guard numbering or update order. A portable extractor should therefore report guard starts in a fixed, documented order, for example row-major:

```text
top to bottom, then left to right
```

### Duplicate decoded storage

The original loader writes decoded values into more than one internal destination or board-related buffer. This reflects the needs of the Apple II implementation and its drawing/runtime organization.

A portable implementation does not need to reproduce the original memory layout byte for byte. It should preserve the behavioral distinction between:

- canonical decoded source data;
- mutable runtime board data;
- derived actor and level state.

## Shared state associated with loading

The chapter touches several categories of shared state.

### Selected level

`DISK_LEVEL_LOC` contains the zero-based location of the selected disk level.

It is used to derive the disk track and sector. The player-facing level number is one greater than this value when referring to the normal sequential level set.

### Game mode

`GAME_MODE` determines whether compressed data is read from disk or copied from an embedded attract-mode data page.

The selected data source must therefore be recorded when testing or documenting a level. “Level 1” alone is ambiguous.

### Compressed-data index

`LEVEL_DATA_INDEX` tracks progress through packed level bytes.

Because each byte supplies two cells, it advances after decoding the high nibble, not after every output cell.

Equivalent portable decoding should normally use direct iteration over the 224 board bytes rather than reproduce this shared index.

### Row and destination pointers

The original code establishes addresses for the current source or destination row and updates them during the row loop.

These pointers are implementation details of the 6502 version. A portable implementation may replace them with normal array indices while preserving row-major traversal.

### Gold state

Level initialization derives the amount of gold required to enable the exit ladders. Runtime collection reduces the remaining count.

The exact original variable names and display-related representation are less important than the invariant:

```text
remaining gold reaches zero
    -> reveal every hidden exit-ladder cell
```

### Player state

Loading establishes at least:

- the player's start coordinate;
- the player's current coordinate;
- the player's active or alive state.

Restarting a level should reconstruct this state from the immutable level definition.

### Guard state

Loading creates the initial set of guards from the guard markers. Each guard subsequently has mutable state not represented by the static level data.

### Exit-ladder state

The runtime must retain:

- the coordinates of every value-6 cell;
- whether the hidden ladders have been enabled.

This may be represented as a coordinate list, a separate mask, or preserved source values combined with mutable runtime cells.

## Portable decoded level record

A controlled extracted-data format should contain enough information to validate the extraction and support later applications.

A conceptual record is:

```yaml
number: 1
index: 0
source:
  image: data/Lode_Runner_1983_Broderbund_cr_Reset_Vector.do
  track: 3
  sector: 0
dimensions:
  rows: 16
  columns: 28
cells:
  - [0, 0, 0, ...]
  - [0, 7, 0, ...]
trailing_bytes:
  - 0
  - 0
player_start:
  row: 12
  column: 13
guard_starts:
  - row: 1
    column: 2
gold_positions:
  - row: 2
    column: 5
exit_ladder_positions:
  - row: 0
    column: 0
```

The exact serialization format remains to be selected. JSON is likely the most convenient controlled format because it is directly readable from Python, JavaScript, and Godot.

Derived fields such as `player_start` and `gold_positions` may be included for convenience, but `cells` remains the canonical decoded source. The extractor should calculate derived fields from `cells` so they cannot diverge manually.

## Validation rules

An extraction utility should validate at least the following:

- the disk image is large enough for every requested track and sector;
- every sector contains exactly 256 bytes;
- the board portion contains exactly 224 bytes;
- decoding produces exactly 448 cells;
- decoding produces exactly 16 rows;
- every row contains exactly 28 cells;
- every stored value is in the range `0` through `9`;
- a level has the expected number of player markers;
- guard, gold, and exit-ladder positions are collected consistently;
- track `$03`, sector `$0` matches `disk/track_03.asm`;
- normal disk level 1 is not confused with embedded attract-mode level 1.

Validation diagnostics should identify the source precisely. For example:

```text
level 1, track $03, sector $0, byte 37,
row 2, column 5: invalid cell value 12
```

## Stylized ASCII representation

For inspection and testing, a decoded level can be rendered as a fixed-width ASCII or Unicode map. `make level-ascii LEVEL=N` prints this mode, with a thin frame so that empty cells at the edges stay visible.

A simple one-character mapping is:

| Value | Character | Meaning |
|---:|:---:|---|
| `0` | space | Empty |
| `1` | `#` | Brick |
| `2` | `X` | Solid block |
| `3` | `H` | Ladder |
| `4` | `-` | Bar |
| `5` | `T` | Trap |
| `6` | `h` | Hidden exit ladder |
| `7` | `$` | Gold |
| `8` | `G` | Guard |
| `9` | `P` | Player |

For example:

```text
              h             
  $       H           G     
##########H###############  
          H                 
------    H       $         
```

The hidden exit ladder uses a different character from the permanent ladder because preserving that distinction is part of the stored-data contract.

A more stylized renderer may use multi-character cells so that bricks, solid blocks, ladders, bars, gold, guards, and the player are easier to distinguish. The extraction utility should first provide a stable one-character mode suitable for tests and diffs.

## What does not need to be reproduced

A later implementation does not need to reproduce:

- the original zero-page addresses;
- the original row-pointer arithmetic;
- the original duplicated memory buffers;
- DOS or RWTS calls;
- the exact shift loop used to obtain a high nibble;
- the assembler's local-label organization;
- the attract-mode storage layout, unless attract mode is implemented.

It must reproduce the observable contract:

- the correct 28-by-16 source board;
- the correct interpretation of values `0` through `9`;
- correct player and guard starts;
- correct gold placement and counting;
- initially hidden exit ladders;
- exit-ladder revelation after all gold is collected.

## `SUBROUTINE` and Noweb notes

`SUBROUTINE` in this source is an assembler directive, not a 6502 machine instruction.

In a construction such as:

```asm
LOAD_LEVEL:
    SUBROUTINE
```

`LOAD_LEVEL` defines the callable address, while `SUBROUTINE` establishes an assembly-time scope for local labels such as `.loop` or `.end`.

It does not:

- call a routine;
- emit a runtime instruction;
- push a return address;
- preserve registers;
- add runtime cost.

The actual runtime call and return use:

```asm
JSR LOAD_LEVEL
RTS
```

The Noweb source introduces another layer of organization:

- a **chunk** is a named piece of source or documentation;
- a **chunk reference** inserts or composes another named chunk;
- **tangling** produces the assembler-oriented source;
- **weaving** produces the human-readable documentation;
- nested chunk references form a hierarchical composition.

These concepts belong in the general Noweb explanation in `index.md`, but they are particularly visible in the construction of `LOAD_LEVEL`.

## Level extractor and catalog

Three scripts in `scripts/` implement the contract of this document, each with its own tests:

- `level_extractor.py` parses the track files and decodes a level. `make level-ascii LEVEL=N` prints one level as an ASCII map. `make level-check` prints one line per level with its numbers of player, guard, gold and exit-ladder cells, followed by the problems it finds: a player count other than one, a guard count outside one to five, and values from 10 to 15 with their byte and nibble.
- `level_images.py` draws each level as a PNG in `images/levels/` (`make level-images`). Each cell is drawn with the sprite whose number is its stored value, so the image shows the level as the level editor shows it: trapdoors (sprite 5) and hidden exit ladders (sprite 6) have shapes of their own.
- `level_catalog.py` writes linked thumbnails of all 150 levels into Chapter 6 of `research/main.nw-edited.md`, between the markers `<!-- level-catalog: begin -->` and `<!-- level-catalog: end -->` (`make level-catalog`).

Findings:

- Every one of the 150 levels has exactly one player marker and only values `0` through `9` (checked with `make level-check`).
- Levels 8, 80 and 113 have six guards, one more than the level editor allows; see "Guard starts".
- After level 150, track `$0C` holds more sectors, which its file header calls "leftover mastering data"; see the table below. `make level-check` lists them separately, for information only. Where they come from is open.
- Sprites 0 to 9 use only the first 10 of their 14 pixel columns; the rest is black (checked against `sprite_tables.tex`). A cell is therefore 10 by 11 pixels, and a level 280 by 176, the full width of the hi-res screen.
- XekriRedmane coloured each sprite on its own, which leaves a black pixel column where two blue cells meet, for example two bricks side by side. On the Apple II a blue or orange area lights only every other pixel, and the TV fills the pixels in between. The images therefore fill a single black pixel between two blue or two orange pixels (Inferred from the colour model in Chapter 3; not measured).

The rest of track `$0C`, read as further levels:

| Level slot | Track `$0C`, sector | Content |
|---:|---|---|
| 151 | `$6` | Not listed in the track file, so empty |
| 152 to 154 | `$7` to `$9` | Plausible levels: one player, three or four guards |
| 155 | `$A` | Not a level: values 10 to 15 in an ascending pattern, 16 player and 25 guard markers |
| 156 to 159 | `$B` to `$E` | Not listed, so empty |
| 160 | `$F` | Not a level: garbled, 7 player markers and many invalid values |

## Open questions

The following questions remain open but do not block extraction:

1. What is the original purpose of the final 32 bytes in each level sector?
2. ~~Do all shipped levels contain exactly one player marker?~~ Answered by the manual: exactly one player, one to five guards, enforced by the level editor. The extractor still counts and reports both (see "Player start"). The shipped levels all have exactly one player; three of them have six guards (see "Guard starts").
3. Is guard scan order observably significant beyond initialization? At initialization it is: it decides which guard is removed from a level with six (see "Guard starts"). Beyond initialization it is still open (Chapter 9).
4. ~~How many normal disk levels should be included in the controlled output?~~ 150: tracks `$03` to `$0B`, and sectors `$0` to `$5` of track `$0C`. The rest of track `$0C` is leftover data (see "Level extractor and catalog"); what it was for is open.
5. Should embedded attract-mode levels be extracted into a separate file?
6. Does the `.do` image use the direct sector offset expected for every relevant track, or is additional sector-order handling required?
7. What exact file format and repository path should be used for the generated controlled level data? Partly answered: the level images are in `images/levels/`. A data format for the Core Game Spec, such as JSON, is still open.
8. ~~Should traps be displayed identically to bricks in the default visualizer, with an optional diagnostic mode that distinguishes them?~~ The level images use the level editor's sprites, which give trapdoors (sprite 5) and hidden exit ladders (sprite 6) shapes of their own.
9. Does dying reload the level from disk, or is it rebuilt from the copy in memory? See `TODO.md`.

These should be answered through extraction validation, targeted source reading, or emulator observation rather than by requiring a complete understanding of the disk subsystem.

## Conclusions

The essential level contract is compact:

1. A level is a 28-column by 16-row grid.
2. The grid contains 448 values in the range `0` through `9`.
3. Two cells are packed into each byte.
4. The low nibble is the left cell and the high nibble is the right cell.
5. A row occupies 14 bytes.
6. A complete board occupies the first 224 bytes of a 256-byte sector.
7. Normal levels begin at track 3 and use one sector per level.
8. Disk level index `n` is found at track `3 + n // 16`, sector `n % 16`.
9. Values `8` and `9` are actor-start markers.
10. Value `6` is an initially hidden exit-ladder marker.
11. Runtime state should be constructed from, but kept separate from, the immutable decoded source board.
12. The embedded attract-mode levels are distinct from the correspondingly numbered disk levels.
13. The game places at most five guards; a sixth guard marker is removed, and because the board is scanned backwards, it is the topmost one.

These facts are sufficient to design a Python extraction utility, produce a controlled file containing the levels, render diagnostic ASCII maps, and later initialize equivalent level state in another implementation.

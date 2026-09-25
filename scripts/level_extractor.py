"""Decode Lode Runner levels from the disk track files, show and check them.

The track files in `reference/lode_runner_reveng/disk/` list the sectors of
the original disk image, one labelled block per sector:

    ; Track $03, sector $0
        HEX     00 00 00 ...    (16 lines of 16 bytes = 256 bytes)

Sectors that a file does not list are zero-filled on the disk.

The level format is the contract in `docs/main-nw/06-levels.md`:

- disk levels start at track 3, one level per 256-byte sector, so level
  index n is at track 3 + n // 16, sector n % 16;
- the first 224 bytes are the board: 16 rows of 14 bytes;
- each byte holds two cells, the low nibble is the left cell;
- the last 32 bytes are not part of the board.

The game has 150 levels, so the last one is track $0C, sector $5. The rest
of track $0C holds more sectors, called "leftover mastering data" in its
file header; `check` shows them separately, for information only.

Usage:
    python scripts/level_extractor.py show TRACK_DIR LEVEL
    python scripts/level_extractor.py check TRACK_DIR

LEVEL is the level number the player sees, starting at 1. `check` prints
one line per level with its counts, and the problems it finds.
"""

import argparse
import re
import sys
from collections import Counter
from pathlib import Path

FIRST_LEVEL_TRACK = 3
SECTORS_PER_TRACK = 16
SECTOR_SIZE = 256

BOARD_ROWS = 16
BOARD_COLUMNS = 28
BYTES_PER_ROW = BOARD_COLUMNS // 2
BOARD_BYTES = BYTES_PER_ROW * BOARD_ROWS  # 224; the rest of the sector is ignored

LEVEL_COUNT = 150

# Stored cell values that `check` counts (see `06-levels.md`).
EXIT_LADDER = 6
GOLD = 7
GUARD = 8
PLAYER = 9

# The manual's rule for a playable level: exactly one player, one to five guards.
MIN_GUARDS = 1
MAX_GUARDS = 5

# Stored cell value -> map character, as in the table in `06-levels.md`.
# 6 (hidden exit ladder) gets its own character: keeping it apart from
# 3 (ladder) is part of the level-data contract.
ASCII_CHARS = {
    0: " ",  # empty
    1: "#",  # brick
    2: "X",  # solid block
    3: "H",  # ladder
    4: "-",  # bar
    5: "T",  # trap
    6: "h",  # hidden exit ladder
    7: "$",  # gold
    8: "G",  # guard start
    9: "P",  # player start
}
# Values 10 to 15 fit in a nibble but are not valid cells. The game treats
# them as empty; here they stay visible until the checking step reports them.
INVALID_CHAR = "?"

SECTOR_LABEL = re.compile(r"^; Track \$([0-9A-Fa-f]{2}), sector \$([0-9A-Fa-f])$")
HEX_LINE = re.compile(r"^HEX\s+(.*)$")


def level_location(level_index: int) -> tuple[int, int]:
    """Return (track, sector) of a zero-based disk level index."""
    if level_index < 0:
        raise ValueError(f"Level index must not be negative, got {level_index}")
    track = FIRST_LEVEL_TRACK + level_index // SECTORS_PER_TRACK
    sector = level_index % SECTORS_PER_TRACK
    return track, sector


def track_file_path(track_dir: Path, track: int) -> Path:
    """Return the path of one track file, e.g. `track_0a.asm` for track $0A."""
    return track_dir / f"track_{track:02x}.asm"


def parse_track_file(text: str, track: int) -> dict[int, bytes]:
    """Return {sector number: 256 bytes} for the sectors listed in `text`.

    `track` is the track the file is expected to hold; a label naming any
    other track is an error, so a misnamed file cannot slip through.
    """
    sectors: dict[int, bytearray] = {}
    current: bytearray | None = None
    for line in text.splitlines():
        line = line.strip()
        label = SECTOR_LABEL.match(line)
        if label:
            label_track = int(label.group(1), 16)
            sector = int(label.group(2), 16)
            if label_track != track:
                raise ValueError(
                    f"Expected track ${track:02X}, found label for track ${label_track:02X}"
                )
            if sector in sectors:
                raise ValueError(
                    f"Track ${track:02X}, sector ${sector:X} appears twice"
                )
            current = sectors[sector] = bytearray()
            continue
        hex_line = HEX_LINE.match(line)
        if not hex_line:
            continue
        if current is None:
            raise ValueError(
                f"HEX line before the first sector label in track ${track:02X}"
            )
        current.extend(bytes.fromhex(hex_line.group(1)))
    for sector, data in sectors.items():
        if len(data) != SECTOR_SIZE:
            raise ValueError(
                f"Track ${track:02X}, sector ${sector:X} has {len(data)} bytes, "
                f"expected {SECTOR_SIZE}"
            )
    return {sector: bytes(data) for sector, data in sectors.items()}


def read_track(track_dir: Path, track: int) -> dict[int, bytes]:
    """Return the listed sectors of one track file."""
    text = track_file_path(track_dir, track).read_text(encoding="utf-8")
    return parse_track_file(text, track)


def read_level_sector(track_dir: Path, level_index: int) -> bytes:
    """Return the 256 bytes of one disk level; unlisted sectors are zeros."""
    track, sector = level_location(level_index)
    return read_track(track_dir, track).get(sector, bytes(SECTOR_SIZE))


def decode_board(sector: bytes) -> list[list[int]]:
    """Decode a level sector into 16 rows of 28 cell values.

    Only the first 224 bytes are used. Within each byte the low nibble is
    the left cell and the high nibble the right cell.
    """
    if len(sector) != SECTOR_SIZE:
        raise ValueError(f"A sector has {SECTOR_SIZE} bytes, got {len(sector)}")
    board: list[list[int]] = []
    for row in range(BOARD_ROWS):
        packed_row = sector[row * BYTES_PER_ROW : (row + 1) * BYTES_PER_ROW]
        cells: list[int] = []
        for packed_byte in packed_row:
            cells.append(packed_byte & 0x0F)
            cells.append((packed_byte >> 4) & 0x0F)
        board.append(cells)
    return board


def render_ascii(board: list[list[int]]) -> str:
    """Render a board as 16 lines of 28 characters, one character per cell."""
    return "\n".join(
        "".join(ASCII_CHARS.get(value, INVALID_CHAR) for value in row) for row in board
    )


def frame_ascii(ascii_map: str) -> str:
    """Draw a thin frame around a map, so empty cells at the edges stay visible."""
    border = "+" + "-" * BOARD_COLUMNS + "+"
    lines = [border]
    lines.extend(f"|{line}|" for line in ascii_map.split("\n"))
    lines.append(border)
    return "\n".join(lines)


def count_cells(board: list[list[int]]) -> Counter[int]:
    """Count how often each cell value occurs on a board."""
    return Counter(value for row in board for value in row)


def describe_invalid_cell(row: int, column: int, value: int) -> str:
    """Name an invalid cell with the byte and nibble it was stored in."""
    byte = row * BYTES_PER_ROW + column // 2
    nibble = "low" if column % 2 == 0 else "high"
    return (
        f"row {row}, column {column}: invalid cell value {value} "
        f"(byte {byte}, {nibble} nibble)"
    )


def check_board(board: list[list[int]]) -> list[str]:
    """Return the problems of one board; an empty list means none."""
    counts = count_cells(board)
    problems: list[str] = []
    if counts[PLAYER] != 1:
        problems.append(f"{counts[PLAYER]} player starts, expected exactly 1")
    if counts[GUARD] < MIN_GUARDS:
        problems.append(
            f"{counts[GUARD]} guards, expected {MIN_GUARDS} to {MAX_GUARDS}"
        )
    elif counts[GUARD] > MAX_GUARDS:
        # The level draw routine removes every guard marker once GUARD_COUNT
        # has reached 5, so the extra guards never appear in the game.
        problems.append(
            f"{counts[GUARD]} guards, but the game places only {MAX_GUARDS} "
            "(level draw routine)"
        )
    for row, cells in enumerate(board):
        for column, value in enumerate(cells):
            if value not in ASCII_CHARS:
                problems.append(describe_invalid_cell(row, column, value))
    return problems


def summary_line(level: int, board: list[list[int]]) -> str:
    """One report line: where the level is stored and what it contains."""
    track, sector = level_location(level - 1)
    counts = count_cells(board)
    return (
        f"Level {level:3d} (track ${track:02X}, sector ${sector:X}): "
        f"{counts[PLAYER]} player, {counts[GUARD]} guards, {counts[GOLD]} gold, "
        f"{counts[EXIT_LADDER]} exit-ladder cells"
    )


def check_levels(track_dir: Path) -> tuple[list[str], int]:
    """Check levels 1 to 150 and describe the rest of the last track.

    Returns the report lines and the number of problems in levels 1 to 150.
    The sectors after level 150 are not levels of the game, so what `check`
    finds there is listed as a note, not counted as a problem.
    """
    tracks: dict[int, dict[int, bytes]] = {}

    def listed_sector(level: int) -> bytes | None:
        """Return a level's sector, or None if its track file does not list it."""
        track, sector = level_location(level - 1)
        if track not in tracks:
            tracks[track] = read_track(track_dir, track)
        return tracks[track].get(sector)

    lines: list[str] = []
    problem_count = 0
    for level in range(1, LEVEL_COUNT + 1):
        board = decode_board(listed_sector(level) or bytes(SECTOR_SIZE))
        problems = check_board(board)
        problem_count += len(problems)
        lines.append(summary_line(level, board))
        lines.extend(f"    problem: {problem}" for problem in problems)

    # The last level's track continues to its last sector (level 160).
    tracks_used = -(-LEVEL_COUNT // SECTORS_PER_TRACK)
    last_slot = tracks_used * SECTORS_PER_TRACK
    lines.append("")
    lines.append(
        f"Beyond level {LEVEL_COUNT}, the rest of the last track (information only):"
    )
    for level in range(LEVEL_COUNT + 1, last_slot + 1):
        sector = listed_sector(level)
        if sector is None:
            track, sector_number = level_location(level - 1)
            lines.append(
                f"Level {level:3d} (track ${track:02X}, sector ${sector_number:X}): "
                "not listed, reads as empty"
            )
            continue
        board = decode_board(sector)
        lines.append(summary_line(level, board))
        lines.extend(f"    note: {problem}" for problem in check_board(board))

    lines.append("")
    if problem_count == 0:
        lines.append(f"No problems in levels 1 to {LEVEL_COUNT}.")
    else:
        lines.append(f"Problems in levels 1 to {LEVEL_COUNT}: {problem_count}")
    return lines, problem_count


def show_level(track_dir: Path, level: int) -> int:
    """The `show` command: print one level as a framed ASCII map."""
    if level < 1:
        print(f"level_extractor: levels start at 1, got {level}", file=sys.stderr)
        return 1

    try:
        level_index = level - 1
        track, sector = level_location(level_index)
        board = decode_board(read_level_sector(track_dir, level_index))
    except (OSError, ValueError) as error:
        print(f"level_extractor: {error}", file=sys.stderr)
        return 1

    print(f"Level {level} (track ${track:02X}, sector ${sector:X})")
    print(frame_ascii(render_ascii(board)))
    return 0


def check_all(track_dir: Path) -> int:
    """The `check` command: print the report for all levels.

    Problems are findings about the data, not failures of the command, so
    the exit code is 0 either way; only unreadable input returns 1.
    """
    try:
        lines, _ = check_levels(track_dir)
    except (OSError, ValueError) as error:
        print(f"level_extractor: {error}", file=sys.stderr)
        return 1
    print("\n".join(lines))
    return 0


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    commands = parser.add_subparsers(dest="command", required=True)
    show = commands.add_parser("show", help="print one level as an ASCII map")
    show.add_argument(
        "track_dir", type=Path, help="directory with the track_XX.asm files"
    )
    show.add_argument(
        "level", type=int, help="level number as the player sees it, from 1"
    )
    check = commands.add_parser(
        "check", help="report counts and problems of all levels"
    )
    check.add_argument(
        "track_dir", type=Path, help="directory with the track_XX.asm files"
    )
    args = parser.parse_args(argv)

    if args.command == "show":
        return show_level(args.track_dir, args.level)
    return check_all(args.track_dir)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

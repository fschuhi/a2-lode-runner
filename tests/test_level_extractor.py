"""Specify how levels are read from the disk track files and shown as ASCII.

The real input is XekriRedmane's `track_03.asm` in
`reference/lode_runner_reveng/disk/`. Small generated track files cover the
parsing rules and the error cases. The expected layout comes from
`docs/main-nw/06-levels.md`.
"""

import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

import level_extractor as extractor  # noqa: E402

REAL_TRACK_DIR = PROJECT_ROOT / "reference" / "lode_runner_reveng" / "disk"


def track_text(track: int, sectors: dict[int, bytes]) -> str:
    """Write a track file in the same layout as the real ones."""
    lines = [f"; Track ${track:02X}: test data", ";"]
    for sector, data in sectors.items():
        lines += ["", f"; Track ${track:02X}, sector ${sector:X}"]
        for start in range(0, len(data), 16):
            chunk = " ".join(f"{b:02X}" for b in data[start : start + 16])
            lines.append(f"    HEX     {chunk}")
    return "\n".join(lines) + "\n"


def sector_with(prefix: bytes) -> bytes:
    """A 256-byte sector that starts with `prefix` and is zero after it."""
    return prefix + bytes(extractor.SECTOR_SIZE - len(prefix))


# --- Location of a level on the disk ---


@pytest.mark.parametrize(
    ("level_index", "expected"),
    [(0, (3, 0)), (15, (3, 15)), (16, (4, 0))],
)
def test_level_location(level_index: int, expected: tuple[int, int]) -> None:
    assert extractor.level_location(level_index) == expected


def test_negative_level_index_is_rejected() -> None:
    with pytest.raises(ValueError):
        extractor.level_location(-1)


def test_track_file_name_uses_lowercase_hex() -> None:
    assert extractor.track_file_path(Path("disk"), 10) == Path("disk/track_0a.asm")


# --- Decoding a sector ---


def test_low_nibble_is_the_left_cell() -> None:
    board = extractor.decode_board(sector_with(bytes([0x06])))
    assert board[0][:2] == [6, 0]


def test_a_row_is_14_bytes() -> None:
    # Byte 14 is the first byte of row 1, not the end of row 0.
    board = extractor.decode_board(sector_with(bytes(14) + bytes([0x21])))
    assert board[0] == [0] * 28
    assert board[1][:2] == [1, 2]


def test_board_is_16_by_28_and_ignores_the_last_32_bytes() -> None:
    sector = bytes(224) + bytes([0xFF] * 32)
    board = extractor.decode_board(sector)
    assert len(board) == 16
    assert all(row == [0] * 28 for row in board)


def test_sector_of_wrong_size_is_rejected() -> None:
    with pytest.raises(ValueError):
        extractor.decode_board(bytes(224))


# --- Parsing track files ---


def test_parse_reads_listed_sectors() -> None:
    first = sector_with(bytes([0x11]))
    third = sector_with(bytes([0x22, 0x33]))
    sectors = extractor.parse_track_file(track_text(5, {0: first, 2: third}), 5)
    assert sectors == {0: first, 2: third}


def test_crlf_input_parses_like_lf() -> None:
    text = track_text(5, {0: sector_with(bytes([0x11]))})
    assert extractor.parse_track_file(
        text.replace("\n", "\r\n"), 5
    ) == extractor.parse_track_file(text, 5)


def test_unlisted_sector_reads_as_zeros(tmp_path: Path) -> None:
    (tmp_path / "track_03.asm").write_text(
        track_text(3, {0: sector_with(bytes([0x11]))})
    )
    assert extractor.read_level_sector(tmp_path, 1) == bytes(256)


def test_label_for_another_track_is_rejected() -> None:
    with pytest.raises(ValueError, match="Expected track"):
        extractor.parse_track_file(track_text(4, {0: bytes(256)}), 3)


def test_duplicate_sector_is_rejected() -> None:
    text = track_text(3, {0: bytes(256)}) + track_text(3, {0: bytes(256)})
    with pytest.raises(ValueError, match="appears twice"):
        extractor.parse_track_file(text, 3)


def test_short_sector_is_rejected() -> None:
    with pytest.raises(ValueError, match="bytes"):
        extractor.parse_track_file(track_text(3, {0: bytes(240)}), 3)


# --- ASCII rendering ---


def test_render_uses_the_character_table() -> None:
    board = [list(range(10)) + [12] + [0] * 17] + [[0] * 28 for _ in range(15)]
    first_line = extractor.render_ascii(board).split("\n")[0]
    assert first_line == " #XH-Th$GP?" + " " * 17


def test_frame_keeps_edge_spaces_visible() -> None:
    framed = extractor.frame_ascii("  \n  ")
    assert framed.split("\n") == [
        "+" + "-" * 28 + "+",
        "|  |",
        "|  |",
        "+" + "-" * 28 + "+",
    ]


# --- Command line ---


def test_main_prints_header_and_framed_map(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    (tmp_path / "track_03.asm").write_text(
        track_text(3, {0: sector_with(bytes([0x97]))})
    )
    assert extractor.main(["show", str(tmp_path), "1"]) == 0
    lines = capsys.readouterr().out.split("\n")
    assert lines[0] == "Level 1 (track $03, sector $0)"
    # $97: the low nibble 7 (gold) is the left cell, the high nibble 9 (player) the right.
    assert lines[2].startswith("|$P ")
    assert len(lines[2]) == 30


def test_main_rejects_level_zero(capsys: pytest.CaptureFixture[str]) -> None:
    assert extractor.main(["show", str(REAL_TRACK_DIR), "0"]) == 1
    assert "levels start at 1" in capsys.readouterr().err


# --- Checking boards ---


def board_with(cells: dict[tuple[int, int], int]) -> list[list[int]]:
    """An empty 16 x 28 board with the given (row, column) cells set."""
    board = [[0] * 28 for _ in range(16)]
    for (row, column), value in cells.items():
        board[row][column] = value
    return board


def test_valid_board_has_no_problems() -> None:
    assert extractor.check_board(board_with({(0, 0): 9, (0, 1): 8})) == []


@pytest.mark.parametrize(
    ("cells", "expected"),
    [
        ({(0, 1): 8}, "0 player starts"),
        ({(0, 0): 9, (0, 1): 9, (0, 2): 8}, "2 player starts"),
        ({(0, 0): 9}, "0 guards"),
        ({(0, 0): 9, **{(1, c): 8 for c in range(6)}}, "6 guards"),
    ],
)
def test_wrong_actor_counts_are_problems(
    cells: dict[tuple[int, int], int], expected: str
) -> None:
    problems = extractor.check_board(board_with(cells))
    assert len(problems) == 1
    assert problems[0].startswith(expected)


def test_too_many_guards_says_what_the_game_does() -> None:
    board = board_with({(0, 0): 9, **{(1, c): 8 for c in range(6)}})
    assert extractor.check_board(board) == [
        "6 guards, but the game places only 5 (level draw routine)"
    ]


def test_invalid_cell_names_byte_and_nibble() -> None:
    # Row 1, column 3 is the high nibble of byte 14 + 1 = 15.
    board = board_with({(0, 0): 9, (0, 1): 8, (1, 3): 12})
    assert extractor.check_board(board) == [
        "row 1, column 3: invalid cell value 12 (byte 15, high nibble)"
    ]


# --- Checking all levels ---


def write_fake_disk(track_dir: Path, broken_level: int | None = None) -> None:
    """Tracks $03 to $0C in which every level has one player and one guard.

    Track $0C lists only the sectors of levels 145 to 150, like the real
    file lists only some sectors after them. `broken_level` gets a second
    player.
    """
    for track in range(3, 13):
        sectors: dict[int, bytes] = {}
        for sector in range(16):
            level = (track - 3) * 16 + sector + 1
            if level > 150:
                break
            actors = bytes([0x99 if level == broken_level else 0x09, 0x08])
            sectors[sector] = sector_with(actors)
        (track_dir / f"track_{track:02x}.asm").write_text(track_text(track, sectors))


def test_check_reports_every_level_and_the_rest_of_the_track(tmp_path: Path) -> None:
    write_fake_disk(tmp_path)
    lines, problem_count = extractor.check_levels(tmp_path)
    assert problem_count == 0
    level_lines = [line for line in lines if line.startswith("Level")]
    assert len(level_lines) == 160
    assert level_lines[0] == (
        "Level   1 (track $03, sector $0): 1 player, 1 guards, 0 gold, "
        "0 exit-ladder cells"
    )
    assert level_lines[150] == (
        "Level 151 (track $0C, sector $6): not listed, reads as empty"
    )
    assert lines[-1] == "No problems in levels 1 to 150."


def test_check_puts_problems_under_their_level(tmp_path: Path) -> None:
    write_fake_disk(tmp_path, broken_level=2)
    lines, problem_count = extractor.check_levels(tmp_path)
    assert problem_count == 1
    level_2 = lines.index(
        "Level   2 (track $03, sector $1): 2 player, 1 guards, 0 gold, "
        "0 exit-ladder cells"
    )
    assert lines[level_2 + 1] == ("    problem: 2 player starts, expected exactly 1")
    assert lines[-1] == "Problems in levels 1 to 150: 1"


def test_main_check_fails_on_missing_track_file(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert extractor.main(["check", str(tmp_path)]) == 1
    assert "level_extractor:" in capsys.readouterr().err


# --- The real track file ---


def test_real_level_1_decodes_to_a_valid_board() -> None:
    board = extractor.decode_board(extractor.read_level_sector(REAL_TRACK_DIR, 0))
    assert len(board) == 16
    assert all(len(row) == 28 for row in board)
    assert all(0 <= value <= 9 for row in board for value in row)
    # Byte 9 of track $03, sector $0 is $06: row 0, columns 18 and 19 are a
    # hidden exit ladder and an empty cell.
    assert board[0][18:20] == [6, 0]


def test_real_levels_only_known_problems() -> None:
    # Levels 8, 80 and 113 have 6 guards on the disk; the level draw routine
    # removes every guard after the fifth. Any other problem is new.
    six_guards = ["6 guards, but the game places only 5 (level draw routine)"]
    found: dict[int, list[str]] = {}
    for level in range(1, 151):
        sector = extractor.read_level_sector(REAL_TRACK_DIR, level - 1)
        problems = extractor.check_board(extractor.decode_board(sector))
        if problems:
            found[level] = problems
    assert found == {8: six_guards, 80: six_guards, 113: six_guards}

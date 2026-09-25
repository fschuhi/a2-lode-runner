"""Specify how levels are drawn as PNG images with the level-editor sprites.

The sprites come from XekriRedmane's real `sprite_tables.tex`. The boards
are small generated ones; rendering the real levels is `make level-images`.
"""

import io
import sys
from pathlib import Path

import pytest
from PIL import Image

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

import level_images as images  # noqa: E402

REAL_TEX = PROJECT_ROOT / "reference" / "lode_runner_reveng" / "sprite_tables.tex"


@pytest.fixture(scope="module")
def sprites() -> dict[int, list[str]]:
    return images.level_sprites(REAL_TEX.read_text(encoding="utf-8"))


def empty_board() -> list[list[int]]:
    return [[0] * 28 for _ in range(16)]


def cell_pixels(image: Image.Image, row: int, column: int) -> list[list[int]]:
    """Palette indices of one board cell in a scale-1 image."""
    left, top = column * 10, row * 11
    return [[image.getpixel((left + x, top + y)) for x in range(10)] for y in range(11)]


def sprite_indices(sprite: list[str]) -> list[list[int]]:
    return [[images.PALETTE_INDEX[css] for css in line] for line in sprite]


# --- Sprites ---


def test_level_sprites_are_0_to_9_cut_to_10_by_11(
    sprites: dict[int, list[str]],
) -> None:
    assert sorted(sprites) == list(range(10))
    for rows in sprites.values():
        assert len(rows) == 11
        assert all(len(row) == 10 for row in rows)


def test_cut_off_pixel_that_is_not_black_is_rejected() -> None:
    rows = ["k" * 14] * 10 + ["k" * 10 + "w" + "k" * 3]
    with pytest.raises(ValueError, match="beyond column 9"):
        images.crop_sprite(1, rows)


# --- Rendering ---


@pytest.mark.parametrize(("scale", "size"), [(1, (280, 176)), (2, (560, 352))])
def test_image_size(
    sprites: dict[int, list[str]], scale: int, size: tuple[int, int]
) -> None:
    assert images.render_level(empty_board(), sprites, scale).size == size


def test_each_cell_shows_its_sprite(sprites: dict[int, list[str]]) -> None:
    board = empty_board()
    board[0][0] = 1  # brick in the upper-left cell
    board[0][1] = 3  # ladder right next to it, 10 pixels further right
    board[15][27] = 9  # player in the lower-right cell
    image = images.render_level(board, sprites)
    assert cell_pixels(image, 0, 0) == sprite_indices(sprites[1])
    assert cell_pixels(image, 0, 1) == sprite_indices(sprites[3])
    assert cell_pixels(image, 15, 27) == sprite_indices(sprites[9])
    assert cell_pixels(image, 1, 0) == sprite_indices(sprites[0])


def test_scale_repeats_each_pixel(sprites: dict[int, list[str]]) -> None:
    board = empty_board()
    board[3][4] = 7  # gold
    small = images.render_level(board, sprites, 1)
    large = images.render_level(board, sprites, 2)
    for y in range(small.height):
        for x in range(small.width):
            pixel = small.getpixel((x, y))
            assert large.getpixel((2 * x, 2 * y)) == pixel
            assert large.getpixel((2 * x + 1, 2 * y + 1)) == pixel


def test_palette_is_the_sprite_catalog_colours(
    sprites: dict[int, list[str]],
) -> None:
    image = images.render_level(empty_board(), sprites)
    assert image.mode == "P"
    assert image.getpalette()[:12] == [
        0x00, 0x00, 0x00,
        0x1B, 0xA1, 0xE2,
        0xE6, 0xE6, 0xE6,
        0xFF, 0x80, 0x00,
    ]  # fmt: skip


def test_sprites_have_no_single_pixel_gaps_inside(
    sprites: dict[int, list[str]],
) -> None:
    # So filling gaps only ever changes the borders between cells.
    for number, rows in sprites.items():
        for row in rows:
            for x in range(1, len(row) - 1):
                gap = row[x] == "k" and row[x - 1] == row[x + 1] != "k"
                assert not gap, f"sprite {number}: {row}"


def row_indices(css: str) -> bytearray:
    return bytearray(images.PALETTE_INDEX[c] for c in css)


@pytest.mark.parametrize(
    ("before", "after"),
    [
        ("bkb", "bbb"),  # blue gap filled
        ("oko", "ooo"),  # orange gap filled
        ("wkw", "wkw"),  # white is two lit pixels, no fill
        ("bko", "bko"),  # different colours, no fill
        ("bkkb", "bkkb"),  # two black pixels are a real gap
    ],
)
def test_fill_colour_gaps(before: str, after: str) -> None:
    filled = images.fill_colour_gaps(row_indices(before), len(before))
    assert filled == row_indices(after)


def test_gaps_are_not_filled_across_image_rows() -> None:
    # Read as one long line, "b" at the end of row 0, "k" at the start of
    # row 1 and "b" after it would look like a gap. They are not neighbours.
    pixels = row_indices("kkb" + "kbk" + "kkk")
    assert images.fill_colour_gaps(pixels, 3) == pixels


def test_neighbouring_bricks_join_up(sprites: dict[int, list[str]]) -> None:
    board = empty_board()
    board[0][0] = board[0][1] = 1
    image = images.render_level(board, sprites)
    blue, black = images.PALETTE_INDEX["b"], images.PALETTE_INDEX["k"]
    # Column 9 of the left brick: filled where column 8 and the next brick's
    # column 0 are both blue; the mortar rows 4 and 10 stay black.
    column_9 = [image.getpixel((9, y)) for y in range(11)]
    assert column_9 == [blue] * 4 + [black] + [blue] * 5 + [black]


def test_invalid_cell_value_is_rejected(sprites: dict[int, list[str]]) -> None:
    board = empty_board()
    board[2][5] = 12
    with pytest.raises(ValueError, match="row 2, column 5"):
        images.render_level(board, sprites)


def test_same_board_gives_identical_png_bytes(
    sprites: dict[int, list[str]],
) -> None:
    # Regenerating unchanged levels must not create changes for git.
    board = empty_board()
    board[5][5] = 8

    def png_bytes() -> bytes:
        buffer = io.BytesIO()
        images.render_level(board, sprites, 2).save(buffer, "PNG", optimize=True)
        return buffer.getvalue()

    assert png_bytes() == png_bytes()


def test_image_file_name() -> None:
    assert images.level_image_path(Path("out"), 1) == Path("out/level-001.png")
    assert images.level_image_path(Path("out"), 150) == Path("out/level-150.png")


# --- Command line ---


def test_scale_below_1_is_rejected(capsys: pytest.CaptureFixture[str]) -> None:
    assert images.main([str(REAL_TEX), "disk", "out", "--scale", "0"]) == 1
    assert "scale starts at 1" in capsys.readouterr().err

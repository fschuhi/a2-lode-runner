"""Render the Lode Runner disk levels as PNG images, drawn with the game's sprites.

A stored cell value 0 to 9 is also the number of the sprite the level editor
draws for that cell (see `docs/main-nw/06-levels.md`), so a level image shows
the level as the editor shows it: trapdoors (sprite 5) and hidden exit
ladders (sprite 6) included, guards and player at their start positions.

The sprite pixels come from XekriRedmane's `sprite_tables.tex`, read with
`sprite_tables_to_html.py`; the colours are the ones of the sprite catalog in
`scripts/web/style.css`.

A sprite is 14 pixels wide, but the ten level sprites use only the first 10
columns, the rest is black. A board cell is therefore 10 x 11 pixels, and a
level 280 x 176 pixels: the width of the Apple II hi-res screen, and 16 of its
cell rows. The images use square pixels, enlarged by `--scale` (default 2).

XekriRedmane coloured each sprite on its own. Where two blue cells meet, as two
bricks side by side do, that leaves a single black pixel column between blue
pixels, which the TV fills with blue. `fill_colour_gaps` does the same, so the
bricks join up as in the game.

Usage:
    python scripts/level_images.py SPRITE_TABLES_TEX TRACK_DIR OUTPUT_DIR [--scale N]

Writes `level-001.png` to `level-150.png` into OUTPUT_DIR.
"""

import argparse
import sys
from pathlib import Path

from PIL import Image

from level_extractor import (
    BOARD_COLUMNS,
    BOARD_ROWS,
    LEVEL_COUNT,
    decode_board,
    read_level_sector,
)
from sprite_tables_to_html import PIXELS_PER_ROW, ROWS_PER_SPRITE, parse_sprite_tables

LEVEL_SPRITE_COUNT = 10  # sprites 0 to 9, one per stored cell value
CELL_WIDTH = 10
CELL_HEIGHT = ROWS_PER_SPRITE  # 11
DEFAULT_SCALE = 2

# Pixel class -> RGB, as in `table.spritegrid td.k/.b/.w/.o` in `style.css`.
# The order of this dict is the order of the PNG palette.
PALETTE = {
    "k": (0x00, 0x00, 0x00),  # black
    "b": (0x1B, 0xA1, 0xE2),  # blue
    "w": (0xE6, 0xE6, 0xE6),  # white
    "o": (0xFF, 0x80, 0x00),  # orange
}
PALETTE_INDEX = {css: index for index, css in enumerate(PALETTE)}

# Colours whose single-pixel black gaps the TV fills (see `fill_colour_gaps`).
GAP_FILL_COLOURS = {PALETTE_INDEX["b"], PALETTE_INDEX["o"]}


def crop_sprite(number: int, rows: list[str]) -> list[str]:
    """Cut a sprite's rows to the width of a board cell.

    Fails if a cut-off pixel is not black, so a change in `sprite_tables.tex`
    cannot make the images lose pixels without notice.
    """
    for row in rows:
        if set(row[CELL_WIDTH:]) - {"k"}:
            raise ValueError(
                f"Sprite {number} has pixels beyond column {CELL_WIDTH - 1}"
            )
    return [row[:CELL_WIDTH] for row in rows]


def level_sprites(tex: str) -> dict[int, list[str]]:
    """Return sprites 0 to 9 from `sprite_tables.tex`, cut to 10 x 11 pixels."""
    sprites = parse_sprite_tables(tex)
    return {
        number: crop_sprite(number, sprites[number])
        for number in range(LEVEL_SPRITE_COUNT)
    }


def fill_colour_gaps(pixels: bytearray, width: int) -> bytearray:
    """Colour each single black pixel that has blue, or orange, on both sides.

    On the Apple II a blue or orange area lights only every other pixel, and
    the TV fills the pixels in between with the same colour. Inside a sprite
    XekriRedmane already coloured them: sprites 0 to 9 contain no "colour,
    black, same colour" (a test checks this). At a sprite's right edge the neighbour belongs to the next cell, so that
    pixel stayed black. This fills it once the whole board is drawn. White
    is two lit pixels side by side, so the reasoning does not hold for it.
    Inferred from the colour model in Chapter 3, not measured.
    """
    black = PALETTE_INDEX["k"]
    filled = bytearray(pixels)  # read from the original, so fills never chain
    for start in range(0, len(pixels), width):
        for x in range(start + 1, start + width - 1):
            left, right = pixels[x - 1], pixels[x + 1]
            if pixels[x] == black and left == right and left in GAP_FILL_COLOURS:
                filled[x] = left
    return filled


def render_level(
    board: list[list[int]], sprites: dict[int, list[str]], scale: int = 1
) -> Image.Image:
    """Draw a board with one sprite per cell, as a palette image."""
    width = BOARD_COLUMNS * CELL_WIDTH
    height = BOARD_ROWS * CELL_HEIGHT
    pixels = bytearray(width * height)
    for row, cells in enumerate(board):
        for column, value in enumerate(cells):
            if value not in sprites:
                raise ValueError(
                    f"row {row}, column {column}: no sprite for cell value {value}"
                )
            for y, line in enumerate(sprites[value]):
                start = (row * CELL_HEIGHT + y) * width + column * CELL_WIDTH
                pixels[start : start + CELL_WIDTH] = bytes(
                    PALETTE_INDEX[css] for css in line
                )
    pixels = fill_colour_gaps(pixels, width)
    image = Image.frombytes("P", (width, height), bytes(pixels))
    image.putpalette([channel for rgb in PALETTE.values() for channel in rgb])
    if scale != 1:
        # NEAREST repeats each pixel, so the enlarged image stays sharp.
        image = image.resize((width * scale, height * scale), Image.Resampling.NEAREST)
    return image


def level_image_path(output_dir: Path, level: int) -> Path:
    """Return the file name of one level image, e.g. `level-001.png`."""
    return output_dir / f"level-{level:03d}.png"


def write_level_images(
    tex_path: Path, track_dir: Path, output_dir: Path, scale: int
) -> int:
    """Render levels 1 to 150 into `output_dir`; return the number written."""
    sprites = level_sprites(tex_path.read_text(encoding="utf-8"))
    output_dir.mkdir(parents=True, exist_ok=True)
    for level in range(1, LEVEL_COUNT + 1):
        board = decode_board(read_level_sector(track_dir, level - 1))
        image = render_level(board, sprites, scale)
        image.save(level_image_path(output_dir, level), optimize=True)
    return LEVEL_COUNT


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("tex", type=Path, help="path to sprite_tables.tex")
    parser.add_argument(
        "track_dir", type=Path, help="directory with the track_XX.asm files"
    )
    parser.add_argument("output_dir", type=Path, help="directory for the PNG files")
    parser.add_argument(
        "--scale", type=int, default=DEFAULT_SCALE, help="pixel enlargement, from 1"
    )
    args = parser.parse_args(argv)
    if args.scale < 1:
        print(f"level_images: scale starts at 1, got {args.scale}", file=sys.stderr)
        return 1

    try:
        count = write_level_images(
            args.tex, args.track_dir, args.output_dir, args.scale
        )
    except (OSError, ValueError) as error:
        print(f"level_images: {error}", file=sys.stderr)
        return 1

    print(f"Wrote {count} level images into {args.output_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

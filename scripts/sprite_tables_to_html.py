"""Convert XekriRedmane's `sprite_tables.tex` into the HTML sprite catalog.

`main.nw` pulls the catalog of all 104 sprites into Chapter 3 with the line
`\\input{sprite_tables.tex}`. That file holds one LaTeX table per pair of
sprites, with one coloured cell per pixel (`\\bk0` black, `\\bl0` blue,
`\\bw0` white, `\\bo0` orange). The colours were worked out by XekriRedmane;
this script only changes the form, from LaTeX cells to HTML cells.

The catalog is written into `research/main.nw-edited.md`, between two marker
comments on lines of their own:

    <!-- sprite-catalog: begin -->
    <!-- sprite-catalog: end -->

Everything between them is replaced; the rest of the file is left alone, so
the conversion can be repeated at any time (`make sprite-catalog`).

The generated HTML contains no blank lines. Markdown ends a raw HTML block at
the first blank line, so a blank line would break the catalog apart.

Usage:
    python scripts/sprite_tables_to_html.py SPRITE_TABLES_TEX MARKDOWN_FILE
"""

import argparse
import re
import sys
from pathlib import Path

SPRITE_COUNT = 104
ROWS_PER_SPRITE = 11
PIXELS_PER_ROW = 14

BEGIN_MARKER = "<!-- sprite-catalog: begin -->"
END_MARKER = "<!-- sprite-catalog: end -->"

# LaTeX colour macro -> CSS class of the pixel cell (see `scripts/web/style.css`).
CELL_CLASSES = {"\\bk0": "k", "\\bl0": "b", "\\bw0": "w", "\\bo0": "o"}

SPRITE_TITLE = re.compile(r"\\multicolumn\{\d+\}\{c\}\{Sprite (\d+)\}")
DATA_ROW = re.compile(r"^\d+\s*&")


def parse_sprite_tables(tex: str) -> dict[int, list[str]]:
    """Return {sprite number: 11 rows of 14 cell classes, e.g. "kkbbw..."}.

    Each table has one title line naming its sprites, followed by rows that
    start with the row number. Within a row, each sprite's 14 cells are
    separated from the next sprite's by an empty cell.
    """
    sprites: dict[int, list[str]] = {}
    current_numbers: list[int] = []
    for line in tex.splitlines():
        line = line.strip()
        titles = SPRITE_TITLE.findall(line)
        if titles:
            current_numbers = [int(number) for number in titles]
            for number in current_numbers:
                if number in sprites:
                    raise ValueError(f"Sprite {number} appears twice")
                sprites[number] = []
            continue
        if not DATA_ROW.match(line):
            continue
        cells = [cell.strip() for cell in line.removesuffix("\\\\").split("&")]
        groups = split_into_sprites(cells[1:])
        if len(groups) != len(current_numbers):
            raise ValueError(
                f"Row {cells[0]!r} has {len(groups)} sprites, "
                f"expected {len(current_numbers)}"
            )
        for number, group in zip(current_numbers, groups):
            sprites[number].append("".join(cell_class(cell) for cell in group))
    check_sprites(sprites)
    return sprites


def split_into_sprites(cells: list[str]) -> list[list[str]]:
    """Group a row's cells into sprites, using the empty cells as separators."""
    groups: list[list[str]] = []
    current: list[str] = []
    for cell in cells:
        if cell:
            current.append(cell)
        elif current:
            groups.append(current)
            current = []
    if current:
        groups.append(current)
    return groups


def cell_class(macro: str) -> str:
    """Translate one LaTeX colour macro into its CSS class letter."""
    if macro not in CELL_CLASSES:
        raise ValueError(f"Unknown cell {macro!r}")
    return CELL_CLASSES[macro]


def check_sprites(sprites: dict[int, list[str]]) -> None:
    """Fail loudly if the input does not have the shape `main.nw` describes."""
    if sorted(sprites) != list(range(SPRITE_COUNT)):
        raise ValueError(f"Expected sprites 0 to {SPRITE_COUNT - 1}")
    for number, rows in sprites.items():
        if len(rows) != ROWS_PER_SPRITE:
            raise ValueError(f"Sprite {number} has {len(rows)} rows")
        for row in rows:
            if len(row) != PIXELS_PER_ROW:
                raise ValueError(f"Sprite {number} has a row of {len(row)} pixels")


def render_catalog(sprites: dict[int, list[str]]) -> str:
    """Render all sprites as one flowing block of captioned pixel tables."""
    lines = ['<div class="sprite-catalog">']
    for number in sorted(sprites):
        lines.append(f'<figure class="sprite"><figcaption>Sprite {number}</figcaption>')
        lines.append('<table class="spritegrid">')
        for row in sprites[number]:
            cells = "".join(f'<td class="{css}"></td>' for css in row)
            lines.append(f"<tr>{cells}</tr>")
        lines.append("</table></figure>")
    lines.append("</div>")
    return "\n".join(lines)


def replace_between_markers(
    markdown: str,
    html: str,
    begin_marker: str = BEGIN_MARKER,
    end_marker: str = END_MARKER,
) -> str:
    """Put `html` between the two marker lines, replacing what was there.

    The markers default to the sprite catalog's; `level_catalog.py` passes
    its own.
    """
    lines = markdown.split("\n")
    begin = [i for i, line in enumerate(lines) if line.strip() == begin_marker]
    end = [i for i, line in enumerate(lines) if line.strip() == end_marker]
    if len(begin) != 1 or len(end) != 1 or begin[0] > end[0]:
        raise ValueError(
            f"Expected exactly one {begin_marker!r} line followed by "
            f"exactly one {end_marker!r} line"
        )
    new_lines = lines[: begin[0] + 1] + html.split("\n") + lines[end[0] :]
    return "\n".join(new_lines)


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("tex", type=Path, help="path to sprite_tables.tex")
    parser.add_argument("markdown", type=Path, help="Markdown file to update in place")
    args = parser.parse_args(argv)

    try:
        sprites = parse_sprite_tables(args.tex.read_text(encoding="utf-8"))
        markdown = args.markdown.read_text(encoding="utf-8")
        updated = replace_between_markers(markdown, render_catalog(sprites))
    except (OSError, ValueError) as error:
        print(f"sprite_tables_to_html: {error}", file=sys.stderr)
        return 1

    args.markdown.write_text(updated, encoding="utf-8")
    print(f"Wrote {len(sprites)} sprites into {args.markdown}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

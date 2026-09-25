"""Write the catalog of level images into Chapter 6 of `main.nw-edited.md`.

The images are made by `level_images.py` (`make level-images`). The catalog
shows each level as a thumbnail, 140 pixels wide, five to a row; a click
opens the full image. 140 is a quarter of the images' 560 pixels, so the
thumbnails stay sharp.

The catalog is written into `research/main.nw-edited.md`, between two
marker comments on lines of their own:

    <!-- level-catalog: begin -->
    <!-- level-catalog: end -->

Everything between them is replaced; the rest of the file is left alone, so
the catalog can be rewritten at any time (`make level-catalog`). This uses
the marker code of `sprite_tables_to_html.py`.

The generated HTML contains no blank lines. Markdown ends a raw HTML block at
the first blank line, so a blank line would break the catalog apart.

Usage:
    python scripts/level_catalog.py IMAGE_DIR MARKDOWN_FILE
"""

import argparse
import sys
from pathlib import Path

from level_extractor import BOARD_COLUMNS, BOARD_ROWS, LEVEL_COUNT
from level_images import CELL_HEIGHT, CELL_WIDTH, level_image_path
from sprite_tables_to_html import replace_between_markers

BEGIN_MARKER = "<!-- level-catalog: begin -->"
END_MARKER = "<!-- level-catalog: end -->"

# Where the images are, seen from the HTML pages: `weave_html.py` copies
# `images/` next to them.
IMAGE_URL_DIR = Path("images/levels")

# A level is 280 x 176 image pixels; the thumbnail shows it at half that.
THUMBNAIL_WIDTH = BOARD_COLUMNS * CELL_WIDTH // 2
THUMBNAIL_HEIGHT = BOARD_ROWS * CELL_HEIGHT // 2


def check_images(image_dir: Path) -> None:
    """Fail if an image for one of the levels is missing."""
    missing = [
        level_image_path(image_dir, level).name
        for level in range(1, LEVEL_COUNT + 1)
        if not level_image_path(image_dir, level).is_file()
    ]
    if missing:
        raise ValueError(
            f"{len(missing)} level images missing in {image_dir}, "
            f"first {missing[0]}; run `make level-images` first"
        )


def render_catalog() -> str:
    """Render all levels as one flowing block of linked, captioned thumbnails."""
    lines = ['<div class="level-catalog">']
    for level in range(1, LEVEL_COUNT + 1):
        url = level_image_path(IMAGE_URL_DIR, level).as_posix()
        lines.append(
            f'<figure class="level"><figcaption>Level {level}</figcaption>'
            f'<a href="{url}"><img src="{url}" alt="Level {level}" '
            f'width="{THUMBNAIL_WIDTH}" height="{THUMBNAIL_HEIGHT}" loading="lazy">'
            "</a></figure>"
        )
    lines.append("</div>")
    return "\n".join(lines)


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("image_dir", type=Path, help="directory with the level PNGs")
    parser.add_argument("markdown", type=Path, help="Markdown file to update in place")
    args = parser.parse_args(argv)

    try:
        check_images(args.image_dir)
        markdown = args.markdown.read_text(encoding="utf-8")
        updated = replace_between_markers(
            markdown, render_catalog(), BEGIN_MARKER, END_MARKER
        )
    except (OSError, ValueError) as error:
        print(f"level_catalog: {error}", file=sys.stderr)
        return 1

    args.markdown.write_text(updated, encoding="utf-8")
    print(f"Wrote {LEVEL_COUNT} levels into {args.markdown}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

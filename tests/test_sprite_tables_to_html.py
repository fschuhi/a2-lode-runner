"""Specify the conversion of `sprite_tables.tex` into the HTML sprite catalog.

The real input is XekriRedmane's file in `reference/lode_runner_reveng/`.
Small inline inputs cover the error cases and the marker replacement.
"""

import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

import sprite_tables_to_html as converter  # noqa: E402

REAL_TEX = PROJECT_ROOT / "reference" / "lode_runner_reveng" / "sprite_tables.tex"


@pytest.fixture(scope="module")
def real_sprites() -> dict[int, list[str]]:
    return converter.parse_sprite_tables(REAL_TEX.read_text(encoding="utf-8"))


def test_real_file_has_all_sprites_in_shape(real_sprites: dict[int, list[str]]) -> None:
    assert sorted(real_sprites) == list(range(104))
    for rows in real_sprites.values():
        assert len(rows) == 11
        assert all(len(row) == 14 for row in rows)
        assert set("".join(rows)) <= {"k", "b", "w", "o"}


def test_second_sprite_of_a_pair_is_read_after_the_separator(
    real_sprites: dict[int, list[str]],
) -> None:
    # First data row of the first table, right-hand sprite (Sprite 1).
    assert real_sprites[0][0] == "k" * 14
    assert real_sprites[1][0] == "bbbbbkkkbkkkkk"


def test_catalog_has_one_figure_per_sprite_and_no_blank_lines(
    real_sprites: dict[int, list[str]],
) -> None:
    html = converter.render_catalog(real_sprites)
    assert html.count('<figure class="sprite">') == 104
    assert "<figcaption>Sprite 103</figcaption>" in html
    assert html.count('<td class="') == 104 * 11 * 14
    # A blank line would end the raw HTML block in Markdown.
    assert "\n\n" not in html


def test_crlf_input_parses_like_lf() -> None:
    tex = REAL_TEX.read_text(encoding="utf-8")
    assert converter.parse_sprite_tables(
        tex.replace("\n", "\r\n")
    ) == converter.parse_sprite_tables(tex)


def test_wrong_row_length_is_rejected() -> None:
    tex = REAL_TEX.read_text(encoding="utf-8").replace("\\bk0 & ", "", 1)
    with pytest.raises(ValueError):
        converter.parse_sprite_tables(tex)


def test_unknown_cell_is_rejected() -> None:
    with pytest.raises(ValueError, match="Unknown cell"):
        converter.cell_class("\\bx0")


MARKDOWN = "\n".join(
    [
        "Before.",
        "",
        converter.BEGIN_MARKER,
        "old catalog",
        converter.END_MARKER,
        "",
        "After.",
    ]
)


def test_markers_replace_only_the_catalog() -> None:
    result = converter.replace_between_markers(MARKDOWN, "<div>new</div>")
    assert result == MARKDOWN.replace("old catalog", "<div>new</div>")


def test_running_twice_gives_the_same_result() -> None:
    once = converter.replace_between_markers(MARKDOWN, "<div>new</div>")
    assert converter.replace_between_markers(once, "<div>new</div>") == once


def test_missing_marker_is_rejected() -> None:
    without_end = MARKDOWN.replace(converter.END_MARKER, "")
    with pytest.raises(ValueError):
        converter.replace_between_markers(without_end, "<div>new</div>")

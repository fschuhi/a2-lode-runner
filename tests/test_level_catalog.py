"""Specify the level catalog that is written into Chapter 6.

The images are stand-ins: empty files with the right names. The Markdown is a
small generated file with the two markers.
"""

import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

import level_catalog as catalog  # noqa: E402


def write_image_stand_ins(image_dir: Path, levels: range = range(1, 151)) -> None:
    image_dir.mkdir(parents=True, exist_ok=True)
    for level in levels:
        (image_dir / f"level-{level:03d}.png").write_bytes(b"")


MARKDOWN = "\n".join(
    [
        "Before.",
        "",
        catalog.BEGIN_MARKER,
        "old catalog",
        catalog.END_MARKER,
        "",
        "After.",
    ]
)


# --- The HTML ---


def test_catalog_has_one_linked_thumbnail_per_level() -> None:
    html = catalog.render_catalog()
    assert html.count('<figure class="level">') == 150
    assert html.startswith('<div class="level-catalog">\n')
    assert html.endswith("\n</div>")
    assert (
        '<figure class="level"><figcaption>Level 1</figcaption>'
        '<a href="images/levels/level-001.png">'
        '<img src="images/levels/level-001.png" alt="Level 1" '
        'width="140" height="88" loading="lazy"></a></figure>'
    ) in html
    assert "<figcaption>Level 150</figcaption>" in html


def test_catalog_has_no_blank_lines() -> None:
    # A blank line would end the raw HTML block in Markdown.
    assert "\n\n" not in catalog.render_catalog()


# --- Checking the images ---


def test_complete_images_pass(tmp_path: Path) -> None:
    write_image_stand_ins(tmp_path)
    catalog.check_images(tmp_path)


def test_missing_image_is_named(tmp_path: Path) -> None:
    write_image_stand_ins(tmp_path, range(2, 151))
    with pytest.raises(ValueError, match="1 level images missing.*level-001.png"):
        catalog.check_images(tmp_path)


# --- Writing the Markdown ---


def test_main_fills_the_level_markers_and_can_run_twice(tmp_path: Path) -> None:
    write_image_stand_ins(tmp_path / "levels")
    markdown = tmp_path / "chapter.md"
    markdown.write_text(MARKDOWN, encoding="utf-8")

    assert catalog.main([str(tmp_path / "levels"), str(markdown)]) == 0
    once = markdown.read_text(encoding="utf-8")
    assert once == MARKDOWN.replace("old catalog", catalog.render_catalog())

    assert catalog.main([str(tmp_path / "levels"), str(markdown)]) == 0
    assert markdown.read_text(encoding="utf-8") == once


def test_main_leaves_sprite_markers_alone(tmp_path: Path) -> None:
    # Only the level markers count; a file with just the sprite markers fails.
    write_image_stand_ins(tmp_path / "levels")
    markdown = tmp_path / "chapter.md"
    sprite_only = "<!-- sprite-catalog: begin -->\n<!-- sprite-catalog: end -->\n"
    markdown.write_text(sprite_only, encoding="utf-8")
    assert catalog.main([str(tmp_path / "levels"), str(markdown)]) == 1
    assert markdown.read_text(encoding="utf-8") == sprite_only


def test_main_fails_without_images(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    markdown = tmp_path / "chapter.md"
    markdown.write_text(MARKDOWN, encoding="utf-8")
    assert catalog.main([str(tmp_path / "levels"), str(markdown)]) == 1
    assert "make level-images" in capsys.readouterr().err
    assert markdown.read_text(encoding="utf-8") == MARKDOWN

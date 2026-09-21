"""Specify the first compact woven Markdown chapter export.

Source ranges are one-based and inclusive. A code fragment's range includes
its definition header but excludes the following documentation marker.
Navigation uses the whole input file, even when exporting only one chapter.
"""

from pathlib import Path
import re
import subprocess
import sys

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
TOOL_PATH = PROJECT_ROOT / "scripts" / "nwtool.py"
FIXTURE_PATH = Path(__file__).parent / "fixtures" / "mini.nw"
REAL_SOURCE = PROJECT_ROOT / "reference" / "lode_runner_reveng" / "main.nw"

CHAPTER_HEADING = re.compile(r"^(?:@ )?\\chapter\{([^}]*)\}")
GENERATED_CHAPTERS = {"Defined Chunks", "Index"}


@pytest.fixture
def source_path(tmp_path: Path) -> Path:
    """Exercise CRLF input without depending on checkout line endings."""
    source_text = FIXTURE_PATH.read_text(encoding="utf-8")
    path = tmp_path / "mini.nw"
    path.write_bytes(source_text.replace("\n", "\r\n").encode("utf-8"))
    return path


def export_chapter(
    source_path: Path,
    output_path: Path,
    chapter: int,
) -> str:
    """Run the public chapter command and return its Markdown output."""
    assert TOOL_PATH.is_file(), (
        "scripts/nwtool.py does not exist yet. "
        "This is expected during the tests-only step."
    )

    result = subprocess.run(
        [
            sys.executable,
            str(TOOL_PATH),
            "chapter",
            str(chapter),
            "--nw",
            str(source_path),
            "-o",
            str(output_path),
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, (
        f"Chapter export failed.\nstdout:\n{result.stdout}\n"
        f"stderr:\n{result.stderr}"
    )
    assert output_path.is_file(), "The command did not create the requested file."
    return output_path.read_text(encoding="utf-8")


def fragment_locator(
    source_path: Path,
    name: str,
    occurrence: int = 0,
) -> str:
    """Build the expected locator from the fixture's physical source lines."""
    lines = source_path.read_text(encoding="utf-8").splitlines()
    starts = [
        index for index, line in enumerate(lines) if line == f"<<{name}>>="
    ]
    start = starts[occurrence]
    end = start + 1

    while end < len(lines):
        line = lines[end]
        if line == "@" or line.startswith("@ ") or (
            line.startswith("<<") and line.endswith(">>=")
        ):
            break
        end += 1

    return f"`{name}` (lines {start + 1}-{end})"


def chunk_blocks(markdown: str) -> list[str]:
    """Separate rendered fragments so footer checks stay local to a block."""
    return markdown.split("**Chunk:** ")[1:]


def footer(block: str, label: str) -> str:
    """Read a labeled, single-line navigation footer."""
    prefix = f"**{label}:** "
    matches = [line for line in block.splitlines() if line.startswith(prefix)]
    assert len(matches) == 1, f"Expected one {label!r} footer in:\n{block}"
    return matches[0][len(prefix) :].rstrip()


def selectable_chapter_range(
    source_path: Path, number: int
) -> tuple[str, int, int]:
    """Return title and inclusive 1-based line range for a selectable chapter."""
    lines = source_path.read_text(encoding="utf-8").splitlines()
    headings: list[tuple[str, int]] = []
    for index, line in enumerate(lines):
        match = CHAPTER_HEADING.match(line)
        if match:
            headings.append((match.group(1), index))

    selectable: list[tuple[str, int, int]] = []
    for index, (title, start) in enumerate(headings):
        if title in GENERATED_CHAPTERS:
            continue
        end = headings[index + 1][1] if index + 1 < len(headings) else len(lines)
        selectable.append((title, start, end))

    title, start, end = selectable[number - 1]
    return title, start + 1, end


def test_chapter_renders_headings_and_prose_in_source_order(
    source_path: Path,
    tmp_path: Path,
) -> None:
    markdown = export_chapter(source_path, tmp_path / "chapter.md", 1)

    expected_parts = [
        "# Chapter 1: First chapter",
        "This chapter explains `WORKER`.",
        "## Running the worker",
        "The worker calls a helper defined in another chapter.",
        f"**Chunk:** {fragment_locator(source_path, '*')}",
        f"**Chunk:** {fragment_locator(source_path, 'worker')}",
        "The worker continues below.",
        f"**Chunk:** {fragment_locator(source_path, 'worker', 1)}",
        "### A diagram",
    ]

    positions = [markdown.index(part) for part in expected_parts]
    assert positions == sorted(positions)
    assert r"\documentclass" not in markdown
    assert r"\begin{document}" not in markdown
    assert "@ %def" not in markdown


def test_assembly_is_preserved_without_per_line_numbers(
    source_path: Path,
    tmp_path: Path,
) -> None:
    markdown = export_chapter(source_path, tmp_path / "chapter.md", 1)

    assert (
        "```asm\n"
        "WORKER:\n"
        "    JSR HELPER\n"
        "    <<shared step>>\n"
        "```"
    ) in markdown
    assert "```asm\n    LDA VALUE\n    RTS\n```" in markdown
    assert "\r" not in (tmp_path / "chapter.md").read_bytes().decode("utf-8")


def test_continuations_have_source_ranges_and_previous_next_locators(
    source_path: Path,
    tmp_path: Path,
) -> None:
    markdown = export_chapter(source_path, tmp_path / "chapter.md", 1)
    blocks = chunk_blocks(markdown)

    assert len(blocks) == 3
    first_worker = blocks[1]
    second_worker = blocks[2]

    assert first_worker.startswith(fragment_locator(source_path, "worker"))
    assert second_worker.startswith(fragment_locator(source_path, "worker", 1))
    assert footer(first_worker, "Previous") == "None"
    assert footer(first_worker, "Next") == fragment_locator(
        source_path, "worker", 1
    )
    assert footer(second_worker, "Previous") == fragment_locator(
        source_path, "worker"
    )
    assert footer(second_worker, "Next") == "None"


def test_local_footers_show_identifier_and_chunk_relationships(
    source_path: Path,
    tmp_path: Path,
) -> None:
    markdown = export_chapter(source_path, tmp_path / "chapter.md", 1)
    root, first_worker, second_worker = chunk_blocks(markdown)

    assert "`WORKER`" in footer(first_worker, "Defines")
    assert "`HELPER`" in footer(first_worker, "Uses")
    assert fragment_locator(source_path, "helper") in footer(
        first_worker, "Uses"
    )
    assert "`VALUE`" in footer(second_worker, "Uses")
    assert fragment_locator(source_path, "helper") in footer(
        second_worker, "Uses"
    )
    assert fragment_locator(source_path, "shared step") in footer(
        first_worker, "References"
    )
    assert fragment_locator(source_path, "*") in footer(
        first_worker, "Referenced by"
    )
    assert fragment_locator(source_path, "worker") in footer(root, "References")
    assert fragment_locator(source_path, "worker", 1) in footer(
        root, "References"
    )


def test_cross_chapter_dependencies_are_located_not_copied(
    source_path: Path,
    tmp_path: Path,
) -> None:
    markdown = export_chapter(source_path, tmp_path / "chapter.md", 1)

    assert fragment_locator(source_path, "helper") in markdown
    assert fragment_locator(source_path, "shared step") in markdown
    assert "This prose belongs only to the second chapter." not in markdown
    assert "HELPER:\n" not in markdown
    assert "VALUE EQU $10" not in markdown
    assert "    NOP" not in markdown


def test_unsupported_diagram_is_preserved_as_fenced_latex(
    source_path: Path,
    tmp_path: Path,
) -> None:
    markdown = export_chapter(source_path, tmp_path / "chapter.md", 1)

    assert (
        "```latex\n"
        "\\begin{tikzpicture}\n"
        "\\node {Worker};\n"
        "\\end{tikzpicture}\n"
        "```"
    ) in markdown


def test_second_chapter_has_reverse_identifier_use_locators(
    source_path: Path,
    tmp_path: Path,
) -> None:
    markdown = export_chapter(source_path, tmp_path / "chapter.md", 2)

    assert "# Chapter 2: Second chapter" in markdown
    assert "This prose belongs only to the second chapter." in markdown
    assert "This chapter explains" not in markdown

    helper, shared_step = chunk_blocks(markdown)
    definitions = footer(helper, "Defines")

    assert "`HELPER`" in definitions
    assert "`VALUE`" in definitions
    assert fragment_locator(source_path, "worker") in definitions
    assert fragment_locator(source_path, "worker", 1) in definitions
    assert fragment_locator(source_path, "worker") in footer(
        shared_step, "Referenced by"
    )


@pytest.mark.skipif(
    not REAL_SOURCE.is_file(),
    reason="bundled main.nw is not present",
)
def test_real_chapter_6_export_smoke(tmp_path: Path) -> None:
    markdown = export_chapter(REAL_SOURCE, tmp_path / "chapter6.md", 6)
    title, first_line, last_line = selectable_chapter_range(REAL_SOURCE, 6)

    assert title == "Levels"
    assert markdown.startswith("# Chapter 6: Levels\n")
    assert f"Source: `main.nw`, lines {first_line}-{last_line}." in markdown
    assert "DRAW_LEVEL_PAGE2" in markdown
    assert "**Chunk:** `level draw routine`" in markdown
    assert r"\documentclass" not in markdown
    assert r"\begin{document}" not in markdown


# ---------------------------------------------------------------------------
# `index` command
#
# One flat, alphabetical list per section (chapters table, chunk names,
# identifiers), built from the whole source regardless of which chapter a
# name belongs to. A handful of real chunk names span multiple chapters
# (aggregating dispatch tables); their chapter field lists every chapter
# they're defined in, comma-separated, not range-collapsed.
# ---------------------------------------------------------------------------


def export_index(
    source_path: Path,
    output_path: Path,
    name: str | None = None,
) -> str:
    """Run the public index command and return its Markdown output."""
    assert TOOL_PATH.is_file(), (
        "scripts/nwtool.py does not exist yet. "
        "This is expected during the tests-only step."
    )

    command = [
        sys.executable,
        str(TOOL_PATH),
        "index",
        "--nw",
        str(source_path),
        "-o",
        str(output_path),
    ]
    if name is not None:
        command.extend(["--name", name])

    result = subprocess.run(
        command,
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, (
        f"Index export failed.\nstdout:\n{result.stdout}\n"
        f"stderr:\n{result.stderr}"
    )
    assert output_path.is_file(), "The command did not create the requested file."
    return output_path.read_text(encoding="utf-8")


def index_entries(markdown: str, heading: str) -> list[str]:
    """Return the bullet lines under one '## heading' section."""
    section = markdown.split(f"## {heading}\n", 1)[1]
    section = section.split("\n## ", 1)[0]
    return [line for line in section.splitlines() if line.startswith("- ")]


def test_index_chapter_table_lists_number_title_range_and_chunk_definitions(
    source_path: Path,
    tmp_path: Path,
) -> None:
    markdown = export_index(source_path, tmp_path / "index.md")

    assert "# Index" in markdown
    assert "| 1 | First chapter | 4-31 | 3 |" in markdown
    assert "| 2 | Second chapter | 32-45 | 2 |" in markdown


def test_index_chunk_entries_list_chapter_lines_defines_and_referrers(
    source_path: Path,
    tmp_path: Path,
) -> None:
    markdown = export_index(source_path, tmp_path / "index.md")
    chunks = index_entries(markdown, "Chunks")

    assert any(
        line.startswith("- `*` ")
        and "chapter 1" in line
        and "lines 10-11" in line
        and "defines: none" in line
        and "referenced by: none" in line
        for line in chunks
    )
    assert any(
        line.startswith("- `worker` ")
        and "chapter 1" in line
        and "lines 14-17, 22-24" in line
        and "defines: `WORKER`" in line
        and f"referenced by: {fragment_locator(source_path, '*')}" in line
        for line in chunks
    )
    assert any(
        line.startswith("- `shared step` ")
        and "chapter 2" in line
        and "lines 41-42" in line
        and "defines: none" in line
        and f"referenced by: {fragment_locator(source_path, 'worker')}" in line
        for line in chunks
    )
    assert any(
        line.startswith("- `helper` ")
        and "chapter 2" in line
        and "lines 35-38" in line
        and "defines: `HELPER`, `VALUE`" in line
        and "referenced by: none" in line
        for line in chunks
    )


def test_index_identifier_entries_list_definer_and_users(
    source_path: Path,
    tmp_path: Path,
) -> None:
    markdown = export_index(source_path, tmp_path / "index.md")
    identifiers = index_entries(markdown, "Identifiers")

    assert any(
        line.startswith("- `HELPER` ")
        and f"defined in {fragment_locator(source_path, 'helper')}" in line
        and f"used in {fragment_locator(source_path, 'worker')}" in line
        for line in identifiers
    )
    assert any(
        line.startswith("- `VALUE` ")
        and f"defined in {fragment_locator(source_path, 'helper')}" in line
        and f"used in {fragment_locator(source_path, 'worker', 1)}" in line
        for line in identifiers
    )
    assert any(
        line.startswith("- `WORKER` ")
        and f"defined in {fragment_locator(source_path, 'worker')}" in line
        and "used in: none" in line
        for line in identifiers
    )


def test_index_name_filter_limits_chunks_and_identifiers_but_not_chapters(
    source_path: Path,
    tmp_path: Path,
) -> None:
    markdown = export_index(source_path, tmp_path / "index.md", name="work")

    assert "First chapter" in markdown
    assert "Second chapter" in markdown

    chunks = index_entries(markdown, "Chunks")
    assert [line.split(" ", 2)[1] for line in chunks] == ["`worker`"]

    identifiers = index_entries(markdown, "Identifiers")
    assert [line.split(" ", 2)[1] for line in identifiers] == ["`WORKER`"]


@pytest.mark.skipif(
    not REAL_SOURCE.is_file(),
    reason="bundled main.nw is not present",
)
def test_real_index_export_smoke(tmp_path: Path) -> None:
    markdown = export_index(REAL_SOURCE, tmp_path / "index.md")

    chapter_rows = [
        line for line in markdown.splitlines() if re.match(r"^\| \d+ \|", line)
    ]
    assert len(chapter_rows) == 13

    chunks = index_entries(markdown, "Chunks")
    assert len(chunks) == 181

    identifiers = index_entries(markdown, "Identifiers")
    assert len(identifiers) == 337

    level_draw = next(
        line for line in chunks if line.startswith("- `level draw routine` ")
    )
    lines_field = level_draw.split("lines ", 1)[1].split(";", 1)[0]
    assert len(re.findall(r"\d+-\d+", lines_field)) == 16

    # A handful of real chunk names span multiple chapters (dispatch tables
    # accumulated chapter by chapter); their chapter field lists all of them.
    defines_entry = next(line for line in chunks if line.startswith("- `defines` "))
    chapters_field = defines_entry.split("chapters ", 1)[1].split(";", 1)[0]
    assert ", " in chapters_field


# ---------------------------------------------------------------------------
# `chunk` command
#
# Every continuation of the named chunk (reusing the exact chapter footer
# format), then, one level deep, every chunk it references by name. Exact
# name match only -- `index --name` is the substring-search entry point.
# ---------------------------------------------------------------------------


def export_chunk(
    source_path: Path,
    output_path: Path,
    name: str,
    max_lines: int | None = None,
) -> subprocess.CompletedProcess[str]:
    """Run the public chunk command and return the completed process."""
    assert TOOL_PATH.is_file(), (
        "scripts/nwtool.py does not exist yet. "
        "This is expected during the tests-only step."
    )

    command = [
        sys.executable,
        str(TOOL_PATH),
        "chunk",
        name,
        "--nw",
        str(source_path),
        "-o",
        str(output_path),
    ]
    if max_lines is not None:
        command.extend(["--max-lines", str(max_lines)])

    return subprocess.run(
        command,
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def run_chunk(
    source_path: Path,
    output_path: Path,
    name: str,
    max_lines: int | None = None,
) -> str:
    """Run `chunk` and return its Markdown, asserting success."""
    result = export_chunk(source_path, output_path, name, max_lines)
    assert result.returncode == 0, (
        f"Chunk export failed.\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    )
    assert output_path.is_file(), "The command did not create the requested file."
    return output_path.read_text(encoding="utf-8")


def test_chunk_renders_every_continuation_with_locators_and_neighbors(
    source_path: Path,
    tmp_path: Path,
) -> None:
    markdown = run_chunk(source_path, tmp_path / "chunk.md", "worker")

    assert "# Chunk: `worker`" in markdown
    assert "2 definition(s)." in markdown

    blocks = chunk_blocks(markdown)
    first_worker, second_worker = blocks[0], blocks[1]

    assert first_worker.startswith(fragment_locator(source_path, "worker"))
    assert second_worker.startswith(fragment_locator(source_path, "worker", 1))
    assert footer(first_worker, "Next") == fragment_locator(
        source_path, "worker", 1
    )
    assert footer(second_worker, "Previous") == fragment_locator(
        source_path, "worker"
    )


def test_chunk_referenced_chunks_render_one_level_deep(
    source_path: Path,
    tmp_path: Path,
) -> None:
    markdown = run_chunk(source_path, tmp_path / "chunk.md", "worker")

    assert "## Referenced chunks" in markdown
    referenced_section = markdown.split("## Referenced chunks", 1)[1]
    blocks = chunk_blocks(referenced_section)

    assert len(blocks) == 1
    assert blocks[0].startswith(fragment_locator(source_path, "shared step"))

    # `helper` is only reached through identifier use (JSR HELPER), never
    # through a <<helper>> chunk reference, so it must not appear here.
    assert "`helper`" not in referenced_section


def test_chunk_requires_an_exact_name_and_reports_a_clear_miss(
    source_path: Path,
    tmp_path: Path,
) -> None:
    result = export_chunk(source_path, tmp_path / "chunk.md", "work")

    assert result.returncode == 1
    assert "work" in result.stderr
    assert "index --name" in result.stderr
    assert not (tmp_path / "chunk.md").is_file()


def test_chunk_max_lines_truncates_body_and_notes_it(
    source_path: Path,
    tmp_path: Path,
) -> None:
    markdown = run_chunk(source_path, tmp_path / "chunk.md", "helper", max_lines=1)
    (block,) = chunk_blocks(markdown)

    assert "```asm\nHELPER:\n```" in block
    assert "VALUE EQU $10" not in block
    assert footer(block, "Truncated") == "showing first 1 of 3 lines"


def test_chunk_default_max_lines_leaves_short_fragments_untouched(
    source_path: Path,
    tmp_path: Path,
) -> None:
    markdown = run_chunk(source_path, tmp_path / "chunk.md", "helper")
    (block,) = chunk_blocks(markdown)

    assert "VALUE EQU $10" in block
    assert "**Truncated:**" not in block


@pytest.mark.skipif(
    not REAL_SOURCE.is_file(),
    reason="bundled main.nw is not present",
)
def test_real_chunk_export_smoke(tmp_path: Path) -> None:
    markdown = run_chunk(REAL_SOURCE, tmp_path / "chunk.md", "level draw routine")

    assert "# Chunk: `level draw routine`" in markdown
    assert "16 definition(s)." in markdown

    own_section = markdown.split("## Referenced chunks", 1)[0]
    assert len(chunk_blocks(own_section)) == 16
    assert "**Truncated:**" not in own_section

    referenced_section = markdown.split("## Referenced chunks", 1)[1]
    assert (
        "`set active row pointer [[PTR1]] for [[Y]]`" in referenced_section
    )
    assert (
        "`set active and background row pointers [[PTR1]] and [[PTR2]] "
        "for [[Y]]`" in referenced_section
    )

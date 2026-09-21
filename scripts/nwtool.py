#!/usr/bin/env python3
"""Export a Noweb chapter as compact woven Markdown.

Reuse the bundled weaver for chunk and identifier relationships. Preserve
source prose and assembly, adding source-line locators and local navigation.
Unsupported LaTeX environments remain verbatim inside fenced code blocks.

Usage:
    python scripts/nwtool.py chapter 6
    python scripts/nwtool.py chapter 1 --nw tests/fixtures/mini.nw -o tmp/mini.md
    python scripts/nwtool.py index
    python scripts/nwtool.py index --name LEVEL
"""

from __future__ import annotations

import argparse
from pathlib import Path
import re
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
WEAVER_DIRECTORY = PROJECT_ROOT / "reference" / "lode_runner_reveng"
DEFAULT_SOURCE = WEAVER_DIRECTORY / "main.nw"

sys.path.insert(0, str(WEAVER_DIRECTORY))
try:
    import weave
except ImportError:
    print(
        f"Cannot import the bundled weaver; expected {WEAVER_DIRECTORY / 'weave.py'}.",
        file=sys.stderr,
    )
    raise SystemExit(1)


CHAPTER = re.compile(r"^(?:@ )?\\chapter\{([^}]*)\}")
HEADING = re.compile(r"^\\(section|subsection|subsubsection)\{([^}]*)\}\s*$")
INLINE_CODE = re.compile(r"\[\[(.*?)\]\]")
ENVIRONMENT_START = re.compile(r"^\\begin\{([^}]*)\}")
ENVIRONMENT_MARKER = re.compile(r"\\(begin|end)\{([^}]*)\}")

GENERATED_CHAPTERS = {"Defined Chunks", "Index"}
HEADING_PREFIXES = {
    "section": "##",
    "subsection": "###",
    "subsubsection": "####",
}


def inline_code(text: str) -> str:
    """Convert Noweb inline code notation without rewriting other prose."""
    return INLINE_CODE.sub(lambda match: code_span(match.group(1)), text)


def code_span(text: str) -> str:
    """Keep names containing backticks valid in generated Markdown."""
    runs = re.findall(r"`+", text)
    delimiter = "`" * (max((len(run) for run in runs), default=0) + 1)
    padding = " " if text.startswith("`") or text.endswith("`") else ""
    return f"{delimiter}{padding}{text}{padding}{delimiter}"


def fenced_block(lines: list[str], language: str) -> str:
    """Preserve block contents, choosing a fence longer than embedded fences."""
    text = "\n".join(lines)
    runs = re.findall(r"`+", text)
    fence = "`" * max(3, max((len(run) + 1 for run in runs), default=3))
    return f"{fence}{language}\n{text}\n{fence}"


def find_chapters(lines: list[str]) -> list[tuple[str, int, int]]:
    """Return chapter titles with zero-based, end-exclusive source ranges.

    Generated index headings still delimit the preceding chapter, but are
    not selectable chapters themselves. The preamble belongs to no chapter.
    """
    headings: list[tuple[str, int]] = []
    for index, line in enumerate(lines):
        match = CHAPTER.match(line)
        if match:
            headings.append((match.group(1), index))

    chapters: list[tuple[str, int, int]] = []
    for index, (title, start) in enumerate(headings):
        end = headings[index + 1][1] if index + 1 < len(headings) else len(lines)
        if title not in GENERATED_CHAPTERS:
            chapters.append((title, start, end))
    return chapters


def chapter_number_for_line(chapters: list[tuple[str, int, int]], line: int) -> int | None:
    """Return the one-based chapter number containing a zero-based line."""
    for number, (_, start, end) in enumerate(chapters, 1):
        if start <= line < end:
            return number
    return None


def fragment_locator(chunk: weave.ChunkInfo) -> str:
    """Translate the weaver's boundaries to inclusive source-line locators."""
    return f"{code_span(chunk.name)} (lines {chunk.start + 1}-{chunk.end})"


def locator_list(chunks: list[weave.ChunkInfo]) -> str:
    """List fragments in source order without repeated entries."""
    unique = {chunk.start: chunk for chunk in chunks}
    return ", ".join(fragment_locator(unique[start]) for start in sorted(unique))


def build_index(
    code_chunks: list[weave.ChunkInfo],
) -> tuple[
    dict[str, list[weave.ChunkInfo]],
    dict[str, weave.ChunkInfo],
    dict[str, weave.ChunkInfo],
    dict[str, list[weave.ChunkInfo]],
]:
    """Group whole-source chunk and identifier relationships once.

    Shared by `chapter` (for local footers) and `index` (for the whole-file
    listing), so the two views can never quietly disagree with each other.
    """
    chunks_by_name: dict[str, list[weave.ChunkInfo]] = {}
    chunks_by_sublabel: dict[str, weave.ChunkInfo] = {}
    definitions: dict[str, weave.ChunkInfo] = {}
    identifier_users: dict[str, list[weave.ChunkInfo]] = {}

    for chunk in code_chunks:
        chunks_by_name.setdefault(chunk.name, []).append(chunk)
        chunks_by_sublabel[chunk.sublabel] = chunk
        for identifier in chunk.defines:
            definitions[identifier] = chunk
        for identifier in chunk.defines_used:
            identifier_users.setdefault(identifier, []).append(chunk)

    return chunks_by_name, chunks_by_sublabel, definitions, identifier_users


def render_fragment(
    chunk: weave.ChunkInfo,
    lines: list[str],
    chunks_by_name: dict[str, list[weave.ChunkInfo]],
    chunks_by_sublabel: dict[str, weave.ChunkInfo],
    definitions: dict[str, weave.ChunkInfo],
    identifier_users: dict[str, list[weave.ChunkInfo]],
    max_lines: int | None = None,
) -> str:
    """Render original assembly separately from generated navigation.

    `max_lines` bounds only this fragment's own assembly body (used by the
    `chunk` command, which can pull in a one-level reference to something
    large); `chapter` never passes it, so its output is unaffected.
    """
    previous = chunks_by_sublabel.get(chunk.prev_sublabel)
    following = chunks_by_sublabel.get(chunk.next_sublabel)

    defined_entries: list[str] = []
    for identifier in sorted(chunk.defines):
        users = identifier_users.get(identifier, [])
        entry = code_span(identifier)
        if users:
            entry += f" -- used in {locator_list(users)}"
        else:
            entry += " -- no indexed uses"
        defined_entries.append(entry)

    used_entries = [
        f"{code_span(identifier)} -- {fragment_locator(definitions[identifier])}"
        for identifier in sorted(chunk.defines_used)
    ]

    referenced_fragments = [
        definition
        for name in sorted(chunk.names_used)
        for definition in chunks_by_name[name]
    ]
    referring_fragments = [
        chunks_by_sublabel[sublabel] for sublabel in chunk.sublabels_used_in
    ]

    body = lines[chunk.start + 1 : chunk.end]
    total_lines = len(body)
    truncated = max_lines is not None and total_lines > max_lines
    if truncated:
        body = body[:max_lines]

    footer_lines = [
        f"**Previous:** {fragment_locator(previous) if previous else 'None'}",
        f"**Next:** {fragment_locator(following) if following else 'None'}",
        f"**Defines:** {'; '.join(defined_entries) or 'None'}",
        f"**Uses:** {'; '.join(used_entries) or 'None'}",
        f"**References:** {locator_list(referenced_fragments) or 'None'}",
        f"**Referenced by:** {locator_list(referring_fragments) or 'None'}",
    ]
    if truncated:
        footer_lines.insert(
            0, f"**Truncated:** showing first {max_lines} of {total_lines} lines"
        )

    return "\n\n".join(
        [
            f"**Chunk:** {fragment_locator(chunk)}",
            fenced_block(body, "asm"),
            "  \n".join(footer_lines),
        ]
    )


def render_prose(lines: list[str]) -> str:
    """Convert basic prose markup and preserve unsupported LaTeX.

    This is deliberately not a general LaTeX converter. An environment is
    kept whole, including nested environments. Standalone LaTeX commands
    are also fenced. Unsupported inline commands remain in the prose.
    """
    output: list[str] = []
    index = 0

    while index < len(lines):
        line = lines[index]

        if re.match(r"^@\s+%def(?:\s|$)", line):
            index += 1
            continue
        if line == "@":
            output.append("")
            index += 1
            continue
        if line.startswith("@ "):
            line = line[2:]

        # Document wrappers have no reading-view content.
        if line.strip() in {r"\begin{document}", r"\end{document}"}:
            index += 1
            continue

        heading = HEADING.match(line)
        if heading:
            prefix = HEADING_PREFIXES[heading.group(1)]
            output.extend(["", f"{prefix} {inline_code(heading.group(2))}", ""])
            index += 1
            continue

        environment = ENVIRONMENT_START.match(line)
        if environment:
            name = environment.group(1)
            block: list[str] = []
            depth = 0

            while index < len(lines):
                current = line if not block else lines[index]
                block.append(current)
                for marker in ENVIRONMENT_MARKER.finditer(current):
                    if marker.group(2) == name:
                        depth += 1 if marker.group(1) == "begin" else -1
                index += 1
                if depth == 0:
                    break

            output.extend(["", fenced_block(block, "latex"), ""])
            continue

        if line.lstrip().startswith("\\"):
            output.extend(["", fenced_block([line], "latex"), ""])
        else:
            output.append(inline_code(line))
        index += 1

    return "\n".join(output).strip()


def render_chapter(
    lines: list[str],
    chunks: list[weave.ChunkInfo],
    number: int,
    chapter: tuple[str, int, int],
    source_name: str,
) -> str:
    """Select chapter content while retaining whole-source navigation."""
    title, start, end = chapter
    code_chunks = [chunk for chunk in chunks if chunk.kind == "code"]

    chunks_by_name, chunks_by_sublabel, definitions, identifier_users = build_index(
        code_chunks
    )

    output = [
        f"# Chapter {number}: {inline_code(title)}",
        f"Source: {code_span(source_name)}, lines {start + 1}-{end}.",
        (
            "Navigation is generated from the full source. Defines and Uses "
            "follow the bundled weaver's identifier index; they are not a "
            "complete assembly symbol analysis. References lists included "
            "chunks; Referenced by lists chunks that include this named chunk. "
            "Locators refer to the original source, not this export."
        ),
    ]

    cursor = start + 1
    for chunk in code_chunks:
        if not start <= chunk.start < end:
            continue

        prose = render_prose(lines[cursor : chunk.start])
        if prose:
            output.append(prose)

        output.append(
            render_fragment(
                chunk,
                lines,
                chunks_by_name,
                chunks_by_sublabel,
                definitions,
                identifier_users,
            )
        )
        cursor = chunk.end

    prose = render_prose(lines[cursor:end])
    if prose:
        output.append(prose)

    return "\n\n".join(output) + "\n"


def render_index(
    lines: list[str],
    chunks: list[weave.ChunkInfo],
    chapters: list[tuple[str, int, int]],
    source_name: str,
    name_filter: str | None,
) -> str:
    """Render the whole-source chapter, chunk, and identifier map."""
    code_chunks = [chunk for chunk in chunks if chunk.kind == "code"]
    chunks_by_name, chunks_by_sublabel, definitions, identifier_users = build_index(
        code_chunks
    )
    needle = name_filter.lower() if name_filter else None

    output = [
        "# Index",
        f"Source: {code_span(source_name)}, lines 1-{len(lines)}.",
        (
            "Navigation is generated from the full source. Defines and Uses "
            "follow the bundled weaver's identifier index; they are not a "
            "complete assembly symbol analysis. References lists included "
            "chunks; Referenced by lists chunks that include this named chunk. "
            "Locators refer to the original source, not this export."
        ),
    ]

    table = [
        "## Chapters",
        "| # | Title | Lines | Chunk definitions |",
        "| --- | --- | --- | --- |",
    ]
    for number, (title, start, end) in enumerate(chapters, 1):
        count = sum(1 for chunk in code_chunks if start <= chunk.start < end)
        table.append(f"| {number} | {inline_code(title)} | {start + 1}-{end} | {count} |")
    output.append("\n".join(table))

    chunk_entries = ["## Chunks"]
    for name in sorted(chunks_by_name):
        if needle and needle not in name.lower():
            continue

        definitions_for_name = sorted(chunks_by_name[name], key=lambda c: c.start)
        chapter_numbers = sorted(
            {chapter_number_for_line(chapters, d.start) for d in definitions_for_name}
        )
        chapter_word = "chapter" if len(chapter_numbers) == 1 else "chapters"
        chapters_field = ", ".join(str(number) for number in chapter_numbers)
        lines_field = ", ".join(
            f"{d.start + 1}-{d.end}" for d in definitions_for_name
        )

        defined_here = sorted(
            {identifier for d in definitions_for_name for identifier in d.defines}
        )
        defines_field = (
            ", ".join(code_span(identifier) for identifier in defined_here) or "none"
        )

        # Every definition of one name shares the same referrers (the weaver
        # keys reference tracking by name, not by individual continuation).
        referring = [
            chunks_by_sublabel[sublabel]
            for sublabel in definitions_for_name[0].sublabels_used_in
        ]
        referenced_field = locator_list(referring) or "none"

        chunk_entries.append(
            f"- {code_span(name)} -- {chapter_word} {chapters_field}; "
            f"lines {lines_field}; defines: {defines_field}; "
            f"referenced by: {referenced_field}"
        )
    output.append("\n".join(chunk_entries))

    identifier_entries = ["## Identifiers"]
    for identifier in sorted(definitions):
        if needle and needle not in identifier.lower():
            continue

        definer = fragment_locator(definitions[identifier])
        used_locators = locator_list(identifier_users.get(identifier, []))
        used_field = f"used in {used_locators}" if used_locators else "used in: none"

        identifier_entries.append(
            f"- {code_span(identifier)} -- defined in {definer}; {used_field}"
        )
    output.append("\n".join(identifier_entries))

    return "\n\n".join(output) + "\n"


def render_chunk(
    lines: list[str],
    chunks: list[weave.ChunkInfo],
    name: str,
    source_name: str,
    max_lines: int | None,
) -> str:
    """Render every continuation of one named chunk, then what it references.

    Referenced chunks are one level deep only: their own References /
    Referenced by footers are locators, not further expansions.
    """
    code_chunks = [chunk for chunk in chunks if chunk.kind == "code"]
    chunks_by_name, chunks_by_sublabel, definitions, identifier_users = build_index(
        code_chunks
    )

    if name not in chunks_by_name:
        raise ValueError(f"No chunk named {name!r}. Try `index --name` to search.")

    def render_all(chunk_name: str) -> list[str]:
        return [
            render_fragment(
                chunk,
                lines,
                chunks_by_name,
                chunks_by_sublabel,
                definitions,
                identifier_users,
                max_lines,
            )
            for chunk in sorted(chunks_by_name[chunk_name], key=lambda c: c.start)
        ]

    definitions_for_name = chunks_by_name[name]
    output = [
        f"# Chunk: {code_span(name)}",
        f"Source: {code_span(source_name)}, {len(definitions_for_name)} definition(s).",
        (
            "Navigation is generated from the full source. Defines and Uses "
            "follow the bundled weaver's identifier index; they are not a "
            "complete assembly symbol analysis. Referenced chunks below are "
            "shown one level deep; their own References / Referenced by "
            "stay as locators. Locators refer to the original source, not "
            "this export."
        ),
        *render_all(name),
    ]

    referenced_names = sorted(
        {used_name for d in definitions_for_name for used_name in d.names_used}
        - {name}
    )
    if referenced_names:
        output.append("## Referenced chunks")
        for referenced_name in referenced_names:
            output.extend(render_all(referenced_name))

    return "\n\n".join(output) + "\n"


def slug(name: str) -> str:
    """Turn a chunk name into a filesystem-safe default filename fragment."""
    text = re.sub(r"[^0-9A-Za-z]+", "-", name.strip().lower()).strip("-")
    return text or "chunk"


def export_chapter(source: Path, output: Path, number: int) -> None:
    """Analyze the full input and write a selected chapter as UTF-8 Markdown."""
    with source.open(encoding="utf-8") as source_file:
        lines = source_file.read().splitlines()

    chapters = find_chapters(lines)
    if not chapters:
        raise ValueError("No selectable chapters found in the source.")
    if number < 1 or number > len(chapters):
        raise ValueError(f"Chapter must be between 1 and {len(chapters)}.")

    chunks = weave.Weaver().extract_chunk_info(lines, str(source), 0)
    markdown = render_chapter(
        lines,
        chunks,
        number,
        chapters[number - 1],
        source.name,
    )

    # An explicit output override must not overwrite the research source.
    if output.resolve() == source.resolve():
        raise ValueError("The output path must differ from the source path.")

    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="\n") as output_file:
        output_file.write(markdown)


def export_index(source: Path, output: Path, name_filter: str | None) -> None:
    """Analyze the full input and write the whole-source index as Markdown."""
    with source.open(encoding="utf-8") as source_file:
        lines = source_file.read().splitlines()

    chapters = find_chapters(lines)
    if not chapters:
        raise ValueError("No selectable chapters found in the source.")

    chunks = weave.Weaver().extract_chunk_info(lines, str(source), 0)
    markdown = render_index(lines, chunks, chapters, source.name, name_filter)

    # An explicit output override must not overwrite the research source.
    if output.resolve() == source.resolve():
        raise ValueError("The output path must differ from the source path.")

    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="\n") as output_file:
        output_file.write(markdown)


def export_chunk(
    source: Path,
    output: Path,
    name: str,
    max_lines: int | None,
) -> None:
    """Analyze the full input and write one named chunk as UTF-8 Markdown."""
    with source.open(encoding="utf-8") as source_file:
        lines = source_file.read().splitlines()

    chunks = weave.Weaver().extract_chunk_info(lines, str(source), 0)
    markdown = render_chunk(lines, chunks, name, source.name, max_lines)

    # An explicit output override must not overwrite the research source.
    if output.resolve() == source.resolve():
        raise ValueError("The output path must differ from the source path.")

    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="\n") as output_file:
        output_file.write(markdown)


def main() -> int:
    """Run the supported commands: woven Markdown chapter and index export."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    commands = parser.add_subparsers(dest="command", required=True)

    chapter_parser = commands.add_parser(
        "chapter",
        help="export one chapter as compact woven Markdown",
    )
    chapter_parser.add_argument("number", type=int, help="one-based chapter number")
    chapter_parser.add_argument(
        "--nw",
        type=Path,
        default=DEFAULT_SOURCE,
        help="source Noweb file (default: bundled main.nw)",
    )
    chapter_parser.add_argument(
        "-o",
        type=Path,
        default=None,
        help="output Markdown path (default: tmp/main-chNN.md)",
    )

    index_parser = commands.add_parser(
        "index",
        help=(
            "export the whole-source chapter, chunk, and identifier map "
            "(Defines/Uses follow the bundled weaver's identifier index, "
            "not a complete assembly symbol analysis)"
        ),
    )
    index_parser.add_argument(
        "--nw",
        type=Path,
        default=DEFAULT_SOURCE,
        help="source Noweb file (default: bundled main.nw)",
    )
    index_parser.add_argument(
        "-o",
        type=Path,
        default=None,
        help="output Markdown path (default: docs/main-nw/main-index.md)",
    )
    index_parser.add_argument(
        "--name",
        type=str,
        default=None,
        help="case-insensitive substring filter on chunk and identifier names",
    )

    chunk_parser = commands.add_parser(
        "chunk",
        help="export one named chunk's continuations and referenced chunks",
    )
    chunk_parser.add_argument("name", type=str, help="exact chunk name")
    chunk_parser.add_argument(
        "--nw",
        type=Path,
        default=DEFAULT_SOURCE,
        help="source Noweb file (default: bundled main.nw)",
    )
    chunk_parser.add_argument(
        "-o",
        type=Path,
        default=None,
        help="output Markdown path (default: tmp/chunk-<slug>.md)",
    )
    chunk_parser.add_argument(
        "--max-lines",
        type=int,
        default=200,
        help="truncate each rendered fragment's own body beyond this many lines",
    )

    args = parser.parse_args()

    if args.command == "chapter":
        output = args.o
        if output is None:
            output = PROJECT_ROOT / "tmp" / f"main-ch{args.number:02d}.md"
        try:
            export_chapter(args.nw, output, args.number)
        except (OSError, UnicodeError, ValueError) as error:
            print(f"nwtool: {error}", file=sys.stderr)
            return 1
    elif args.command == "index":
        output = args.o
        if output is None:
            output = PROJECT_ROOT / "docs" / "main-nw" / "main-index.md"
        try:
            export_index(args.nw, output, args.name)
        except (OSError, UnicodeError, ValueError) as error:
            print(f"nwtool: {error}", file=sys.stderr)
            return 1
    else:
        output = args.o
        if output is None:
            output = PROJECT_ROOT / "tmp" / f"chunk-{slug(args.name)}.md"
        try:
            export_chunk(args.nw, output, args.name, args.max_lines)
        except (OSError, UnicodeError, ValueError) as error:
            print(f"nwtool: {error}", file=sys.stderr)
            return 1

    print(f"Wrote {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

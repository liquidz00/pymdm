"""
Bash text-processing utilities for MacAdmin scripts.

Provides the TextTools class, which mirrors common Unix text commands
(``grep``, ``sed``, ``awk``, ``tr``, ``cut``, ``head``, ``tail``, ``wc``,
``sort``, ``uniq``) as Python methods. Useful when porting MacAdmin bash
scripts to Python where the same idioms repeat across parsing
``system_profiler``, ``scutil``, ``defaults``, ``log show``, ``/etc/passwd``,
and similar output.

Stdlib-only. The implementation is platform-agnostic, but the API and
examples are positioned for macOS MacAdmin workflows.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Literal, overload

if TYPE_CHECKING:
    from .logger import MdmLogger


class TextTools:
    """Bash-equivalent text utilities with optional logging."""

    def __init__(self, logger: MdmLogger | None = None) -> None:
        """
        Initialize TextTools.

        :param logger: Optional MdmLogger instance for debug logging of each
            method call, defaults to None
        :type logger: MdmLogger | None, optional
        """
        self.logger = logger

    @staticmethod
    def _to_lines(text: str | list[str]) -> list[str]:
        """Normalize input to a list of lines (no trailing newlines)."""
        if isinstance(text, list):
            return list(text)
        return text.splitlines()

    @overload
    def grep(
        self,
        pattern: str,
        text: str | list[str],
        *,
        invert: bool = False,
        ignore_case: bool = False,
        count: Literal[True],
    ) -> int: ...

    @overload
    def grep(
        self,
        pattern: str,
        text: str | list[str],
        *,
        invert: bool = False,
        ignore_case: bool = False,
        count: Literal[False] = False,
    ) -> list[str]: ...

    def grep(
        self,
        pattern: str,
        text: str | list[str],
        *,
        invert: bool = False,
        ignore_case: bool = False,
        count: bool = False,
    ) -> list[str] | int:
        """
        Filter lines matching a regex pattern (mirrors ``grep``).

        Returns matched lines (or non-matched if ``invert=True``). When
        ``count=True``, returns the count of matched lines instead.

        :param pattern: Python regex pattern (close enough to POSIX ERE for
            most MacAdmin use cases)
        :type pattern: str
        :param text: Input text as a multi-line string or a list of lines
        :type text: str | list[str]
        :param invert: If True, return lines that do NOT match (like ``grep -v``),
            defaults to False
        :type invert: bool, optional
        :param ignore_case: Case-insensitive matching (like ``grep -i``),
            defaults to False
        :type ignore_case: bool, optional
        :param count: If True, return the number of matched lines instead of
            the lines themselves (like ``grep -c``), defaults to False
        :type count: bool, optional
        :return: List of matched lines, or an int count when ``count=True``
        :rtype: list[str] | int
        :raises re.error: When the pattern is not a valid Python regex
        """
        lines = self._to_lines(text)
        flags = re.IGNORECASE if ignore_case else 0
        compiled = re.compile(pattern, flags)

        if invert:
            matches = [ln for ln in lines if not compiled.search(ln)]
        else:
            matches = [ln for ln in lines if compiled.search(ln)]

        if self.logger:
            self.logger.debug(
                f"grep(pattern={pattern!r}, lines={len(lines)}, "
                f"invert={invert}, ignore_case={ignore_case}) -> {len(matches)} match(es)"
            )

        if count:
            return len(matches)
        return matches

    def sed(
        self,
        pattern: str,
        replacement: str,
        text: str | list[str],
        *,
        count: int = 0,
        ignore_case: bool = False,
    ) -> str:
        """
        Substitute matches of ``pattern`` with ``replacement`` (mirrors ``sed s///``).

        Replacement is applied per-line and the result is rejoined with ``\\n``.
        Backreferences (``\\1``, ``\\g<name>``) work as in Python's ``re.sub``.

        :param pattern: Python regex pattern
        :type pattern: str
        :param replacement: Replacement string (may contain backreferences)
        :type replacement: str
        :param text: Input text as a multi-line string or a list of lines
        :type text: str | list[str]
        :param count: Maximum replacements per line. ``0`` (default) means
            replace all (like ``sed s/.../.../g``); ``1`` mimics the default
            ``sed s/.../...//`` (first match only).
        :type count: int, optional
        :param ignore_case: Case-insensitive matching, defaults to False
        :type ignore_case: bool, optional
        :return: Substituted text as a single string with ``\\n`` line separators
        :rtype: str
        :raises re.error: When the pattern is not a valid Python regex
        """
        flags = re.IGNORECASE if ignore_case else 0
        compiled = re.compile(pattern, flags)
        lines = self._to_lines(text)

        if self.logger:
            self.logger.debug(
                f"sed(pattern={pattern!r}, replacement={replacement!r}, "
                f"lines={len(lines)}, count={count})"
            )

        return "\n".join(compiled.sub(replacement, ln, count=count) for ln in lines)

    def awk(
        self,
        text: str | list[str],
        *,
        field: int | None = None,
        fields: list[int] | None = None,
        delimiter: str | None = None,
        filter: str | None = None,
        output_separator: str = " ",
    ) -> list[str]:
        """
        Extract one or more 1-indexed fields per line (mirrors a simplified
        ``awk -F<delim> '/filter/ {print $field}'``).

        This is a deliberately small subset of ``awk``: field extraction with
        an optional row filter. For more complex transformations, use a list
        comprehension.

        :param text: Input text as a multi-line string or a list of lines
        :type text: str | list[str]
        :param field: A single 1-indexed field to extract. Mutually exclusive
            with ``fields``.
        :type field: int | None, optional
        :param fields: A list of 1-indexed fields to extract, joined by
            ``output_separator``. Mutually exclusive with ``field``.
        :type fields: list[int] | None, optional
        :param delimiter: Field delimiter. ``None`` (default) splits on any
            whitespace (matches default ``awk`` behavior).
        :type delimiter: str | None, optional
        :param filter: Optional regex; only rows matching ``filter`` contribute
            to the output (like ``awk '/pattern/ {...}'``).
        :type filter: str | None, optional
        :param output_separator: Separator used when joining multiple fields
            per row, defaults to a single space
        :type output_separator: str, optional
        :return: List of extracted strings, one per matched row. Rows with
            out-of-range field indices contribute empty strings for those
            fields (matches ``awk`` behavior).
        :rtype: list[str]
        :raises ValueError: When neither ``field`` nor ``fields`` is given,
            or when both are given
        :raises re.error: When ``filter`` is not a valid Python regex
        """
        if field is not None and fields is not None:
            raise ValueError("awk: specify either 'field' or 'fields', not both")
        if field is None and fields is None:
            raise ValueError("awk: must specify 'field' or 'fields'")

        target_fields: list[int] = [field] if field is not None else list(fields or [])
        filter_re = re.compile(filter) if filter else None
        lines = self._to_lines(text)

        result: list[str] = []
        for ln in lines:
            if filter_re and not filter_re.search(ln):
                continue
            parts = ln.split(delimiter) if delimiter is not None else ln.split()
            extracted = [parts[f - 1] if 0 < f <= len(parts) else "" for f in target_fields]
            result.append(output_separator.join(extracted))

        if self.logger:
            self.logger.debug(
                f"awk(fields={target_fields}, delimiter={delimiter!r}, "
                f"filter={filter!r}) -> {len(result)} row(s)"
            )

        return result

    def tr(
        self,
        from_chars: str,
        to_chars: str,
        text: str,
        *,
        delete: bool = False,
        squeeze: bool = False,
    ) -> str:
        """
        Character translation, deletion, or squeezing (mirrors ``tr``).

        Default behavior: replace each character in ``from_chars`` with the
        positionally-corresponding character in ``to_chars``. If ``to_chars``
        is shorter, its last character is repeated to pad (matching ``tr``).

        ``delete=True``: drop all characters in ``from_chars`` (``to_chars``
        is ignored).

        ``squeeze=True``: after any translation/deletion, collapse consecutive
        runs of any character in the squeeze set into one. The squeeze set is
        ``to_chars`` for translation mode (the destination set) and
        ``from_chars`` for delete mode — matching the ``tr -s`` "last operand"
        rule.

        :param from_chars: Source character set
        :type from_chars: str
        :param to_chars: Destination character set. Ignored when ``delete=True``.
        :type to_chars: str
        :param text: Input text (note: ``tr`` is character-oriented, so input
            is a plain string, not a list of lines)
        :type text: str
        :param delete: If True, delete characters in ``from_chars`` rather than
            translate, defaults to False
        :type delete: bool, optional
        :param squeeze: If True, collapse runs of the squeeze-set characters
            into a single occurrence, defaults to False
        :type squeeze: bool, optional
        :return: Transformed string
        :rtype: str
        """
        if delete:
            translated = text.translate({ord(c): None for c in from_chars})
            squeeze_set = from_chars
        else:
            padded_to = to_chars
            if padded_to and len(padded_to) < len(from_chars):
                padded_to = padded_to + padded_to[-1] * (len(from_chars) - len(padded_to))
            if not padded_to:
                translated = text
            else:
                table = str.maketrans(from_chars, padded_to[: len(from_chars)])
                translated = text.translate(table)
            squeeze_set = to_chars or from_chars

        if squeeze and squeeze_set:
            pattern = "[" + re.escape(squeeze_set) + "]"
            translated = re.sub(rf"({pattern})\1+", r"\1", translated)

        if self.logger:
            self.logger.debug(
                f"tr(from_chars={from_chars!r}, to_chars={to_chars!r}, "
                f"delete={delete}, squeeze={squeeze}) -> {len(translated)} char(s)"
            )

        return translated

    def cut(
        self,
        text: str | list[str],
        *,
        delimiter: str = "\t",
        fields: int | list[int] | None = None,
        characters: tuple[int, int] | None = None,
    ) -> list[str]:
        """
        Extract fields by delimiter or characters by position (mirrors ``cut``).

        Provide exactly one of ``fields`` (delimiter-based) or ``characters``
        (position-based, 1-indexed inclusive range like ``cut -c 1-5``).

        :param text: Input text as a multi-line string or a list of lines
        :type text: str | list[str]
        :param delimiter: Field delimiter for ``fields`` mode, defaults to TAB
            (matching ``cut``)
        :type delimiter: str, optional
        :param fields: A single 1-indexed field or list of 1-indexed fields.
            Mutually exclusive with ``characters``.
        :type fields: int | list[int] | None, optional
        :param characters: ``(start, end)`` 1-indexed inclusive character range
            (like ``cut -c start-end``). Mutually exclusive with ``fields``.
        :type characters: tuple[int, int] | None, optional
        :return: List of extracted strings, one per input line. Out-of-range
            fields contribute empty strings.
        :rtype: list[str]
        :raises ValueError: When neither ``fields`` nor ``characters`` is given,
            or when both are given
        """
        if fields is not None and characters is not None:
            raise ValueError("cut: specify either 'fields' or 'characters', not both")
        if fields is None and characters is None:
            raise ValueError("cut: must specify 'fields' or 'characters'")

        lines = self._to_lines(text)
        result: list[str] = []

        if characters is not None:
            start, end = characters
            start_idx = max(start - 1, 0)
            for ln in lines:
                result.append(ln[start_idx:end])
        else:
            field_list = [fields] if isinstance(fields, int) else list(fields or [])
            for ln in lines:
                parts = ln.split(delimiter)
                extracted = [parts[f - 1] if 0 < f <= len(parts) else "" for f in field_list]
                result.append(delimiter.join(extracted))

        if self.logger:
            self.logger.debug(
                f"cut(delimiter={delimiter!r}, fields={fields}, characters={characters}) "
                f"-> {len(result)} row(s)"
            )

        return result

    def head(self, text: str | list[str], *, lines: int = 10) -> list[str]:
        """
        Return the first ``lines`` lines of input (mirrors ``head -n``).

        :param text: Input text as a multi-line string or a list of lines
        :type text: str | list[str]
        :param lines: Maximum number of lines to return, defaults to 10
        :type lines: int, optional
        :return: First ``lines`` lines (or all lines if input has fewer).
            Returns an empty list when ``lines <= 0``.
        :rtype: list[str]
        """
        all_lines = self._to_lines(text)
        result = all_lines[:lines] if lines > 0 else []

        if self.logger:
            self.logger.debug(f"head(lines={lines}) -> {len(result)} line(s)")

        return result

    def tail(self, text: str | list[str], *, lines: int = 10) -> list[str]:
        """
        Return the last ``lines`` lines of input (mirrors ``tail -n``).

        :param text: Input text as a multi-line string or a list of lines
        :type text: str | list[str]
        :param lines: Maximum number of lines to return, defaults to 10
        :type lines: int, optional
        :return: Last ``lines`` lines (or all lines if input has fewer).
            Returns an empty list when ``lines <= 0``.
        :rtype: list[str]
        """
        all_lines = self._to_lines(text)
        result = all_lines[-lines:] if lines > 0 else []

        if self.logger:
            self.logger.debug(f"tail(lines={lines}) -> {len(result)} line(s)")

        return result

    def wc(self, text: str | list[str]) -> dict[str, int]:
        """
        Count lines, words, and characters (mirrors ``wc``).

        :param text: Input text as a multi-line string or a list of lines
        :type text: str | list[str]
        :return: Dictionary with keys ``lines``, ``words``, ``chars``
        :rtype: dict[str, int]
        """
        if isinstance(text, list):
            text_str = "\n".join(text)
            line_count = len(text)
        else:
            text_str = text
            line_count = len(text.splitlines())

        word_count = len(text_str.split())
        char_count = len(text_str)

        result = {"lines": line_count, "words": word_count, "chars": char_count}

        if self.logger:
            self.logger.debug(f"wc() -> {result}")

        return result

    def sort(
        self,
        text: str | list[str],
        *,
        reverse: bool = False,
        numeric: bool = False,
        unique: bool = False,
        field: int | None = None,
        delimiter: str | None = None,
    ) -> list[str]:
        """
        Sort lines (mirrors ``sort``).

        :param text: Input text as a multi-line string or a list of lines
        :type text: str | list[str]
        :param reverse: Sort in descending order (like ``sort -r``),
            defaults to False
        :type reverse: bool, optional
        :param numeric: Sort numerically rather than lexicographically (like
            ``sort -n``). Non-numeric keys sort after numeric keys.
            Defaults to False
        :type numeric: bool, optional
        :param unique: Remove duplicate lines after sorting (like ``sort -u``),
            defaults to False
        :type unique: bool, optional
        :param field: 1-indexed sort key field. When given, sort by that field
            instead of the whole line. Defaults to None.
        :type field: int | None, optional
        :param delimiter: Field delimiter when ``field`` is given. ``None``
            splits on any whitespace.
        :type delimiter: str | None, optional
        :return: Sorted list of lines
        :rtype: list[str]
        """
        lines = self._to_lines(text)

        def extract_key(line: str) -> str:
            if field is None:
                return line
            parts = line.split(delimiter) if delimiter is not None else line.split()
            idx = field - 1
            return parts[idx] if 0 <= idx < len(parts) else ""

        def sort_key(line: str) -> tuple[int, float | str]:
            raw = extract_key(line)
            if numeric:
                try:
                    return (0, float(raw))
                except ValueError:
                    return (1, raw)
            return (0, raw)

        sorted_lines = sorted(lines, key=sort_key, reverse=reverse)

        if unique:
            seen: set[str] = set()
            deduped: list[str] = []
            for ln in sorted_lines:
                if ln not in seen:
                    seen.add(ln)
                    deduped.append(ln)
            sorted_lines = deduped

        if self.logger:
            self.logger.debug(
                f"sort(reverse={reverse}, numeric={numeric}, unique={unique}, "
                f"field={field}) -> {len(sorted_lines)} line(s)"
            )

        return sorted_lines

    def uniq(
        self,
        text: str | list[str],
        *,
        count: bool = False,
        duplicates_only: bool = False,
        unique_only: bool = False,
    ) -> list[str]:
        """
        Collapse consecutive duplicate lines (mirrors ``uniq``).

        Like the bash ``uniq``, this assumes input is already sorted — it only
        collapses *consecutive* duplicates. Pair with :meth:`sort` for the
        common ``sort | uniq`` idiom.

        :param text: Input text as a multi-line string or a list of lines
        :type text: str | list[str]
        :param count: Prefix each line with its occurrence count (like
            ``uniq -c``), defaults to False
        :type count: bool, optional
        :param duplicates_only: Emit only lines that appeared more than once
            (like ``uniq -d``). Mutually exclusive with ``unique_only``.
        :type duplicates_only: bool, optional
        :param unique_only: Emit only lines that appeared exactly once (like
            ``uniq -u``). Mutually exclusive with ``duplicates_only``.
        :type unique_only: bool, optional
        :return: Deduplicated list of lines
        :rtype: list[str]
        :raises ValueError: When both ``duplicates_only`` and ``unique_only``
            are True
        """
        if duplicates_only and unique_only:
            raise ValueError("uniq: 'duplicates_only' and 'unique_only' are mutually exclusive")

        lines = self._to_lines(text)
        if not lines:
            return []

        groups: list[tuple[int, str]] = []
        current = lines[0]
        n = 1
        for ln in lines[1:]:
            if ln == current:
                n += 1
            else:
                groups.append((n, current))
                current = ln
                n = 1
        groups.append((n, current))

        if duplicates_only:
            groups = [(c, ln) for c, ln in groups if c > 1]
        elif unique_only:
            groups = [(c, ln) for c, ln in groups if c == 1]

        if count:
            result = [f"{c} {ln}" for c, ln in groups]
        else:
            result = [ln for _, ln in groups]

        if self.logger:
            self.logger.debug(
                f"uniq(count={count}, duplicates_only={duplicates_only}, "
                f"unique_only={unique_only}) -> {len(result)} line(s)"
            )

        return result

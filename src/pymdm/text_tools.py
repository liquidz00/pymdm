"""
Text-processing helpers for the few Unix idioms whose Python equivalent is
non-obvious or fiddly to hand-roll.

``TextTools`` exposes ``awk`` (bounds-checked field extraction), ``sort``
(numeric / field-key / unique), and ``uniq`` (consecutive-run collapsing with
``-c`` counts, which has no clean stdlib equivalent). These are the operations
worth a helper when parsing output from ``system_profiler``, ``scutil``,
``defaults``, ``log show``, or ``/etc/passwd``.

For the trivial cases, prefer native Python over a wrapper: filter lines with
``re.search`` in a comprehension, slice with ``lines[:n]`` / ``lines[-n:]``, and
substitute with ``re.sub``.

Stdlib-only. The implementation is platform-agnostic, but the API and examples
are positioned for macOS MacAdmin workflows.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .logger import MdmLogger


class TextTools:
    """Text utilities for the Unix idioms Python doesn't make obvious."""

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

import re

import pytest

from pymdm import MdmLogger, TextTools

PASSWD_SAMPLE = (
    "root:*:0:0:System Administrator:/var/root:/bin/sh\n"
    "daemon:*:1:1:System Services:/var/root:/usr/bin/false\n"
    "jappleseed:*:501:20:Johnny Appleseed:/Users/jappleseed:/bin/zsh\n"
    "guest:*:201:201:Guest User:/var/empty:/usr/bin/false"
)


def test_text_tools_initialization():
    """Test TextTools initialization."""
    tools = TextTools()
    assert tools.logger is None

    logger = MdmLogger()
    tools = TextTools(logger=logger)
    assert tools.logger is logger


# ──────────────────────────────────────────────────────────────────────────
# grep
# ──────────────────────────────────────────────────────────────────────────


def test_grep_basic_string_input():
    tools = TextTools()
    result = tools.grep(r"ssh", "ssh\nhttp\nssh-keygen")
    assert result == ["ssh", "ssh-keygen"]


def test_grep_basic_list_input():
    tools = TextTools()
    result = tools.grep(r"ssh", ["ssh", "http", "ssh-keygen"])
    assert result == ["ssh", "ssh-keygen"]


def test_grep_empty_input():
    tools = TextTools()
    assert tools.grep(r"x", "") == []
    assert tools.grep(r"x", []) == []


def test_grep_invert():
    tools = TextTools()
    result = tools.grep(r"ssh", "ssh\nhttp\nftp", invert=True)
    assert result == ["http", "ftp"]


def test_grep_ignore_case():
    tools = TextTools()
    result = tools.grep(r"SSH", "ssh\nHTTP\nSSH-keygen", ignore_case=True)
    assert result == ["ssh", "SSH-keygen"]


def test_grep_count():
    tools = TextTools()
    result = tools.grep(r"ssh", "ssh\nhttp\nssh-keygen", count=True)
    assert result == 2
    assert isinstance(result, int)


def test_grep_count_zero_when_no_matches():
    tools = TextTools()
    assert tools.grep(r"nope", "ssh\nhttp", count=True) == 0


def test_grep_invalid_regex_raises():
    tools = TextTools()
    with pytest.raises(re.error):
        tools.grep(r"(unclosed", "anything")


def test_grep_logs_with_logger(capsys):
    tools = TextTools(logger=MdmLogger(debug=True))
    tools.grep(r"ssh", "ssh\nhttp")
    captured = capsys.readouterr()
    assert "grep(" in captured.out


# ──────────────────────────────────────────────────────────────────────────
# sed
# ──────────────────────────────────────────────────────────────────────────


def test_sed_global_replacement():
    tools = TextTools()
    result = tools.sed(r"foo", "bar", "foo foo\nfoo")
    assert result == "bar bar\nbar"


def test_sed_count_one_first_only():
    tools = TextTools()
    result = tools.sed(r"foo", "bar", "foo foo\nfoo", count=1)
    assert result == "bar foo\nbar"


def test_sed_list_input_preserves_newlines():
    tools = TextTools()
    result = tools.sed(r"x", "y", ["axa", "bxb"])
    assert result == "aya\nbyb"


def test_sed_empty_input():
    tools = TextTools()
    assert tools.sed(r"x", "y", "") == ""
    assert tools.sed(r"x", "y", []) == ""


def test_sed_ignore_case():
    tools = TextTools()
    result = tools.sed(r"FOO", "bar", "Foo foo FOO", ignore_case=True)
    assert result == "bar bar bar"


def test_sed_backreference():
    tools = TextTools()
    result = tools.sed(r"(\w+)@(\w+)", r"\2/\1", "user@host")
    assert result == "host/user"


def test_sed_invalid_regex_raises():
    tools = TextTools()
    with pytest.raises(re.error):
        tools.sed(r"(unclosed", "x", "anything")


def test_sed_logs_with_logger(capsys):
    tools = TextTools(logger=MdmLogger(debug=True))
    tools.sed(r"x", "y", "axa")
    captured = capsys.readouterr()
    assert "sed(" in captured.out


# ──────────────────────────────────────────────────────────────────────────
# awk
# ──────────────────────────────────────────────────────────────────────────


def test_awk_passwd_field_one():
    """awk -F: '{print $1}' against an /etc/passwd snippet."""
    tools = TextTools()
    result = tools.awk(PASSWD_SAMPLE, field=1, delimiter=":")
    assert result == ["root", "daemon", "jappleseed", "guest"]


def test_awk_whitespace_default_delimiter():
    """awk '{print $2}' — default delimiter is any whitespace."""
    tools = TextTools()
    result = tools.awk("PID NAME\n123 sshd\n456 launchd", field=2)
    assert result == ["NAME", "sshd", "launchd"]


def test_awk_filter():
    tools = TextTools()
    result = tools.awk(PASSWD_SAMPLE, field=1, delimiter=":", filter=r"^root")
    assert result == ["root"]


def test_awk_multiple_fields():
    tools = TextTools()
    result = tools.awk(PASSWD_SAMPLE, fields=[1, 3], delimiter=":", output_separator=",")
    assert result == ["root,0", "daemon,1", "jappleseed,501", "guest,201"]


def test_awk_out_of_range_field_is_empty():
    tools = TextTools()
    result = tools.awk("a b", field=5)
    assert result == [""]


def test_awk_list_input():
    tools = TextTools()
    result = tools.awk(["a:b:c", "1:2:3"], field=2, delimiter=":")
    assert result == ["b", "2"]


def test_awk_empty_input():
    tools = TextTools()
    assert tools.awk("", field=1) == []
    assert tools.awk([], field=1) == []


def test_awk_both_field_and_fields_raises():
    tools = TextTools()
    with pytest.raises(ValueError, match="either"):
        tools.awk("x", field=1, fields=[1, 2])


def test_awk_no_field_args_raises():
    tools = TextTools()
    with pytest.raises(ValueError, match="must specify"):
        tools.awk("x")


def test_awk_logs_with_logger(capsys):
    tools = TextTools(logger=MdmLogger(debug=True))
    tools.awk("a b c", field=1)
    captured = capsys.readouterr()
    assert "awk(" in captured.out


# ──────────────────────────────────────────────────────────────────────────
# tr
# ──────────────────────────────────────────────────────────────────────────


def test_tr_basic_translation():
    tools = TextTools()
    assert tools.tr("abc", "xyz", "aabbcc") == "xxyyzz"


def test_tr_pads_short_to_chars():
    """When to_chars is shorter than from_chars, last char is repeated."""
    tools = TextTools()
    assert tools.tr("abc", "x", "abc") == "xxx"


def test_tr_uppercase():
    """Classic tr 'a-z' 'A-Z' use case."""
    tools = TextTools()
    result = tools.tr("abcdefghijklmnopqrstuvwxyz", "ABCDEFGHIJKLMNOPQRSTUVWXYZ", "hello world")
    assert result == "HELLO WORLD"


def test_tr_delete():
    tools = TextTools()
    assert tools.tr("aeiou", "", "hello world", delete=True) == "hll wrld"


def test_tr_squeeze_runs():
    """tr -s ' ' ' ' collapses runs of spaces."""
    tools = TextTools()
    result = tools.tr(" ", " ", "hello   world  here", squeeze=True)
    assert result == "hello world here"


def test_tr_squeeze_after_translation():
    """tr -s 'a' 'x' on 'aaa' -> 'x' (squeezes the translated 'x' run)."""
    tools = TextTools()
    assert tools.tr("a", "x", "aaa", squeeze=True) == "x"


def test_tr_squeeze_with_delete():
    """tr -ds: delete from_chars, then squeeze runs of from_chars (no-op since deleted)."""
    tools = TextTools()
    result = tools.tr("a", "", "aaabbbccc", delete=True, squeeze=True)
    assert result == "bbbccc"


def test_tr_empty_text():
    tools = TextTools()
    assert tools.tr("a", "b", "") == ""


def test_tr_empty_to_chars_without_delete_is_noop():
    """tr with empty to_chars and delete=False returns text unchanged."""
    tools = TextTools()
    assert tools.tr("a", "", "abc") == "abc"


def test_tr_logs_with_logger(capsys):
    tools = TextTools(logger=MdmLogger(debug=True))
    tools.tr("a", "b", "abc")
    captured = capsys.readouterr()
    assert "tr(" in captured.out


# ──────────────────────────────────────────────────────────────────────────
# cut
# ──────────────────────────────────────────────────────────────────────────


def test_cut_fields_single():
    tools = TextTools()
    result = tools.cut(PASSWD_SAMPLE, delimiter=":", fields=1)
    assert result == ["root", "daemon", "jappleseed", "guest"]


def test_cut_fields_list():
    tools = TextTools()
    result = tools.cut("a:b:c:d\n1:2:3:4", delimiter=":", fields=[1, 3])
    assert result == ["a:c", "1:3"]


def test_cut_characters_range():
    tools = TextTools()
    result = tools.cut(["abcdef", "uvwxyz"], characters=(2, 4))
    assert result == ["bcd", "vwx"]


def test_cut_default_delimiter_is_tab():
    tools = TextTools()
    result = tools.cut("a\tb\tc\n1\t2\t3", fields=2)
    assert result == ["b", "2"]


def test_cut_out_of_range_field_is_empty():
    tools = TextTools()
    result = tools.cut("a:b", delimiter=":", fields=5)
    assert result == [""]


def test_cut_list_input():
    tools = TextTools()
    result = tools.cut(["a:b", "c:d"], delimiter=":", fields=1)
    assert result == ["a", "c"]


def test_cut_empty_input():
    tools = TextTools()
    assert tools.cut("", fields=1) == []


def test_cut_both_fields_and_characters_raises():
    tools = TextTools()
    with pytest.raises(ValueError, match="either"):
        tools.cut("x", fields=1, characters=(1, 2))


def test_cut_no_mode_raises():
    tools = TextTools()
    with pytest.raises(ValueError, match="must specify"):
        tools.cut("x")


def test_cut_logs_with_logger(capsys):
    tools = TextTools(logger=MdmLogger(debug=True))
    tools.cut("a:b", delimiter=":", fields=1)
    captured = capsys.readouterr()
    assert "cut(" in captured.out


# ──────────────────────────────────────────────────────────────────────────
# head / tail
# ──────────────────────────────────────────────────────────────────────────


def test_head_default_ten():
    tools = TextTools()
    text = "\n".join(str(i) for i in range(20))
    result = tools.head(text)
    assert result == [str(i) for i in range(10)]


def test_head_custom_lines():
    tools = TextTools()
    result = tools.head(["a", "b", "c", "d"], lines=2)
    assert result == ["a", "b"]


def test_head_zero_or_negative():
    tools = TextTools()
    assert tools.head("a\nb\nc", lines=0) == []
    assert tools.head("a\nb\nc", lines=-5) == []


def test_head_more_than_available():
    tools = TextTools()
    assert tools.head("a\nb", lines=100) == ["a", "b"]


def test_head_empty():
    tools = TextTools()
    assert tools.head("") == []


def test_head_logs_with_logger(capsys):
    tools = TextTools(logger=MdmLogger(debug=True))
    tools.head("a\nb", lines=1)
    captured = capsys.readouterr()
    assert "head(" in captured.out


def test_tail_default_ten():
    tools = TextTools()
    text = "\n".join(str(i) for i in range(20))
    result = tools.tail(text)
    assert result == [str(i) for i in range(10, 20)]


def test_tail_custom_lines():
    tools = TextTools()
    result = tools.tail(["a", "b", "c", "d"], lines=2)
    assert result == ["c", "d"]


def test_tail_zero_or_negative():
    tools = TextTools()
    assert tools.tail("a\nb\nc", lines=0) == []
    assert tools.tail("a\nb\nc", lines=-5) == []


def test_tail_more_than_available():
    tools = TextTools()
    assert tools.tail("a\nb", lines=100) == ["a", "b"]


def test_tail_empty():
    tools = TextTools()
    assert tools.tail("") == []


def test_tail_logs_with_logger(capsys):
    tools = TextTools(logger=MdmLogger(debug=True))
    tools.tail("a\nb", lines=1)
    captured = capsys.readouterr()
    assert "tail(" in captured.out


# ──────────────────────────────────────────────────────────────────────────
# wc
# ──────────────────────────────────────────────────────────────────────────


def test_wc_basic_string():
    tools = TextTools()
    assert tools.wc("hello world\nfoo bar baz") == {"lines": 2, "words": 5, "chars": 23}


def test_wc_list_input():
    tools = TextTools()
    assert tools.wc(["hello world", "foo bar baz"]) == {"lines": 2, "words": 5, "chars": 23}


def test_wc_empty_string():
    tools = TextTools()
    assert tools.wc("") == {"lines": 0, "words": 0, "chars": 0}


def test_wc_empty_list():
    tools = TextTools()
    assert tools.wc([]) == {"lines": 0, "words": 0, "chars": 0}


def test_wc_logs_with_logger(capsys):
    tools = TextTools(logger=MdmLogger(debug=True))
    tools.wc("hi")
    captured = capsys.readouterr()
    assert "wc(" in captured.out


# ──────────────────────────────────────────────────────────────────────────
# sort
# ──────────────────────────────────────────────────────────────────────────


def test_sort_basic():
    tools = TextTools()
    assert tools.sort(["c", "a", "b"]) == ["a", "b", "c"]


def test_sort_string_input():
    tools = TextTools()
    assert tools.sort("c\na\nb") == ["a", "b", "c"]


def test_sort_reverse():
    tools = TextTools()
    assert tools.sort(["a", "b", "c"], reverse=True) == ["c", "b", "a"]


def test_sort_numeric():
    """Numeric sort handles values like 1, 2, 10 correctly."""
    tools = TextTools()
    assert tools.sort(["10", "2", "1"], numeric=True) == ["1", "2", "10"]


def test_sort_lexicographic_default():
    """Default (non-numeric) sort gives lexicographic order."""
    tools = TextTools()
    assert tools.sort(["10", "2", "1"]) == ["1", "10", "2"]


def test_sort_unique():
    tools = TextTools()
    assert tools.sort(["b", "a", "a", "b", "c"], unique=True) == ["a", "b", "c"]


def test_sort_by_field():
    """Sort lines by a 1-indexed field."""
    tools = TextTools()
    result = tools.sort(["c 3", "a 1", "b 2"], field=2)
    assert result == ["a 1", "b 2", "c 3"]


def test_sort_numeric_field_with_delimiter():
    tools = TextTools()
    result = tools.sort(["item:10", "item:2", "item:30"], field=2, delimiter=":", numeric=True)
    assert result == ["item:2", "item:10", "item:30"]


def test_sort_numeric_mixed_with_non_numeric():
    """Non-numeric keys sort after numeric ones in numeric mode."""
    tools = TextTools()
    result = tools.sort(["abc", "2", "1"], numeric=True)
    assert result == ["1", "2", "abc"]


def test_sort_empty():
    tools = TextTools()
    assert tools.sort("") == []


def test_sort_logs_with_logger(capsys):
    tools = TextTools(logger=MdmLogger(debug=True))
    tools.sort(["b", "a"])
    captured = capsys.readouterr()
    assert "sort(" in captured.out


# ──────────────────────────────────────────────────────────────────────────
# uniq
# ──────────────────────────────────────────────────────────────────────────


def test_uniq_consecutive_dedup():
    tools = TextTools()
    assert tools.uniq(["a", "a", "b", "b", "c"]) == ["a", "b", "c"]


def test_uniq_does_not_dedup_non_consecutive():
    """Bash uniq only collapses CONSECUTIVE duplicates."""
    tools = TextTools()
    assert tools.uniq(["a", "b", "a"]) == ["a", "b", "a"]


def test_uniq_count():
    tools = TextTools()
    assert tools.uniq(["a", "a", "b", "b", "c"], count=True) == ["2 a", "2 b", "1 c"]


def test_uniq_duplicates_only():
    tools = TextTools()
    assert tools.uniq(["a", "a", "b", "c", "c"], duplicates_only=True) == ["a", "c"]


def test_uniq_unique_only():
    tools = TextTools()
    assert tools.uniq(["a", "a", "b", "c", "c"], unique_only=True) == ["b"]


def test_uniq_string_input():
    tools = TextTools()
    assert tools.uniq("a\na\nb") == ["a", "b"]


def test_uniq_empty():
    tools = TextTools()
    assert tools.uniq("") == []
    assert tools.uniq([]) == []


def test_uniq_duplicates_and_unique_only_raises():
    tools = TextTools()
    with pytest.raises(ValueError, match="mutually exclusive"):
        tools.uniq(["a"], duplicates_only=True, unique_only=True)


def test_uniq_logs_with_logger(capsys):
    tools = TextTools(logger=MdmLogger(debug=True))
    tools.uniq(["a", "a"])
    captured = capsys.readouterr()
    assert "uniq(" in captured.out


# ──────────────────────────────────────────────────────────────────────────
# Integration: sort | uniq idiom
# ──────────────────────────────────────────────────────────────────────────


def test_sort_uniq_idiom():
    """The classic `sort | uniq -c` pipeline."""
    tools = TextTools()
    text = ["http", "ssh", "http", "ftp", "ssh", "http"]
    sorted_text = tools.sort(text)
    counted = tools.uniq(sorted_text, count=True)
    assert counted == ["1 ftp", "3 http", "2 ssh"]

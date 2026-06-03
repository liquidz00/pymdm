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

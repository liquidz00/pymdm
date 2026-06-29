(text_tools_module)=
# TextTools

:::{rst-class} lead
The handful of Unix text idioms whose Python equivalent is non-obvious: awk-style field extraction, multi-key sort, and uniq.
:::

`TextTools` is intentionally small. It wraps only the operations where native Python is fiddly to hand-roll. For the trivial cases, reach for the language directly: filter lines with `re.search` in a comprehension, slice with `lines[:n]` / `lines[-n:]`, and substitute with `re.sub`.

## Usage

```python
from pymdm import TextTools

tools = TextTools()

# awk -F: '{print $1}' /etc/passwd
usernames = tools.awk(passwd_text, field=1, delimiter=":")

# the classic `sort | uniq -c` count-occurrences pipeline
sorted_lines = tools.sort(["http", "ssh", "http", "ftp", "ssh", "http"])
counts = tools.uniq(sorted_lines, count=True)
# -> ["1 ftp", "3 http", "2 ssh"]
```

Each method accepts input as either a multi-line `str` or a `list[str]`. Pass an optional `MdmLogger` to the constructor for debug-level call tracing.

```{eval-rst}
.. autoclass:: pymdm.TextTools
   :members:
   :undoc-members:
   :show-inheritance:
```

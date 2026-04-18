import inspect
import os
import sys
import warnings

import pymdm

sys.path.insert(0, os.path.abspath("../src"))

# -- Project information -----------------------------------------------------

project = "pymdm"
copyright = "Copyright &copy; 2026, Andrew Lerman"
author = "Andrew Lerman"

version = pymdm.__version__
release = pymdm.__title__

# -- General configuration ---------------------------------------------------

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.intersphinx",
    "sphinx.ext.linkcode",
    "sphinx.ext.autosectionlabel",
    "myst_parser",
    "sphinx_copybutton",
    "sphinx_design",
    "sphinx_iconify",
]

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
}

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

suppress_warnings = [
    "autodoc",
    "myst.xref_ambiguous",
    "autosectionlabel.*",
]

# Autodoc configuration
add_module_names = False
autodoc_typehints = "both"
autodoc_member_order = "bysource"
autosectionlabel_prefix_document = True
toc_object_entries_show_parents = "hide"

# MyST opts
myst_enable_extensions = [
    "colon_fence",
    "substitution",
]

myst_heading_anchors = 3

myst_substitutions = {
    "version": version,
}

# -- Link Code ---------------------------------------------------------------


def linkcode_resolve(domain, info):
    """Generate external links to source code on GitHub."""
    if domain != "py":
        return None

    modname = info.get("module")
    fullname = info.get("fullname")

    submod = sys.modules.get(modname)
    if submod is None:
        return None

    obj = submod
    for part in fullname.split("."):
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", FutureWarning)
                obj = getattr(obj, part)
        except AttributeError:
            return None

    try:
        fn = inspect.getsourcefile(inspect.unwrap(obj))
    except TypeError:
        try:
            fn = inspect.getsourcefile(inspect.unwrap(obj.fget))
        except (AttributeError, TypeError):
            fn = None
    if not fn:
        return None

    try:
        source, lineno = inspect.getsourcelines(obj)
    except (TypeError, OSError):
        try:
            source, lineno = inspect.getsourcelines(obj.fget)
        except (AttributeError, TypeError):
            lineno = None

    linespec = f"#L{lineno}-L{lineno + len(source) - 1}" if lineno else ""

    fn = os.path.relpath(fn, start=os.path.dirname(pymdm.__file__))

    return f"https://github.com/liquidz00/pymdm/blob/main/src/pymdm/{fn}{linespec}"


# -- Strip @overload signatures from autodoc output -------------------------
# Sphinx's ModuleAnalyzer parses the source AST to find @overload-decorated
# functions, ignoring runtime guards like TYPE_CHECKING. This patch clears the
# overload registry after analysis so only the implementation signature renders.
from sphinx.pycode import ModuleAnalyzer

_original_analyze = ModuleAnalyzer.analyze


def _analyze_without_overloads(self):
    _original_analyze(self)
    self.overloads.clear()


ModuleAnalyzer.analyze = _analyze_without_overloads


# -- Options for copy button -------------------------------------------------

copybutton_prompt_text = r">>> |\.\.\. |\$ "
copybutton_prompt_is_regexp = True

# -- Options for HTML output -------------------------------------------------

html_theme = "shibuya"
html_static_path = ["_static"]
html_title = f"{release}"
html_css_files = [
    "css/custom.css",
    "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/7.0.1/css/all.min.css",
]

html_theme_options = {
    "dark_code": True,
    "nav_links": [
        {
            "title": "Changelog",
            "url": "https://github.com/liquidz00/pymdm/blob/main/CHANGELOG.md",
            "external": True,
        },
        {
            "title": "More",
            "children": [
                {
                    "title": "MacAdmins Foundation",
                    "url": "https://www.macadmins.org",
                },
                {
                    "title": "MacAdmins Python",
                    "url": "https://github.com/macadmins/python",
                },
                {
                    "title": "PyPI",
                    "url": "https://pypi.org/project/pymdm/",
                },
            ],
        },
    ],
}

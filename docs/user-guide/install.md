# Installation

:::{rst-class} lead
Install pymdm for development or deployment.
:::

## Install from PyPI

:::::{tab-set}
::::{tab-item} {iconify}`material-icon-theme:uv` uv

```bash
$ uv pip install pymdm
```

With webhook support (`requests`):

```bash
$ uv pip install pymdm[requests]
```

::::

::::{tab-item} {iconify}`devicon:pypi` pip

```bash
$ pip install pymdm
```

With webhook support (`requests`):

```bash
$ pip install pymdm[requests]
```

::::

::::{tab-item} {iconify}`material-icon-theme:python` MacAdmins Python

For environments using [MacAdmins Python](https://github.com/macadmins/python) (`/usr/local/bin/managed_python3`):

```bash
$ /usr/local/bin/managed_python3 -m pip install --force-reinstall --upgrade pymdm
```

:::{note}
MacAdmins Python includes `requests` in its standard library, so the `[requests]` extra is not needed.
:::

::::
:::::

## Install from Source

:::::{tab-set}
::::{tab-item} {iconify}`material-icon-theme:uv` uv

```bash
$ git clone https://github.com/liquidz00/pymdm.git
$ cd pymdm
$ uv pip install -e .
```

::::

::::{tab-item} {iconify}`devicon:pypi` pip

```bash
$ git clone https://github.com/liquidz00/pymdm.git
$ cd pymdm
$ pip install -e .
```

::::
:::::

## Development

```bash
$ git clone https://github.com/liquidz00/pymdm.git
$ cd pymdm
$ make install-dev # Install with dev dependencies (includes docs tooling)
$ make test        # Run tests
$ make format      # Format code with ruff
$ make docs        # Build documentation locally
```

## Fleet Deployment

To deploy pymdm to managed Macs via Jamf Pro policy:

```bash
/usr/local/bin/managed_python3 -m pip install --force-reinstall --upgrade pymdm
```

This command can be added as a script payload in a Jamf Pro policy scoped to your managed endpoints.

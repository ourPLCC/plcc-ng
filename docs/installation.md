# Installation

This page covers installing plcc-ng via pip.
Additional installation methods will be documented here as they become available.

## Requirements

- Python 3.12 or later
- Java JDK 21 or later (only needed if implementing semantics in Java)

## Install

```bash
pip install plcc-ng
```

Verify the installation:

```bash
plcc-version
```

## Upgrade

```bash
pip install --upgrade plcc-ng
```

Verify the new version:

```bash
plcc-version
```

Check the [Changelog](changelog.md) for breaking changes between versions before upgrading.

## Pin a Specific Version

To install a specific version:

```bash
pip install plcc-ng==X.Y.Z
```

To pin in `requirements.txt`:

```
plcc-ng==X.Y.Z
```

To pin in `pyproject.toml`:

```toml
[project]
dependencies = [
    "plcc-ng==X.Y.Z",
]
```

Check which version is currently installed:

```bash
plcc-version
```

## Uninstall

```bash
pip uninstall plcc-ng
```

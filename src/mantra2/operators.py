"""Discovery of mutation schemas declared in ``mutation_patterns.yaml``.

A schema entry maps a name to the operator class that rewrites the AST and to
the parent/child class-name sequence that identifies legal mutation points::

    NSubUpdate:
      OPClass: NSubUpdate
      pattern:
        - class_name: Always
        - class_name: NonblockingSubstitution

Custom operators are supported without touching this package: add ``module``
to an entry and Mantra2 will import the class from that dotted path instead of
from :mod:`mantra2.mutation.implementations`.
"""

from __future__ import annotations

import importlib
from pathlib import Path
from typing import Any

import yaml

from .mutation import implementations

PACKAGE_ROOT = Path(__file__).resolve().parent
DEFAULT_PATTERNS = PACKAGE_ROOT / "configs" / "mutation_patterns.yaml"
DEFAULT_CATALOG = PACKAGE_ROOT / "configs" / "operators.yaml"


def load_patterns(path: Path = DEFAULT_PATTERNS) -> dict[str, Any]:
    """Return the ``patterns`` mapping of a mutation-patterns file."""
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    patterns = data.get("patterns")
    if not patterns:
        raise ValueError(f"{path}: no 'patterns' section found")
    return patterns


def load_catalog(path: Path = DEFAULT_CATALOG) -> dict[str, Any]:
    """Return the operator families declared in ``operators.yaml``."""
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    return data


def schema_to_operator(catalog: dict[str, Any]) -> dict[str, str]:
    """Map every implementation schema to its canonical operator name."""
    mapping: dict[str, str] = {}
    for name, entry in (catalog.get("operators") or {}).items():
        for schema in entry.get("schemas") or []:
            mapping[schema] = name
    return mapping


def resolve_operator_class(definition: dict[str, Any], schema: str):
    """Instantiable operator class for one schema entry."""
    module = definition.get("module")
    if module:
        return getattr(importlib.import_module(module), definition["OPClass"])
    try:
        return getattr(implementations, definition["OPClass"])
    except AttributeError as error:
        raise ValueError(
            f"schema {schema!r}: unknown operator class {definition['OPClass']!r}"
        ) from error


def select_schemas(
    patterns: dict[str, Any], operators: list[str] | None
) -> list[str]:
    """Validate the requested schema names against the pattern file."""
    selected = list(operators) if operators else list(patterns)
    unknown = sorted(set(selected) - set(patterns))
    if unknown:
        raise ValueError(f"unknown mutation schemas: {', '.join(unknown)}")
    return selected

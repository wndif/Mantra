"""Tests for mutation-schema discovery and operator resolution."""

from pathlib import Path

import pytest

from mantra2.mutation import MantraOperator
from mantra2.operators import (
    DEFAULT_CATALOG,
    DEFAULT_PATTERNS,
    load_catalog,
    load_patterns,
    resolve_operator_class,
    schema_to_operator,
    select_schemas,
)

pytest.importorskip("pyverilog", reason="PyVerilog is required for mutation")


def test_default_pattern_file_is_loadable():
    patterns = load_patterns(DEFAULT_PATTERNS)
    assert patterns, "the bundled pattern file defines no schemas"


def test_every_schema_resolves_to_an_operator_class():
    patterns = load_patterns(DEFAULT_PATTERNS)
    for schema, definition in patterns.items():
        operator_class = resolve_operator_class(definition, schema)
        assert issubclass(operator_class, MantraOperator), schema


def test_every_schema_has_a_pattern():
    patterns = load_patterns(DEFAULT_PATTERNS)
    for schema, definition in patterns.items():
        assert definition.get("pattern"), f"{schema} has no pattern"
        for step in definition["pattern"]:
            assert step.get("class_name"), f"{schema} has a step without class_name"


def test_catalog_covers_all_executable_schemas():
    patterns = load_patterns(DEFAULT_PATTERNS)
    to_operator = schema_to_operator(load_catalog(DEFAULT_CATALOG))
    assert set(to_operator) == set(patterns)


def test_select_schemas_defaults_to_all():
    patterns = load_patterns(DEFAULT_PATTERNS)
    assert set(select_schemas(patterns, None)) == set(patterns)


def test_select_schemas_rejects_unknown_names():
    patterns = load_patterns(DEFAULT_PATTERNS)
    with pytest.raises(ValueError, match="unknown mutation schemas"):
        select_schemas(patterns, ["NoSuchSchema"])


def test_custom_schema_can_come_from_another_module(tmp_path: Path):
    patterns = load_patterns(DEFAULT_PATTERNS)
    patterns["CustomSchema"] = {
        "OPClass": "NSubUpdate",
        "module": "mantra2.mutation.implementations.NSubUpdate",
        "pattern": [{"class_name": "Always"}, {"class_name": "NonblockingSubstitution"}],
    }
    operator_class = resolve_operator_class(patterns["CustomSchema"], "CustomSchema")
    assert operator_class.__name__ == "NSubUpdate"

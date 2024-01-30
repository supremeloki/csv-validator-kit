import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pytest

from csv_validator_kit import (
    ColumnRule,
    Schema,
    SchemaDefinitionError,
    ValidationError,
    ValidationResult,
    Violation,
    validate_file,
    validate_rows,
)


def make_schema() -> Schema:
    return Schema(
        required_columns=["email", "age"],
        optional_columns=["role", "name"],
        rules=[
            ColumnRule(column="email", rule_name="email"),
            ColumnRule(column="age", rule_name="int"),
            ColumnRule(column="role", rule_name="one_of", params={"choices": "admin|user|guest"}),
            ColumnRule(column="name", rule_name="min_len", params={"n": "2"}),
        ],
    )


def test_valid_rows_pass():
    rows = [{"email": "a@b.com", "age": "30", "role": "admin", "name": "ali"}]
    result = validate_rows(rows, make_schema())
    assert result.valid
    assert result.summary().startswith("PASS")


def test_bad_email_fails():
    rows = [{"email": "not-an-email", "age": "30", "role": "user", "name": "ab"}]
    result = validate_rows(rows, make_schema())
    assert not result.valid
    assert any(v.rule == "email" for v in result.violations)


def test_missing_required_column():
    rows = [{"email": "x@y.com", "role": "user", "name": "abc"}]
    result = validate_rows(rows, make_schema())
    assert any(v.rule == "required" and v.column == "age" for v in result.violations)


def test_one_of_rejects_unknown_choice():
    rows = [{"email": "a@b.com", "age": "1", "role": "superadmin", "name": "ok"}]
    result = validate_rows(rows, make_schema())
    assert any(v.rule == "one_of" for v in result.violations)


def test_min_len_rule():
    rows = [{"email": "a@b.com", "age": "5", "role": "user", "name": "a"}]
    result = validate_rows(rows, make_schema())
    assert any(v.rule == "min_len" for v in result.violations)


def test_regex_rule():
    schema = Schema(
        required_columns=["code"],
        rules=[ColumnRule("code", "regex", {"pattern": r"\d{4}"})],
    )
    assert validate_rows([{"code": "1234"}], schema).valid
    assert not validate_rows([{"code": "12"}], schema).valid


def test_unknown_rule_raises_at_check_time():
    rule = ColumnRule(column="x", rule_name="nonexistent")
    with pytest.raises(SchemaDefinitionError):
        rule.check("anything")


def test_rule_on_unknown_column_raises_at_schema_build():
    schema = Schema(required_columns=["known"], rules=[ColumnRule("ghost", "int")])
    result = validate_rows([{"known": "1", "ghost": "5"}], schema)
    assert not result.valid
    assert any(v.column == "ghost" for v in result.violations)


def test_validate_file(tmp_path):
    src = tmp_path / "data.csv"
    src.write_text("email,age,role,name\nbad,,hacker,x\n", encoding="utf-8")
    result = validate_file(src, make_schema())
    assert not result.valid
    assert result.total_rows == 1
    assert len(result.violations) >= 3


def test_empty_file_zero_rows(tmp_path):
    src = tmp_path / "empty.csv"
    src.write_text("email,age,role,name\n", encoding="utf-8")
    result = validate_file(src, make_schema())
    assert result.valid
    assert result.total_rows == 0

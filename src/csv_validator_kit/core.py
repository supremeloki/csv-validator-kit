from __future__ import annotations

import csv
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

Row = dict[str, str]


class ValidationError(Exception):
    pass


class SchemaDefinitionError(ValidationError):
    pass


@dataclass(frozen=True)
class Violation:
    row_index: int
    column: str
    rule: str
    value: str | None
    message: str


@dataclass(frozen=True)
class ValidationResult:
    valid: bool
    total_rows: int
    violations: tuple[Violation, ...] = field(default_factory=tuple)

    def summary(self) -> str:
        status = "PASS" if self.valid else "FAIL"
        return f"{status}: {len(self.violations)} violation(s) across {self.total_rows} rows"


TypeChecker = Callable[[str], bool]


def _is_int(value: str) -> bool:
    try:
        int(value.strip())
        return True
    except ValueError:
        return False


def _is_float(value: str) -> bool:
    try:
        float(value.strip())
        return True
    except ValueError:
        return False


def _is_email(value: str) -> bool:
    return bool(re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", value))


TYPE_CHECKERS: dict[str, TypeChecker] = {
    "int": _is_int,
    "float": _is_float,
    "email": _is_email,
    "nonempty": lambda v: v.strip() != "",
}


BUILTIN_RULES: dict[str, Callable[[str], bool]] = {
    **TYPE_CHECKERS,
    "min_len:5": lambda v: len(v) >= 5,
}


@dataclass(frozen=True)
class ColumnRule:
    column: str
    rule_name: str
    params: dict[str, str] = field(default_factory=dict)

    def check(self, value: str) -> bool:
        if self.rule_name in TYPE_CHECKERS:
            return TYPE_CHECKERS[self.rule_name](value)
        if self.rule_name == "regex":
            return bool(re.fullmatch(self.params.get("pattern", ""), value))
        if self.rule_name == "min_len":
            return len(value) >= int(self.params.get("n", "0"))
        if self.rule_name == "max_len":
            return len(value) <= int(self.params.get("n", "999999"))
        if self.rule_name == "one_of":
            return value in self.params.get("choices", "").split("|")
        raise SchemaDefinitionError(f"unknown rule: {self.rule_name!r}")


class Schema:
    def __init__(self, required_columns: list[str], rules: list[ColumnRule], optional_columns: list[str] | None = None) -> None:
        self._required = required_columns
        self._rules = rules
        self._known_columns = set(required_columns) | set(optional_columns or ())

    def validate_row(self, row_index: int, row: Row) -> list[Violation]:
        violations: list[Violation] = []
        for column in self._required:
            if column not in row or row[column].strip() == "":
                violations.append(
                    Violation(row_index, column, "required", row.get(column), "missing or empty")
                )
        for key in row:
            if key not in self._known_columns:
                violations.append(
                    Violation(row_index, key, "unknown_column", row[key], "column not declared in schema")
                )
        for rule in self._rules:
            value = row.get(rule.column)
            if value is None:
                continue
            if not rule.check(value):
                violations.append(
                    Violation(row_index, rule.column, rule.rule_name, value, f"failed {rule.rule_name}")
                )
        return violations


def validate_file(path: Path, schema: Schema, encoding: str = "utf-8-sig") -> ValidationResult:
    if not path.exists():
        raise FileNotFoundError(f"source not found: {path}")
    with path.open(encoding=encoding, newline="") as handle:
        reader = csv.DictReader(handle)
        all_violations: list[Violation] = []
        total = 0
        for index, record in enumerate(reader):
            total += 1
            clean = {k: (v or "") for k, v in record.items()}
            all_violations.extend(schema.validate_row(index, clean))
    return ValidationResult(
        valid=len(all_violations) == 0,
        total_rows=total,
        violations=tuple(all_violations),
    )


def validate_rows(rows: list[Row], schema: Schema) -> ValidationResult:
    violations: list[Violation] = []
    for index, row in enumerate(rows):
        violations.extend(schema.validate_row(index, row))
    return ValidationResult(
        valid=len(violations) == 0,
        total_rows=len(rows),
        violations=tuple(violations),
    )

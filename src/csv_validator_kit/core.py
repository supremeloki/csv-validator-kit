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

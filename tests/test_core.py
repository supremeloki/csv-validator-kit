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

# csv-validator-kit

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Validates CSV rows against a declarative schema — required columns, type checks, regex, length bounds, and choice lists — returning typed violations instead of failing fast.

## 🚀 Overview

Data files from clients always break somewhere: empty required cells, ages like `thirty`, roles nobody defined. `csv-validator-kit` collects *all* violations in one pass instead of stopping at the first bad row, so you can hand the client a complete fix-list. Rules are plain data (`ColumnRule`), schemas validate themselves (a rule on an unknown column raises immediately), and results carry row index + column + rule name for precise reporting.

## ✨ Features

- **Declarative schema:** list required columns, attach rules per column
- **Built-in rules:** `int`, `float`, `email`, `nonempty`, `regex`, `min_len`, `max_len`, `one_of`
- **Collect-all reporting:** every violation returned as a frozen dataclass with row/column/rule
- **Schema self-checks:** unknown rule names and orphan columns raise at construction time
- **File or rows API:** validate from disk or straight from parsed dicts
- **Summary line:** one-line PASS/FAIL with counts for logs
- **Zero dependencies**

## 🚧 Structure

```
csv-validator-kit/
├── src/csv_validator_kit/
│   ├── __init__.py
│   └── core.py
├── tests/
│   └── test_core.py
├── README.md
└── pyproject.toml
```

## 📦 Installation

### For Development

```bash
git clone https://github.com/supremeloki/csv-validator-kit.git
cd csv-validator-kit
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"
```

## 📋 Requirements

- Python 3.11+
- No runtime dependencies

## 🏃 Quick Start

```python
from pathlib import Path
from csv_validator_kit import ColumnRule, Schema, validate_file

schema = Schema(
    required_columns=["email", "age"],
    rules=[
        ColumnRule(column="email", rule_name="email"),
        ColumnRule(column="age", rule_name="int"),
        ColumnRule(column="role", rule_name="one_of",
                   params={"choices": "admin|user|guest"}),
    ],
)

result = validate_file(Path("users.csv"), schema)
print(result.summary())
for v in result.violations:
    print(f"row {v.row_index} · {v.column} · {v.rule}")
```

## 🔧 Error Handling

```text
ValidationError
└── SchemaDefinitionError   # unknown rule or rule on missing column
```

Row-level problems never raise — they become `Violation` entries.

## 🧪 Testing

```bash
pytest tests/ -v
```

## 📝 Code Quality

- Full type hints (`X | None` style)
- Zero comments — names carry the meaning
- `ruff` clean

## 📄 License

MIT — see [LICENSE](LICENSE).

## 👤 Author

**Kooroush Masoumi**

---

⭐ Star this repo if you find it useful!

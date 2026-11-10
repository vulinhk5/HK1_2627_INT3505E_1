import re
from pathlib import Path

import pytest
import yaml
from openapi_spec_validator import validate

SPEC_DIR = Path(__file__).resolve().parent.parent / "openapi"
SPEC_FILES = sorted(SPEC_DIR.glob("*.yaml"))
HTTP_METHODS = {"get", "post", "put", "patch", "delete"}


def _normalize(path: str) -> str:
    """'/x/{id}' và '/x/<int:product_id>' đều -> '/x/{}' để so sánh với nhau."""
    return re.sub(r"\{[^}]+\}|<[^>]+>", "{}", path)


def _load(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def test_spec_files_exist():
    assert {f.name for f in SPEC_FILES} >= {"products.yaml", "orders.yaml"}


@pytest.mark.parametrize("spec_file", SPEC_FILES, ids=lambda f: f.name)
def test_spec_is_valid_openapi(spec_file):
    validate(_load(spec_file))  


def test_spec_matches_flask_routes(app):
    documented = set()
    for spec_file in SPEC_FILES:
        for path, item in _load(spec_file)["paths"].items():
            for method in item.keys() & HTTP_METHODS:
                documented.add((method.upper(), _normalize(path)))

    implemented = set()
    for rule in app.url_map.iter_rules():
        if rule.rule.startswith("/api/v1"):
            for method in rule.methods - {"HEAD", "OPTIONS"}:
                implemented.add((method, _normalize(rule.rule)))

    assert documented - implemented == set(), "có trong spec nhưng app chưa làm"
    assert implemented - documented == set(), "app có route nhưng spec chưa mô tả"

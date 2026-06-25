"""asserts exact shacl validation behavior for the two fixtures."""

import sys
from pathlib import Path

from rdflib import URIRef
from rdflib.namespace import SH

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from validate import validate_data  # noqa: E402

DATA = ROOT / "data"
TDY = "https://tdytrading.example/parts#"

# invalid.ttl has six broken records, but listing_missing_refs breaks two rules
# at once (no sells and no listedBy), so the shacl results graph holds 7 results.
EXPECTED_VIOLATIONS = 7


def focus_nodes(results_graph):
    return set(results_graph.objects(None, SH.focusNode))


def test_valid_conforms():
    conforms, _ = validate_data(DATA / "valid.ttl")
    assert conforms, "good data should pass the shapes"


def test_invalid_does_not_conform():
    conforms, _ = validate_data(DATA / "invalid.ttl")
    assert not conforms


def test_exact_violation_count():
    _, results = validate_data(DATA / "invalid.ttl")
    n = len(list(results.triples((None, SH.result, None))))
    assert n == EXPECTED_VIOLATIONS


def test_expected_focus_nodes_present():
    _, results = validate_data(DATA / "invalid.ttl")
    found = focus_nodes(results)
    for name in ("listing_bad_price", "listing_bad_grade", "gpu_gtx1060"):
        assert URIRef(TDY + name) in found, f"{name} should be flagged"

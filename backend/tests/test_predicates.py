from app.twin.predicates import canonicalize_predicate


def test_collapses_phrasing_variants():
    # the exact D-06 case: these should all normalize to the same predicate
    assert canonicalize_predicate("has range") == "range"
    assert canonicalize_predicate("hasRange") == "range"
    assert canonicalize_predicate("Range") == "range"
    assert canonicalize_predicate("driving range") == "range"
    assert canonicalize_predicate("has_range") == "range"


def test_aliases():
    assert canonicalize_predicate("MSRP") == "price"
    assert canonicalize_predicate("starts at") == "price"
    assert canonicalize_predicate("towing") == "towing_capacity"
    assert canonicalize_predicate("hp") == "horsepower"


def test_never_collapses_to_empty():
    assert canonicalize_predicate("has") == "has"   # bare filler kept
    assert canonicalize_predicate("") == ""


def test_multiword_kept():
    assert canonicalize_predicate("integrates with") == "integrates_with"
    assert canonicalize_predicate("competes_with") == "competes_with"

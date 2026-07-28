from app.twin.governance import clean_display_name, resolution_key
from app.verticals.automotive import AUTOMOTIVE


def test_variants_collapse_to_same_key():
    k = lambda n: resolution_key(n, AUTOMOTIVE, "Rivian")
    assert k("2026 R1S Dual") == k("r1s") == k("Rivian R1S") == k("R1S Dual Motor with Large Battery")


def test_different_models_stay_distinct():
    # the critical guard: R1S and R1T must NOT merge (embeddings would wrongly merge them)
    assert resolution_key("R1S", AUTOMOTIVE, "Rivian") != resolution_key("R1T", AUTOMOTIVE, "Rivian")
    assert resolution_key("2026 R1S Dual", AUTOMOTIVE, "Rivian") != resolution_key("R1T Dual", AUTOMOTIVE, "Rivian")


def test_clean_display_name_strips_year_trim_brand():
    assert clean_display_name("2026 R1S Dual Motor", AUTOMOTIVE, "Rivian") == "R1S"
    assert clean_display_name("Rivian R1T", AUTOMOTIVE, "Rivian") == "R1T"


def test_key_never_empty():
    # a name made entirely of variant terms shouldn't collapse to nothing
    assert resolution_key("Dual Motor", AUTOMOTIVE, "Rivian") != ""

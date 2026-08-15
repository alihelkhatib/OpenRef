from validate_fgm230_kicad_library import balanced_sexpression, validate_library


def test_library_matches_controlled_generator_and_geometry() -> None:
    assert validate_library() == []


def test_sexpression_balance_rejects_truncation_and_ignores_quoted_parens() -> None:
    assert balanced_sexpression('(root (value "(") (item))')
    assert not balanced_sexpression("(root (item)")

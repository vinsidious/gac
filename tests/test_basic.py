def test_import():
    """Verify that we can import the package."""
    import gac

    assert gac is not None


def test_version():
    """Verify that version is defined."""
    import gac

    assert gac.__version__ is not None
    assert isinstance(gac.__version__, str)

def test_cache_dir(hatch, helpers, temp_dir_cache):
    result = hatch("cache", "dir")

    assert result.exit_code == 0, result.output
    assert result.output == helpers.dedent(
        f"""
        {temp_dir_cache / "cache"}
        """
    )


def test_data_dir(hatch, helpers, temp_dir_data):
    result = hatch("cache", "dir", "--data")

    assert result.exit_code == 0, result.output
    assert result.output == helpers.dedent(
        f"""
        {temp_dir_data / "data"}
        """
    )

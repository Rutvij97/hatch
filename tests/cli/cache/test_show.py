import pytest
from rich.box import ASCII_DOUBLE_HEAD
from rich.console import Console
from rich.table import Table

from hatch.cli.cache import format_size


def render_table(title, rows):
    console = Console(force_terminal=False, no_color=True, legacy_windows=False)
    table = Table(title=title, show_lines=True, title_style="", box=ASCII_DOUBLE_HEAD, safe_box=True)

    for column in rows[0]:
        table.add_column(column, style="bold")

    for row in rows[1:]:
        table.add_row(*row)

    with console.capture() as capture:
        console.print(table, overflow="ignore", no_wrap=True, crop=False)

    return capture.get()


@pytest.mark.parametrize(
    ("size", "expected"),
    [
        (0, "0 B"),
        (1023, "1023 B"),
        (1024, "1.0 KiB"),
        (1536, "1.5 KiB"),
        (1024**2, "1.0 MiB"),
        (3 * 1024**3, "3.0 GiB"),
        (1024**5, "1024.0 TiB"),
    ],
)
def testformat_size(size, expected):
    assert format_size(size) == expected


def test_nothing_cached(hatch, helpers, temp_dir_data, temp_dir_cache):  # noqa: ARG001
    result = hatch("cache", "show", "--ascii")

    assert result.exit_code == 0, result.output
    assert result.output == helpers.dedent(
        """
        Nothing is cached
        """
    )


def test_populated(hatch, populated_dirs):
    data_dir, cache_dir = populated_dirs

    result = hatch("cache", "show", "--ascii")

    assert result.exit_code == 0, result.output
    assert result.output == render_table(
        "Cache",
        [
            ["Category", "Location", "Size"],
            ["Project environments (virtual)", str(data_dir / "env" / "virtual"), "2.0 KiB"],
            ["Script environments (virtual)", str(data_dir / "env" / "virtual" / ".scripts"), "512 B"],
            ["Internal environments", str(data_dir / "env" / ".internal"), "256 B"],
            ["Python distributions", str(data_dir / "pythons"), "128 B"],
            ["Cache (licenses)", str(cache_dir / "licenses"), "64 B"],
        ],
    )


def test_only_pythons_and_cache(hatch, temp_dir_data, temp_dir_cache):
    data_dir = temp_dir_data / "data"
    cache_dir = temp_dir_cache / "cache"
    (data_dir / "pythons" / "3.12").ensure_dir_exists()
    (cache_dir / "shell").ensure_dir_exists()

    result = hatch("cache", "show", "--ascii")

    assert result.exit_code == 0, result.output
    assert result.output == render_table(
        "Cache",
        [
            ["Category", "Location", "Size"],
            ["Python distributions", str(data_dir / "pythons"), "0 B"],
            ["Cache (shell)", str(cache_dir / "shell"), "0 B"],
        ],
    )

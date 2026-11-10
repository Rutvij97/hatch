import pytest

from hatch.utils.fs import Path


def write_file(path: Path, size: int) -> None:
    path.parent.ensure_dir_exists()
    path.write_bytes(b"x" * size)


@pytest.fixture
def populated_dirs(temp_dir_data, temp_dir_cache):
    """Populate the isolated data and cache directories with every kind of cached content."""
    data_dir = temp_dir_data / "data"
    cache_dir = temp_dir_cache / "cache"

    write_file(data_dir / "env" / "virtual" / "my-app" / "aBcDeFgH" / "my-app" / "pyvenv.cfg", 1024)
    write_file(data_dir / "env" / "virtual" / "my-app" / "aBcDeFgH" / "test" / "pyvenv.cfg", 1024)
    write_file(data_dir / "env" / "virtual" / ".scripts" / "12345678" / "pyvenv.cfg", 512)
    write_file(data_dir / "env" / ".internal" / "hatch-test" / "hatch-test" / "pyvenv.cfg", 256)
    write_file(data_dir / "pythons" / "3.12" / "hatch-dist.json", 128)
    write_file(cache_dir / "licenses" / "MIT.txt", 64)

    return data_dir, cache_dir

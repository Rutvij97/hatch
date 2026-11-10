from __future__ import annotations

import os
from typing import TYPE_CHECKING

import click

if TYPE_CHECKING:
    from hatch.cli.application import Application
    from hatch.utils.fs import Path

INTERNAL_ENV_DIR = ".internal"
SCRIPTS_ENV_DIR = ".scripts"


def _dir_size(path: Path) -> int:
    """Return the total size in bytes of all files below ``path`` without following symbolic links."""
    total = 0
    stack = [str(path)]
    while stack:
        current = stack.pop()
        try:
            with os.scandir(current) as entries:
                for entry in entries:
                    try:
                        if entry.is_dir(follow_symlinks=False):
                            stack.append(entry.path)
                        else:
                            total += entry.stat(follow_symlinks=False).st_size
                    except OSError:  # no cov
                        continue
        except OSError:  # no cov
            continue

    return total


def format_size(size: int) -> str:
    value = float(size)
    for unit in ("B", "KiB", "MiB", "GiB", "TiB"):
        if value < 1024 or unit == "TiB":  # noqa: PLR2004
            break
        value /= 1024

    if unit == "B":
        return f"{size} B"

    return f"{value:.1f} {unit}"


def _project_env_paths(type_dir: Path) -> list[Path]:
    """The per-project storage directories of an environment type, excluding environments for scripts."""
    return sorted(path for path in type_dir.iterdir() if path.is_dir() and path.name != SCRIPTS_ENV_DIR)


def _env_type_dirs(app: Application) -> list[Path]:
    env_dir = app.data_dir / "env"
    if not env_dir.is_dir():
        return []

    # Hidden directories hold internal environments and environment metadata rather than an environment type
    return sorted(path for path in env_dir.iterdir() if path.is_dir() and not path.name.startswith("."))


@click.group(short_help="Manage cached data and environments")
def cache():
    pass


@cache.command(name="dir", short_help="Show the location of the cache directory")
@click.option("--data", "show_data", is_flag=True, help="Show the data directory, where environments are stored")
@click.pass_obj
def directory(app: Application, *, show_data: bool):
    """Show the location of the cache directory."""
    app.display(str(app.data_dir if show_data else app.cache_dir))


@cache.command(short_help="Show what is cached and how much space it uses")
@click.option("--ascii", "force_ascii", is_flag=True, help="Whether or not to only use ASCII characters")
@click.pass_obj
def show(app: Application, *, force_ascii: bool):
    """Show what is cached and how much space it uses."""
    columns: dict[str, dict[int, str]] = {"Category": {}, "Location": {}, "Size": {}}
    rows: list[tuple[str, Path, int]] = []

    for type_dir in _env_type_dirs(app):
        project_paths = _project_env_paths(type_dir)
        if project_paths:
            rows.append((f"Project environments ({type_dir.name})", type_dir, sum(map(_dir_size, project_paths))))

        scripts_dir = type_dir / SCRIPTS_ENV_DIR
        if scripts_dir.is_dir():
            rows.append((f"Script environments ({type_dir.name})", scripts_dir, _dir_size(scripts_dir)))

    internal_dir = app.data_dir / "env" / INTERNAL_ENV_DIR
    if internal_dir.is_dir():
        rows.append(("Internal environments", internal_dir, _dir_size(internal_dir)))

    pythons_dir = app.data_dir / "pythons"
    if pythons_dir.is_dir():
        rows.append(("Python distributions", pythons_dir, _dir_size(pythons_dir)))

    if app.cache_dir.is_dir():
        rows.extend(
            (f"Cache ({path.name})", path, _dir_size(path)) for path in sorted(app.cache_dir.iterdir()) if path.is_dir()
        )

    if not rows:
        app.display_info("Nothing is cached")
        return

    for i, (category, path, size) in enumerate(rows):
        columns["Category"][i] = category
        columns["Location"][i] = str(path)
        columns["Size"][i] = format_size(size)

    app.display_table("Cache", columns, show_lines=True, force_ascii=force_ascii)


@cache.command(short_help="Remove cached environments")
@click.option("--envs", is_flag=True, help="Remove the environments of all projects")
@click.option("--scripts", is_flag=True, help="Remove the environments created for running scripts")
@click.option("--internal", is_flag=True, help="Remove the internal environments, such as those used by `hatch test`")
@click.option("--yes", "-y", is_flag=True, help="Remove without confirmation")
@click.pass_obj
def clean(app: Application, *, envs: bool, scripts: bool, internal: bool, yes: bool):
    """
    Remove cached environments. When no category is selected, all of them are removed.

    Installed Python distributions are never removed; use `hatch python remove` for those.
    """
    if app.env_active:
        app.abort(f"Cannot remove environments while one is active: {app.env_active}")

    if not (envs or scripts or internal):
        envs = scripts = internal = True

    targets: list[tuple[str, Path]] = []
    for type_dir in _env_type_dirs(app):
        if envs:
            targets.extend((f"project environments ({type_dir.name})", path) for path in _project_env_paths(type_dir))

        scripts_dir = type_dir / SCRIPTS_ENV_DIR
        if scripts and scripts_dir.is_dir():
            targets.append((f"script environments ({type_dir.name})", scripts_dir))

    internal_dir = app.data_dir / "env" / INTERNAL_ENV_DIR
    if internal and internal_dir.is_dir():
        targets.append(("internal environments", internal_dir))

    if not targets:
        app.display_info("Nothing to remove")
        return

    total_size = sum(_dir_size(path) for _, path in targets)
    if not (
        yes
        or app.confirm(
            f"Remove {len(targets)} director{'y' if len(targets) == 1 else 'ies'} ({format_size(total_size)})?"
        )
    ):
        app.abort("No cached data was removed")

    for label, path in targets:
        with app.status(f"Removing {label}: {path}"):
            path.remove()

from hatch.config.constants import AppEnvVars
from hatch.project.core import Project
from hatch.utils.structures import EnvVars


def test_nothing_to_remove(hatch, helpers, temp_dir_data):  # noqa: ARG001
    result = hatch("cache", "clean", "-y")

    assert result.exit_code == 0, result.output
    assert result.output == helpers.dedent(
        """
        Nothing to remove
        """
    )


def test_active_environment(hatch, helpers, populated_dirs):
    data_dir, _ = populated_dirs

    with EnvVars({AppEnvVars.ENV_ACTIVE: "default"}):
        result = hatch("cache", "clean", "-y")

    assert result.exit_code == 1, result.output
    assert result.output == helpers.dedent(
        """
        Cannot remove environments while one is active: default
        """
    )
    assert (data_dir / "env" / "virtual" / "my-app").is_dir()


def test_prompt_declined(hatch, helpers, populated_dirs):
    data_dir, _ = populated_dirs

    result = hatch("cache", "clean", input="n\n")

    assert result.exit_code == 1, result.output
    assert result.output == helpers.dedent(
        """
        Remove 3 directories (2.8 KiB)? [y/N]: n
        No cached data was removed
        """
    )
    assert (data_dir / "env" / "virtual" / "my-app").is_dir()
    assert (data_dir / "env" / "virtual" / ".scripts").is_dir()
    assert (data_dir / "env" / ".internal").is_dir()


def test_prompt_accepted(hatch, helpers, populated_dirs):
    data_dir, cache_dir = populated_dirs

    result = hatch("cache", "clean", input="y\n")

    assert result.exit_code == 0, result.output
    assert result.output == helpers.dedent(
        f"""
        Remove 3 directories (2.8 KiB)? [y/N]: y
        Removing project environments (virtual): {data_dir / "env" / "virtual" / "my-app"}
        Removing script environments (virtual): {data_dir / "env" / "virtual" / ".scripts"}
        Removing internal environments: {data_dir / "env" / ".internal"}
        """
    )
    assert not (data_dir / "env" / "virtual" / "my-app").exists()
    assert not (data_dir / "env" / "virtual" / ".scripts").exists()
    assert not (data_dir / "env" / ".internal").exists()
    assert (data_dir / "pythons" / "3.12").is_dir()
    assert (cache_dir / "licenses" / "MIT.txt").is_file()


def test_all_without_prompt(hatch, helpers, populated_dirs):
    data_dir, cache_dir = populated_dirs

    result = hatch("cache", "clean", "-y")

    assert result.exit_code == 0, result.output
    assert result.output == helpers.dedent(
        f"""
        Removing project environments (virtual): {data_dir / "env" / "virtual" / "my-app"}
        Removing script environments (virtual): {data_dir / "env" / "virtual" / ".scripts"}
        Removing internal environments: {data_dir / "env" / ".internal"}
        """
    )
    assert not (data_dir / "env" / "virtual" / "my-app").exists()
    assert not (data_dir / "env" / "virtual" / ".scripts").exists()
    assert not (data_dir / "env" / ".internal").exists()
    assert (data_dir / "pythons" / "3.12").is_dir()
    assert (cache_dir / "licenses" / "MIT.txt").is_file()


def test_envs_only(hatch, helpers, populated_dirs):
    data_dir, _ = populated_dirs

    result = hatch("cache", "clean", "--envs", "-y")

    assert result.exit_code == 0, result.output
    assert result.output == helpers.dedent(
        f"""
        Removing project environments (virtual): {data_dir / "env" / "virtual" / "my-app"}
        """
    )
    assert not (data_dir / "env" / "virtual" / "my-app").exists()
    assert (data_dir / "env" / "virtual" / ".scripts").is_dir()
    assert (data_dir / "env" / ".internal").is_dir()


def test_scripts_and_internal(hatch, helpers, populated_dirs):
    data_dir, _ = populated_dirs

    result = hatch("cache", "clean", "--scripts", "--internal", "-y")

    assert result.exit_code == 0, result.output
    assert result.output == helpers.dedent(
        f"""
        Removing script environments (virtual): {data_dir / "env" / "virtual" / ".scripts"}
        Removing internal environments: {data_dir / "env" / ".internal"}
        """
    )
    assert (data_dir / "env" / "virtual" / "my-app").is_dir()
    assert not (data_dir / "env" / "virtual" / ".scripts").exists()
    assert not (data_dir / "env" / ".internal").exists()


def test_removes_created_environment(hatch, helpers, temp_dir_data, config_file):
    config_file.model.template.plugins["default"]["tests"] = False
    config_file.save()

    project_name = "My.App"

    with temp_dir_data.as_cwd():
        result = hatch("new", project_name)

    assert result.exit_code == 0, result.output

    project_path = temp_dir_data / "my-app"

    project = Project(project_path)
    helpers.update_project_environment(project, "default", {"skip-install": True, **project.config.envs["default"]})

    with project_path.as_cwd():
        result = hatch("env", "create")

    assert result.exit_code == 0, result.output

    project_data_path = temp_dir_data / "data" / "env" / "virtual" / project_path.name
    assert project_data_path.is_dir()

    with project_path.as_cwd():
        result = hatch("cache", "clean", "--envs", "-y")

    assert result.exit_code == 0, result.output
    assert result.output == helpers.dedent(
        f"""
        Removing project environments (virtual): {project_data_path}
        """
    )
    assert not project_data_path.exists()

    with project_path.as_cwd():
        result = hatch("env", "find")

    assert result.exit_code == 0, result.output
    assert not (temp_dir_data / "data" / "env" / "virtual" / project_path.name).exists()

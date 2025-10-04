import tempfile
from pathlib import Path
from unittest import mock

from click.testing import CliRunner

from gac.init_cli import init


def test_init_cli_interactive(monkeypatch):
    runner = CliRunner()
    with tempfile.TemporaryDirectory() as tmpdir:
        env_path = Path(tmpdir) / ".gac.env"
        # Patch GAC_ENV_PATH in the module to point to our temp env file
        with mock.patch("gac.init_cli.GAC_ENV_PATH", env_path):
            # Simulate user input for: provider, model, api key
            user_inputs = [
                "Groq",  # provider
                "meta-llama/llama-4-scout-17b-16e-instruct",  # model
                "main-api-key",  # main api key
            ]
            # Patch questionary.select/text/password/confirm to return our sequence
            with (
                mock.patch("questionary.select") as mselect,
                mock.patch("questionary.text") as mtext,
                mock.patch("questionary.password") as mpass,
            ):
                mselect.return_value.ask.return_value = user_inputs[0]
                mtext.return_value.ask.return_value = user_inputs[1]
                mpass.return_value.ask.return_value = user_inputs[2]
                result = runner.invoke(init)
                assert result.exit_code == 0
                env_text = env_path.read_text()
                assert "GAC_MODEL='groq:meta-llama/llama-4-scout-17b-16e-instruct'" in env_text
                assert "GROQ_API_KEY='main-api-key'" in env_text


def test_init_cli_non_interactive(monkeypatch):
    runner = CliRunner()
    with tempfile.TemporaryDirectory() as tmpdir:
        env_path = Path(tmpdir) / ".gac.env"
        # Patch GAC_ENV_PATH in the module to point to our temp env file
        with mock.patch("gac.init_cli.GAC_ENV_PATH", env_path):
            # Simulate user input for: provider, model, api key
            user_inputs = [
                "Groq",  # provider
                "meta-llama/llama-4-scout-17b-16e-instruct",  # model
                "main-api-key",  # main api key
            ]
            # Patch questionary.select/text/password/confirm to return our sequence
            with (
                mock.patch("questionary.select") as mselect,
                mock.patch("questionary.text") as mtext,
                mock.patch("questionary.password") as mpass,
            ):
                mselect.return_value.ask.return_value = user_inputs[0]
                mtext.return_value.ask.return_value = user_inputs[1]
                mpass.return_value.ask.return_value = user_inputs[2]
                result = runner.invoke(init)
                assert result.exit_code == 0
                env_text = env_path.read_text()
                assert "GAC_MODEL='groq:meta-llama/llama-4-scout-17b-16e-instruct'" in env_text
                assert "GROQ_API_KEY='main-api-key'" in env_text


def test_init_cli_zai_with_coding_plan(monkeypatch):
    runner = CliRunner()
    with tempfile.TemporaryDirectory() as tmpdir:
        env_path = Path(tmpdir) / ".gac.env"
        # Patch GAC_ENV_PATH in the module to point to our temp env file
        with mock.patch("gac.init_cli.GAC_ENV_PATH", env_path):
            # Simulate user input for: provider, model, api key, coding plan
            user_inputs = [
                "Z.AI",  # provider
                "glm-4.6",  # model
                "zai-api-key",  # api key
                True,  # coding plan confirmation
            ]
            # Patch questionary.select/text/password/confirm to return our sequence
            with (
                mock.patch("questionary.select") as mselect,
                mock.patch("questionary.text") as mtext,
                mock.patch("questionary.password") as mpass,
                mock.patch("questionary.confirm") as mconfirm,
            ):
                mselect.return_value.ask.return_value = user_inputs[0]
                mtext.return_value.ask.return_value = user_inputs[1]
                mpass.return_value.ask.return_value = user_inputs[2]
                mconfirm.return_value.ask.return_value = user_inputs[3]
                result = runner.invoke(init)
                assert result.exit_code == 0
                env_text = env_path.read_text()
                assert "GAC_MODEL='zai:glm-4.6'" in env_text
                assert "ZAI_API_KEY='zai-api-key'" in env_text
                assert "GAC_ZAI_USE_CODING_PLAN='true'" in env_text


def test_init_cli_zai_without_coding_plan(monkeypatch):
    runner = CliRunner()
    with tempfile.TemporaryDirectory() as tmpdir:
        env_path = Path(tmpdir) / ".gac.env"
        # Patch GAC_ENV_PATH in the module to point to our temp env file
        with mock.patch("gac.init_cli.GAC_ENV_PATH", env_path):
            # Simulate user input for: provider, model, api key, coding plan
            user_inputs = [
                "Z.AI",  # provider
                "glm-4.6",  # model
                "zai-api-key",  # api key
                False,  # coding plan confirmation
            ]
            # Patch questionary.select/text/password/confirm to return our sequence
            with (
                mock.patch("questionary.select") as mselect,
                mock.patch("questionary.text") as mtext,
                mock.patch("questionary.password") as mpass,
                mock.patch("questionary.confirm") as mconfirm,
            ):
                mselect.return_value.ask.return_value = user_inputs[0]
                mtext.return_value.ask.return_value = user_inputs[1]
                mpass.return_value.ask.return_value = user_inputs[2]
                mconfirm.return_value.ask.return_value = user_inputs[3]
                result = runner.invoke(init)
                assert result.exit_code == 0
                env_text = env_path.read_text()
                assert "GAC_MODEL='zai:glm-4.6'" in env_text
                assert "ZAI_API_KEY='zai-api-key'" in env_text
                assert "GAC_ZAI_USE_CODING_PLAN" not in env_text


def test_init_cli_non_interactive_zai_with_coding_plan(monkeypatch):
    runner = CliRunner()
    with tempfile.TemporaryDirectory() as tmpdir:
        env_path = Path(tmpdir) / ".gac.env"
        # Patch GAC_ENV_PATH in the module to point to our temp env file
        with mock.patch("gac.init_cli.GAC_ENV_PATH", env_path):
            # Simulate user input for: provider, model, api key, coding plan
            user_inputs = [
                "Z.AI",  # provider
                "glm-4.6",  # model
                "zai-api-key",  # api key
                True,  # coding plan confirmation
            ]
            # Patch questionary.select/text/password/confirm to return our sequence
            with (
                mock.patch("questionary.select") as mselect,
                mock.patch("questionary.text") as mtext,
                mock.patch("questionary.password") as mpass,
                mock.patch("questionary.confirm") as mconfirm,
            ):
                mselect.return_value.ask.return_value = user_inputs[0]
                mtext.return_value.ask.return_value = user_inputs[1]
                mpass.return_value.ask.return_value = user_inputs[2]
                mconfirm.return_value.ask.return_value = user_inputs[3]
                result = runner.invoke(init)
                assert result.exit_code == 0
                env_text = env_path.read_text()
                assert "GAC_MODEL='zai:glm-4.6'" in env_text
                assert "ZAI_API_KEY='zai-api-key'" in env_text
                assert "GAC_ZAI_USE_CODING_PLAN='true'" in env_text


def test_init_cli_non_interactive_zai_without_coding_plan(monkeypatch):
    runner = CliRunner()
    with tempfile.TemporaryDirectory() as tmpdir:
        env_path = Path(tmpdir) / ".gac.env"
        # Patch GAC_ENV_PATH in the module to point to our temp env file
        with mock.patch("gac.init_cli.GAC_ENV_PATH", env_path):
            # Simulate user input for: provider, model, api key, coding plan
            user_inputs = [
                "Z.AI",  # provider
                "glm-4.6",  # model
                "zai-api-key",  # api key
                False,  # coding plan confirmation
            ]
            # Patch questionary.select/text/password/confirm to return our sequence
            with (
                mock.patch("questionary.select") as mselect,
                mock.patch("questionary.text") as mtext,
                mock.patch("questionary.password") as mpass,
                mock.patch("questionary.confirm") as mconfirm,
            ):
                mselect.return_value.ask.return_value = user_inputs[0]
                mtext.return_value.ask.return_value = user_inputs[1]
                mpass.return_value.ask.return_value = user_inputs[2]
                mconfirm.return_value.ask.return_value = user_inputs[3]
                result = runner.invoke(init)
                assert result.exit_code == 0
                env_text = env_path.read_text()
                assert "GAC_MODEL='zai:glm-4.6'" in env_text
                assert "ZAI_API_KEY='zai-api-key'" in env_text
                assert "GAC_ZAI_USE_CODING_PLAN" not in env_text

import tempfile
from pathlib import Path
from unittest import mock

from click.testing import CliRunner

from gac.init_cli import init


def _setup_env_file(tmpdir: str) -> Path:
    env_path = Path(tmpdir) / ".gac.env"
    env_path.touch()
    return env_path


def test_init_cli_groq(monkeypatch):
    runner = CliRunner()
    with tempfile.TemporaryDirectory() as tmpdir:
        env_path = _setup_env_file(tmpdir)
        with mock.patch("gac.init_cli.GAC_ENV_PATH", env_path):
            with (
                mock.patch("questionary.select") as mselect,
                mock.patch("questionary.text") as mtext,
                mock.patch("questionary.password") as mpass,
            ):
                # Provider selection, then language selection (English = no prefix prompt)
                mselect.return_value.ask.side_effect = ["Groq", "English"]
                mtext.return_value.ask.side_effect = ["meta-llama/llama-4-scout-17b-16e-instruct"]
                mpass.return_value.ask.side_effect = ["main-api-key"]

                result = runner.invoke(init)
                assert result.exit_code == 0
                env_text = env_path.read_text()
                assert "GAC_MODEL='groq:meta-llama/llama-4-scout-17b-16e-instruct'" in env_text
                assert "GROQ_API_KEY='main-api-key'" in env_text


def test_init_cli_zai_regular_provider(monkeypatch):
    runner = CliRunner()
    with tempfile.TemporaryDirectory() as tmpdir:
        env_path = _setup_env_file(tmpdir)
        with mock.patch("gac.init_cli.GAC_ENV_PATH", env_path):
            with (
                mock.patch("questionary.select") as mselect,
                mock.patch("questionary.text") as mtext,
                mock.patch("questionary.password") as mpass,
            ):
                # Provider selection, then language selection
                mselect.return_value.ask.side_effect = ["Z.AI", "English"]
                mtext.return_value.ask.side_effect = ["glm-4.6"]
                mpass.return_value.ask.side_effect = ["zai-api-key"]

                result = runner.invoke(init)
                assert result.exit_code == 0
                env_text = env_path.read_text()
                assert "GAC_MODEL='zai:glm-4.6'" in env_text
                assert "ZAI_API_KEY='zai-api-key'" in env_text


def test_init_cli_zai_coding_provider(monkeypatch):
    runner = CliRunner()
    with tempfile.TemporaryDirectory() as tmpdir:
        env_path = _setup_env_file(tmpdir)
        with mock.patch("gac.init_cli.GAC_ENV_PATH", env_path):
            with (
                mock.patch("questionary.select") as mselect,
                mock.patch("questionary.text") as mtext,
                mock.patch("questionary.password") as mpass,
            ):
                # Provider selection, then language selection
                mselect.return_value.ask.side_effect = ["Z.AI Coding", "English"]
                mtext.return_value.ask.side_effect = ["glm-4.6"]
                mpass.return_value.ask.side_effect = ["zai-api-key"]

                result = runner.invoke(init)
                assert result.exit_code == 0
                env_text = env_path.read_text()
                assert "GAC_MODEL='zai-coding:glm-4.6'" in env_text
                assert "ZAI_API_KEY='zai-api-key'" in env_text


def test_init_cli_streamlake_requires_endpoint(monkeypatch):
    runner = CliRunner()
    with tempfile.TemporaryDirectory() as tmpdir:
        env_path = _setup_env_file(tmpdir)
        with mock.patch("gac.init_cli.GAC_ENV_PATH", env_path):
            with (
                mock.patch("questionary.select") as mselect,
                mock.patch("questionary.text") as mtext,
                mock.patch("questionary.password") as mpass,
            ):
                # Provider selection, then language selection
                mselect.return_value.ask.side_effect = ["Streamlake", "English"]
                # First text prompt is for the endpoint ID (required)
                mtext.return_value.ask.side_effect = ["ep-custom-12345"]
                mpass.return_value.ask.side_effect = ["streamlake-key"]

                result = runner.invoke(init)
                assert result.exit_code == 0
                env_text = env_path.read_text()
                assert "GAC_MODEL='streamlake:ep-custom-12345'" in env_text
                assert "STREAMLAKE_API_KEY='streamlake-key'" in env_text


def test_init_cli_ollama_optional_api_key_and_url(monkeypatch):
    runner = CliRunner()
    with tempfile.TemporaryDirectory() as tmpdir:
        env_path = _setup_env_file(tmpdir)
        with mock.patch("gac.init_cli.GAC_ENV_PATH", env_path):
            with (
                mock.patch("questionary.select") as mselect,
                mock.patch("questionary.text") as mtext,
                mock.patch("questionary.password") as mpass,
            ):
                # Provider selection, then language selection
                mselect.return_value.ask.side_effect = ["Ollama", "English"]
                # Text prompts: model, API URL
                mtext.return_value.ask.side_effect = ["gemma3", "http://localhost:11434"]
                mpass.return_value.ask.side_effect = [""]  # optional key skipped

                result = runner.invoke(init)
                assert result.exit_code == 0
                env_text = env_path.read_text()
                assert "GAC_MODEL='ollama:gemma3'" in env_text
                assert "OLLAMA_API_URL='http://localhost:11434'" in env_text
                assert "OLLAMA_API_KEY" not in env_text


def test_init_cli_lmstudio_optional_api_key_and_url(monkeypatch):
    runner = CliRunner()
    with tempfile.TemporaryDirectory() as tmpdir:
        env_path = _setup_env_file(tmpdir)
        with mock.patch("gac.init_cli.GAC_ENV_PATH", env_path):
            with (
                mock.patch("questionary.select") as mselect,
                mock.patch("questionary.text") as mtext,
                mock.patch("questionary.password") as mpass,
            ):
                # Provider selection, then language selection
                mselect.return_value.ask.side_effect = ["LM Studio", "English"]
                # Text prompts: model, API URL
                mtext.return_value.ask.side_effect = ["deepseek-r1-distill-qwen-7b", "http://localhost:1234"]
                mpass.return_value.ask.side_effect = [""]  # optional key skipped

                result = runner.invoke(init)
                assert result.exit_code == 0
                env_text = env_path.read_text()
                assert "GAC_MODEL='lm-studio:deepseek-r1-distill-qwen-7b'" in env_text
                assert "LMSTUDIO_API_URL='http://localhost:1234'" in env_text
                assert "LMSTUDIO_API_KEY" not in env_text


def test_init_cli_provider_selection_cancelled():
    """Test behavior when user cancels provider selection."""
    runner = CliRunner()
    with tempfile.TemporaryDirectory() as tmpdir:
        env_path = _setup_env_file(tmpdir)
        with mock.patch("gac.init_cli.GAC_ENV_PATH", env_path):
            with mock.patch("questionary.select") as mselect:
                mselect.return_value.ask.return_value = None

                result = runner.invoke(init)
                assert result.exit_code == 0
                assert "Provider selection cancelled" in result.output


def test_init_cli_streamlake_endpoint_cancelled():
    """Test behavior when user cancels Streamlake endpoint entry."""
    runner = CliRunner()
    with tempfile.TemporaryDirectory() as tmpdir:
        env_path = _setup_env_file(tmpdir)
        with mock.patch("gac.init_cli.GAC_ENV_PATH", env_path):
            with (
                mock.patch("questionary.select") as mselect,
                mock.patch("questionary.text") as mtext,
            ):
                mselect.return_value.ask.return_value = "Streamlake"
                mtext.return_value.ask.return_value = None

                result = runner.invoke(init)
                assert result.exit_code == 0
                assert "Streamlake configuration cancelled" in result.output


def test_init_cli_model_entry_cancelled():
    """Test behavior when user cancels model entry."""
    runner = CliRunner()
    with tempfile.TemporaryDirectory() as tmpdir:
        env_path = _setup_env_file(tmpdir)
        with mock.patch("gac.init_cli.GAC_ENV_PATH", env_path):
            with (
                mock.patch("questionary.select") as mselect,
                mock.patch("questionary.text") as mtext,
            ):
                mselect.return_value.ask.return_value = "OpenAI"
                mtext.return_value.ask.return_value = None

                result = runner.invoke(init)
                assert result.exit_code == 0
                assert "Model entry cancelled" in result.output


def test_init_cli_ollama_url_cancelled():
    """Test behavior when user cancels Ollama URL entry."""
    runner = CliRunner()
    with tempfile.TemporaryDirectory() as tmpdir:
        env_path = _setup_env_file(tmpdir)
        with mock.patch("gac.init_cli.GAC_ENV_PATH", env_path):
            with (
                mock.patch("questionary.select") as mselect,
                mock.patch("questionary.text") as mtext,
            ):
                mselect.return_value.ask.return_value = "Ollama"
                mtext.return_value.ask.side_effect = ["gemma3", None]

                result = runner.invoke(init)
                assert result.exit_code == 0
                assert "Ollama URL entry cancelled" in result.output


def test_init_cli_lmstudio_url_cancelled():
    """Test behavior when user cancels LM Studio URL entry."""
    runner = CliRunner()
    with tempfile.TemporaryDirectory() as tmpdir:
        env_path = _setup_env_file(tmpdir)
        with mock.patch("gac.init_cli.GAC_ENV_PATH", env_path):
            with (
                mock.patch("questionary.select") as mselect,
                mock.patch("questionary.text") as mtext,
            ):
                mselect.return_value.ask.return_value = "LM Studio"
                mtext.return_value.ask.side_effect = ["gemma3", None]

                result = runner.invoke(init)
                assert result.exit_code == 0
                assert "LM Studio URL entry cancelled" in result.output


def test_prompt_required_text_retry_on_empty():
    """Test _prompt_required_text retries on empty input and handles cancellation."""
    from gac.init_cli import _prompt_required_text

    with mock.patch("questionary.text") as mtext:
        # Simulate: empty string, whitespace, then valid value
        mtext.return_value.ask.side_effect = ["", "  ", "valid-value"]
        with mock.patch("click.echo"):
            result = _prompt_required_text("Enter value:")
            assert result == "valid-value"


def test_prompt_required_text_cancelled():
    """Test _prompt_required_text returns None when user cancels."""
    from gac.init_cli import _prompt_required_text

    with mock.patch("questionary.text") as mtext:
        mtext.return_value.ask.return_value = None
        result = _prompt_required_text("Enter value:")
        assert result is None

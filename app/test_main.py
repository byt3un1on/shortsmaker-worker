"""Tests for the main module."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from infra.config.settings import Settings
from main import main, print_startup_banner, run_worker, validate_configuration


def test_placeholder():
    """Placeholder test to ensure tests can run."""
    assert True


class TestValidateConfiguration:
    """Test configuration validation."""

    @patch("main.get_settings")
    def test_validate_configuration_success(self, mock_get_settings):
        """Test successful configuration validation."""
        # Arrange
        mock_settings = MagicMock()
        mock_settings.validate_required_configs = MagicMock()
        mock_get_settings.return_value = mock_settings

        # Act
        result = validate_configuration()

        # Assert
        assert result == mock_settings
        mock_settings.validate_required_configs.assert_called_once()

    @patch("main.get_settings")
    def test_validate_configuration_failure(self, mock_get_settings):
        """Test configuration validation failure."""
        # Arrange
        mock_settings = MagicMock()
        mock_settings.validate_required_configs.side_effect = ValueError(
            "Invalid config"
        )
        mock_get_settings.return_value = mock_settings

        # Act & Assert
        with patch("sys.exit") as mock_exit:
            validate_configuration()
            mock_exit.assert_called_once_with(1)

    @patch("main.get_settings")
    def test_validate_configuration_unexpected_error(self, mock_get_settings):
        """Test unexpected error during configuration validation."""
        # Arrange
        mock_settings = MagicMock()
        mock_settings.validate_required_configs.side_effect = RuntimeError(
            "Unexpected error"
        )
        mock_get_settings.return_value = mock_settings

        # Act & Assert
        with patch("sys.exit") as mock_exit:
            validate_configuration()
            mock_exit.assert_called_once_with(1)


class TestPrintStartupBanner:
    """Test startup banner printing."""

    def test_print_startup_banner_gemini_provider(self, capsys):
        """Test banner printing with Gemini provider."""
        # Arrange
        settings = Settings(
            llm_provider="gemini",
            storage_provider="supabase",
            video_provider="gemini",
            audio_provider="elevenlabs",
            worker_poll_interval=5,
            log_level="INFO",
        )

        # Act
        print_startup_banner(settings)

        # Assert
        captured = capsys.readouterr()
        assert "SHORTSMAKER WORKER" in captured.out
        assert "LLM Provider: gemini" in captured.out
        assert "Storage:      supabase" in captured.out

    def test_print_startup_banner_openai_provider(self, capsys):
        """Test banner printing with OpenAI provider."""
        # Arrange
        settings = Settings(
            llm_provider="openai",
            storage_provider="minio",
            video_provider="placeholder",
            audio_provider="placeholder",
            worker_poll_interval=10,
            log_level="DEBUG",
        )

        # Act
        print_startup_banner(settings)

        # Assert
        captured = capsys.readouterr()
        assert "LLM Provider: openai" in captured.out
        assert "Storage:      minio" in captured.out


class TestRunWorker:
    """Test the main worker execution."""

    @patch("main.setup_logging")
    @patch("main.validate_configuration")
    @patch("main.print_startup_banner")
    @patch("main.build_container")
    @patch("infra.database.migrations.run_migrations", return_value=True)
    @patch("asyncio.sleep", new_callable=AsyncMock)  # Prevent actual sleeping
    def test_run_worker_successful_initialization(
        self,
        mock_sleep,
        mock_run_migrations,
        mock_build_container,
        mock_print_banner,
        mock_validate_config,
        mock_setup_logging,
    ):
        """Test successful worker initialization and execution."""
        # Arrange
        mock_settings = MagicMock()
        mock_validate_config.return_value = mock_settings

        mock_container = MagicMock()
        mock_worker_manager = AsyncMock()
        mock_worker_manager.start.side_effect = (
            asyncio.CancelledError()
        )  # Simulate cancellation
        mock_container.worker_manager.return_value = mock_worker_manager
        mock_build_container.return_value = mock_container

        # Act - Should complete without raising exception (graceful shutdown)
        asyncio.run(run_worker())

        # Assert all initialization steps were called
        mock_setup_logging.assert_called_once()
        mock_validate_config.assert_called_once()
        mock_print_banner.assert_called_once_with(mock_settings)
        mock_build_container.assert_called_once_with(mock_settings)
        mock_run_migrations.assert_called_once()
        mock_container.worker_manager.assert_called_once()
        mock_worker_manager.start.assert_called_once()
        mock_worker_manager.stop.assert_called_once()  # Called on cancellation

    @patch("main.setup_logging")
    @patch("main.validate_configuration")
    @patch("main.print_startup_banner")
    @patch("main.build_container", side_effect=Exception("Container build failed"))
    def test_run_worker_container_build_failure(
        self,
        mock_build_container,
        mock_print_banner,
        mock_validate_config,
        mock_setup_logging,
    ):
        """Test worker failure during container building."""
        # Arrange
        mock_settings = MagicMock()
        mock_validate_config.return_value = mock_settings

        # Act & Assert
        with pytest.raises(SystemExit, match="1"):
            asyncio.run(run_worker())

    @patch("main.setup_logging")
    @patch("main.validate_configuration")
    @patch("main.print_startup_banner")
    @patch("main.build_container")
    @patch("infra.database.migrations.run_migrations", return_value=False)
    def test_run_worker_migration_failure(
        self,
        mock_run_migrations,
        mock_build_container,
        mock_print_banner,
        mock_validate_config,
        mock_setup_logging,
    ):
        """Test worker failure during database migrations."""
        # Arrange
        mock_settings = MagicMock()
        mock_validate_config.return_value = mock_settings
        mock_container = MagicMock()
        mock_worker_manager = AsyncMock()  # Need AsyncMock for await
        mock_container.worker_manager.return_value = mock_worker_manager
        mock_build_container.return_value = mock_container

        # Act & Assert
        with pytest.raises(SystemExit, match="1"):
            asyncio.run(run_worker())


class TestMainFunction:
    """Test the main entry point function."""

    @patch("asyncio.run")
    def test_main_success(self, mock_asyncio_run):
        """Test successful main execution."""
        # Arrange
        mock_asyncio_run.return_value = None

        # Act
        main()

        # Assert
        mock_asyncio_run.assert_called_once()

    @patch("asyncio.run", side_effect=KeyboardInterrupt())
    @patch("main.logger")
    def test_main_keyboard_interrupt(self, mock_logger, mock_asyncio_run):
        """Test main with keyboard interrupt."""
        # Act
        main()

        # Assert
        mock_asyncio_run.assert_called_once()
        mock_logger.info.assert_called_with("Shutting down gracefully...")

    @patch("asyncio.run", side_effect=Exception("Test error"))
    @patch("main.logger")
    def test_main_unexpected_error(self, mock_logger, mock_asyncio_run):
        """Test main with unexpected error."""
        # Act
        with patch("sys.exit") as mock_exit:
            main()

        # Assert
        mock_asyncio_run.assert_called_once()
        mock_logger.error.assert_called_with(
            "Application terminated with error: Test error"
        )
        mock_exit.assert_called_once_with(1)


class TestIntegrationScenarios:
    """Integration tests for main functionality."""

    @patch("main.setup_logging")
    @patch("main.validate_configuration")
    @patch("main.print_startup_banner")
    @patch("main.build_container")
    @patch("infra.database.migrations.run_migrations", return_value=True)
    def test_full_initialization_flow(
        self,
        mock_run_migrations,
        mock_build_container,
        mock_print_banner,
        mock_validate_config,
        mock_setup_logging,
    ):
        """Test the complete initialization flow."""
        # Arrange
        mock_settings = Settings(
            llm_provider="gemini",
            storage_provider="supabase",
            video_provider="gemini",
            audio_provider="elevenlabs",
        )
        mock_validate_config.return_value = mock_settings

        mock_container = MagicMock()
        mock_worker_manager = AsyncMock()
        mock_worker_manager.start.side_effect = (
            asyncio.CancelledError()
        )  # Stop immediately
        mock_container.worker_manager.return_value = mock_worker_manager
        mock_build_container.return_value = mock_container

        # Act - Should complete without raising exception (graceful shutdown)
        asyncio.run(run_worker())

        # Verify the complete flow
        assert mock_setup_logging.called
        assert mock_validate_config.called
        assert mock_print_banner.called
        assert mock_build_container.called
        assert mock_run_migrations.called
        assert mock_worker_manager.start.called
        assert mock_worker_manager.stop.called  # Should be called on cancellation

    @patch("main.setup_logging")
    @patch("main.validate_configuration")
    @patch("main.print_startup_banner")
    @patch("main.build_container")
    @patch("infra.database.migrations.run_migrations", return_value=True)
    def test_worker_manager_graceful_shutdown(
        self,
        mock_run_migrations,
        mock_build_container,
        mock_print_banner,
        mock_validate_config,
        mock_setup_logging,
    ):
        """Test graceful shutdown of worker manager."""
        # Arrange
        mock_settings = MagicMock()
        mock_validate_config.return_value = mock_settings

        mock_container = MagicMock()
        mock_worker_manager = AsyncMock()
        mock_worker_manager.start.side_effect = Exception("Worker error")
        mock_container.worker_manager.return_value = mock_worker_manager
        mock_build_container.return_value = mock_container

        # Act & Assert
        with pytest.raises(Exception, match="Worker error"):
            asyncio.run(run_worker())

        # Verify shutdown was called even on error
        mock_worker_manager.stop.assert_called_once()

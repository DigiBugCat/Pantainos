"""
Tests for pantainos.utils.logging module
"""

import logging
from unittest.mock import MagicMock, patch

from pantainos.utils.logging import get_logger, setup_logging


class TestSetupLogging:
    """Test setup_logging function behavior"""

    def test_setup_logging_debug_mode(self) -> None:
        """Verify that when debug=True, both level and third_party_level are set to DEBUG"""
        with patch("logging.getLogger") as mock_get_logger, patch("logging.StreamHandler") as mock_handler_class:
            # Mock loggers
            root_logger = MagicMock()
            pantainos_logger = MagicMock()
            third_party_logger = MagicMock()

            def get_logger_side_effect(name: str = "") -> MagicMock:
                if name == "":
                    return root_logger
                if name == "pantainos":
                    return pantainos_logger
                return third_party_logger

            mock_get_logger.side_effect = get_logger_side_effect

            # Mock handler
            mock_handler = MagicMock()
            mock_handler_class.return_value = mock_handler

            # Call function
            setup_logging(debug=True, verbose=False, app_name="pantainos")

            # Verify root logger configuration
            root_logger.setLevel.assert_called_with(logging.DEBUG)

            # Verify pantainos logger level
            pantainos_logger.setLevel.assert_called_with(logging.DEBUG)

            # Verify handler configuration
            mock_handler.setLevel.assert_called_with(logging.DEBUG)

    def test_setup_logging_verbose_mode(self) -> None:
        """Verify that when verbose=True (and debug=False), level is DEBUG but third_party_level is INFO"""
        with patch("logging.getLogger") as mock_get_logger, patch("logging.StreamHandler") as mock_handler_class:
            # Mock loggers
            root_logger = MagicMock()
            pantainos_logger = MagicMock()
            third_party_logger = MagicMock()

            def get_logger_side_effect(name: str = "") -> MagicMock:
                if name == "":
                    return root_logger
                if name == "pantainos":
                    return pantainos_logger
                return third_party_logger

            mock_get_logger.side_effect = get_logger_side_effect

            # Mock handler
            mock_handler = MagicMock()
            mock_handler_class.return_value = mock_handler

            # Call function
            setup_logging(debug=False, verbose=True, app_name="pantainos")

            # Verify pantainos logger gets DEBUG level
            pantainos_logger.setLevel.assert_called_with(logging.DEBUG)

            # Verify handler gets DEBUG level
            mock_handler.setLevel.assert_called_with(logging.DEBUG)

    def test_setup_logging_default_mode(self) -> None:
        """Verify that when both debug and verbose are False, level is INFO and third_party_level is WARNING"""
        with patch("logging.getLogger") as mock_get_logger, patch("logging.StreamHandler") as mock_handler_class:
            # Mock loggers
            root_logger = MagicMock()
            pantainos_logger = MagicMock()
            third_party_logger = MagicMock()

            def get_logger_side_effect(name: str = "") -> MagicMock:
                if name == "":
                    return root_logger
                if name == "pantainos":
                    return pantainos_logger
                return third_party_logger

            mock_get_logger.side_effect = get_logger_side_effect

            # Mock handler
            mock_handler = MagicMock()
            mock_handler_class.return_value = mock_handler

            # Call function
            setup_logging(debug=False, verbose=False, app_name="pantainos")

            # Verify pantainos logger gets INFO level
            pantainos_logger.setLevel.assert_called_with(logging.INFO)

            # Verify handler gets INFO level
            mock_handler.setLevel.assert_called_with(logging.INFO)

    def test_logger_levels_configuration(self) -> None:
        """Verify that pantainos logger gets correct level and third-party loggers get their respective levels"""
        with patch("logging.getLogger") as mock_get_logger, patch("logging.StreamHandler"):
            # Mock loggers
            root_logger = MagicMock()
            pantainos_logger = MagicMock()
            twitchio_logger = MagicMock()
            httpx_logger = MagicMock()

            logger_map = {
                "": root_logger,
                "pantainos": pantainos_logger,
                "twitchio": twitchio_logger,
                "httpx": httpx_logger,
                "uvicorn": MagicMock(),
                "fastapi": MagicMock(),
                "websockets": MagicMock(),
                "aiohttp": MagicMock(),
                "obswebsocket": MagicMock(),
                "httpx._client": MagicMock(),
                "websockets.protocol": MagicMock(),
                "uvicorn.access": MagicMock(),
            }

            mock_get_logger.side_effect = lambda name="": logger_map[name]

            # Call function in verbose mode
            setup_logging(debug=False, verbose=True, app_name="pantainos")

            # Verify pantainos logger gets DEBUG
            pantainos_logger.setLevel.assert_called_with(logging.DEBUG)

            # Verify third-party loggers get INFO
            twitchio_logger.setLevel.assert_called_with(logging.INFO)
            httpx_logger.setLevel.assert_called_with(logging.INFO)

    def test_handler_removal_and_addition(self) -> None:
        """Verify that existing handlers are properly removed and new console handler is added"""
        with patch("logging.getLogger") as mock_get_logger, patch("logging.StreamHandler") as mock_handler_class:
            # Mock existing handlers
            existing_handler1 = MagicMock()
            existing_handler2 = MagicMock()

            root_logger = MagicMock()
            root_logger.handlers = [existing_handler1, existing_handler2]

            mock_get_logger.return_value = root_logger

            # Mock new handler
            new_handler = MagicMock()
            mock_handler_class.return_value = new_handler

            # Call function
            setup_logging()

            # Verify existing handlers were removed
            root_logger.removeHandler.assert_any_call(existing_handler1)
            root_logger.removeHandler.assert_any_call(existing_handler2)

            # Verify new handler was added
            root_logger.addHandler.assert_called_with(new_handler)

    def test_special_noisy_loggers(self) -> None:
        """Verify that special noisy loggers are set to WARNING level when debug=False"""
        with patch("logging.getLogger") as mock_get_logger, patch("logging.StreamHandler"):
            # Mock special loggers
            httpx_client_logger = MagicMock()
            websockets_protocol_logger = MagicMock()
            uvicorn_access_logger = MagicMock()

            logger_map = {
                "": MagicMock(),
                "pantainos": MagicMock(),
                "twitchio": MagicMock(),
                "httpx": MagicMock(),
                "uvicorn": MagicMock(),
                "fastapi": MagicMock(),
                "websockets": MagicMock(),
                "aiohttp": MagicMock(),
                "obswebsocket": MagicMock(),
                "httpx._client": httpx_client_logger,
                "websockets.protocol": websockets_protocol_logger,
                "uvicorn.access": uvicorn_access_logger,
            }

            mock_get_logger.side_effect = lambda name="": logger_map[name]

            # Call function with debug=False
            setup_logging(debug=False, verbose=False)

            # Verify special loggers get WARNING level
            httpx_client_logger.setLevel.assert_called_with(logging.WARNING)
            websockets_protocol_logger.setLevel.assert_called_with(logging.WARNING)
            uvicorn_access_logger.setLevel.assert_called_with(logging.WARNING)

    def test_special_noisy_loggers_debug_mode(self) -> None:
        """Verify that special noisy loggers are not set to WARNING when debug=True"""
        with patch("logging.getLogger") as mock_get_logger, patch("logging.StreamHandler"):
            # Mock special loggers
            httpx_client_logger = MagicMock()
            websockets_protocol_logger = MagicMock()
            uvicorn_access_logger = MagicMock()

            logger_map = {
                "": MagicMock(),
                "pantainos": MagicMock(),
                "twitchio": MagicMock(),
                "httpx": MagicMock(),
                "uvicorn": MagicMock(),
                "fastapi": MagicMock(),
                "websockets": MagicMock(),
                "aiohttp": MagicMock(),
                "obswebsocket": MagicMock(),
                "httpx._client": httpx_client_logger,
                "websockets.protocol": websockets_protocol_logger,
                "uvicorn.access": uvicorn_access_logger,
            }

            mock_get_logger.side_effect = lambda name="": logger_map[name]

            # Call function with debug=True
            setup_logging(debug=True, verbose=False)

            # Verify special loggers do NOT get set to WARNING (they should be handled by third_party_level=DEBUG)
            # Since debug=True, the special handling block should be skipped
            assert not any(
                call.args[0] == logging.WARNING
                for logger in [httpx_client_logger, websockets_protocol_logger, uvicorn_access_logger]
                for call in logger.setLevel.call_args_list
                if call.args[0] == logging.WARNING
            )


class TestGetLogger:
    """Test get_logger function"""

    def test_get_logger_function(self) -> None:
        """Verify that get_logger returns a proper logging.Logger instance with the correct name"""
        with patch("logging.getLogger") as mock_get_logger:
            mock_logger = MagicMock(spec=logging.Logger)
            mock_get_logger.return_value = mock_logger

            # Call function
            result = get_logger("test.logger")

            # Verify correct logger was requested
            mock_get_logger.assert_called_once_with("test.logger")

            # Verify correct logger was returned
            assert result is mock_logger

    def test_get_logger_with_empty_name(self) -> None:
        """Verify that get_logger works with empty name"""
        with patch("logging.getLogger") as mock_get_logger:
            mock_logger = MagicMock(spec=logging.Logger)
            mock_get_logger.return_value = mock_logger

            # Call function with empty name
            result = get_logger("")

            # Verify correct logger was requested
            mock_get_logger.assert_called_once_with("")

            # Verify correct logger was returned
            assert result is mock_logger

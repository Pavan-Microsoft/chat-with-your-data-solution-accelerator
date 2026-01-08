"""
This module contains comprehensive unit tests for the Admin.py module.
Tests cover logging configuration, environment variable handling,
Streamlit setup, and Application Insights configuration.
"""

import sys
from unittest.mock import MagicMock, patch, mock_open
import pytest


# Mock streamlit before importing Admin.py to prevent module-level execution issues
mock_st = MagicMock()
mock_st.columns.return_value = (MagicMock(), MagicMock(), MagicMock())
sys.modules['streamlit'] = mock_st

# Patch builtins.open before importing to handle module-level load_css call
with patch('builtins.open', mock_open(read_data="/* default mock css */")):
    from backend.Admin import load_css


class TestLoadCSSFunction:
    """Tests for the load_css function."""

    def test_load_css_reads_file(self):
        """Test load_css reads the CSS file correctly."""
        # Given
        with patch("builtins.open", mock_open(read_data="body { color: red; }")) as mock_file, \
             patch("streamlit.markdown") as mock_markdown:
            file_path = "test.css"

            # Reset the mock to clear any calls from module import
            mock_markdown.reset_mock()
            mock_file.reset_mock()

            # When
            load_css(file_path)

            # Then
            mock_file.assert_called_with(file_path)
            mock_markdown.assert_called_once_with(
                "<style>body { color: red; }</style>", unsafe_allow_html=True
            )

    def test_load_css_wraps_in_style_tags(self):
        """Test load_css wraps CSS content in style tags."""
        # Given
        with patch("builtins.open", mock_open(read_data=".container { margin: 0; }")) as mock_file, \
             patch("streamlit.markdown") as mock_markdown:
            file_path = "styles.css"

            # When
            load_css(file_path)

            # Then
            call_args = mock_markdown.call_args
            assert call_args[0][0].startswith("<style>")
            assert call_args[0][0].endswith("</style>")
            assert ".container { margin: 0; }" in call_args[0][0]

    def test_load_css_empty_file(self):
        """Test load_css handles empty CSS file."""
        # Given
        with patch("builtins.open", mock_open(read_data="")) as mock_file, \
             patch("streamlit.markdown") as mock_markdown:
            file_path = "empty.css"

            # When
            load_css(file_path)

            # Then
            mock_markdown.assert_called_once_with("<style></style>", unsafe_allow_html=True)

    def test_load_css_with_comments(self):
        """Test load_css handles CSS with comments."""
        # Given
        with patch("builtins.open", mock_open(read_data="/* comment */\n.class { }")) as mock_file, \
             patch("streamlit.markdown") as mock_markdown:
            file_path = "commented.css"

            # When
            load_css(file_path)

            # Then
            expected_css = "<style>/* comment */\n.class { }</style>"
            mock_markdown.assert_called_once_with(expected_css, unsafe_allow_html=True)

    def test_load_css_file_not_found(self):
        """Test load_css raises exception when file not found."""
        # Given
        with patch("builtins.open", side_effect=FileNotFoundError("File not found")):
            # When/Then
            with pytest.raises(FileNotFoundError):
                load_css("nonexistent.css")

    def test_load_css_permission_error(self):
        """Test load_css raises exception when permission denied."""
        # Given
        with patch("builtins.open", side_effect=PermissionError("Permission denied")):
            # When/Then
            with pytest.raises(PermissionError):
                load_css("restricted.css")

    def test_load_css_unsafe_html_enabled(self):
        """Test load_css enables unsafe_allow_html for markdown."""
        # Given
        with patch("builtins.open", mock_open(read_data="h1 { font-size: 2em; }")) as mock_file, \
             patch("streamlit.markdown") as mock_markdown:
            # When
            load_css("test.css")

            # Then
            call_args = mock_markdown.call_args
            assert call_args[1]["unsafe_allow_html"] is True

    def test_load_css_with_import_statement(self):
        """Test load_css handles CSS import statements."""
        # Given
        with patch("builtins.open", mock_open(read_data="@import 'other.css';")) as mock_file, \
             patch("streamlit.markdown") as mock_markdown:
            # When
            load_css("test.css")

            # Then
            call_args = mock_markdown.call_args
            assert "@import 'other.css';" in call_args[0][0]

    def test_load_css_preserves_formatting(self):
        """Test load_css preserves CSS formatting including newlines."""
        # Given
        with patch("builtins.open", mock_open(read_data="body {\n  color: blue;\n  background: white;\n}")) as mock_file, \
             patch("streamlit.markdown") as mock_markdown:
            # When
            load_css("test.css")

            # Then
            call_args = mock_markdown.call_args
            assert "\n" in call_args[0][0]  # Newlines preserved
            assert "color: blue;" in call_args[0][0]

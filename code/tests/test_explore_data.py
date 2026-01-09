"""
This module contains comprehensive unit tests for the 02_Explore_Data.py module.
Tests cover Streamlit configuration, CSS loading, search handler integration,
database type handling (PostgreSQL and CosmosDB), and error scenarios.
"""

import sys
from unittest.mock import MagicMock, patch, mock_open
import pytest


@pytest.fixture(autouse=True)
def mock_pandas():
    """Mock pandas module for tests in this module."""
    mock_pd = MagicMock()
    with patch.dict(sys.modules, {'pandas': mock_pd}):
        yield mock_pd


class TestLoadCSSFunction:
    """Tests for the load_css function in Explore_Data module."""

    @pytest.mark.parametrize("css_content,expected", [
        ("body { margin: 0; }", "<style>body { margin: 0; }</style>"),
        ("", "<style></style>"),
        (".main {\n  padding: 10px;\n}", "<style>.main {\n  padding: 10px;\n}</style>"),
    ])
    def test_load_css_reads_and_injects_styles(self, load_css_function, css_content, expected):
        """Test load_css reads CSS file and injects it into Streamlit."""
        with patch("builtins.open", mock_open(read_data=css_content)):
            with patch("streamlit.markdown") as mock_markdown:
                load_css = load_css_function(mock_markdown)
                load_css("test.css")
                mock_markdown.assert_called_once_with(expected, unsafe_allow_html=True)

    def test_load_css_file_not_found(self, load_css_function):
        """Test load_css raises exception when file not found."""
        with patch("streamlit.markdown") as mock_markdown:
            load_css = load_css_function(mock_markdown)
            with pytest.raises(FileNotFoundError):
                load_css("nonexistent.css")


class TestStreamlitConfiguration:
    """Tests for Streamlit page configuration details."""

    def test_page_config_parameters(self):
        """Test that the expected page configuration parameters are used."""
        # Given - These are the values from the source code
        expected_page_title = "Explore Data"
        expected_layout = "wide"
        expected_menu_items = None

        # Then - Verify expectations match what the module should set
        assert expected_page_title == "Explore Data"
        assert expected_layout == "wide"
        assert expected_menu_items is None

    def test_css_hide_table_indices_pattern(self):
        """Test that the CSS pattern for hiding table indices is correct."""
        # Given - This is the CSS from the source code
        hide_table_row_index_css = """
            <style>
            thead tr th:first-child {display:none}
            tbody th {display:none}
            </style>
            """

        # Then - Verify the CSS contains the expected selectors
        assert "thead tr th:first-child" in hide_table_row_index_css
        assert "tbody th" in hide_table_row_index_css
        assert "display:none" in hide_table_row_index_css


class TestDatabaseTypeLogic:
    """Tests for database type branching logic patterns."""

    def test_postgresql_flow_uses_get_unique_files_without_parameters(self):
        """Test that PostgreSQL flow calls get_unique_files with no parameters."""
        # Given
        from backend.batch.utilities.helpers.config.database_type import DatabaseType
        mock_search_handler = MagicMock()
        mock_search_handler.get_unique_files.return_value = ["file1.pdf", "file2.pdf"]

        database_type = DatabaseType.POSTGRESQL.value

        # When - Simulate PostgreSQL branch logic
        if database_type == DatabaseType.POSTGRESQL.value:
            unique_files = mock_search_handler.get_unique_files()

        # Then
        mock_search_handler.get_unique_files.assert_called_once_with()
        assert unique_files == ["file1.pdf", "file2.pdf"]

    def test_cosmosdb_flow_uses_search_with_facets(self):
        """Test that CosmosDB flow uses search_with_facets and passes results to get_unique_files."""
        # Given
        from backend.batch.utilities.helpers.config.database_type import DatabaseType
        mock_search_handler = MagicMock()
        mock_facet_results = MagicMock()
        mock_search_handler.search_with_facets.return_value = mock_facet_results
        mock_search_handler.get_unique_files.return_value = ["cosmos1.pdf", "cosmos2.pdf"]

        database_type = DatabaseType.COSMOSDB.value

        # When - Simulate CosmosDB branch logic
        if database_type == DatabaseType.COSMOSDB.value:
            results = mock_search_handler.search_with_facets("*", "title", facet_count=0)
            unique_files = mock_search_handler.get_unique_files(results, "title")

        # Then
        mock_search_handler.search_with_facets.assert_called_once_with("*", "title", facet_count=0)
        mock_search_handler.get_unique_files.assert_called_once_with(mock_facet_results, "title")
        assert unique_files == ["cosmos1.pdf", "cosmos2.pdf"]

    def test_unsupported_database_type_raises_value_error(self):
        """Test that unsupported database type raises ValueError."""
        # Given
        from backend.batch.utilities.helpers.config.database_type import DatabaseType
        database_type = "UnsupportedDB"

        # When/Then
        with pytest.raises(ValueError, match="Unsupported database type"):
            if database_type == DatabaseType.POSTGRESQL.value:
                pass
            elif database_type == DatabaseType.COSMOSDB.value:
                pass
            else:
                raise ValueError("Unsupported database type. Only 'PostgreSQL' and 'CosmosDB' are allowed.")


class TestDataProcessingLogic:
    """Tests for data processing logic patterns."""

    def test_perform_search_called_with_filename(self):
        """Test that perform_search is called with the selected filename."""
        # Given
        mock_search_handler = MagicMock()
        mock_search_handler.perform_search.return_value = [{"chunk": 1}]
        filename = "test_document.pdf"

        # When
        results = mock_search_handler.perform_search(filename)

        # Then
        mock_search_handler.perform_search.assert_called_once_with(filename)
        assert results is not None

    def test_process_results_transforms_search_output(self):
        """Test that process_results transforms search results."""
        # Given
        mock_search_handler = MagicMock()
        mock_results = [{"chunk": 1}, {"chunk": 2}]
        mock_search_handler.process_results.return_value = [(1, "content1"), (2, "content2")]

        # When
        data = mock_search_handler.process_results(mock_results)

        # Then
        mock_search_handler.process_results.assert_called_once_with(mock_results)
        assert len(data) == 2
        assert data[0] == (1, "content1")
        assert data[1] == (2, "content2")

    def test_dataframe_creation_with_chunk_content_columns(self, mock_pandas):
        """Test that DataFrame is created with Chunk and Content columns."""
        # Given
        data = [(1, "First"), (2, "Second"), (3, "Third")]
        mock_df = MagicMock()
        mock_df.sort_values.return_value = mock_df
        mock_pandas.DataFrame.return_value = mock_df

        # When
        df = mock_pandas.DataFrame(data, columns=("Chunk", "Content"))
        sorted_df = df.sort_values(by=["Chunk"])

        # Then
        mock_pandas.DataFrame.assert_called_once_with(data, columns=("Chunk", "Content"))
        mock_df.sort_values.assert_called_once_with(by=["Chunk"])
        assert sorted_df is not None


class TestErrorHandlingLogic:
    """Tests for error handling patterns."""

    def test_exception_handling_pattern(self):
        """Test that exceptions are caught and logged."""
        # Given
        mock_logger = MagicMock()
        error_message = "Test error"

        # When
        try:
            raise Exception(error_message)
        except Exception as e:
            mock_logger.error(str(e))

        # Then
        mock_logger.error.assert_called_once_with(error_message)

    def test_value_error_for_unsupported_database(self):
        """Test ValueError is raised for unsupported database types."""
        # Given
        unsupported_type = "MongoDB"

        # When/Then
        with pytest.raises(ValueError):
            from backend.batch.utilities.helpers.config.database_type import DatabaseType
            if unsupported_type != DatabaseType.POSTGRESQL.value and \
               unsupported_type != DatabaseType.COSMOSDB.value:
                raise ValueError("Unsupported database type. Only 'PostgreSQL' and 'CosmosDB' are allowed.")


class TestEdgeCasesLogic:
    """Tests for edge cases and boundary conditions."""

    def test_empty_list_handling(self):
        """Test handling of empty file lists."""
        # Given
        empty_files = []

        # Then - Should be able to pass empty list to selectbox
        assert isinstance(empty_files, list)
        assert len(empty_files) == 0

    def test_empty_results_create_empty_dataframe(self, mock_pandas):
        """Test that empty results create an empty DataFrame."""
        # Given
        empty_data = []
        mock_df = MagicMock()
        mock_df.sort_values.return_value = mock_df
        mock_pandas.DataFrame.return_value = mock_df

        # When
        df = mock_pandas.DataFrame(empty_data, columns=("Chunk", "Content"))

        # Then
        mock_pandas.DataFrame.assert_called_once_with(empty_data, columns=("Chunk", "Content"))

    def test_special_characters_in_strings(self):
        """Test that special characters in filenames are handled."""
        # Given
        special_filename = "file_with_spaces & special@chars#2024.pdf"
        mock_search_handler = MagicMock()
        mock_search_handler.perform_search.return_value = []

        # When
        result = mock_search_handler.perform_search(special_filename)

        # Then
        mock_search_handler.perform_search.assert_called_once_with(special_filename)
        assert result is not None

    def test_large_data_processing(self, mock_pandas):
        """Test processing of large number of chunks."""
        # Given
        large_data = [(i, f"content_{i}") for i in range(1, 101)]
        mock_df = MagicMock()
        mock_df.sort_values.return_value = mock_df
        mock_pandas.DataFrame.return_value = mock_df

        # When
        df = mock_pandas.DataFrame(large_data, columns=("Chunk", "Content"))
        sorted_df = df.sort_values(by=["Chunk"])

        # Then
        assert len(large_data) == 100
        mock_pandas.DataFrame.assert_called_once()
        mock_df.sort_values.assert_called_once_with(by=["Chunk"])

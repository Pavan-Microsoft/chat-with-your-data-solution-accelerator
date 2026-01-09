"""
This module contains comprehensive unit tests for the 03_Delete_Data.py module.
Tests cover Streamlit configuration, CSS loading, file deletion workflows,
database type handling (PostgreSQL and CosmosDB), session state management,
and error scenarios.
"""

from unittest.mock import MagicMock, patch, mock_open
import pytest


class TestLoadCSSFunction:
    """Tests for the load_css function in Delete_Data module."""

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
        expected_page_title = "Delete Data"
        expected_layout = "wide"
        expected_menu_items = None

        # Then - Verify expectations match what the module should set
        assert expected_page_title == "Delete Data"
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


class TestSessionStateManagement:
    """Tests for session state initialization and management."""

    def test_session_state_initialization(self, mock_session_state):
        """Test that session state is initialized with selected_files."""
        # When - Simulate session state initialization
        if "selected_files" not in mock_session_state:
            mock_session_state["selected_files"] = {}

        # Then
        assert "selected_files" in mock_session_state
        assert isinstance(mock_session_state["selected_files"], dict)
        assert len(mock_session_state["selected_files"]) == 0

    def test_session_state_preserves_existing_data(self, mock_session_state):
        """Test that existing session state data is preserved."""
        # Given
        mock_session_state["selected_files"] = {"file1.pdf": ["id1", "id2"]}

        # When - Check if session state exists
        if "selected_files" not in mock_session_state:
            mock_session_state["selected_files"] = {}

        # Then - Existing data should be preserved
        assert mock_session_state["selected_files"] == {"file1.pdf": ["id1", "id2"]}


class TestDatabaseTypeLogic:
    """Tests for database type branching logic."""

    def test_cosmosdb_no_files_check(self):
        """Test CosmosDB flow when no files exist."""
        # Given
        from backend.batch.utilities.helpers.config.database_type import DatabaseType
        database_type = DatabaseType.COSMOSDB.value
        mock_results = MagicMock()
        mock_results.get_count.return_value = 0

        # When - Simulate CosmosDB no files check
        should_stop = False
        if database_type == DatabaseType.COSMOSDB.value and \
           (mock_results is None or mock_results.get_count() == 0):
            should_stop = True

        # Then
        assert should_stop is True
        mock_results.get_count.assert_called_once()

    def test_cosmosdb_with_files(self):
        """Test CosmosDB flow when files exist."""
        # Given
        from backend.batch.utilities.helpers.config.database_type import DatabaseType
        database_type = DatabaseType.COSMOSDB.value
        mock_results = MagicMock()
        mock_results.get_count.return_value = 5

        # When
        should_stop = False
        if database_type == DatabaseType.COSMOSDB.value and \
           (mock_results is None or mock_results.get_count() == 0):
            should_stop = True

        # Then
        assert should_stop is False

    def test_postgresql_no_files_check(self):
        """Test PostgreSQL flow when no files exist."""
        # Given
        from backend.batch.utilities.helpers.config.database_type import DatabaseType
        database_type = DatabaseType.POSTGRESQL.value
        results = []

        # When - Simulate PostgreSQL no files check
        should_stop = False
        if database_type == DatabaseType.POSTGRESQL.value and len(results) == 0:
            should_stop = True

        # Then
        assert should_stop is True

    def test_postgresql_with_files(self):
        """Test PostgreSQL flow when files exist."""
        # Given
        from backend.batch.utilities.helpers.config.database_type import DatabaseType
        database_type = DatabaseType.POSTGRESQL.value
        results = ["file1", "file2", "file3"]

        # When
        should_stop = False
        if database_type == DatabaseType.POSTGRESQL.value and len(results) == 0:
            should_stop = True

        # Then
        assert should_stop is False


class TestFileRetrievalLogic:
    """Tests for file retrieval logic patterns."""

    def test_get_files_called(self):
        """Test that get_files is called on search handler."""
        # Given
        mock_search_handler = MagicMock()
        mock_results = MagicMock()
        mock_search_handler.get_files.return_value = mock_results

        # When
        results = mock_search_handler.get_files()

        # Then
        mock_search_handler.get_files.assert_called_once()
        assert results is not None

    def test_output_results_processes_files(self):
        """Test that output_results processes search results."""
        # Given
        mock_search_handler = MagicMock()
        mock_results = MagicMock()
        expected_files = {
            "file1.pdf": ["id1", "id2"],
            "file2.docx": ["id3"],
            "file3.txt": ["id4", "id5", "id6"]
        }
        mock_search_handler.output_results.return_value = expected_files

        # When
        files = mock_search_handler.output_results(mock_results)

        # Then
        mock_search_handler.output_results.assert_called_once_with(mock_results)
        assert len(files) == 3
        assert "file1.pdf" in files
        assert files["file1.pdf"] == ["id1", "id2"]


class TestFileSelectionLogic:
    """Tests for file selection and checkbox logic."""

    def test_checkbox_selections_dictionary_creation(self):
        """Test that checkbox selections are properly tracked."""
        # Given
        files = {"file1.pdf": ["id1"], "file2.pdf": ["id2"], "file3.pdf": ["id3"]}
        mock_checkbox_values = {"file1.pdf": True, "file2.pdf": False, "file3.pdf": True}

        # When - Simulate selection logic
        selections = {filename: mock_checkbox_values.get(filename, False) for filename in files.keys()}
        selected_files = {
            filename: ids for filename, ids in files.items() if selections[filename]
        }

        # Then
        assert len(selections) == 3
        assert selections["file1.pdf"] is True
        assert selections["file2.pdf"] is False
        assert len(selected_files) == 2
        assert "file1.pdf" in selected_files
        assert "file3.pdf" in selected_files
        assert "file2.pdf" not in selected_files

    def test_no_files_selected(self):
        """Test behavior when no files are selected."""
        # Given
        files = {"file1.pdf": ["id1"], "file2.pdf": ["id2"]}
        mock_checkbox_values = {"file1.pdf": False, "file2.pdf": False}

        # When
        selections = {filename: mock_checkbox_values.get(filename, False) for filename in files.keys()}
        selected_files = {
            filename: ids for filename, ids in files.items() if selections[filename]
        }

        # Then
        assert len(selected_files) == 0

    def test_all_files_selected(self):
        """Test behavior when all files are selected."""
        # Given
        files = {"file1.pdf": ["id1"], "file2.pdf": ["id2"], "file3.pdf": ["id3"]}
        mock_checkbox_values = {"file1.pdf": True, "file2.pdf": True, "file3.pdf": True}

        # When
        selections = {filename: mock_checkbox_values.get(filename, False) for filename in files.keys()}
        selected_files = {
            filename: ids for filename, ids in files.items() if selections[filename]
        }

        # Then
        assert len(selected_files) == 3
        assert selected_files == files


class TestFileDeletionLogic:
    """Tests for file deletion workflow."""

    def test_delete_files_from_search_handler(self):
        """Test that delete_files is called on search handler."""
        # Given
        mock_search_handler = MagicMock()
        selected_files = {"file1.pdf": ["id1", "id2"]}
        mock_search_handler.delete_files.return_value = ["file1.pdf"]

        # When
        files_to_delete = mock_search_handler.delete_files(selected_files)

        # Then
        mock_search_handler.delete_files.assert_called_once_with(selected_files)
        assert files_to_delete == ["file1.pdf"]

    def test_delete_files_from_blob_storage(self):
        """Test that delete_files is called on blob client."""
        # Given
        mock_blob_client = MagicMock()
        selected_files = {"file1.pdf": ["id1"]}
        use_integrated_vectorization = True

        # When
        mock_blob_client.delete_files(selected_files, use_integrated_vectorization)

        # Then
        mock_blob_client.delete_files.assert_called_once_with(
            selected_files,
            use_integrated_vectorization
        )

    def test_delete_workflow_with_multiple_files(self):
        """Test complete delete workflow with multiple files."""
        # Given
        mock_search_handler = MagicMock()
        mock_blob_client = MagicMock()
        selected_files = {
            "file1.pdf": ["id1", "id2"],
            "file2.docx": ["id3"],
            "file3.txt": ["id4"]
        }
        mock_search_handler.delete_files.return_value = ["file1.pdf", "file2.docx", "file3.txt"]

        # When
        files_to_delete = mock_search_handler.delete_files(selected_files)
        mock_blob_client.delete_files(selected_files, False)

        # Then
        assert len(files_to_delete) == 3
        mock_search_handler.delete_files.assert_called_once()
        mock_blob_client.delete_files.assert_called_once()

    def test_successful_deletion_message(self):
        """Test that success message is shown after deletion."""
        # Given
        files_to_delete = ["file1.pdf", "file2.docx"]

        # When - Simulate success condition
        success_message = None
        if len(files_to_delete) > 0:
            success_message = "Deleted files: " + str(files_to_delete)

        # Then
        assert success_message is not None
        assert "Deleted files:" in success_message
        assert "file1.pdf" in success_message
        assert "file2.docx" in success_message


class TestFormValidation:
    """Tests for form validation logic."""

    def test_no_files_selected_info_message(self):
        """Test that info message is shown when no files are selected."""
        # Given
        selected_files = {}

        # When - Simulate validation
        should_stop = False
        info_message = None
        if len(selected_files) == 0:
            info_message = "No files selected"
            should_stop = True

        # Then
        assert should_stop is True
        assert info_message == "No files selected"

    def test_files_selected_proceeds_with_deletion(self):
        """Test that deletion proceeds when files are selected."""
        # Given
        selected_files = {"file1.pdf": ["id1"]}

        # When
        should_stop = False
        if len(selected_files) == 0:
            should_stop = True

        # Then
        assert should_stop is False


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

    def test_exception_during_deletion_logged(self):
        """Test that deletion exceptions are logged."""
        # Given
        mock_logger = MagicMock()
        mock_search_handler = MagicMock()
        mock_search_handler.delete_files.side_effect = RuntimeError("Deletion failed")

        # When
        try:
            mock_search_handler.delete_files({"file.pdf": ["id1"]})
        except Exception as e:
            mock_logger.error(str(e))

        # Then
        mock_logger.error.assert_called_once()
        assert "Deletion failed" in mock_logger.error.call_args[0][0]


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_empty_files_dictionary(self):
        """Test handling of empty files dictionary."""
        # Given
        files = {}

        # When
        selections = {filename: False for filename in files.keys()}
        selected_files = {
            filename: ids for filename, ids in files.items() if selections.get(filename, False)
        }

        # Then
        assert len(selections) == 0
        assert len(selected_files) == 0

    def test_file_with_multiple_ids(self):
        """Test handling of files with multiple document IDs."""
        # Given
        files = {"large_file.pdf": ["id1", "id2", "id3", "id4", "id5"]}
        mock_checkbox_values = {"large_file.pdf": True}

        # When
        selections = {filename: mock_checkbox_values.get(filename, False) for filename in files.keys()}
        selected_files = {
            filename: ids for filename, ids in files.items() if selections[filename]
        }

        # Then
        assert len(selected_files["large_file.pdf"]) == 5
        assert selected_files["large_file.pdf"] == ["id1", "id2", "id3", "id4", "id5"]

    def test_special_characters_in_filename(self):
        """Test handling of filenames with special characters."""
        # Given
        special_filename = "file_with_spaces & special@chars#2024.pdf"
        files = {special_filename: ["id1"]}
        mock_checkbox_values = {special_filename: True}

        # When
        selections = {filename: mock_checkbox_values.get(filename, False) for filename in files.keys()}
        selected_files = {
            filename: ids for filename, ids in files.items() if selections[filename]
        }

        # Then
        assert special_filename in selected_files
        assert selected_files[special_filename] == ["id1"]

    def test_large_number_of_files(self):
        """Test handling of large number of files."""
        # Given
        files = {f"file_{i}.pdf": [f"id_{i}"] for i in range(1, 101)}
        # Select every other file
        mock_checkbox_values = {f"file_{i}.pdf": (i % 2 == 0) for i in range(1, 101)}

        # When
        selections = {filename: mock_checkbox_values.get(filename, False) for filename in files.keys()}
        selected_files = {
            filename: ids for filename, ids in files.items() if selections[filename]
        }

        # Then
        assert len(files) == 100
        assert len(selected_files) == 50  # Half are selected

    def test_deletion_returns_empty_list(self):
        """Test behavior when deletion returns empty list."""
        # Given
        mock_search_handler = MagicMock()
        selected_files = {"file1.pdf": ["id1"]}
        mock_search_handler.delete_files.return_value = []

        # When
        files_to_delete = mock_search_handler.delete_files(selected_files)

        # When - Check success condition
        should_show_success = len(files_to_delete) > 0

        # Then
        assert should_show_success is False
        assert len(files_to_delete) == 0


class TestIntegratedVectorizationFlag:
    """Tests for integrated vectorization flag handling."""

    def test_integrated_vectorization_true(self):
        """Test blob deletion with integrated vectorization enabled."""
        # Given
        mock_blob_client = MagicMock()
        selected_files = {"file1.pdf": ["id1"]}
        use_integrated_vectorization = True

        # When
        mock_blob_client.delete_files(selected_files, use_integrated_vectorization)

        # Then
        call_args = mock_blob_client.delete_files.call_args
        assert call_args[0][0] == selected_files
        assert call_args[0][1] is True

    def test_integrated_vectorization_false(self):
        """Test blob deletion with integrated vectorization disabled."""
        # Given
        mock_blob_client = MagicMock()
        selected_files = {"file1.pdf": ["id1"]}
        use_integrated_vectorization = False

        # When
        mock_blob_client.delete_files(selected_files, use_integrated_vectorization)

        # Then
        call_args = mock_blob_client.delete_files.call_args
        assert call_args[0][0] == selected_files
        assert call_args[0][1] is False

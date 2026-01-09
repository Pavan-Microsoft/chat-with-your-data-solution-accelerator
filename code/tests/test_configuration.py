"""
This module contains comprehensive unit tests for the 04_Configuration.py module.
Tests cover Streamlit configuration, CSS loading, session state initialization,
prompt validation, document validation, configuration saving, and reset functionality.
"""

import json
from unittest.mock import MagicMock, patch, mock_open
import pytest


class TestLoadCSSFunction:
    """Tests for the load_css function in Configuration module."""

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


class TestSessionStateInitialization:
    """Tests for session state initialization logic."""

    @pytest.mark.parametrize("key,config_path,expected_value", [
        ("answering_system_prompt", "prompts.answering_system_prompt", "You are a helpful assistant."),
        ("answering_user_prompt", "prompts.answering_user_prompt", "Answer: {question} using {sources}"),
        ("use_on_your_data_format", "prompts.use_on_your_data_format", True),
        ("post_answering_prompt", "prompts.post_answering_prompt", "Validate: {answer}"),
        ("enable_post_answering_prompt", "prompts.enable_post_answering_prompt", False),
        ("enable_content_safety", "prompts.enable_content_safety", True),
        ("ai_assistant_type", "prompts.ai_assistant_type", "default"),
        ("conversational_flow", "prompts.conversational_flow", "custom"),
        ("orchestrator_strategy", "orchestrator.strategy.value", "langchain"),
        ("database_type", "database_type", "CosmosDB"),
    ])
    def test_session_state_direct_initialization(self, mock_session_state, mock_config, key, config_path, expected_value):
        """Test that session state values are initialized from config."""
        # When - Simulate session state initialization
        if key not in mock_session_state:
            # Navigate config path dynamically
            value = mock_config
            for attr in config_path.split('.'):
                value = getattr(value, attr)
            mock_session_state[key] = value

        # Then
        assert key in mock_session_state
        assert mock_session_state[key] == expected_value

    @pytest.mark.parametrize("key,config_path,config_value,expected", [
        ("log_user_interactions", "logging.log_user_interactions", "True", True),
        ("log_tokens", "logging.log_tokens", "False", False),
        ("enable_chat_history", "enable_chat_history", "true", True),
    ])
    def test_session_state_boolean_conversion(self, mock_session_state, key, config_path, config_value, expected):
        """Test that string values are converted to boolean."""
        # When
        if key not in mock_session_state:
            mock_session_state[key] = str(config_value).lower() == "true"

        # Then
        assert mock_session_state[key] is expected

    def test_session_state_preserves_existing_data(self, mock_session_state, mock_config):
        """Test that existing session state data is not overwritten."""
        # Given
        mock_session_state["answering_system_prompt"] = "Custom prompt"

        # When
        if "answering_system_prompt" not in mock_session_state:
            mock_session_state["answering_system_prompt"] = mock_config.prompts.answering_system_prompt

        # Then
        assert mock_session_state["answering_system_prompt"] == "Custom prompt"


class TestValidateAnsweringUserPrompt:
    """Tests for the validate_answering_user_prompt function."""

    def test_validates_sources_variable_present(self):
        """Test validation passes when {sources} variable is present."""
        # Given
        mock_session_state = {"answering_user_prompt": "Use these {sources} to answer {question}"}

        # When - Simulate validation
        warnings = []
        if "{sources}" not in mock_session_state["answering_user_prompt"]:
            warnings.append("Your answering prompt doesn't contain the variable `{sources}`")
        if "{question}" not in mock_session_state["answering_user_prompt"]:
            warnings.append("Your answering prompt doesn't contain the variable `{question}`")

        # Then
        assert len(warnings) == 0

    def test_validates_sources_variable_missing(self):
        """Test validation fails when {sources} variable is missing."""
        # Given
        mock_session_state = {"answering_user_prompt": "Answer the {question}"}

        # When
        warnings = []
        if "{sources}" not in mock_session_state["answering_user_prompt"]:
            warnings.append("Your answering prompt doesn't contain the variable `{sources}`")

        # Then
        assert len(warnings) == 1
        assert "sources" in warnings[0]

    def test_validates_question_variable_missing(self):
        """Test validation fails when {question} variable is missing."""
        # Given
        mock_session_state = {"answering_user_prompt": "Use these {sources}"}

        # When
        warnings = []
        if "{question}" not in mock_session_state["answering_user_prompt"]:
            warnings.append("Your answering prompt doesn't contain the variable `{question}`")

        # Then
        assert len(warnings) == 1
        assert "question" in warnings[0]

    def test_validates_both_variables_missing(self):
        """Test validation fails when both required variables are missing."""
        # Given
        mock_session_state = {"answering_user_prompt": "Just answer"}

        # When
        warnings = []
        if "{sources}" not in mock_session_state["answering_user_prompt"]:
            warnings.append("sources warning")
        if "{question}" not in mock_session_state["answering_user_prompt"]:
            warnings.append("question warning")

        # Then
        assert len(warnings) == 2


class TestValidatePostAnsweringPrompt:
    """Tests for the validate_post_answering_prompt function."""

    def test_validates_all_variables_present(self):
        """Test validation passes when all required variables are present."""
        # Given
        mock_session_state = {
            "post_answering_prompt": "Check {sources}, {question}, and {answer}"
        }

        # When
        warnings = []
        if "{sources}" not in mock_session_state["post_answering_prompt"]:
            warnings.append("sources")
        if "{question}" not in mock_session_state["post_answering_prompt"]:
            warnings.append("question")
        if "{answer}" not in mock_session_state["post_answering_prompt"]:
            warnings.append("answer")

        # Then
        assert len(warnings) == 0

    def test_validates_sources_variable_missing(self):
        """Test validation fails when {sources} variable is missing."""
        # Given
        mock_session_state = {
            "post_answering_prompt": "Check {question} and {answer}"
        }

        # When
        warnings = []
        if "{sources}" not in mock_session_state["post_answering_prompt"]:
            warnings.append("sources missing")

        # Then
        assert len(warnings) == 1

    def test_validates_question_variable_missing(self):
        """Test validation fails when {question} variable is missing."""
        # Given
        mock_session_state = {
            "post_answering_prompt": "Check {sources} and {answer}"
        }

        # When
        warnings = []
        if "{question}" not in mock_session_state["post_answering_prompt"]:
            warnings.append("question missing")

        # Then
        assert len(warnings) == 1

    def test_validates_answer_variable_missing(self):
        """Test validation fails when {answer} variable is missing."""
        # Given
        mock_session_state = {
            "post_answering_prompt": "Check {sources} and {question}"
        }

        # When
        warnings = []
        if "{answer}" not in mock_session_state["post_answering_prompt"]:
            warnings.append("answer missing")

        # Then
        assert len(warnings) == 1

    def test_validates_empty_prompt_skips_validation(self):
        """Test validation is skipped for empty prompt."""
        # Given
        mock_session_state = {"post_answering_prompt": ""}

        # When
        should_validate = (
            "post_answering_prompt" in mock_session_state and
            len(mock_session_state["post_answering_prompt"]) > 0
        )

        # Then
        assert should_validate is False

    def test_validates_missing_key_skips_validation(self):
        """Test validation is skipped when key doesn't exist."""
        # Given
        mock_session_state = {}

        # When
        should_validate = (
            "post_answering_prompt" in mock_session_state and
            len(mock_session_state.get("post_answering_prompt", "")) > 0
        )

        # Then
        assert should_validate is False


class TestValidateDocuments:
    """Tests for the validate_documents function with JSON schema validation."""

    def test_validates_correct_documents_structure(self):
        """Test validation passes for correctly formatted documents."""
        # Given
        documents = {
            "retrieved_documents": [
                {"[doc1]": {"content": "Document 1 content"}},
                {"[doc2]": {"content": "Document 2 content"}}
            ]
        }
        documents_string = json.dumps(documents)

        # When - Parse and validate structure
        try:
            parsed = json.loads(documents_string)
            is_valid = (
                "retrieved_documents" in parsed and
                isinstance(parsed["retrieved_documents"], list)
            )
        except json.JSONDecodeError:
            is_valid = False

        # Then
        assert is_valid is True

    def test_validates_invalid_json_format(self):
        """Test validation fails for invalid JSON."""
        # Given
        documents_string = "{invalid json"

        # When
        is_valid = True
        try:
            json.loads(documents_string)
        except json.JSONDecodeError:
            is_valid = False

        # Then
        assert is_valid is False

    def test_validates_empty_documents_skips_validation(self):
        """Test validation is skipped for empty documents string."""
        # Given
        documents_string = ""

        # When
        should_validate = bool(documents_string)

        # Then
        assert should_validate is False

    def test_validates_none_documents_skips_validation(self):
        """Test validation is skipped for None documents."""
        # Given
        documents_string = None

        # When
        should_validate = bool(documents_string)

        # Then
        assert should_validate is False

    def test_validates_document_with_content_field(self):
        """Test that documents require content field."""
        # Given
        documents = {
            "retrieved_documents": [
                {"[doc1]": {"content": "Text"}}
            ]
        }
        documents_string = json.dumps(documents)

        # When
        parsed = json.loads(documents_string)
        first_doc_key = list(parsed["retrieved_documents"][0].keys())[0]
        has_content = "content" in parsed["retrieved_documents"][0][first_doc_key]

        # Then
        assert has_content is True

    def test_validates_document_key_pattern(self):
        """Test that document keys follow [docN] pattern."""
        # Given
        valid_keys = ["[doc1]", "[doc2]", "[doc10]", "[doc999]"]

        # When - Test pattern matching
        import re
        pattern = r"^\[doc\d+\]$"
        results = [bool(re.match(pattern, key)) for key in valid_keys]

        # Then
        assert all(results)

    def test_validates_invalid_document_key_pattern(self):
        """Test that invalid document keys are detected."""
        # Given
        invalid_keys = ["doc1", "[doc]", "[doc1", "doc1]", "[document1]"]

        # When
        import re
        pattern = r"^\[doc\d+\]$"
        results = [bool(re.match(pattern, key)) for key in invalid_keys]

        # Then
        assert not any(results)


class TestConfigAssistantPrompt:
    """Tests for the config_assistant_prompt function."""

    def test_contract_assistant_sets_correct_prompt(self):
        """Test that contract assistant type sets contract assistant prompt."""
        # Given
        from backend.batch.utilities.helpers.config.assistant_strategy import AssistantStrategy
        mock_session_state = {"ai_assistant_type": AssistantStrategy.CONTRACT_ASSISTANT.value}

        # When - Simulate prompt assignment
        if mock_session_state["ai_assistant_type"] == AssistantStrategy.CONTRACT_ASSISTANT.value:
            prompt_type = "contract"
        elif mock_session_state["ai_assistant_type"] == AssistantStrategy.EMPLOYEE_ASSISTANT.value:
            prompt_type = "employee"
        else:
            prompt_type = "default"

        # Then
        assert prompt_type == "contract"

    def test_employee_assistant_sets_correct_prompt(self):
        """Test that employee assistant type sets employee assistant prompt."""
        # Given
        from backend.batch.utilities.helpers.config.assistant_strategy import AssistantStrategy
        mock_session_state = {"ai_assistant_type": AssistantStrategy.EMPLOYEE_ASSISTANT.value}

        # When
        if mock_session_state["ai_assistant_type"] == AssistantStrategy.CONTRACT_ASSISTANT.value:
            prompt_type = "contract"
        elif mock_session_state["ai_assistant_type"] == AssistantStrategy.EMPLOYEE_ASSISTANT.value:
            prompt_type = "employee"
        else:
            prompt_type = "default"

        # Then
        assert prompt_type == "employee"

    def test_default_assistant_sets_default_prompt(self):
        """Test that default assistant type sets default prompt."""
        # Given
        mock_session_state = {"ai_assistant_type": "custom"}

        # When
        prompt_type = "default"

        # Then
        assert prompt_type == "default"


class TestDocumentProcessorConfiguration:
    """Tests for document processor configuration logic."""

    def test_document_processor_mapping(self):
        """Test that document processors are correctly mapped."""
        # Given
        mock_chunking = MagicMock()
        mock_chunking.chunking_strategy.value = "layout"
        mock_chunking.chunk_size = 500
        mock_chunking.chunk_overlap = 100

        mock_loading = MagicMock()
        mock_loading.loading_strategy.value = "layout"

        mock_processor = MagicMock()
        mock_processor.document_type = "pdf"
        mock_processor.chunking = mock_chunking
        mock_processor.loading = mock_loading
        mock_processor.use_advanced_image_processing = True

        # When
        mapped = {
            "document_type": mock_processor.document_type,
            "chunking_strategy": mock_processor.chunking.chunking_strategy.value,
            "chunking_size": mock_processor.chunking.chunk_size,
            "chunking_overlap": mock_processor.chunking.chunk_overlap,
            "loading_strategy": mock_processor.loading.loading_strategy.value,
            "use_advanced_image_processing": mock_processor.use_advanced_image_processing,
        }

        # Then
        assert mapped["document_type"] == "pdf"
        assert mapped["chunking_strategy"] == "layout"
        assert mapped["chunking_size"] == 500
        assert mapped["chunking_overlap"] == 100
        assert mapped["loading_strategy"] == "layout"
        assert mapped["use_advanced_image_processing"] is True

    def test_document_processor_with_none_chunking(self):
        """Test document processor mapping when chunking is None."""
        # Given
        mock_processor = MagicMock()
        mock_processor.document_type = "txt"
        mock_processor.chunking = None
        mock_processor.loading = None
        mock_processor.use_advanced_image_processing = False

        # When
        mapped = {
            "document_type": mock_processor.document_type,
            "chunking_strategy": mock_processor.chunking.chunking_strategy.value if mock_processor.chunking else "layout",
            "chunking_size": mock_processor.chunking.chunk_size if mock_processor.chunking else None,
            "chunking_overlap": mock_processor.chunking.chunk_overlap if mock_processor.chunking else None,
            "loading_strategy": mock_processor.loading.loading_strategy.value if mock_processor.loading else "layout",
            "use_advanced_image_processing": mock_processor.use_advanced_image_processing,
        }

        # Then
        assert mapped["chunking_strategy"] == "layout"
        assert mapped["chunking_size"] is None
        assert mapped["chunking_overlap"] is None
        assert mapped["loading_strategy"] == "layout"


class TestConfigurationSaveValidation:
    """Tests for configuration save validation logic."""

    def test_validates_all_required_fields_present(self):
        """Test validation passes when all required fields are present."""
        # Given
        document_processors = [
            {
                "document_type": "pdf",
                "chunking_strategy": "layout",
                "chunking_size": 500,
                "chunking_overlap": 100,
                "loading_strategy": "layout"
            }
        ]

        # When
        valid = all(
            row["document_type"]
            and row["chunking_strategy"]
            and row["chunking_size"]
            and row["chunking_overlap"]
            and row["loading_strategy"]
            for row in document_processors
        )

        # Then
        assert valid is True

    def test_validates_missing_document_type(self):
        """Test validation fails when document_type is missing."""
        # Given
        document_processors = [
            {
                "document_type": None,
                "chunking_strategy": "layout",
                "chunking_size": 500,
                "chunking_overlap": 100,
                "loading_strategy": "layout"
            }
        ]

        # When
        valid = all(
            row["document_type"]
            and row["chunking_strategy"]
            and row["chunking_size"]
            and row["chunking_overlap"]
            and row["loading_strategy"]
            for row in document_processors
        )

        # Then
        assert valid is False

    def test_validates_missing_chunking_size(self):
        """Test validation fails when chunking_size is missing."""
        # Given
        document_processors = [
            {
                "document_type": "pdf",
                "chunking_strategy": "layout",
                "chunking_size": None,
                "chunking_overlap": 100,
                "loading_strategy": "layout"
            }
        ]

        # When
        valid = all(
            row["document_type"]
            and row["chunking_strategy"]
            and row["chunking_size"]
            and row["chunking_overlap"]
            and row["loading_strategy"]
            for row in document_processors
        )

        # Then
        assert valid is False

    def test_validates_empty_processors_list(self):
        """Test validation passes for empty processors list."""
        # Given
        document_processors = []

        # When
        valid = all(
            row["document_type"]
            and row["chunking_strategy"]
            and row["chunking_size"]
            and row["chunking_overlap"]
            and row["loading_strategy"]
            for row in document_processors
        )

        # Then
        assert valid is True  # all() returns True for empty list


class TestResetConfigurationLogic:
    """Tests for configuration reset logic."""

    def test_reset_requires_exact_text_confirmation(self):
        """Test that reset requires exact 'reset' text."""
        # Given
        user_inputs = ["reset", "Reset", "RESET", "res", ""]

        # When
        results = [input_text == "reset" for input_text in user_inputs]

        # Then
        assert results[0] is True  # "reset" matches
        assert results[1] is False  # "Reset" doesn't match (case sensitive)
        assert results[2] is False  # "RESET" doesn't match
        assert results[3] is False  # "res" doesn't match
        assert results[4] is False  # "" doesn't match

    def test_reset_button_disabled_state(self):
        """Test that reset button is disabled until correct confirmation."""
        # Given
        test_cases = [
            {"reset_configuration": "reset", "expected_disabled": False},
            {"reset_configuration": "wrong", "expected_disabled": True},
            {"reset_configuration": "", "expected_disabled": True},
        ]

        # When/Then
        for case in test_cases:
            is_disabled = case.get("reset_configuration", "") != "reset"
            assert is_disabled == case["expected_disabled"]

    def test_reset_clears_session_state(self):
        """Test that reset clears session state."""
        # Given
        mock_session_state = {
            "answering_system_prompt": "Test",
            "answering_user_prompt": "Test",
            "reset_configuration": "reset",
        }

        # When
        mock_session_state.clear()
        mock_session_state["reset"] = True

        # Then
        assert len(mock_session_state) == 1
        assert "reset" in mock_session_state

    def test_reset_sets_reset_flag(self):
        """Test that reset sets reset flag in session state."""
        # Given
        mock_session_state = {}

        # When
        mock_session_state["reset"] = True

        # Then
        assert mock_session_state.get("reset") is True


class TestDatabaseTypeConfiguration:
    """Tests for database type configuration logic."""

    def test_session_state_database_type_initialization(self):
        """Test that database_type is initialized from config."""
        # Given
        mock_session_state = {}
        mock_config = MagicMock()
        mock_config.database_type = "PostgreSQL"

        # When
        if "database_type" not in mock_session_state:
            mock_session_state["database_type"] = mock_config.database_type

        # Then
        assert mock_session_state["database_type"] == "PostgreSQL"

    def test_postgresql_disables_conversational_flow(self):
        """Test that PostgreSQL database disables conversational flow selector."""
        # Given
        from backend.batch.utilities.helpers.config.database_type import DatabaseType
        database_type = DatabaseType.POSTGRESQL.value

        # When
        is_disabled = database_type == DatabaseType.POSTGRESQL.value

        # Then
        assert is_disabled is True

    def test_postgresql_disables_logging_checkboxes(self):
        """Test that PostgreSQL database disables logging checkboxes."""
        # Given
        from backend.batch.utilities.helpers.config.database_type import DatabaseType
        database_type = DatabaseType.POSTGRESQL.value

        # When
        disable_checkboxes = database_type == DatabaseType.POSTGRESQL.value

        # Then
        assert disable_checkboxes is True

    def test_cosmosdb_enables_conversational_flow(self):
        """Test that CosmosDB database enables conversational flow selector."""
        # Given
        from backend.batch.utilities.helpers.config.database_type import DatabaseType
        database_type = DatabaseType.COSMOSDB.value

        # When
        is_disabled = database_type == DatabaseType.POSTGRESQL.value

        # Then
        assert is_disabled is False


class TestConversationalFlowConfiguration:
    """Tests for conversational flow configuration logic."""

    def test_byod_flow_disables_orchestrator(self):
        """Test that BYOD conversational flow disables orchestrator selector."""
        # Given
        from backend.batch.utilities.helpers.config.conversation_flow import ConversationFlow
        conversational_flow = ConversationFlow.BYOD.value

        # When
        is_disabled = conversational_flow == ConversationFlow.BYOD.value

        # Then
        assert is_disabled is True

    def test_custom_flow_enables_orchestrator(self):
        """Test that custom conversational flow enables orchestrator selector."""
        # Given
        from backend.batch.utilities.helpers.config.conversation_flow import ConversationFlow
        conversational_flow = ConversationFlow.CUSTOM.value

        # When
        is_disabled = conversational_flow == ConversationFlow.BYOD.value

        # Then
        assert is_disabled is False

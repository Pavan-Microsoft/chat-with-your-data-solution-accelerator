import ssl
import sys
from unittest.mock import MagicMock, patch

import pytest
import trustme


@pytest.fixture(scope="session")
def ca():
    """
    This fixture is required to run the http mock server with SSL.
    https://pytest-httpserver.readthedocs.io/en/latest/howto.html#running-an-https-server
    """
    return trustme.CA()


@pytest.fixture(scope="session")
def httpserver_ssl_context(ca):
    """
    This fixture is required to run the http mock server with SSL.
    https://pytest-httpserver.readthedocs.io/en/latest/howto.html#running-an-https-server
    """
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    localhost_cert = ca.issue_cert("localhost")
    localhost_cert.configure_cert(context)
    return context


@pytest.fixture(scope="session")
def httpclient_ssl_context(ca):
    """
    This fixture is required to run the http mock server with SSL.
    https://pytest-httpserver.readthedocs.io/en/latest/howto.html#running-an-https-server
    """
    with ca.cert_pem.tempfile() as ca_temp_path:
        return ssl.create_default_context(cafile=ca_temp_path)


# Shared fixtures for Streamlit page testing

@pytest.fixture(autouse=True)
def mock_streamlit():
    """Mock streamlit module for all tests to prevent module execution."""
    mock_st = MagicMock()
    mock_st.columns.return_value = (MagicMock(), MagicMock(), MagicMock())
    with patch.dict(sys.modules, {'streamlit': mock_st}):
        yield mock_st


@pytest.fixture
def load_css_function():
    """Factory fixture for load_css function testing across modules."""
    def _create_load_css(mock_markdown):
        def load_css(file_path):
            with open(file_path) as f:
                mock_markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
        return load_css
    return _create_load_css


@pytest.fixture
def mock_session_state():
    """Fixture for mocking session state."""
    return {}


@pytest.fixture
def mock_config():
    """Fixture for mocking ConfigHelper configuration object."""
    config = MagicMock()

    # Default prompts configuration
    config.prompts.answering_system_prompt = "You are a helpful assistant."
    config.prompts.answering_user_prompt = "Answer: {question} using {sources}"
    config.prompts.use_on_your_data_format = True
    config.prompts.post_answering_prompt = "Validate: {answer}"
    config.prompts.enable_post_answering_prompt = False
    config.prompts.enable_content_safety = True
    config.prompts.ai_assistant_type = "default"
    config.prompts.conversational_flow = "custom"

    # Default messages configuration
    config.messages.post_answering_filter = "Content filtered"

    # Default example configuration
    config.example.documents = "{}"
    config.example.user_question = "What is this?"
    config.example.answer = "This is an answer."

    # Default logging configuration
    config.logging.log_user_interactions = "True"
    config.logging.log_tokens = "False"

    # Default orchestrator configuration
    mock_strategy = MagicMock()
    mock_strategy.value = "langchain"
    config.orchestrator.strategy = mock_strategy

    # Default chat history and database type
    config.enable_chat_history = "True"
    config.database_type = "CosmosDB"

    # Integrated vectorization config
    config.integrated_vectorization_config.max_page_length = 2000
    config.integrated_vectorization_config.page_overlap_length = 200

    return config

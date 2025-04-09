"""
Common test fixtures for all test files
"""
import json
import os
from unittest.mock import MagicMock, patch
import pytest
from src.processors import AnalyticsProcessor


@pytest.fixture
def mock_azure_storage():
    """Mock all Azure Storage classes to prevent connection attempts"""

    # Mock the client creation methods directly - this is the most reliable approach
    with patch(
            'azure.storage.blob.BlobServiceClient.from_connection_string', autospec=True
    ) as mock_blob_from_conn, \
            patch(
                'azure.storage.queue.QueueClient.from_connection_string', autospec=True
            ) as mock_queue_from_conn:
        # Create mock instances
        mock_blob_service = MagicMock()
        mock_blob_container = MagicMock()
        mock_blob_client = MagicMock()
        mock_queue = MagicMock()

        # Set up return values
        mock_blob_from_conn.return_value = mock_blob_service
        mock_blob_service.get_container_client.return_value = mock_blob_container
        mock_blob_container.get_blob_client.return_value = mock_blob_client
        mock_queue_from_conn.return_value = mock_queue

        yield {
            'blob_service': mock_blob_service,
            'container_instance': mock_blob_container,
            'blob_client': mock_blob_client,
            'queue_instance': mock_queue
        }


@pytest.fixture
# pylint: disable=redefined-outer-name
def analytics_processor(mock_azure_storage):
    """Return an instance of AnalyticsProcessor with mocked services"""
    return AnalyticsProcessor(
        blob_service=mock_azure_storage['blob_service'],
        queue_service=mock_azure_storage['queue_instance']
    )


@pytest.fixture
def mock_env_variables():
    """
    Set up environment variables for tests
    """
    with patch.dict(os.environ, {
        'HTTP_ALMA_ANALYTICS_URL': 'https://example.com/api',
        'IZ': 'TEST_IZ',
        'ANALYSIS_NAME': 'TEST_ANALYSIS',
        'HTTP_ALMA_ANALYTICS_API_KEY': 'test-key',
        'AZURE_STORAGE_CONNECTION_STRING': 'DefaultEndpointsProtocol=https;AccountName=devstoreaccount1;AccountKey'
                                           '=Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq'
                                           '/K1SZFPTOtr/KBHBeksoGMGw==;BlobEndpoint=https://devstoreaccount1.blob'
                                           '.core.windows.net;QueueEndpoint=https://devstoreaccount1.queue.core'
                                           '.windows.net;TableEndpoint=https://devstoreaccount1.table.core.windows'
                                           '.net;',
        'NEXT_REQUEST_QUEUE': 'next-request-queue',
        'EMAIL_QUEUE': 'email-queue',
        'EMAIL_RECIPIENTS': 'test@example.com',
        'EMAIL_SENDER': 'sender@example.com'
    }):
        yield


@pytest.fixture
def mock_successful_response():
    """
    Creates a mock successful response
    """
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = json.dumps({
        'status': 'success',
        'data': {
            'is_finished': 'true',
            'columns': ['barcode', 'title'],
            'rows': [['123456789', 'Test Book']]
        }
    })
    return mock_response


@pytest.fixture
def mock_continuation_response():
    """
    Creates a mock response with continuation token
    """
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = json.dumps({
        'status': 'success',
        'data': {
            'is_finished': 'false',
            'resume': 'token123',
            'columns': ['barcode', 'title'],
            'rows': [['123456789', 'Test Book']]
        }
    })
    return mock_response

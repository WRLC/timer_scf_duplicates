"""Unit tests for storage.py"""

import json
from unittest.mock import MagicMock, patch
from src.storage import set_blob_data, queue_email, get_container_client, merge_blob_data, set_next_request


class TestStorage:
    """Test the storage helper functions"""

    @patch('src.storage.get_container_client')
    # pylint: disable=redefined-outer-name,unused-argument
    def test_set_blob_data(self, mock_get_container, mock_env_variables, mock_azure_storage):
        """Test the set_blob_data function

        Parameters:
        mock_get_container (MagicMock): Mocked get_container_client function
        mock_env_variables (dict): Mocked environment variables
        mock_azure_storage (dict): Mocked Azure Storage services

        Returns:
        None

        """
        mock_container = MagicMock()
        mock_container.exists.return_value = False
        mock_get_container.return_value = mock_container

        test_data = {'status': 'success', 'data': {'rows': []}}

        batch_id = set_blob_data(test_data)

        assert batch_id is not None
        mock_container.create_container.assert_called_once()
        mock_container.get_blob_client.assert_called_once()

    @patch('azure.storage.queue.QueueClient')
    # pylint: disable=redefined-outer-name,unused-argument
    def test_queue_email(self, mock_queue_client, mock_env_variables, mock_azure_storage):
        """Test the queue_email function

        Parameters:
        mock_queue_client (MagicMock): Mocked QueueClient
        mock_env_variables (dict): Mocked environment variables
        mock_azure_storage (dict): Mocked Azure Storage services

        Returns:
        None

        """
        test_data = {
            'columns': {'column1': 'barcode', 'column2': 'title'},
            'rows': [['123456789', 'Test Book']]
        }

        mock_queue = mock_azure_storage['queue_instance']
        mock_queue_client.from_connection_string.return_value = mock_queue

        queue_email(test_data)

        mock_queue.send_message.assert_called_once()

    @patch('azure.storage.blob.BlobServiceClient.from_connection_string')
    # pylint: disable=redefined-outer-name,unused-argument
    def test_get_container_client(self, mock_from_connection_string, mock_env_variables):
        """Test get_container_client function

        Parameters:
        mock_from_connection_string (MagicMock): Mocked BlobServiceClient
        mock_env_variables (dict): Mocked environment variables
        mock_azure_storage (dict): Mocked Azure Storage services

        Returns:
        None

        """
        # Setup mock
        mock_service = MagicMock()
        mock_container = MagicMock()
        mock_from_connection_string.return_value = mock_service
        mock_service.get_container_client.return_value = mock_container

        # Call the function
        result = get_container_client()

        # Assert the result is the mock container client
        assert result == mock_container
        mock_service.get_container_client.assert_called_once_with('duplicates-barcode-data')

    @patch('azure.storage.queue.QueueClient.from_connection_string')
    # pylint: disable=redefined-outer-name,unused-argument
    def test_set_next_request(self, mock_queue_client, mock_env_variables):
        """Test set_next_request function

        Parameters:
        mock_queue_client (MagicMock): Mocked QueueClient
        mock_env_variables (dict): Mocked environment variables

        Returns:
        None

        """
        # Setup mocks
        mock_queue = MagicMock()
        mock_queue_client.return_value = mock_queue

        # Test data
        test_data = {
            'data': {
                'resume': 'test-token',
                'columns': ['barcode', 'title']
            }
        }
        batch_id = '123456789'

        # Call the function
        set_next_request(test_data, batch_id)

        # Verify queue client was used correctly
        mock_queue_client.assert_called_once()
        mock_queue.send_message.assert_called_once()

    # noinspection PyUnusedLocal
    @patch('src.storage.get_container_client')
    # pylint: disable=redefined-outer-name,unused-argument
    def test_merge_blob_data(self, mock_get_container, mock_env_variables):
        """Test merge_blob_data function

        Parameters:
        mock_get_container (MagicMock): Mocked get_container_client function
        mock_env_variables (dict): Mocked environment variables

        Returns:
        None

        """
        # Setup mocks
        mock_container = MagicMock()
        mock_blob_client = MagicMock()

        # Setup blob list mock
        blob1 = MagicMock()
        blob1.name = 'batch-123-part1.json'
        blob_list = [blob1]

        # Configure mock returns
        mock_container.list_blobs.return_value = blob_list
        mock_container.get_blob_client.return_value = mock_blob_client

        # Mock download_blob to return test data
        mock_download = MagicMock()
        mock_download.readall.return_value = json.dumps({
            'data': {
                'rows': [['987654321', 'Another Book']]
            }
        })
        mock_blob_client.download_blob.return_value = mock_download

        # Test data
        test_data = {
            'batch_id': '123',
            'data': {
                'rows': [['123456789', 'Test Book']]
            }
        }

        # Call function
        result = merge_blob_data(mock_container, test_data)

        # Verify blobs were listed, downloaded, and deleted
        mock_container.list_blobs.assert_called_once_with(name_starts_with='batch-123')
        mock_container.get_blob_client.assert_called_once_with(blob1.name)
        mock_blob_client.download_blob.assert_called_once()
        mock_blob_client.delete_blob.assert_called_once()

        # Verify data was merged correctly
        assert len(result['data']['rows']) == 2
        assert ['123456789', 'Test Book'] in result['data']['rows']
        assert ['987654321', 'Another Book'] in result['data']['rows']


class TestStorageErrorHandling:
    """Tests for error handling in storage functions"""

    # pylint: disable=redefined-outer-name,unused-argument
    @patch('azure.storage.queue.QueueClient.from_connection_string')
    def test_set_next_request_exception_handling(self, mock_queue_client, mock_env_variables):
        """Test set_next_request function's exception handling

        Parameters:
        mock_queue_client (MagicMock): Mocked QueueClient
        mock_env_variables (dict): Mocked environment variables

        Returns:
        None

        """
        # Setup mock to raise an exception
        mock_queue_client.side_effect = Exception("Test exception")

        # Test data
        test_data = {'data': {'resume': 'test-token'}}
        batch_id = '123456789'

        # Mock the logging.error function to verify it's called
        with patch('src.storage.logging.error') as mock_logging:
            # Call the function that should catch the exception
            set_next_request(test_data, batch_id)

            # Verify error was logged
            mock_logging.assert_called_once()

    # pylint: disable=redefined-outer-name,unused-argument
    def test_set_blob_data_exception_handling(self, mock_env_variables):
        """Test set_blob_data function's exception handling

        Parameters:
        mock_env_variables (dict): Mocked environment variables

        Returns:
        None

        """
        # Create a mock container client
        mock_container_client = MagicMock()

        # Create a mock blob client that raises an exception
        mock_blob_client = MagicMock()
        mock_blob_client.upload_blob.side_effect = Exception("Test blob exception")

        # Make the container return our problematic blob client
        mock_container_client.get_blob_client.return_value = mock_blob_client

        # Patch the get_container_client function to return our mock
        with patch('src.storage.get_container_client', return_value=mock_container_client):
            with patch('src.storage.logging.error') as mock_logging:
                # Call the function
                result = set_blob_data({"key": "value"})

                # Verify error was logged and function returned None
                mock_logging.assert_called_once()
                assert result is None

    # pylint: disable=redefined-outer-name,unused-argument
    def test_merge_blob_data_exception_handling(self, mock_env_variables):
        """Test merge_blob_data exception handling

        Parameters:
        mock_env_variables (dict): Mocked environment variables

        Returns:
        None

        """
        # Create a mock container client
        mock_container = MagicMock()

        # Configure the mock to raise an exception when list_blobs is called
        mock_container.list_blobs.side_effect = Exception("Test container exception")

        # Test data
        test_data = {'batch_id': '123', 'data': {'rows': []}}

        # Mock logging
        with patch('src.storage.logging.error') as mock_logging:
            # Call function with the container that will raise exception
            result = merge_blob_data(mock_container, test_data)

            # Verify logging occurred and function returned original data
            mock_logging.assert_called_once()
            assert result == test_data

    def test_merge_blob_data_return_value_on_exception(self, mock_env_variables):
        """Test that merge_blob_data returns the original data when an exception occurs

        Parameters:
        mock_env_variables (dict): Mocked environment variables

        Returns:
        None

        """

        # Create test data with a unique identifier to verify it's returned unchanged
        original_data = {
            'columns': {'column1': 'barcode', 'column2': 'title'},
            'rows': [['123456789', 'Test Book']]
        }

        # Create a mock container that raises an exception
        mock_container = MagicMock()
        mock_container.list_blobs.side_effect = Exception("Test exception")

        # Call the function
        result = merge_blob_data(mock_container, original_data)

        # The key assertion - verify line 93 executes by confirming
        # the original data object is returned unchanged
        assert result is original_data  # Using 'is' instead of '==' for strict identity check

    # pylint: disable=redefined-outer-name,unused-argument
    def test_queue_email_exception_handling(self, mock_env_variables):
        """Test exception handling in queue_email function

        Parameters:
        mock_env_variables (dict): Mocked environment variables

        Returns:
        None

        """
        # Create test data
        test_data = {
            'columns': {'column1': 'barcode', 'column2': 'title'},
            'rows': [['123456789', 'Test Book']]
        }

        # Mock QueueClient to raise an exception when called
        with patch('src.storage.QueueClient.from_connection_string') as mock_queue_client:
            mock_queue_client.side_effect = Exception("Test queue exception")

            # Mock logging to verify it's called
            with patch('src.storage.logging.error') as mock_logging:
                # Call the function that should catch the exception
                queue_email(test_data)

                # Verify error was logged
                mock_logging.assert_called_once_with(
                    "Error sending message to email queue: %s",
                    "Test queue exception"
                )

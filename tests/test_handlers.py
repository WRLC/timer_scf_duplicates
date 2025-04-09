# test_handlers.py
"""
Unit tests for handlers.py
"""
import json
from unittest.mock import MagicMock, patch
import azure.functions as func
import requests
from src.handlers import start_analytics, send_next_request


class TestStartDuplicatesData:
    """
    Test the start_duplicates_data function
    """

    @patch('requests.post')
    @patch('src.handlers.process_response')
    # pylint: disable=redefined-outer-name,unused-argument
    def test_successful_request(
            self, mock_process, mock_post, mock_env_variables, mock_successful_response, mock_azure_storage
    ):
        """Test the start_duplicates_data function with a successful request"""
        mock_post.return_value = mock_successful_response

        # Create a mock TimerRequest
        mock_timer = MagicMock(spec=func.TimerRequest)

        start_analytics(mock_timer)

        # Verify request was made with correct parameters
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args  # pylint: disable=unused-variable
        assert kwargs['json']['iz'] == 'TEST_IZ'
        assert kwargs['json']['analysis'] == 'TEST_ANALYSIS'
        assert kwargs['headers']['x-functions-key'] == 'test-key'

        # Verify response was processed
        mock_process.assert_called_once_with(mock_successful_response.text)

    @patch('requests.post')
    # pylint: disable=redefined-outer-name,unused-argument
    def test_failed_request(self, mock_post, mock_env_variables, mock_azure_storage):
        """Test handling of failed requests"""
        # Configure the mock to raise an exception
        mock_post.side_effect = Exception("Connection error")

        # Create a mock TimerRequest
        mock_timer = MagicMock(spec=func.TimerRequest)

        # The test should expect logging.error to be called
        with patch('logging.error') as mock_log:
            # This should not re-raise the exception
            start_analytics(mock_timer)
            # Verify that error was logged
            mock_log.assert_called_once()


class TestSendNextRequest:  # pylint: disable=too-few-public-methods
    """
    Test the send_next_request function
    """

    @patch('requests.post')
    @patch('src.handlers.process_response')
    # pylint: disable=redefined-outer-name,unused-argument
    def test_successful_continuation(
            self, mock_process, mock_post, mock_env_variables, mock_successful_response, mock_azure_storage):
        """Test the send_next_request function with a successful continuation"""
        # Setup the response
        mock_post.return_value = mock_successful_response

        # Create a mock QueueMessage
        mock_msg = MagicMock(spec=func.QueueMessage)
        mock_msg.get_body.return_value = json.dumps({
            'iz': 'TEST_IZ',
            'analysis': 'TEST_ANALYSIS',
            'resume': 'token123',
            'batch_id': '123456789'
        }).encode()

        # Execute the function
        send_next_request(mock_msg)

        # Verify request was made
        mock_post.assert_called_once()

        # Verify response was processed
        mock_process.assert_called_once_with(mock_successful_response.text)


class TestHandlersErrorHandling:
    """Tests for error paths and edge cases in handlers"""

    def test_start_analytics_request_exception(self):
        """Test handling of request exception in start_analytics"""
        mock_timer = MagicMock(spec=func.TimerRequest)

        with patch('requests.post', side_effect=requests.RequestException("Test error")):
            with patch('src.handlers.logging.error') as mock_logging:
                start_analytics(mock_timer)

                mock_logging.assert_called_once()

    def test_start_analytics_general_exception(self):
        """Test general exception handling in start_analytics"""
        mock_timer = MagicMock(spec=func.TimerRequest)

        with patch('requests.post', side_effect=Exception("Test error")):
            with patch('src.handlers.logging.error') as mock_logging:
                # noinspection PyNoneFunctionAssignment
                start_analytics(mock_timer)

                mock_logging.assert_called_once()

    def test_start_analytics_non_200_response(self):
        """Test handling of non-200 response in start_analytics"""
        mock_timer = MagicMock(spec=func.TimerRequest)
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = "Error response"

        with patch('requests.post', return_value=mock_response):
            with patch('src.handlers.logging.warning') as mock_logging:
                start_analytics(mock_timer)

                mock_logging.assert_called_once_with("Error response")

    def test_send_next_request_invalid_json(self):
        """Test handling of invalid JSON in queue message"""
        mock_msg = MagicMock(spec=func.QueueMessage)
        mock_msg.get_body.return_value = b'invalid json'

        with patch('src.handlers.logging.error') as mock_logging:
            send_next_request(mock_msg)

            mock_logging.assert_called_once()

    def test_send_next_request_request_exception(self):
        """Test handling of request exception in send_next_request"""
        mock_msg = MagicMock(spec=func.QueueMessage)
        mock_msg.get_body.return_value = json.dumps({"test": "data"}).encode()

        with patch('requests.post', side_effect=requests.RequestException("Test error")):
            with patch('src.handlers.logging.error') as mock_logging:
                send_next_request(mock_msg)

                mock_logging.assert_called_once()

    def test_send_next_request_general_exception(self):
        """Test handling of general exception in send_next_request"""
        # Create a mock QueueMessage with valid JSON
        mock_msg = MagicMock(spec=func.QueueMessage)
        mock_msg.get_body.return_value = json.dumps({"test": "data"}).encode()

        # Force a general exception (not a RequestException) to trigger the catchall
        with patch('requests.post', side_effect=Exception("General error")):
            with patch('src.handlers.logging.error') as mock_logging:
                send_next_request(mock_msg)

                # Verify that error was logged
                mock_logging.assert_called_once()

    def test_send_next_request_non_200_response(self):
        """Test handling of non-200 response in send_next_request"""
        mock_msg = MagicMock(spec=func.QueueMessage)
        mock_msg.get_body.return_value = json.dumps({"test": "data"}).encode()

        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = "Error response"

        with patch('requests.post', return_value=mock_response):
            with patch('src.handlers.logging.warning') as mock_logging:
                send_next_request(mock_msg)

                mock_logging.assert_called_once_with("Error response")

# test_processors.py
"""
Unit tests for processors.py
"""
import json
from unittest.mock import MagicMock, patch
from src.processors import process_response


class TestProcessResponse:
    """
    Test the process_response function
    """

    @patch('src.processors.set_blob_data')
    @patch('src.processors.set_next_request')
    # pylint: disable=redefined-outer-name,unused-argument
    def test_process_with_continuation(
            self, mock_set_next, mock_set_blob, analytics_processor, mock_env_variables
    ):
        """
        Test the process_response function with a continuation token
        """

        data = json.dumps({
            'status': 'success',
            'data': {
                'is_finished': 'false',
                'resume': 'token123',
                'columns': ['barcode', 'title'],
                'rows': [['123456789', 'Test Book']]
            }
        })

        process_response(data)

        mock_set_blob.assert_called_once()
        mock_set_next.assert_called_once()

    @patch('src.processors.get_container_client')
    @patch('src.processors.merge_blob_data')
    @patch('src.processors.queue_email')
    # pylint: disable=redefined-outer-name,unused-argument
    def test_process_final_batch(
            self, mock_queue, mock_merge, mock_get_container, analytics_processor, mock_env_variables
    ):
        """
        Test the process_response function with final batch data
        """
        mock_container = MagicMock()
        mock_get_container.return_value = mock_container

        merged_data = {
            'data': {
                'is_finished': 'true',
                'batch_id': 'batch123',
                'columns': ['barcode', 'title'],
                'rows': [['123456789', 'Test Book'], ['987654321', 'Another Book']]
            }
        }
        mock_merge.return_value = merged_data

        data = json.dumps({
            'status': 'success',
            'data': {
                'is_finished': 'true',
                'batch_id': 'batch123',
                'columns': ['barcode', 'title'],
                'rows': [['123456789', 'Test Book']]
            }
        })

        process_response(data)

        mock_get_container.assert_called_once()
        mock_merge.assert_called_once()
        mock_queue.assert_called_once_with(merged_data)

    def test_process_response_general_exception(self):
        """Test handling of general exception in process_response function"""
        # Create valid-looking response data as a string
        response_data = json.dumps({
            "status": "success",
            "data": {
                "is_finished": "false",
                "columns": ["barcode", "title"],
                "rows": [["123456789", "Test Book"]]
            }
        })

        # Patch json.loads to raise an exception
        with patch('json.loads', side_effect=Exception("JSON parsing error")):
            with patch('src.processors.logging.error') as mock_logging:
                process_response(response_data)

                # Verify error was logged
                mock_logging.assert_called_once()

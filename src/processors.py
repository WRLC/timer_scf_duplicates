"""Analytics Processor Module"""

import json
import logging
from typing import Any

from src.storage import set_blob_data, set_next_request, get_container_client, merge_blob_data, queue_email


def process_response(response_text: str) -> None:
    """Process the response from Alma Analytics API

    Parameters:
    response_text (str): The response text from the API.

    Returns:
    None

    """
    try:
        data: Any = json.loads(response_text)

    except Exception as e:
        logging.error("Error processing response: %s", str(e))
        return

    if data['status'] == 'success':
        if data['data']['is_finished'] == 'false':
            # Not finished, save data and queue next request
            batch_id = set_blob_data(data)
            set_next_request(data, batch_id)  # type:ignore[arg-type]
        else:
            # Final batch, merge all data and send email
            container_client = get_container_client()
            merged_data = merge_blob_data(container_client, data['data'])
            queue_email(merged_data)


class AnalyticsProcessor:  # pylint: disable=too-few-public-methods
    """Class to process analytics responses"""

    def __init__(self, blob_service=None, queue_service=None):
        """Initialize the processor

        Parameters:
        blob_service (BlobServiceClient): Blob service client.
        queue_service (QueueServiceClient): Queue service client.

        Returns:
        None

        """
        self.blob_service = blob_service
        self.queue_service = queue_service

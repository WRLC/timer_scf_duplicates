"""Analytics handlers module"""

import json
import logging
import os
import azure.functions as func
import requests  # type:ignore[import-untyped]
from src.processors import process_response


# noinspection PyUnusedLocal
def start_analytics(req: func.TimerRequest) -> None:  # pylint: disable=unused-argument
    """Process a timer trigger to start analytics data collection.

    Parameters:
    req (func.TimerRequest): The timer trigger request object.

    Returns:
    None

    """
    logging.info("Starting analytics data collection")

    try:
        # Call Alma Analytics API
        response = requests.post(
            os.getenv('HTTP_ALMA_ANALYTICS_URL'),  # type:ignore[arg-type]
            json={
                'iz': os.getenv('IZ'),
                'analysis': os.getenv('ANALYSIS_NAME')
            },
            headers={'x-functions-key': os.getenv('HTTP_ALMA_ANALYTICS_API_KEY')},
            timeout=300
        )
    except requests.RequestException as e:
        logging.error("Request failed: %s", e)
        return
    except Exception as e:
        logging.error("An error occurred: %s", e)
        return

    if response.status_code != 200:
        logging.warning(response.text)
        return

    process_response(response.text)


def send_next_request(msg: func.QueueMessage) -> None:
    """Process the queue message and send the next request to Alma Analytics API.

    Parameters:
    msg (func.QueueMessage): The queue message object.

    Returns:
    None

    """
    logging.info("Sending next request to Alma Analytics API")

    try:
        message_body = msg.get_body().decode()
        message_data = json.loads(message_body)
    except (ValueError, TypeError) as e:
        logging.error("Invalid message format: %s", str(e))
        return

    try:
        response = requests.post(
            os.getenv('HTTP_ALMA_ANALYTICS_URL'),  # type:ignore[arg-type]
            json=message_data,
            headers={'x-functions-key': os.getenv('HTTP_ALMA_ANALYTICS_API_KEY')},
            timeout=300
        )
        response.raise_for_status()

    except requests.RequestException as e:
        logging.error("Error processing API request: %s", str(e))
        return
    except Exception as e:
        logging.error("An error occurred: %s", str(e))
        return

    if response.status_code != 200:
        logging.warning(response.text)
        return

    process_response(response.text)

"""Azure Function App main entry file"""
import azure.functions as func

from src.processors import AnalyticsProcessor, process_response
from src.storage import set_blob_data, set_next_request, get_container_client, merge_blob_data, queue_email
from src.handlers import start_analytics, send_next_request

# Create Azure Function app
app = func.FunctionApp()

# Export classes and functions needed by tests
__all__ = [
    'AnalyticsProcessor',
    'process_response',
    'set_blob_data',
    'set_next_request',
    'get_container_client',
    'merge_blob_data',
    'queue_email',
    'start_analytics',
    'send_next_request',
]


# Register Azure Functions
@app.function_name("startduplicatesdata")
@app.timer_trigger(
    schedule="0 0 10 1 * *",  # First day of every month at 10:00 AM UTC
    arg_name="timer",
    run_on_startup=False,
    use_monitor=False
)
def start_duplicates_data(timer: func.TimerRequest) -> None:
    """Azure Function timer trigger wrapper

    Parameters:
    timer (func.TimerRequest): The timer trigger request object.

    Returns:
    None

    """
    return start_analytics(timer)


@app.function_name("sendnextrequest")
@app.queue_trigger(
    arg_name='msg',
    queue_name="%NEXT_REQUEST_QUEUE%",
    connection='AzureWebJobsStorage'
)
def send_next_analytics_request(msg: func.QueueMessage) -> None:
    """Azure Function queue trigger wrapper

    Parameters:
    msg (func.QueueMessage): The queue message object.

    Returns:
    None

    """
    return send_next_request(msg)

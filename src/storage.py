"""Analytics Storage Module"""
import json
import time
import logging
import os
from typing import Any
from azure.storage.blob import BlobServiceClient, ContainerClient, BlobClient
from azure.storage.queue import QueueClient, BinaryBase64EncodePolicy, BinaryBase64DecodePolicy


def set_blob_data(data: Any) -> str | None:
    """Set blob data in Azure Blob Storage.

    Parameters:
    data (dict): The data to be stored in the blob.

    Returns:
    str: The batch ID of the blob.

    """
    container_client: ContainerClient = get_container_client()

    if not container_client.exists():
        container_client.create_container()

    batch_id: str = str(int(time.time()))

    blob_client: BlobClient = container_client.get_blob_client(f'{batch_id}.json')

    try:
        blob_client.upload_blob(json.dumps(data), overwrite=True)
    except Exception as e:
        logging.error("Error uploading blob: %s", str(e))
        return None

    return batch_id


def set_next_request(data: Any, batch_id: str) -> None:
    """Set next request in Azure Queue Storage.

    Parameters:
    data (dict): The data to be sent in the queue message.
    batch_id (str): The batch ID of the blob.

    Returns:
    None

    """
    try:
        queue_client: QueueClient = QueueClient.from_connection_string(
            conn_str=os.getenv('AZURE_STORAGE_CONNECTION_STRING'),  # type:ignore[arg-type]
            queue_name=os.getenv('NEXT_REQUEST_QUEUE'),  # type:ignore[arg-type]
            message_encode_policy=BinaryBase64EncodePolicy(),
            message_decode_policy=BinaryBase64DecodePolicy()
        )

        message: dict[str, Any] = {
            'iz': os.getenv('IZ'),
            'analysis': os.getenv('ANALYSIS_NAME'),
            'resume': data['data']['resume'],
            'columns': data['data']['columns'],
            'batch_id': batch_id,
        }

        json_data: str = json.dumps(message)
        encoded_data: bytes = json_data.encode()
        queue_client.send_message(encoded_data)

    except Exception as e:
        logging.error("Error sending message to queue: %s", str(e))


def get_container_client() -> ContainerClient:
    """Get container client for Azure Blob Storage.

    Returns:
    ContainerClient: The container client for the blob storage.

    """
    blob_service: BlobServiceClient = BlobServiceClient.from_connection_string(
        os.getenv('AZURE_STORAGE_CONNECTION_STRING')  # type:ignore[arg-type]
    )
    container_client: ContainerClient = blob_service.get_container_client(
        'duplicates-barcode-data')

    return container_client


def merge_blob_data(container_client, data):
    """Merge blob data in Azure Blob Storage.

    Parameters:
    container_client (ContainerClient): The container client for the blob storage.
    data (dict): The data to be merged.

    Returns:
    dict: The merged data.

    """
    if 'batch_id' not in data:
        return data

    batch_prefix = f"batch-{data['batch_id']}"

    try:
        blob_list = container_client.list_blobs(name_starts_with=batch_prefix)

        for blob in blob_list:
            blob_client = container_client.get_blob_client(blob.name)
            batch_data = json.loads(blob_client.download_blob().readall())
            data['data']['rows'].extend(batch_data['data']['rows'])
            blob_client.delete_blob()
    except Exception as e:
        logging.error("Error merging blob data: %s", str(e))
        # Return original data as fallback

    return data


def queue_email(data: Any) -> None:
    """Queue email with complete data.

    Parameters:
    data (dict): The data to be sent in the email.

    Returns:
    None

    """
    mail: dict[str, Any] = {
        'subject': 'SCF Duplicate Barcodes',
        'header': 'Duplicate barcodes have been found int the SCF',
        'caption': 'SCF Duplicate Barcodes',
        'columns': data['columns'],
        'rows': data['rows'],
        'footer': 'This is an automated message. Please do not reply.',
        'recipients': os.getenv('EMAIL_RECIPIENTS'),
        'sender': os.getenv('EMAIL_SENDER'),
    }
    try:
        queue_client: QueueClient = QueueClient.from_connection_string(
            conn_str=os.getenv('AZURE_STORAGE_CONNECTION_STRING'),  # type:ignore[arg-type]
            queue_name=os.getenv('EMAIL_QUEUE'),  # type:ignore[arg-type]
            message_encode_policy=BinaryBase64EncodePolicy(),
            message_decode_policy=BinaryBase64DecodePolicy()
        )

        json_data: str = json.dumps(mail)
        encoded_data: bytes = json_data.encode()
        queue_client.send_message(encoded_data)

    except Exception as e:
        logging.error("Error sending message to email queue: %s", str(e))

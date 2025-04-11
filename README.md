# timer_scf_duplicates

[![Python Tests](https://github.com/wrlc/timer_scf_duplicates/actions/workflows/tests.yml/badge.svg)](https://github.com/wrlc/timer_scf_duplicates/actions/workflows/tests.yml)
[![Code Quality](https://github.com/wrlc/timer_scf_duplicates/actions/workflows/code-quality.yml/badge.svg)](https://github.com/wrlc/timer_scf_duplicates/actions/workflows/code-quality.yml)


Timer-triggered Azure Function to check for duplicate barcodes in the WRLC Shared Collection Facility (SCF) and send
a list of duplicates to an Azure Storage Queue for notification by email.

## Prerequisites

- [http_alma_analytics](https://github.com/WRLC/http_alma_analytics): Azure Function to retrieve Alma Analytics data.
- [queue_send_email](https://github.com/WRLC/queue_send_email): Azure Function to send email notifications.
- Azure Storage Queues for email messages and additional requests messages.
- Azure Blob Storage for storing the list of duplicate barcodes.


## Required Environment Variables

- `SQLALCHEMY_DB_URL`: The connection string for the database.
- `HTTP_ALMA_ANALYTICS_URL`: The URL for the Azure Function to retrieve Alma Analytics data.
- `HTTP_ALMA_ANALYTICS_API_KEY`: The Admin API key for the HTTP_ALMA_ANALYTICS_URL Azure Function.
- `IZ`: The IZ code for the Alma institution.
- `ANALYSIS_NAME`: The name of the Alma Analytics analysis to run.
- `AZURE_STORAGE_CONNECTION_STRING`: The connection string for the Azure Storage account.
- `NEXT_REQUEST_QUEUE`: The name of the Azure Storage Queue for making additional requests with a resume token.
- `EMAIL_STORAGE_CONNECTION_STRING`: The connection string for the Azure Storage account for the email queue.
- `EMAIL_QUEUE`: The name of the Azure Storage Queue for email notifications.
- `EMAIL_RECIPIENTS`: A comma-separated list of email addresses to send notifications to. (Will be replaced by DB)
- `EMAIL_SENDER`: The email address to send notifications from

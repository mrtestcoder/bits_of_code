# Freshservice Ticket Merger

This script automatically merges Freshservice tickets based on a set of predefined criteria. It is designed to be run as a webhook receiver, triggering when a new ticket is created in Freshservice.

## Features

- Merges tickets with the same title.
- Merges tickets with the same "action" and "who" fields in the description.
- The earliest ticket becomes the parent ticket.
- Subsequent matching tickets are merged as child tickets.
- The original child tickets are deleted after merging.

## Prerequisites

- Python 3.6+
- A Freshservice account with admin privileges.
- A server to host the Python script and receive webhooks.

## Installation

1.  Clone this repository:
    ```bash
    git clone https://github.com/your-username/freshservice-ticket-merger.git
    cd freshservice-ticket-merger
    ```

2.  Install the required Python packages:
    ```bash
    pip install -r requirements.txt
    ```

3.  Set the following environment variables:
    - `FRESHSERVICE_DOMAIN`: Your Freshservice domain (e.g., `yourcompany.freshservice.com`).
    - `FRESHSERVICE_API_KEY`: Your Freshservice API key.

## Usage

1.  Run the Flask application:
    ```bash
    python freshservice_merger.py
    ```
    The application will start on `http://127.0.0.1:5000` by default.

2.  **Expose the webhook endpoint to the internet.** You can use a tool like [ngrok](https://ngrok.com/) to expose your local server to the internet for testing purposes.
    ```bash
    ngrok http 5000
    ```
    This will give you a public URL (e.g., `https://your-unique-id.ngrok.io`) that forwards to your local server.

## Freshservice Webhook Configuration

1.  In your Freshservice account, go to **Admin > Workflows > Automations > Ticket Creation**.
2.  Create a new rule.
3.  Set the event to "Ticket is Created".
4.  In the "Actions" section, select "Trigger Webhook".
5.  Set the webhook URL to the public URL of your server (e.g., `https://your-unique-id.ngrok.io/webhook`).
6.  Set the request type to **POST**.
7.  Set the encoding to **JSON**.
8.  Make sure the content includes the ticket details. You can use the following JSON payload as a template:
    ```json
    {
      "freshservice_webhook": {
        "ticket": {
          "id": "{{ticket.id}}",
          "subject": "{{ticket.subject}}",
          "description_text": "{{ticket.description_text}}",
          "created_at": "{{ticket.created_at}}",
          "email": "{{ticket.requester.email}}",
          "priority": "{{ticket.priority}}",
          "status": "{{ticket.status}}"
        }
      }
    }
    ```
9.  Save and enable the rule.

## Running Tests

To run the unit tests, use the following command:

```bash
python -m unittest test_freshservice_merger.py
```

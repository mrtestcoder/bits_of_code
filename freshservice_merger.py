import requests
import json
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Freshservice API configuration
FRESHSERVICE_DOMAIN = os.environ.get("FRESHSERVICE_DOMAIN")
API_KEY = os.environ.get("FRESHSERVICE_API_KEY")

def get_tickets():
    """
    Fetches all tickets from Freshservice.
    """
    tickets = []
    page = 1
    while True:
        url = f"https://{FRESHSERVICE_DOMAIN}/api/v2/tickets?page={page}"
        headers = {
            "Content-Type": "application/json",
        }
        try:
            response = requests.get(url, auth=(API_KEY, "X"), headers=headers)
            response.raise_for_status()  # Raise an exception for bad status codes
            current_tickets = response.json().get("tickets", [])
            if not current_tickets:
                break
            tickets.extend(current_tickets)
            page += 1
        except requests.exceptions.RequestException as e:
            logging.error(f"Error fetching tickets: {e}")
            return None
    return tickets

def parse_ticket_description(description):
    """
    Parses the ticket description to extract action and who.
    """
    action = None
    who = None
    if description:
        # A simple way to parse key-value pairs from the description.
        # This can be made more robust based on the actual format of the description.
        lines = description.split('\\n')
        for line in lines:
            if line.startswith("action:"):
                action = line.split(":", 1)[1].strip()
            elif line.startswith("who:"):
                who = line.split(":", 1)[1].strip()
    return action, who

def group_tickets(tickets):
    """
    Groups tickets based on title, action, and who.
    """
    grouped_tickets = {}
    for ticket in tickets:
        title = ticket.get("subject")
        description = ticket.get("description_text")
        action, who = parse_ticket_description(description)

        if title and action and who:
            group_key = (title, action, who)
            if group_key not in grouped_tickets:
                grouped_tickets[group_key] = []
            grouped_tickets[group_key].append(ticket)
    return grouped_tickets

def merge_tickets(grouped_tickets):
    """
    Merges child tickets into parent tickets.
    """
    for group, tickets in grouped_tickets.items():
        if len(tickets) > 1:
            # Sort tickets by creation date to find the parent
            sorted_tickets = sorted(tickets, key=lambda t: t['created_at'])
            parent_ticket = sorted_tickets[0]
            child_tickets = sorted_tickets[1:]

            print(f"Merging tickets for group: {group}")
            print(f"Parent ticket: {parent_ticket['id']}")

            for child in child_tickets:
                print(f"  Merging child ticket: {child['id']}")
                url = f"https://{FRESHSERVICE_DOMAIN}/api/v2/tickets/{parent_ticket['id']}/create_child_ticket"
                headers = {
                    "Content-Type": "application/json",
                }
                # The body of the child ticket can be customized as needed.
                # Here, we're creating a simple child ticket with the same subject and description.
                data = {
                    "subject": child['subject'],
                    "description": child['description'],
                    "email": child['email'],
                    "priority": child['priority'],
                    "status": child['status'],
                }
                try:
                    response = requests.post(url, auth=(API_KEY, "X"), headers=headers, json=data)
                    response.raise_for_status()
                    logging.info(f"  Successfully created child ticket for {child['id']}.")

                    # Now, delete the original child ticket
                    delete_url = f"https://{FRESHSERVICE_DOMAIN}/api/v2/tickets/{child['id']}"
                    delete_response = requests.delete(delete_url, auth=(API_KEY, "X"), headers=headers)
                    delete_response.raise_for_status()
                    logging.info(f"  Successfully deleted original child ticket {child['id']}.")
                except requests.exceptions.RequestException as e:
                    logging.error(f"  Error merging ticket {child['id']}: {e}")

from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/webhook', methods=['POST'])
def webhook():
    """
    Receives webhook notifications from Freshservice.
    """
    if not request.is_json:
        logging.error("Request is not in JSON format")
        return jsonify({"error": "Invalid request format"}), 400

    data = request.get_json()

    # The ticket data is expected to be in the 'freshservice_webhook' key
    # This might need to be adjusted based on the actual webhook payload from Freshservice
    ticket = data.get('freshservice_webhook', {}).get('ticket')

    if not ticket:
        logging.error("No ticket data found in webhook payload")
        return jsonify({"error": "No ticket data found"}), 400

    logging.info(f"Received new ticket: {ticket.get('id')}")

    # Now, find matching tickets and merge
    # This will be a new function that combines searching and merging
    find_and_merge_tickets(ticket)

    return jsonify({"status": "success"}), 200

def find_and_merge_tickets(new_ticket):
    """
    Finds matching tickets and merges them.
    """
    title = new_ticket.get("subject")
    description = new_ticket.get("description_text")
    action, who = parse_ticket_description(description)

    if not (title and action and who):
        logging.info(f"Ticket {new_ticket.get('id')} does not have the required fields for merging.")
        return

    # Search for existing tickets with the same criteria
    # We'll need to use the "Filter Tickets" endpoint for this
    # Note: This is a simplified query. A more robust solution might involve a more complex query or multiple API calls.
    query = f"subject:'{title}'"
    url = f"https://{FRESHSERVICE_DOMAIN}/api/v2/tickets/filter?query={query}"

    headers = {
        "Content-Type": "application/json",
    }

    try:
        response = requests.get(url, auth=(API_KEY, "X"), headers=headers)
        response.raise_for_status()
        existing_tickets = response.json().get("tickets", [])

        # Filter the tickets further based on the description
        matching_tickets = [t for t in existing_tickets if parse_ticket_description(t.get("description_text")) == (action, who)]

        # Add the new ticket to the list of matching tickets
        all_matching_tickets = matching_tickets + [new_ticket]

        if len(all_matching_tickets) > 1:
            grouped_tickets = {(title, action, who): all_matching_tickets}
            merge_tickets(grouped_tickets)
        else:
            logging.info(f"No matching tickets found for ticket {new_ticket.get('id')}.")

    except requests.exceptions.RequestException as e:
        logging.error(f"Error searching for matching tickets: {e}")

def main():
    """
    Main function to run the ticket merger.
    """
    # The main function will now run the Flask app
    app.run(debug=True)

if __name__ == "__main__":
    main()

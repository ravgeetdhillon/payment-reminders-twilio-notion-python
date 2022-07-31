"""
Client Payment Reminders using Twilio, Notion, and Python.
by https://github.com/ravgeetdhillon
"""

import os
from datetime import datetime

import requests
from dotenv import load_dotenv
from requests.models import Response
from twilio.rest import Client


load_dotenv()

TWILIO_ACCOUNT_SID = os.getenv('ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.getenv('AUTH_TOKEN')
NOTION_API_BASE_URL = 'https://api.notion.com/v1'
NOTION_API_TOKEN = os.getenv('NOTION_API_TOKEN')
NOTION_DATABASE_ID = os.getenv('NOTION_DATABASE_ID')


def get_client_details() -> list:
    """
    This function calls the Notion API to get a list of clients that we need to monitor.
    """

    headers: dict = {
        'Authorization': f'Bearer {NOTION_API_TOKEN}',
        'Content-Type': 'application/json',
        'Notion-Version': '2021-08-16',
    }

    # uses https://developers.notion.com/reference/post-database-query
    response: Response = requests.post(
        f'{NOTION_API_BASE_URL}/databases/{NOTION_DATABASE_ID}/query', headers=headers)

    if response.status_code == 200:
        json_response: dict = response.json()['results']
    else:
        print("Something went wrong.")
        return

    clients: list = []
    for item in json_response:
        client: dict = {
            'id': item['id'],
            'name': item['properties']['Name']['title'][0]['plain_text'],
            'pending_amount': item['properties']['Pending Amount']['number'],
            'due_date': item['properties']['Due Date']['date']['start'],
            'phone_number': item['properties']['Phone No.']['phone_number'],
        }
        clients.append(client)

    return clients


def is_past_due_date(due_date: str) -> bool:
    """
    This function checks if the a date is due or not.
    """

    today = datetime.today()
    delta = datetime.strptime(due_date, "%Y-%m-%d") - today
    return delta.days < 0


def send_reminder(client: dict):
    """
    This function sends a WhatsApp notification using the Twilio WhatsApp Business API.
    """

    twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

    # This is the Twilio Sandbox number. Don't change it.
    from_whatsapp_number = 'whatsapp:+14155238886',
    to_whatsapp_number = f"whatsapp:{client['phone_number']}"
    body: str = f"Hi {client['name']}. Your payment of USD{client['pending_amount']} is due since {client['due_date']}."

    try:
        twilio_client.messages.create(body=body,
                                      from_=from_whatsapp_number,
                                      to=to_whatsapp_number)
    except:
        print('There was an error sending the message')


def main():
    clients: list = get_client_details()
    for client in clients:
        if is_past_due_date(client['due_date']):
            send_reminder(client)


if __name__ == '__main__':
    main()

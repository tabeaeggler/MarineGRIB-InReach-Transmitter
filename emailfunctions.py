import os
import pickle
import base64
from email.mime.text import MIMEText
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request



# GMAIL permissions (https://developers.google.com/gmail/api/quickstart/python)
# Set up the Gmail API: https://developers.google.com/gmail/api/quickstart/python

SCOPES = ['https://mail.google.com/'] # Set full access permission scope (https://developers.google.com/gmail/api/auth/scopes)
GMAIL_ADDRESS = 'FILL IN' # Your gmail e-mail address
TOKEN_PATH = './token.pickle' # Path to save token file -> created automatically when the authorisation completes first time
CREDENTIALS_PATH = './credentials.json' # Path of the downloaded Gmail credentials
FILE_PATH = './attachments' # Path to save attachment files



def gmail_authenticate():
    """Authenticates the user and returns the Gmail API service."""
    creds = None
    if os.path.exists(TOKEN_PATH):  # Check for existing token
        with open(TOKEN_PATH, "rb") as token:
            creds = pickle.load(token)

    if not creds or not creds.valid:
        creds = _get_new_or_refreshed_credentials(creds)
        # Save the credentials for the next run
        with open(TOKEN_PATH, "wb") as token:
            pickle.dump(creds, token)
    return build('gmail', 'v1', credentials=creds)

def _get_new_or_refreshed_credentials(creds):
    """Obtain new credentials or refresh existing ones."""
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    else:
        flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
        creds = flow.run_local_server(port=0)
    return creds


def build_message(destination, obj, body):
    message = MIMEText(body)
    message['to'] = destination
    message['from'] = GMAIL_ADDRESS
    message['subject'] = obj

    return {'raw': base64.urlsafe_b64encode(message.as_bytes()).decode()}



def send_message(service, destination, obj, body):
    return service.users().messages().send(
        userId="me",
        body=build_message(destination, obj, body)
    ).execute()


def search_messages(service, query):
# loop will continue retrieving pages of messages as long as there's a nextPageToken
    page_token = None
    messages = []

    while True:
        result = service.users().messages().list(userId='me', q=query, pageToken=page_token).execute()
        if 'messages' in result:
            messages.extend(result['messages'])
            
        page_token = result.get('nextPageToken', None)
        if not page_token:
            break
    return messages



def _download_attachment(service, user_id, msg_id, att_id, filename):
    """Download an attachment."""
    att = service.users().messages().attachments().get(userId=user_id, messageId=msg_id, id=att_id).execute()
    data = att['data']
    file_data = base64.urlsafe_b64decode(data.encode('UTF-8'))
    
    path = os.path.join(FILE_PATH, filename)
    with open(path, 'wb') as f:
        f.write(file_data)
    
    return path


def get_attachments(service, msg_id, user_id='me', save_path='.'):
    """Retrieve and store attachment from a message with a given ID. Returns Path to the downloaded file."""
    try:
        message = service.users().messages().get(userId=user_id, id=msg_id).execute()
        attachments_paths = []

        for part in message['payload']['parts']:
            if part['filename']:
                if 'data' in part['body']:
                    data = part['body']['data']
                else:
                    att_id = part['body']['attachmentId']
                    path = _download_attachment(service, user_id, msg_id, att_id, part['filename'])
                    attachments_paths.append(path)         
        return attachments_paths

    except Exception as error:
        print(f'An error occurred: {error}')
        return []

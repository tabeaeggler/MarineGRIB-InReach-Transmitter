import os
import pickle
import base64
from email.mime.text import MIMEText
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

import configs as configs

# Set up the Gmail API: https://developers.google.com/gmail/api/quickstart/python

def gmail_authenticate():
    """Authenticates the user and returns the Gmail API service."""
    creds = None
    if os.path.exists(configs.TOKEN_PATH):  # Check for existing token
        with open(configs.TOKEN_PATH, "rb") as token:
            creds = pickle.load(token)

    if not creds or not creds.valid:
        creds = _get_new_or_refreshed_credentials(creds)
        # Save the credentials for the next run
        with open(configs.TOKEN_PATH, "wb") as token:
            pickle.dump(creds, token)
    return build('gmail', 'v1', credentials=creds)



def build_message(destination, obj, body):
    """Construct a MIMEText message for the Gmail API.
    
    Args:
    destination (str): Email address of the recipient.
    obj (str): Subject of the email.
    body (str): Body content of the email.

    Returns:
    dict: Gmail API compatible message structure.
    """
    message = MIMEText(body)
    message['to'] = destination
    message['from'] = configs.GMAIL_ADDRESS
    message['subject'] = obj

    return {'raw': base64.urlsafe_b64encode(message.as_bytes()).decode()}



def send_message(service, destination, obj, body):
    """Send an email message through Gmail API.
    
    Args:
    service: Authenticated Gmail API service instance.
    destination (str): Email address of the recipient.
    obj (str): Subject of the email.
    body (str): Body content of the email.

    Returns:
    dict: Information about the sent message.
    """
    return service.users().messages().send(
        userId="me",
        body=build_message(destination, obj, body)
    ).execute()


def search_messages(service, query):
    """Search for Gmail messages that match a query. Loop will continue retrieving pages of messages as long as there's a nextPageToken.
    
    Args:
    service: Authenticated Gmail API service instance.
    query (str): Query string to filter messages.

    Returns:
    list: List of matching message IDs.
    """
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



def get_attachments(service, msg_id, user_id='me', save_path='.'):
    """Retrieve and save attachments from a Gmail message.
    
    Args:
    service: Authenticated Gmail API service instance.
    msg_id (str): ID of the Gmail message.
    user_id (str, optional): Gmail user ID. Defaults to 'me' for the authenticated user.
    save_path (str, optional): Path to save downloaded attachments. Defaults to current directory.

    Returns:
    list: Paths to the downloaded attachments.
    """
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



def check_and_answer_mail(auth_service):
    """
    Check for new messages, process them, and record their IDs.

    Args:
        auth_service (obj): The authentication service object.
    """
    previous_messages = _load_previous_messages()
    unanswered_messages = _get_new_inreach_messages(auth_service, previous_messages)
    
    for message_id in unanswered_messages:
        try:
            answer_service(message_id, auth_service)
            print(f"Successfully answered message {message_id}", flush=True)
        except Exception as e:
            print(f"Error answering message {message_id}: {e}", flush=True)
        finally:
            _append_to_previous_messages(message_id)




######## HELPERS ########

def _get_new_or_refreshed_credentials(creds):
    """Helper to obtain new credentials or refresh expired ones.
    
    Args:
    creds: google.oauth2.credentials.Credentials object

    Returns:
    google.oauth2.credentials.Credentials: Refreshed or newly obtained credentials
    """
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    else:
        flow = InstalledAppFlow.from_client_secrets_file(configs.CREDENTIALS_PATH, configs.SCOPES)
        creds = flow.run_local_server(port=0)
    return creds


def _download_attachment(service, user_id, msg_id, att_id, filename):
    """Helper to download and save an attachment from a Gmail message.
    
    Args:
    service: Authenticated Gmail API service instance.
    user_id (str): Gmail user ID. Use 'me' for the authenticated user.
    msg_id (str): ID of the Gmail message.
    att_id (str): ID of the attachment to download.
    filename (str): Filename to save the attachment.

    Returns:
    str: Path to the downloaded attachment.
    """
    att = service.users().messages().attachments().get(userId=user_id, messageId=msg_id, id=att_id).execute()
    data = att['data']
    file_data = base64.urlsafe_b64decode(data.encode('UTF-8'))
    
    path = os.path.join(configs.FILE_PATH, filename)
    with open(path, 'wb') as f:
        f.write(file_data)
    
    return path


def _load_previous_messages():
    """
    Helper to load previously processed messages from the file.

    Returns:
        set: A set of message IDs that have been processed before.
    """
    with open(configs.LIST_OF_PREVIOUS_MESSAGES_FILE_LOCATION, 'r') as f:
        return set(f.read().splitlines())


def _append_to_previous_messages(message_id):
    """
    Helper to append a new message ID to the file.

    Args:
        message_id (str): The ID of the message to be appended.
    """
    with open(configs.LIST_OF_PREVIOUS_MESSAGES_FILE_LOCATION, 'a') as f:
        f.write(f'{message_id}\n')


def _get_new_inreach_messages(auth_service, previous_messages):
    """
    Helper to retrieve new InReach messages that haven't been processed.

    Args:
        auth_service (obj): The authentication service object.
        previous_messages (set): A set of message IDs that have been processed before.

    Returns:
        set: A set of new message IDs that haven't been processed.
    """
    inreach_msgs = search_messages(auth_service, configs.SERVICE_EMAIL)
    inreach_msgs_ids = {msg['id'] for msg in inreach_msgs}
    
    return inreach_msgs_ids.difference(previous_messages)
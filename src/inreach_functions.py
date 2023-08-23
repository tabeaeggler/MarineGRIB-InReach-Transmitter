import numpy as np
import requests
import random
import time

import sys
sys.path.append(".")
from src import configs


def send_messages_to_inreach(url, gribmessage):
    """
    Splits the gribmessage and sends each part to InReach.

    Parameters:
    - url (str): The target URL for the InReach API.
    - gribmessage (str): The full message string to be split and sent.

    Returns:
    - list: A list of response objects from the InReach API for each sent message.
    """
    print('original message: ', gribmessage)
    message_parts = _split_message(gribmessage)
    responses = [_post_request_to_inreach(url, part) for part in message_parts]
    
    # Introducing a delay to prevent overwhelming the API
    time.sleep(configs.DELAY_BETWEEN_MESSAGES)
    
    return responses



######## HELPERS ########

def _split_message(gribmessage):
    """
    Splits a given grib message into chunks and encapsulates each chunk with its index.
    
    Args:
    gribmessage (str): The grib message that needs to be split into chunks.
    
    Returns:
    list: A list of formatted strings where each string has the format `index\nchunk\nindex`.
    """
    chunks = [gribmessage[i:i+configs.MESSAGE_SPLIT_LENGTH] for i in range(0, len(gribmessage), configs.MESSAGE_SPLIT_LENGTH)]
    return [f"{index}\n{chunk}\n{index}" for index, chunk in enumerate(chunks)]


def _post_request_to_inreach(url, message_str): 
    """
    Sends a post request with the message to the specified InReach URL.
    
    Args:
    url (str): The InReach endpoint URL to send the post request.
    message_str (str): The message string to be sent to InReach.
    
    Returns:
    Response: A Response object containing the server's response to the request.
    """
    guid = url.split('extId=')[1].split('&adr')[0]
    data = {
        'ReplyAddress': configs.GMAIL_ADDRESS,
        'ReplyMessage': message_str,
        'MessageId': str(random.randint(10000000, 99999999)),
        'Guid': guid,
    }
    
    response = requests.post(url, cookies=configs.INREACH_COOKIES, headers=configs.INREACH_HEADERS, data=data)
    if response.status_code == 200:
        print('Reply to InReach Sent:', message_str)
    else:
        print('Error sending part:', message_str)
        print(f'Status Code: {response.status_code}')
        print(f'Response Content: {response.content}')
        
    return response

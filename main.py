import emailfunctions
from base64 import urlsafe_b64decode
import time
from datetime import datetime
import pandas as pd
import xarray as xr
import numpy as np
import os
import requests
import random

LIST_OF_PREVIOUS_MESSAGES_FILE_LOCATION = "./prev_messages.txt"
GMAIL_EMAIL = "FILL IN"
SERVICE_EMAIL = "no.reply.inreach@garmin.com"
BASE_GARMIN_REPLY_URL = 'explore.garmin.com'
SAILDOCS_EMAIL_QUERY = "query@saildocs.com"
SAILDOCS_RESPONSE_EMAIL = "query-reply@saildocs.com"
INREACH_BASE_URL_POST_REQUEST_EUR = 'https://eur.explore.garmin.com/TextMessage/TxtMsg' 
INREACH_BASE_URL_POST_REQUEST_DEFAULT = 'https://explore.garmin.com/TextMessage/TxtMsg' 

INREACH_HEADERS = {
    'authority': 'explore.garmin.com',
    'accept': '*/*',
    'accept-language': 'en-US,en;q=0.9',
    'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
    'origin': 'https://explore.garmin.com',
    'sec-ch-ua': '"Chromium";v="106", "Not;A=Brand";v="99", "Google Chrome";v="106.0.5249.119"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-origin',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.0.0 Safari/537.36',
    'x-requested-with': 'XMLHttpRequest',
}

INREACH_COOKIES = {
    'BrowsingMode': 'Desktop',
}

def process_saildocs_grib_file(path):
    def get_unique_values_from_index(dataframe, level):
        """Get unique values from a multi-index dataframe based on the specified level."""
        return dataframe.index.get_level_values(level).unique()

    def get_difference(data):
        """Compute the difference between consecutive values and ensure uniqueness."""
        diff = pd.Series(data).diff().dropna().round(6).unique()
        return diff
    

    dataset = xr.open_dataset(path[0], engine='cfgrib')
    grib = dataset.to_dataframe()

    # Extracting unique timepoints, latitudes and longitudes
    try:
        grib = xr.open_dataset(path[0], engine='cfgrib').to_dataframe()
    except Exception as e:
        print(f"Error reading grib file: {e}")

    timepoints = get_unique_values_from_index(grib, 0)
    latitudes = get_unique_values_from_index(grib, 1)
    longitudes = get_unique_values_from_index(grib, 2)
    latmin, latmax = latitudes.min(), latitudes.max()
    lonmin, lonmax = longitudes.min(), longitudes.max()
    latdiff = get_difference(latitudes)
    londiff = get_difference(longitudes)
    gribtime = grib['time'].iloc[0]

    u_component = grib['u10']
    v_component = grib['v10']
    magnitude = np.sqrt(u_component ** 2 + v_component ** 2) * 1.94384 / 5

    # Calculating wind magnitude: grabs the U-component and V-component of wind speed, calculates the magnitude in kts, rounds to the nearest 5kt speed, and converts to binary.
    wind_magnitude = (
        (np.sqrt(grib['u10'] ** 2 + grib['v10'] ** 2) * 1.94384 / 5)
        .round()
        .astype('int')
        .clip(upper=15)
        .apply(lambda x: "{0:04b}".format(x))
        .str.cat()
    )
    #  Calculating wind direction: encodes the wind direction into 16 cardinal directions and converts to binary.
    wind_direction = (
        (((round(np.arctan2(grib['v10'], grib['u10']) / (2 * np.pi / 16))) + 16) % 16)
        .astype('int')
        .apply(lambda x: "{0:04b}".format(x))
        .str.cat()
    )

    # Cleaning up
    os.remove(path[0])

    return (wind_magnitude + wind_direction, timepoints, latmin, latmax, lonmin, lonmax, latdiff, londiff, gribtime)



def message_encoder_splitter(bin_data, timepoints, latmin, latmax, lonmin, lonmax, latdiff, londiff, gribtime, shift):
    """This function encodes the grib binary data into characters that can be sent over the inReach."""
    
    # Allowed inReach characters.
    inreach_chars = """!"#$%\'()*+,-./:;<=>?_¡£¥¿&¤0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyzÄÅÆÇÉÑØøÜßÖàäåæèéìñòöùüΔΦΓΛΩΠΨΣΘΞ"""
    
    # Extra two character codes to get a full range of 128 code possibilities.
    extra_chars = {122: '@!',123: '@@',124: '@#',125: '@$',126: '@%',127: '@?'}

    def encoder(binary_chunk, shift):
        """Encodes the binary 8-bit chunks into the coding scheme based on the SHIFT."""
        
        if len(binary_chunk) < 7:
            binary_chunk = binary_chunk + '0' * (7 - len(binary_chunk))
        
        new_chars = inreach_chars[shift:] + inreach_chars[:shift]
        decimal_value = int(binary_chunk, 2)
        
        return new_chars[decimal_value] if decimal_value < 122 else extra_chars[decimal_value]

    # Convert binary data into chunks and send them to the encoder.
    encoded_chunks = [encoder(bin_data[i:i+7], shift) for i in range(0, len(bin_data), 7)]
    encoded = ''.join(encoded_chunks)

    # Forming the message to be sent
    times = ",".join((timepoints / np.timedelta64(1, 'h')).astype('int').astype('str').to_list())
    iss = str(gribtime)
    minmax = ','.join(str(x) for x in [latmin, latmax, lonmin, lonmax])
    diff = str(latdiff[0]) + "," + str(londiff[0])
    data = encoded


    gribmessage = f"""{times}{iss}{minmax}{diff}{shift}{data}END"""
    msg_len = 130

    message_parts = [gribmessage[i:i+msg_len] for i in range(0, len(gribmessage), msg_len)]
    return [f"{part}\n{index}" if index > 0 else f"{index}\n{part}" for index, part in enumerate(message_parts)]



def send_reply_to_inreach(url, message_str):
    guid = url.split('extId=')[1].split('&adr')[0]
    data = {
        'ReplyAddress': GMAIL_EMAIL,
        'ReplyMessage': message_str,
        'MessageId': str(random.randint(10000000, 99999999)),
        'Guid': guid,
    }

    response = requests.post(url, cookies=INREACH_COOKIES, headers=INREACH_HEADERS, data=data)

    if response.status_code == 200:
        print('Reply to InReach Sent', message_str)
    else:
        print('Error!')
    return response



 
def answer_service(message_id, auth_service):
    msg_text, garmin_reply_url = fetch_message_text_and_url(message_id, auth_service)

    # check models
    if not msg_text.startswith(('ecmwf', 'gfs')):
        send_reply_to_inreach(garmin_reply_url, "Invalid model")
        return False

    # request saildocs grib data
    emailfunctions.send_message(auth_service, SAILDOCS_EMAIL_QUERY, "", "send " + msg_text)
    time_sent = datetime.utcnow()
    last_response = wait_for_saildocs_response(auth_service, time_sent)
    
    if not last_response:
        send_reply_to_inreach(garmin_reply_url, "Saildocs timeout")
        return False

    # process saildocs answer
    try:
        grib_path = emailfunctions.get_attachments(auth_service, last_response['id'])
    except:
        send_reply_to_inreach(garmin_reply_url, "Could not download attachment")
        return False

    bin_data, timepoints, latmin, latmax, lonmin, lonmax, latdiff, londiff, gribtime = process_saildocs_grib_file(grib_path)
    for shift in range(1, 10): 
        message_parts = message_encoder_splitter(bin_data, timepoints, latmin, latmax, lonmin, lonmax, latdiff, londiff, gribtime, shift)
        for part in message_parts:
            res = send_reply_to_inreach(garmin_reply_url, part)
            if res.status_code != 200:
                time.sleep(10)
                if part == message_parts[0]:
                    break
                else:
                    send_reply_to_inreach(garmin_reply_url, 'Message failed attempting shift')
                    break
            time.sleep(10)
        if res.status_code == 200:
            return True
    
    send_reply_to_inreach(garmin_reply_url, "All shifts failed")
    return False


def fetch_message_text_and_url(message_id, auth_service):
    """Fetches the message text and Garmin URL for the given message ID."""
    msg = auth_service.users().messages().get(userId='me', id=message_id).execute()
    msg_text = urlsafe_b64decode(msg['payload']['body']['data']).decode().split('\r')[0].lower()
    garmin_reply_url = next((x.replace('\r', '') for x in urlsafe_b64decode(msg['payload']['body']['data']).decode().split('\n') if BASE_GARMIN_REPLY_URL in x), None) # Grabs the unique Garmin URL for answering
    
    return msg_text, garmin_reply_url



def wait_for_saildocs_response(auth_service, time_sent):
    """Waits for a response and verifies if the response aligns with the request."""
    for _ in range(60):
        time.sleep(10)
        last_response = emailfunctions.search_messages(auth_service, SAILDOCS_RESPONSE_EMAIL)[0]
        time_received = pd.to_datetime(auth_service.users().messages().get(userId='me', id=last_response['id']).execute()['payload']['headers'][-1]['value'].split('(UTC)')[0])
        if time_received > time_sent:
            return last_response
    return None





##### Functions for checking and answering gmail emails #####
def _get_unanswered_inreach_messages(auth_service):
    inreach_msgs = emailfunctions.search_messages(auth_service, SERVICE_EMAIL)
    inreach_msgs_ids = [msg['id'] for msg in inreach_msgs]

    with open(LIST_OF_PREVIOUS_MESSAGES_FILE_LOCATION, 'r') as f:
        previous_messages = f.read().split('\n')
    
    return [msg_id for msg_id in inreach_msgs_ids if msg_id not in previous_messages]


def _record_inreach_message_as_answered(message_id):
    with open(LIST_OF_PREVIOUS_MESSAGES_FILE_LOCATION, 'a') as file:
        file.write(f'\n{message_id}')

        
def check_and_answer_mail(auth_service):
    unanswered_messages = _get_unanswered_inreach_messages(auth_service)
    
    for message_id in unanswered_messages:
        try:
            answer_service(message_id, auth_service)
            print(f"Successfully answered message {message_id}", flush=True)
        except Exception as e:
            print(f"Error answering message {message_id}: {e}", flush=True)
        finally:
            _record_inreach_message_as_answered(message_id)


if __name__ == "__main__":
    auth_service = emailfunctions.gmail_authenticate()
    
    # check emails every 1 minutes
    while True:
        print('Checking...', flush=True)
        check_and_answer_mail(auth_service)
        time.sleep(60)
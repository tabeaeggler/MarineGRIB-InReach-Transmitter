import numpy as np
import requests
import random
import configs


ALLOWED_CHARS = """!"#$%\'()*+,-./:;<=>?_¡£¥¿&¤0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyzÄÅÆÇÉÑØøÜßÖàäåæèéìñòöùüΔΦΓΛΩΠΨΣΘΞ"""
EXTRA_CHARS = {122: '@!', 123: '@@', 124: '@#', 125: '@$', 126: '@%', 127: '@?'}


def message_encoder_splitter(bin_data, timepoints, latmin, latmax, lonmin, lonmax, latdiff, londiff, gribtime, shift):
    """
    Encodes grib binary data into characters suitable for inReach transmission.

    Parameters:
    - bin_data (str): Binary representation of grib data.
    - timepoints (list): List of timepoints.
    - latmin, latmax, lonmin, lonmax (float): Latitude and Longitude boundaries.
    - latdiff, londiff (list): Latitude and Longitude differences.
    - gribtime (str): The time associated with the grib data.
    - shift (int): The number of positions each character should be shifted during encoding.

    Returns:
    - list: A list of encoded message parts.
    """
    
    encoded_chunks = [_encoder(bin_data[i:i+7], shift) for i in range(0, len(bin_data), 7)]
    encoded = ''.join(encoded_chunks)

    times = ",".join((timepoints / np.timedelta64(1, 'h')).astype('int').astype('str').tolist())
    minmax = ','.join(str(x) for x in [latmin, latmax, lonmin, lonmax])
    diff = f"{latdiff[0]},{londiff[0]}"
    data = encoded
    gribmessage = f"{times}{gribtime}{minmax}{diff}{shift}{data}END"
    
    msg_len = 120
    message_parts = [gribmessage[i:i+msg_len] for i in range(0, len(gribmessage), msg_len)]
    
    return [f"{part}\n{index}" if index > 0 else f"{index}\n{part}" for index, part in enumerate(message_parts)]



def send_reply_to_inreach(url, message_str):
    """
    Sends a message string as a reply to a given inReach URL.

    Parameters:
    - url (str): The inReach URL to which the reply should be sent.
    - message_str (str): The message content to be sent as a reply.

    Returns:
    - requests.Response: The response object from the POST request to the inReach service.
    """
    
    guid = url.split('extId=')[1].split('&adr')[0]
    data = {
        'ReplyAddress': configs.GMAIL_EMAIL,
        'ReplyMessage': message_str,
        'MessageId': str(random.randint(10000000, 99999999)),
        'Guid': guid,
    }
    
    response = requests.post(url, cookies=configs.INREACH_COOKIES, headers=configs.INREACH_HEADERS, data=data)

    if response.status_code == 200:
        print('Reply to InReach Sent', message_str)
    else:
        print('Error!')
    
    return response




######## HELPERS ########

def _encoder(binary_chunk, shift):
    """
    Helper to encode a binary chunk using a specified shift on ALLOWED_CHARS.

    Parameters:
    - binary_chunk (str): A string representation of the binary data to be encoded.
    - shift (int): The number of positions each character in ALLOWED_CHARS should be shifted.

    Returns:
    - str: Encoded representation of the binary_chunk.
    """
    
    if len(binary_chunk) < 7:
        binary_chunk = binary_chunk + '0' * (7 - len(binary_chunk))

    new_chars = ALLOWED_CHARS[shift:] + ALLOWED_CHARS[:shift]
    decimal_value = int(binary_chunk, 2)
    
    return new_chars[decimal_value] if decimal_value < 122 else EXTRA_CHARS[decimal_value]
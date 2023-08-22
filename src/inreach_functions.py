import numpy as np
import requests
import random


import configs as configs
import gmail_functions as gmail_func



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
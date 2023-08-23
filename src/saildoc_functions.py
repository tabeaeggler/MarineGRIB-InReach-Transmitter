import time
import pandas as pd
import xarray as xr
import numpy as np
import os
import base64

import sys
sys.path.append(".")
from src import configs
from src import email_functions as email_func


def encode_saildocs_grib_file(file_path):
    """
    Encodes the content of a GRIB file into a base64 string.
    
    Args:
    file_path (str): Path to the GRIB file that needs to be encoded.
    
    Returns:
    str: Base64 encoded string representation of the GRIB file content.
    """
    
    # Open the file in binary read mode and read its content
    with open(file_path, 'rb') as file:
        grib_binary = file.read()

    # Convert the binary content to a base64 encoded string
    encoded_data = base64.b64encode(grib_binary).decode('utf-8')

    return encoded_data


def wait_for_saildocs_response(auth_service, time_sent):
    """Wait for a SailDocs response and verify if the response matches the request timestamp.
    
    Args:
    auth_service: Authenticated Gmail API service instance.
    time_sent (datetime): Timestamp of the SailDocs request.

    Returns:
    dict or None: Returns the latest email response or None if no valid response is received within the timeout.
    """
    for _ in range(60):
        time.sleep(10)
        last_response = email_func.search_messages(auth_service, configs.SAILDOCS_RESPONSE_EMAIL)[0]
        time_received = pd.to_datetime(auth_service.users().messages().get(userId='me', id=last_response['id']).execute()['payload']['headers'][-1]['value'].split('(UTC)')[0])
        if time_received > time_sent:
            return last_response
    return None


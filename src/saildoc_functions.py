import time
import pandas as pd
import xarray as xr
import numpy as np
import os

import configs as configs
import email_functions as email_func


def process_saildocs_grib_file(path):
    """Process the SailDocs GRIB file, extract wind magnitude and direction information.
    
    Args:
    path (str): Path to the GRIB file.

    Returns:
    tuple: Comprises wind data in binary format, timepoints, and geolocation details.
    """

    dataset = xr.open_dataset(path[0], engine='cfgrib')
    grib = dataset.to_dataframe()

    # Extracting unique timepoints, latitudes and longitudes
    try:
        grib = xr.open_dataset(path[0], engine='cfgrib').to_dataframe()
    except Exception as e:
        print(f"Error reading grib file: {e}")

    timepoints = _get_unique_values_from_index(grib, 0)
    latitudes = _get_unique_values_from_index(grib, 1)
    longitudes = _get_unique_values_from_index(grib, 2)
    latmin, latmax = latitudes.min(), latitudes.max()
    lonmin, lonmax = longitudes.min(), longitudes.max()
    latdiff = _get_difference(latitudes)
    londiff = _get_difference(longitudes)
    gribtime = grib['time'].iloc[0]

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

    # Clean up: remove the GRIB file after processing
    os.remove(path[0])

    return (wind_magnitude + wind_direction, timepoints, latmin, latmax, lonmin, lonmax, latdiff, londiff, gribtime)



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




######## HELPERS ########

def _get_unique_values_from_index(dataframe, level):
    """Helper to get unique values from a multi-index dataframe based on the specified level."""
    return dataframe.index.get_level_values(level).unique()

def _get_difference(data):
    """Helper to compute the difference between consecutive values and ensure uniqueness."""
    diff = pd.Series(data).diff().dropna().round(6).unique()
    return diff
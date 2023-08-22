from base64 import urlsafe_b64decode
import time
from datetime import datetime

import configs as configs
import email_functions as email_func
import saildoc_functions as saildoc_func
import inreach_functions as inreach_func


def answer_service(message_id, auth_service):
    """
    Process the given message ID: validate its content, fetch necessary data, 
    and send back the appropriate response.

    Args:
        message_id (str): The ID of the message to process.
        auth_service (obj): The authentication service object.

    Returns:
        bool: True if the operation succeeded, False otherwise.
    """
    
    msg_text, garmin_reply_url = _fetch_message_text_and_url(message_id, auth_service)

    # Check the model in the message
    if not msg_text.startswith(('ecmwf', 'gfs')):
        inreach_func.send_reply_to_inreach(garmin_reply_url, "Invalid model")
        return False

    # Request saildocs grib data
    email_func.send_message(auth_service, configs.SAILDOCS_EMAIL_QUERY, "", "send " + msg_text)
    time_sent = datetime.utcnow()
    last_response = saildoc_func.wait_for_saildocs_response(auth_service, time_sent)
    
    if not last_response:
        inreach_func.send_reply_to_inreach(garmin_reply_url, "Saildocs timeout")
        return False

    # Process the saildocs response
    try:
        grib_path = email_func.get_attachments(auth_service, last_response['id'])
    except:
        inreach_func.send_reply_to_inreach(garmin_reply_url, "Could not download attachment")
        return False

    bin_data, timepoints, latmin, latmax, lonmin, lonmax, latdiff, londiff, gribtime = saildoc_func.process_saildocs_grib_file(grib_path)
    for shift in range(1, 10): 
        message_parts = inreach_func.message_encoder_splitter(bin_data, timepoints, latmin, latmax, lonmin, lonmax, latdiff, londiff, gribtime, shift)
        for part in message_parts:
            res = inreach_func.send_reply_to_inreach(garmin_reply_url, part)
            if res.status_code != 200:
                time.sleep(10)
                if part == message_parts[0]:
                    break
                else:
                    inreach_func.send_reply_to_inreach(garmin_reply_url, 'Message failed attempting shift')
                    break
            time.sleep(10)
        if res.status_code == 200:
            return True
    
    inreach_func.send_reply_to_inreach(garmin_reply_url, "All shifts failed")
    return False


def _fetch_message_text_and_url(message_id, auth_service):
    """
    Retrieve the content of a message and extract the text and reply URL.

    Args:
        message_id (str): The ID of the message to retrieve.
        auth_service (obj): The authentication service object.

    Returns:
        tuple: The extracted message text and Garmin reply URL.
    """
    msg = auth_service.users().messages().get(userId='me', id=message_id).execute()
    msg_text = urlsafe_b64decode(msg['payload']['body']['data']).decode().split('\r')[0].lower()
    garmin_reply_url = next((x.replace('\r', '') for x in urlsafe_b64decode(msg['payload']['body']['data']).decode().split('\n') if configs.BASE_GARMIN_REPLY_URL in x), None)
    
    return msg_text, garmin_reply_url



if __name__ == "__main__":
    auth_service = email_func.gmail_authenticate()
    
    # check emails every 3 minutes
    while True:
        print('Checking...', flush=True)
        email_func.check_and_answer_mail(auth_service)
        time.sleep(60)

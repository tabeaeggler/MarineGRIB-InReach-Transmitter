import time
import sys

sys.path.append(".")
from src import email_functions as email_func
from src import saildoc_functions as saildoc_func
from src import inreach_functions as inreach_func
from src import chatgpt_functions as chatgpt_func

if __name__ == "__main__":
    # authenticate Gmail API
    auth_service = email_func.gmail_authenticate()

    # check for new InReach messages every minute
    while True:
        print('Checking...', flush=True)
        
        # check and fetch new messages
        new_msg = email_func.fetch_message_text_and_url(auth_service)

        # check if new message
        if new_msg is not None:
            msg_text, msg_id, garmin_reply_url = new_msg
            print("New msg received")

            # check whether it is a GRIB or CHATGPT request
            if msg_text.startswith("gpt"):
                print("gpt1")
                # chatgpt request
                encoded_file = chatgpt_func.generate_gpt_response(msg_text)
                        
            else:  
                # GRIB request
                print("grib1")
                result = email_func.request_and_process_saildocs_grib(msg_id, auth_service, msg_text, garmin_reply_url)
                if result is not None:
                    grib_path, garmin_reply_url = result
                encoded_file = saildoc_func.encode_saildocs_grib_file(grib_path)

            # send the encoded file to InReach
            inreach_func.send_messages_to_inreach(garmin_reply_url, encoded_file)

        else:
            # No new message, so wait 60 seconds and start the loop again
            print("No new message. Waiting for 60 seconds...", flush=True)
            time.sleep(60)




             
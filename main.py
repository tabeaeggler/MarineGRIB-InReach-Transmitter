from base64 import urlsafe_b64decode
import time
from datetime import datetime

import sys
sys.path.append(".")
from src import email_functions as email_func



if __name__ == "__main__":
    auth_service = email_func.gmail_authenticate()
    
    # check emails every 1 minutes
    while True:
        print('Checking...', flush=True)
        email_func.handle_new_inreach_messages(auth_service)
        time.sleep(60)

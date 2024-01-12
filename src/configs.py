# Paths
TOKEN_PATH = './token.pickle'
CREDENTIALS_PATH = './credentials.json'
FILE_PATH = './files/attachments'
LIST_OF_PREVIOUS_MESSAGES_FILE_LOCATION = "./files/prev_messages.txt"

# GMAIL permissions: set full access permission scope (https://developers.google.com/gmail/api/auth/scopes)
SCOPES = ['https://mail.google.com/']

# E-Mails and Links
GMAIL_ADDRESS = "FILL IN"
SERVICE_EMAIL = "no.reply.inreach@garmin.com"
BASE_GARMIN_REPLY_URL = 'explore.garmin.com'
SAILDOCS_EMAIL_QUERY = "query@saildocs.com"
SAILDOCS_RESPONSE_EMAIL = "query-reply@saildocs.com"
INREACH_BASE_URL_POST_REQUEST_EUR = 'https://eur.explore.garmin.com/TextMessage/TxtMsg' 
INREACH_BASE_URL_POST_REQUEST_DEFAULT = 'https://explore.garmin.com/TextMessage/TxtMsg' 

# E-Mail Headers
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

# Others
MESSAGE_SPLIT_LENGTH = 120 # Save length as the message got cut sometimes
DELAY_BETWEEN_MESSAGES = 5

#chatgpt API
OPEN_AI_KEY = "FILL IN"
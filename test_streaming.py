import logging
from contextlib import suppress
from pprint import pprint

import requests
from faker import Faker

logging.basicConfig(level=logging.DEBUG)

logger = logging.getLogger("test")
info = logging.info
debug = logging.debug
warn = logging.warn

fake = Faker()

BASE_URL = "http://127.0.0.1:8000"
QUERY_URL = BASE_URL + "/chat?stream=true"
STREAM_URL = BASE_URL + "/chat/stream/{chat_id}"
AUTH_TOKEN = ""  # noqa: E501

info("started")
debug("creating account...")
payload = {
    "first_name": fake.first_name(),
    "last_name": fake.first_name(),
    "email": fake.email(),
    "password": fake.password(),
}
response = requests.post(f"{BASE_URL}/auth/signup", json=payload)
response.raise_for_status()

debug("signing in...")
del payload["first_name"]
del payload["last_name"]
payload["login"] = payload.pop("email")
response = requests.post(f"{BASE_URL}/auth/login", json=payload)
response.raise_for_status()
pprint(response.json())
exit()
AUTH_TOKEN = response.json()["auth_info"]["atoken"]

debug("sending query")
for i in range(10):
    response = requests.post(
        QUERY_URL,
        json={"query": "hi"},
        headers={"Authorization": f"Bearer {AUTH_TOKEN}"},
    )
    debug("response recieved")
    response.raise_for_status()
    json = response.json()
    debug(json)
    info("1st read")
    debug("reading stream")
    chat_id = response.json()["chat"]["id"]
    response = requests.get(
        STREAM_URL.format(chat_id=chat_id),
        stream=True,
        headers={"Authorization": f"Bearer {AUTH_TOKEN}"},
    )
    response.raise_for_status()
    count = 0
    undecoded_bytes = b""
    for token in response.iter_content():
        try:
            print(token.decode(), end="", flush=True)
        except UnicodeDecodeError:
            undecoded_bytes += token
            with suppress(UnicodeDecodeError):
                print(undecoded_bytes.decode(), end="", flush=True)
                undecoded_bytes = b""
        count += 1
    info(f"\n{count} tokens received")

# info("2nd read")
# debug("reading stream")
# response = requests.get(
#     STREAM_URL.format(chat_id=chat_id),
#     stream=True,
#     headers={"Authorization": f"Bearer {AUTH_TOKEN}"},
# )
# response.raise_for_status()
# count = 0
# for token in response.iter_content():
#     try:
#         print(token.decode(), end="", flush=True)
#     except UnicodeDecodeError:
#         undecoded_bytes += token
#         with suppress(UnicodeDecodeError):
#             print(undecoded_bytes.decode(), end="", flush=True)
#             undecoded_bytes = b""
#     count += 1
# info(f"\n{count} tokens received")

import os

SUPPORT_CHAT_ID = int(os.getenv("SUPPORT_CHAT_ID"))
IGNORE_USERS = list(
    map(int, os.getenv("IGNORE_USERS", "").split(",")))
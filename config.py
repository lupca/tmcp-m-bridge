import os
from dotenv import load_dotenv

load_dotenv()

POCKETBASE_URL = os.getenv("POCKETBASE_URL", "http://127.0.0.1:8090")
POCKETBASE_USER = os.getenv("POCKETBASE_USER", "admin@admin.com")
POCKETBASE_PASSWORD = os.getenv("POCKETBASE_PASSWORD", "123qweasdzxc")

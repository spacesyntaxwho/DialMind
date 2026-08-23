import os

from dotenv import load_dotenv
from calle import CalleClient

load_dotenv()

api_key = os.getenv("CALLE_API_KEY")

if not api_key:
    raise RuntimeError("CALLE_API_KEY is not set")

client = CalleClient(api_key=api_key)

print("CALL-E client initialized successfully!")
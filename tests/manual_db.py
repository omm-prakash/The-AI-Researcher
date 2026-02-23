import psycopg, os
from dotenv import load_dotenv
load_dotenv()
url = os.getenv("DATABASE_URL")
try:
    with psycopg.connect(url) as conn:
        print("Success")
except Exception as e:
    print(e)

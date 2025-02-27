from os import getenv
from dotenv import load_dotenv

load_dotenv(override=True)

DATABASE_URL = getenv("DATABASE_URL")
COOKIE_KEY =getenv("COOKIE_KEY")
SMTP_HOST = getenv("SMTP_HOST")
SMTP_PORT =getenv("SMTP_PORT")
SMTP_PASSWORD =getenv("SMTP_PASSWORD")
FROM_EMAIL =getenv("FROM_EMAIL")
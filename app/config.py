import os

from dotenv import load_dotenv

# Reads the .env file into the process environment.
# Must run BEFORE any os.getenv() call below.
load_dotenv()


class Config:
    # Credentials come from .env and are never written in the code,
    # because the code goes to GitHub and the credentials do not.
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL")

    # Turns off an SQLAlchemy signal system we do not use.
    # It only adds memory overhead.
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # No default for DATABASE_URL on purpose: if it is missing, the app
    # should fail loudly instead of connecting somewhere unexpected.
    SECRET_KEY = os.getenv("SECRET_KEY", "dev")
import os
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

def _get_bearer():
    return os.getenv('BEARER')

def create_headers():
    # handle oauth for user privileged data
    return {"Authorization": "Bearer {}".format(_get_bearer())}

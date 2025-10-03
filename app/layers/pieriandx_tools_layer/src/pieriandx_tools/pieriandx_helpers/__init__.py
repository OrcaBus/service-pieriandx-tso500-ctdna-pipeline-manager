#!/usr/bin/env python3

"""
Use low-level pyriandx commands
"""

# Standard imports
from typing import Optional, Dict
from os import environ
import logging
import json
from time import sleep
from copy import copy

# Custom imports
from pyriandx.client import Client

# Other layers
from orcabus_api_tools.utils.aws_helpers import get_ssm_value, get_secret_value

# Set logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Globals
PIERIANDX_EMAIL = None
PIERIANDX_TOKEN = None
PIERIANDX_INSTITUTION = None
PIERIANDX_BASE_URL = None


def get_pieriandx_email():
    global PIERIANDX_EMAIL
    if PIERIANDX_EMAIL is None:
        PIERIANDX_EMAIL = get_ssm_value(environ.get("PIERIANDX_USER_EMAIL_SSM_PARAMETER_NAME", None))
    return PIERIANDX_EMAIL


def get_token():
    global PIERIANDX_TOKEN
    if PIERIANDX_TOKEN is None:
        PIERIANDX_TOKEN = get_pieriandx_auth_token()
    return PIERIANDX_TOKEN


def get_institution():
    global PIERIANDX_INSTITUTION
    if PIERIANDX_INSTITUTION is None:
        PIERIANDX_INSTITUTION = get_ssm_value(environ.get("PIERIANDX_INSTITUTION_SSM_PARAMETER_NAME", None))
    return PIERIANDX_INSTITUTION


def get_base_url():
    global PIERIANDX_BASE_URL
    if PIERIANDX_BASE_URL is None:
        PIERIANDX_BASE_URL = get_ssm_value(environ.get("PIERIANDX_BASE_URL_SSM_PARAMETER_NAME", None))
    return PIERIANDX_BASE_URL


def get_pieriandx_auth_token() -> str:
    # Local relative imports
    from ..aws_helpers.lambda_helpers import run_lambda_function

    # Collect token
    collection_token_lambda = environ.get("PIERIANDX_COLLECT_AUTH_TOKEN_LAMBDA_NAME")

    # Run lambda to get token
    auth_token = run_lambda_function(collection_token_lambda, "")

    while (
            auth_token is None or
            auth_token == 'null' or
            json.loads(auth_token).get("auth_token") is None
    ):
        sleep(5)
        auth_token = run_lambda_function(collection_token_lambda, "")

    return json.loads(auth_token).get("auth_token")


def get_pieriandx_s3_access_credentials() -> Dict:
    secret_id = environ.get("PIERIANDX_S3_ACCESS_CREDENTIALS_SECRET_ID")

    access_credentials = get_secret_value(secret_id)

    access_credentials_dict = json.loads(access_credentials)

    for key in copy(access_credentials_dict).keys():
        access_credentials_dict[key.replace("s3", "aws").upper()] = access_credentials_dict.pop(key)

    return access_credentials_dict


def get_pieriandx_client(
    email: Optional[str] = None,
    token: Optional[str] = None,
    institution: Optional[str] = None,
    base_url: Optional[str] = None,
) -> Client:
    """
    Get the pieriandx client, validate environment variables
    PIERIANDX_BASE_URL
    PIERIANDX_INSTITUTION
    PIERIANDX_USER_EMAIL
    PIERIANDX_USER_AUTH_TOKEN
    :return:
    """

    # Check env vars
    if email is None:
        email = get_pieriandx_email()

    if token is None:
        token = get_pieriandx_auth_token()

    if institution is None:
        institution = get_institution()

    if base_url is None:
        base_url = get_base_url()

    return Client(
        email=email,
        key=token,
        institution=institution,
        base_url=base_url,
        key_is_auth_token=True
    )

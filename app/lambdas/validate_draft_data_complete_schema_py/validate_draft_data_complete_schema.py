#!/usr/bin/env python3

"""
Download the draft schema, validate it against the current schema, and print the results.
"""

# Imports
import json
import boto3
import typing
import jsonschema
from os import environ
from typing import Dict
import logging
from jsonschema import ValidationError
from pathlib import Path

# Type checking imports
if typing.TYPE_CHECKING:
    from mypy_boto3_schemas import SchemasClient
    from mypy_boto3_ssm import SSMClient

# Globals
SSM_REGISTRY_NAME_ENV_VAR = "SSM_REGISTRY_NAME"
SSM_SCHEMA_PATH_ENV_VAR = "SSM_SCHEMA_PATH"
DEFAULT_PAYLOAD_VERSION_ENV_VAR = "DEFAULT_PAYLOAD_VERSION"

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def get_ssm_parameter_value(parameter_name: str) -> str:
    """
    Get the SSM parameter for the schema.
    :return: The SSM parameter value.
    """

    # Get the ssm client
    ssm_client: SSMClient = boto3.client("ssm")

    # Get the SSM parameter value
    response = ssm_client.get_parameter(
        Name=parameter_name,
        WithDecryption=True
    )

    return response["Parameter"]["Value"]


def get_schema_from_registry(
        registry_name: str,
        schema_name: str
) -> str:
    """
    Get the schema from the schema registry.
    :param registry_name: The name of the schema registry.
    :param schema_name: The name of the schema.
    :return: The schema as a string.
    """

    # Get the schemas client
    schemas_client: SchemasClient = boto3.client("schemas")

    # Get the schema from the registry
    response = schemas_client.describe_schema(
        RegistryName=registry_name,
        SchemaName=schema_name
    )

    return response["Content"]


def validate_draft_schema(
        json_schema: str,
        json_body: str
) -> bool:
    """
    Download the draft schema, validate it against the current schema, and print the results.
    """
    try:
        jsonschema.validate(
            instance=json.loads(json_body),
            schema=json.loads(json_schema)
        )
    except ValidationError as e:
        logger.info("Validation error: %s", e)
        return False
    return True


def handler(event, context) -> Dict[str, bool]:
    """
    Given a draft schema, validate it against the current schema and print the results.

    Input:
      {
        "data": { ... },              # The data payload to validate
        "payloadVersion": "2025.09.25"  # Optional, defaults to DEFAULT_PAYLOAD_VERSION
      }

    Output:
      {"isValid": true}   — validation passes
      {"isValid": false}  — validation fails
    """
    # Get the event data
    payload_version = event.get("payloadVersion", environ[DEFAULT_PAYLOAD_VERSION_ENV_VAR])
    payload_data = event.get('data', event)

    # Get the SSM parameters
    schema_registry = get_ssm_parameter_value(environ[SSM_REGISTRY_NAME_ENV_VAR])
    schema_name = json.loads(get_ssm_parameter_value(
        str(Path(environ[SSM_SCHEMA_PATH_ENV_VAR]) / payload_version)
    ))['schemaName']

    # Get the current schema from the schema registry
    current_schema = get_schema_from_registry(
        registry_name=schema_registry,
        schema_name=schema_name
    )

    # Validate the draft schema against the current schema
    return {
        "isValid": validate_draft_schema(
            current_schema,
            json.dumps(payload_data)
        )
    }


# if __name__ == "__main__":
#     from os import environ
#     import json
#     environ['AWS_PROFILE'] = 'umccr-development'
#     environ["SSM_REGISTRY_NAME"] = '/orcabus/workflows/pieriandx-tso500-ctdna/schemas/registry'
#     environ["SSM_SCHEMA_PATH"] = '/orcabus/workflows/pieriandx-tso500-ctdna/schemas/complete-data-draft'
#     environ["DEFAULT_PAYLOAD_VERSION"] = '2025.09.25'
#     print(json.dumps(
#         handler({"data": {}, "payloadVersion": "2025.09.25"}, None),
#         indent=4
#     ))

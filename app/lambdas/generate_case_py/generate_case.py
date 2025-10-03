#!/usr/bin/env python

"""
Generate a case from a case object

Environment variables
PIERIANDX_COLLECT_AUTH_TOKEN_LAMBDA_NAME: The secret name for the PierianDx Auth Token 'PierianDx/JwtKey'
PIERIANDX_USER_EMAIL:
PIERIANDX_INSTITUTION
PIERIANDX_BASE_URL

A Case object will look like this

{
    "identified": true,
    "indication": "indication",
    "panelName": "panelname",
    "sampleType": "patientcare",
    "specimens": [
      {
        "accessionNumber": "caseaccessionnumber",
        "dateAccessioned": "2021-01-01TZ:00+Z",
        "dateReceived": "2021-01-01TZ:00+Z",
        "datecollected": "2021-01-01TZ:00+Z",
        "externalSpecimenId": "externalspecimenid",
        "name": "panelspecimenscheme",
        "type": {
          "code": "specimentypecode",
          "label": "specimentypelabel"
        },
        "firstName": "John",
        "lastName": "Doe",
        "dateOfBirth": "1970-01-01",
        "medicalRecordNumbers": [
          {
            "mrn": "mrn",
            "medicalFacility": {
              "facility": "facility",
              "hospitalNumber": "hospitalnumber"
            }
          }
        ]
      }
    ],
    "dagDescription": "dagdescription",
    "dagName": "dagname",
    "disease": {
      "code": "diseasecode",
      "label": "diseaselabel"
    },
    "physicians": [
      {
        "firstName": "Meredith",
        "lastName": "Gray"
      }
    ]
    }
"""

# Standard imports
import logging
from requests import Response, HTTPError

# Layer imports
from pieriandx_tools.pieriandx_helpers import get_pieriandx_client
from pieriandx_tools.pieriandx_models.case_creation import CaseCreationDictType


def handler(event, context):
    pyriandx_client = get_pieriandx_client()
    case_creation_obj: CaseCreationDictType = event.get("caseCreationObj", {})

    try:
        response: Response = pyriandx_client._post_api(
            endpoint="/case",
            data=case_creation_obj
        )
        response.raise_for_status()
    except HTTPError as e:
        logging.error(f"Failed to create case: {e}")
        # raise Exception(f"Failed to create case: {e}")

    if response.status_code != 200:
        logging.error(f"Failed to create case: {response.json()}")
        raise Exception(f"Failed to create case: {response.json()}")

    return {
        "caseObj": response.json()
    }

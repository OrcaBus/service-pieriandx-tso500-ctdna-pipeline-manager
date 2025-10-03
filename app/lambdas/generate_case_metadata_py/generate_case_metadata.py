#!/usr/bin/env python3

"""
Return payload of de-identified case metadata

Payload will look a bit like this:

{
  "isIdentified": false,
  "caseAccessionNumber": "SBJ04407__L2400161__V2__abcd1238",
  "externalSpecimenId": "externalspecimenid",
  "sampleType": "PatientCare",
  "specimenLabel": "primarySpecimen",
  "indication": "Test",
  "diseaseCode": 64572001,
  "specimenCode": 122561005,
  "sampleReception": {
    "dateAccessioned": "2021-01-01T00:00:00Z",
    "dateCollected": "2024-02-20T20:17:00Z",
    "dateReceived": "2021-01-01T00:00:00Z"
  },
  "study": {
    "id": "studyid",
    "subjectIdentifier": "subject"
  }
}

"""

# Standard Imports
from typing import Dict
from urllib.error import HTTPError

import pytz
from datetime import datetime
import logging
import pandas as pd

# Layer imports
from orcabus_api_tools.metadata import get_library_from_library_id
from orcabus_api_tools.metadata.models import Library
from pieriandx_tools.pieriandx_helpers import get_pieriandx_client


# Set logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Globals
AUS_TIMEZONE = pytz.timezone("Australia/Melbourne")
AUS_TIME = datetime.now(AUS_TIMEZONE)
AUS_TIME_AS_STR = f"{AUS_TIME.date().isoformat()}T{AUS_TIME.time().isoformat(timespec='seconds')}{AUS_TIME.strftime('%z')}"

DEFAULT_INDICATION = "NA"
DEFAULT_REQUESTING_PHYSICIAN = {
    "first_name": "Sean",
    "last_name": "Grimmond"
}
DEFAULT_HOSPITAL_NUMBER = "99"
DEFAULT_SPECIMEN_CODE = '122561005'
DEFAULT_SPECIMEN_LABEL = 'primarySpecimen'


def handler(event, context) -> Dict:
    # Return payload of case metadata
    library_id = event["libraryId"]

    # Get redcap information from the event
    # For deidentified samples, we only need to
    redcap_dict = event.get("redcapData", None)
    if redcap_dict is None:
        redcap_dict = {}

    # Generate the case accession number
    counter = 1
    while True:
        case_accession_number = f"{library_id}_{str(counter).zfill(3)}"
        # Check if the case accession number exists in PierianDx
        response = get_pieriandx_client()._get_api(
            endpoint=f"/case",
            params={
                "accessionNumber": case_accession_number,
            }
        )

        if response is None:
            break
        counter += 1

    # Get the external specimen id from the event
    library_obj: Library = get_library_from_library_id(library_id)
    external_sample_id = library_obj['sample']['externalSampleId']
    external_subject_id = library_obj['subject']['subjectId']
    project_id = library_obj['projectSet'][0]['projectId']

    # Get the sample type from the event
    sample_type = event.get("sampleType")
    # Sample type might also be in the redcap data, which should take priority
    sample_type = redcap_dict.get("sampleType", sample_type)

    # Get the specimen label from the event
    specimen_label = event.get("specimenLabel", DEFAULT_SPECIMEN_LABEL)

    # Get the indication from the event
    indication = event.get("indication", DEFAULT_INDICATION)

    # Get the specimen code from the event
    specimen_code = event.get("specimenCode", DEFAULT_SPECIMEN_CODE)

    # Get the sample reception from the redcap data if it exists
    date_accessioned = pd.to_datetime(redcap_dict.get("dateAccessioned", AUS_TIME_AS_STR)).astimezone(AUS_TIMEZONE)
    date_collected = pd.to_datetime(redcap_dict.get("dateCollected", AUS_TIME_AS_STR)).astimezone(AUS_TIMEZONE)
    date_received = pd.to_datetime(redcap_dict.get("dateReceived", AUS_TIME_AS_STR)).astimezone(AUS_TIMEZONE)

    # Set the sample reception dictionary
    # Set as camel case for event type
    sample_reception = {
        "dateAccessioned": date_accessioned.isoformat(timespec='seconds'),
        "dateCollected": date_collected.isoformat(timespec='seconds'),
        "dateReceived": date_received.isoformat(timespec='seconds'),
    }

    # Get the disease code from the event if it exists or
    disease_code = event.get("defaultSnomedDiseaseCode", None)
    disease_code = redcap_dict.get("diseaseId", disease_code)

    # Determine if the case is 'identified' or not
    is_identifed = event.get("isIdentified", False)

    if not is_identifed:
        # Return the payload with the study information
        return {
            "caseMetadata": {
                "isIdentified": False,
                "caseAccessionNumber": case_accession_number,
                "externalSpecimenId": external_sample_id,
                "sampleType": sample_type,
                "specimenLabel": specimen_label,
                "indication": indication,
                "diseaseCode": disease_code,
                "specimenCode": specimen_code,
                "sampleReception": sample_reception,
                "study": {
                    "id": project_id,
                    "subjectIdentifier": external_subject_id
                }
            }
        }

    # Identified case, we need patient info, medical record numbers and requesting physician
    # Get patient information from redcap
    if redcap_dict is not None:
        patient_information = {
            "dateOfBirth": "1970-01-01",
            "firstName": (
                "Jane"
                if (
                        redcap_dict.get("gender", None) is not None and
                        redcap_dict.get("gender") == "female"
                )
                else "John"
            ),
            "lastName": "Doe"
        }
    else:
        patient_information = {
            "dateOfBirth": "1970-01-01",
            "firstName": "John",
            "lastName": "Doe"
        }

    # Get medical record numbers from redcap
    medical_record_numbers = {
        "mrn": external_subject_id,
        "medicalFacility": {
            "facility": "Not Available",
            "hospitalNumber": DEFAULT_HOSPITAL_NUMBER
        }
    }

    # Get requesting physician from redcap
    requesting_physician = {
        "firstName": redcap_dict.get("requesting_physician_first_name", DEFAULT_REQUESTING_PHYSICIAN["first_name"]),
        "lastName": redcap_dict.get("requesting_physician_last_name", DEFAULT_REQUESTING_PHYSICIAN["last_name"])
    }

    # Return the payload
    return {
        "caseMetadata": {
            "isIdentified": True,
            "caseAccessionNumber": case_accession_number,
            "externalSpecimenId": external_sample_id,
            "sampleType": sample_type,
            "specimenLabel": specimen_label,
            "indication": indication,
            "diseaseCode": disease_code,
            "specimenCode": specimen_code,
            "sampleReception": sample_reception,
            "patientInformation": patient_information,
            "medicalRecordNumbers": medical_record_numbers,
            "requestingPhysician": requesting_physician
        }
    }

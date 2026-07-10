#!/usr/bin/env python3

"""
Post-schema validation for PierianDx TSO500 ctDNA pipeline manager.

Unlike ICAv2-based pipeline managers, this service does NOT have standard ICAv2 engine parameters
(projectId, pipelineId, outputUri, logsUri). Instead, it uses the PierianDx CGW API as its
execution backend.

This Lambda validates PierianDx-specific requirements:
  - Validates that data.tags has required fields (libraryId, sampleType, panelVersion, etc.)
  - Validates that data.inputs.caseMetadata is well-formed when present
  - Validates that data.inputs.dataFiles contains expected file keys when present
  - Writes descriptive failure comments via the OrcaBus API on failure
  - Returns {"isValid": true} when all checks pass, {"isValid": false} otherwise
"""

# Imports
from typing import Dict, List, Tuple
import logging
from os import environ

# Layer imports
from orcabus_api_tools.workflow import add_comment_to_workflow_run

# Globals
WORKFLOW_NAME_ENV_VAR = "WORKFLOW_NAME"
WORKFLOW_NAME = environ[WORKFLOW_NAME_ENV_VAR]
COMMENT_AUTHOR = f"{WORKFLOW_NAME}-post-schema-validation-service"

# Expected tags fields
REQUIRED_TAG_FIELDS = [
    "libraryId",
    "subjectId",
    "individualId",
    "projectId",
    "fastqRgidList",
    "panelVersion",
    "instrumentRunId",
    "isIdentified",
    "sampleType",
]

# Expected dataFiles keys
REQUIRED_DATA_FILE_KEYS = [
    "cnvVcfUri",
    "fusionsUri",
    "tmbMetricsUri",
    "samplesheetUri",
    "metricsOutputUri",
    "microsatOutputUri",
    "hardFilteredVcfUri",
]

# Valid sample types
VALID_SAMPLE_TYPES = [
    "patientcare",
    "clinical_trial",
    "validation",
    "proficiency_testing",
    "assay_updates",
    "panel_review_sample",
]

# Required base case metadata fields
REQUIRED_BASE_CASE_METADATA_FIELDS = [
    "indication",
    "sampleType",
    "diseaseCode",
    "specimenCode",
    "externalSpecimenId",
    "caseAccessionNumber",
    "isIdentified",
]

# Required identified case metadata fields
REQUIRED_IDENTIFIED_CASE_METADATA_FIELDS = [
    "sampleReception",
    "patientInformation",
    "requestingPhysician",
    "medicalRecordNumbers",
]

# Comment formatting constants
MAX_COMMENT_LENGTH = 1024
TRUNCATION_SUFFIX = "\n... [truncated, see execution ARN for full detail]"

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def _format_comment_with_arn(body: str, execution_arn: str) -> str:
    """
    Append the execution ARN footer to a comment and enforce the 1024 char limit.
    """
    footer = f"---\nStep Functions Execution: {execution_arn}"
    full_comment = f"{body}\n{footer}"

    if len(full_comment) > MAX_COMMENT_LENGTH:
        available = MAX_COMMENT_LENGTH - len(footer) - len(TRUNCATION_SUFFIX) - 1
        full_comment = f"{body[:available]}{TRUNCATION_SUFFIX}\n{footer}"

    return full_comment


def validate_tags(tags: Dict) -> Tuple[bool, List[str]]:
    """
    Validate that data.tags has all required fields and correct types.

    :param tags: The tags dictionary from the event payload
    :return: Tuple of (is_valid, list of failure reasons)
    """
    failures: List[str] = []

    if not tags:
        failures.append("data.tags is missing or empty")
        return False, failures

    # Check required fields exist
    for field in REQUIRED_TAG_FIELDS:
        if field not in tags or tags[field] is None:
            failures.append(f"data.tags.{field} is missing or null")

    # Validate sampleType is a valid enum value
    sample_type = tags.get("sampleType")
    if sample_type is not None and sample_type not in VALID_SAMPLE_TYPES:
        failures.append(
            f"data.tags.sampleType '{sample_type}' is not a valid value. "
            f"Expected one of: {', '.join(VALID_SAMPLE_TYPES)}"
        )

    # Validate fastqRgidList is a non-empty list
    fastq_rgid_list = tags.get("fastqRgidList")
    if fastq_rgid_list is not None:
        if not isinstance(fastq_rgid_list, list):
            failures.append("data.tags.fastqRgidList must be a list")
        elif len(fastq_rgid_list) == 0:
            failures.append("data.tags.fastqRgidList must not be empty")

    # Validate isIdentified is boolean
    is_identified = tags.get("isIdentified")
    if is_identified is not None and not isinstance(is_identified, bool):
        failures.append("data.tags.isIdentified must be a boolean")

    is_valid = len(failures) == 0
    return is_valid, failures


def validate_case_metadata(case_metadata: Dict, is_identified: bool) -> Tuple[bool, List[str]]:
    """
    Validate that data.inputs.caseMetadata is well-formed.

    :param case_metadata: The caseMetadata dictionary from the event payload
    :param is_identified: Whether this is an identified sample (determines required fields)
    :return: Tuple of (is_valid, list of failure reasons)
    """
    failures: List[str] = []

    if not case_metadata:
        failures.append("data.inputs.caseMetadata is missing or empty")
        return False, failures

    # Validate base case metadata fields
    for field in REQUIRED_BASE_CASE_METADATA_FIELDS:
        if field not in case_metadata or case_metadata[field] is None:
            failures.append(f"data.inputs.caseMetadata.{field} is missing or null")

    # Validate sampleType in caseMetadata
    sample_type = case_metadata.get("sampleType")
    if sample_type is not None and sample_type not in VALID_SAMPLE_TYPES:
        failures.append(
            f"data.inputs.caseMetadata.sampleType '{sample_type}' is not valid. "
            f"Expected one of: {', '.join(VALID_SAMPLE_TYPES)}"
        )

    # Validate diseaseCode is a number
    disease_code = case_metadata.get("diseaseCode")
    if disease_code is not None and not isinstance(disease_code, (int, float)):
        failures.append("data.inputs.caseMetadata.diseaseCode must be a number")

    # Validate specimenCode is a number
    specimen_code = case_metadata.get("specimenCode")
    if specimen_code is not None and not isinstance(specimen_code, (int, float)):
        failures.append("data.inputs.caseMetadata.specimenCode must be a number")

    # If identified, check for required identified fields
    if is_identified:
        for field in REQUIRED_IDENTIFIED_CASE_METADATA_FIELDS:
            if field not in case_metadata or case_metadata[field] is None:
                failures.append(
                    f"data.inputs.caseMetadata.{field} is required for identified samples but is missing or null"
                )

        # Validate sub-structures if present
        patient_info = case_metadata.get("patientInformation", {})
        if patient_info:
            for required_field in ["firstName", "lastName", "dateOfBirth"]:
                if required_field not in patient_info or patient_info[required_field] is None:
                    failures.append(
                        f"data.inputs.caseMetadata.patientInformation.{required_field} is missing or null"
                    )

        sample_reception = case_metadata.get("sampleReception", {})
        if sample_reception:
            for required_field in ["dateReceived", "dateCollected", "dateAccessioned"]:
                if required_field not in sample_reception or sample_reception[required_field] is None:
                    failures.append(
                        f"data.inputs.caseMetadata.sampleReception.{required_field} is missing or null"
                    )

        requesting_physician = case_metadata.get("requestingPhysician", {})
        if requesting_physician:
            for required_field in ["firstName", "lastName"]:
                if required_field not in requesting_physician or requesting_physician[required_field] is None:
                    failures.append(
                        f"data.inputs.caseMetadata.requestingPhysician.{required_field} is missing or null"
                    )

    is_valid = len(failures) == 0
    return is_valid, failures


def validate_data_files(data_files: Dict) -> Tuple[bool, List[str]]:
    """
    Validate that data.inputs.dataFiles contains the expected file keys and
    that URI values have valid S3 URI format.

    :param data_files: The dataFiles dictionary from the event payload
    :return: Tuple of (is_valid, list of failure reasons)
    """
    failures: List[str] = []

    if not data_files:
        failures.append("data.inputs.dataFiles is missing or empty")
        return False, failures

    # Check required file keys exist
    for key in REQUIRED_DATA_FILE_KEYS:
        if key not in data_files or data_files[key] is None:
            failures.append(f"data.inputs.dataFiles.{key} is missing or null")
        elif not isinstance(data_files[key], str):
            failures.append(f"data.inputs.dataFiles.{key} must be a string")
        elif not data_files[key].startswith("s3://"):
            failures.append(
                f"data.inputs.dataFiles.{key} value '{data_files[key]}' is not a valid S3 URI (must start with s3://)"
            )

    is_valid = len(failures) == 0
    return is_valid, failures


def handler(event, context) -> Dict[str, bool]:
    """
    Post-schema validation for PierianDx TSO500 ctDNA pipeline.

    Validates:
      1. data.tags has required fields with correct types
      2. data.inputs.caseMetadata is well-formed (when present)
      3. data.inputs.dataFiles contains expected file keys with valid S3 URIs (when present)

    Input event:
      {
        "workflowRunId": "wfr.xxx",
        "data": {
          "tags": { "libraryId": "...", "sampleType": "...", ... },
          "inputs": {
            "caseMetadata": { ... },
            "dataFiles": { "cnvVcfUri": "s3://...", ... },
            ...
          }
        },
        "executionArn": "arn:aws:states:..."
      }

    Output:
      {"isValid": true}  — all checks pass
      {"isValid": false}  — at least one check failed (comments written)
    """
    # Get the event data
    payload_data = event.get("data", {})
    workflow_run_id = event.get("workflowRunId", "")
    execution_arn = event.get("executionArn", "")

    tags = payload_data.get("tags", {})
    inputs = payload_data.get("inputs", {})

    all_failures: List[str] = []

    # 1. Validate tags
    tags_valid, tags_failures = validate_tags(tags)
    if not tags_valid:
        all_failures.extend(tags_failures)

    # 2. Validate caseMetadata (when present in inputs)
    case_metadata = inputs.get("caseMetadata")
    if case_metadata is not None:
        # Determine if sample is identified from tags
        is_identified = tags.get("isIdentified", False)
        case_valid, case_failures = validate_case_metadata(case_metadata, is_identified)
        if not case_valid:
            all_failures.extend(case_failures)

    # 3. Validate dataFiles (when present in inputs)
    data_files = inputs.get("dataFiles")
    if data_files is not None:
        files_valid, files_failures = validate_data_files(data_files)
        if not files_valid:
            all_failures.extend(files_failures)

    # Handle failures
    if all_failures:
        logger.info(f"Post-schema validation failed with {len(all_failures)} issue(s)")

        if len(all_failures) == 1:
            add_comment_to_workflow_run(
                workflow_run_orcabus_id=workflow_run_id,
                comment=_format_comment_with_arn(
                    f"Post schema validation failed: {all_failures[0]}",
                    execution_arn,
                ),
                author=COMMENT_AUTHOR,
            )
        else:
            # Write summary comment
            add_comment_to_workflow_run(
                workflow_run_orcabus_id=workflow_run_id,
                comment=_format_comment_with_arn(
                    f"Post schema validation failed for {len(all_failures)} reasons",
                    execution_arn,
                ),
                author=COMMENT_AUTHOR,
            )
            # Write each failure as a separate numbered comment
            for idx, failure in enumerate(all_failures, start=1):
                add_comment_to_workflow_run(
                    workflow_run_orcabus_id=workflow_run_id,
                    comment=_format_comment_with_arn(
                        f"Reason {idx} of {len(all_failures)}: {failure}",
                        execution_arn,
                    ),
                    author=COMMENT_AUTHOR,
                )

        return {"isValid": False}

    logger.info("Post-schema validation passed")
    return {"isValid": True}

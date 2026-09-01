#!/usr/bin/env python3

"""
Get informatics job status

Given a case id and an informatics job id, return the status of the job

The job status can be one of the following:
* waiting  #  PROCESSING
* ready    #  PROCESSING
* running  #  PROCESSING
* complete #  TERMINAL
* failed   #  TERMINAL
* canceled #  TERMINAL

If the job is complete, check the reports for the case to see if the report generation is also complete

Also return the DynamoDB object to the expression reference and the object dict since
the object can vary depending on what status the job / report is at

job_status:  STR VALUE OF THE JOB STATUS
report_id:  INT VALUE OF THE REPORT ID
report_status: STR VALUE OF THE REPORT STATUS
report_status_bool: BOOL VALUE OF THE REPORT STATUS  TRUE IF COMPLETE, FALSE IF FAILED, NONE OTHERWISE
job_status_changed: BOOL VALUE OF WHETHER THE JOB STATUS HAS CHANGED TRUE OR FALSE
expression_attribute_values_dict: DICT OF THE EXPRESSION ATTRIBUTE VALUES FOR DYNAMODB UPDATE EXPRESSION
update_expression_str: STR OF THE UPDATE EXPRESSION FOR DYNAMODB

"""

# Standard imports
from os import environ
import logging

# Orcabus API tooling
from orcabus_api_tools.workflow import (
    get_workflow_run_from_portal_run_id,
    add_comment_to_workflow_run,
)
from orcabus_api_tools.utils.aws_helpers import get_ssm_value

# Layer imports
from pieriandx_tools.pieriandx_helpers import get_pieriandx_client

# Set logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Environment variables
MAX_ATTEMPTS_SSM_PARAMETER_NAME_ENV_VAR = "MAX_ATTEMPTS_SSM_PARAMETER_NAME"

# Comment author for workflow run comments posted by this service
COMMENT_AUTHOR = "pieriandx-monitoring-service"

# Maximum number of informatics job attempts (original + retries) before a run is marked FAILED.
# Read once from SSM at module load time.
MAX_ATTEMPTS = int(get_ssm_value(environ[MAX_ATTEMPTS_SSM_PARAMETER_NAME_ENV_VAR]))

REPORT_STATUS_BOOL = {
    "waiting": None,
    "ready": None,
    "running": None,
    "report_generation_complete": True,
    "complete": True,
    "failed": False,
    "canceled": False
}


def handler(event, context):
    """
    Get informatics job status
    Args:
        event:
        context:

    Returns:

    """
    # Setup
    pyriandx_client = get_pieriandx_client()

    # Get event values
    case_id = event.get("caseId", None)
    portal_run_id = event.get("portalRunId", None)
    max_retries = event.get("maxRetries", 1)

    # Get the case data
    case_data = pyriandx_client._get_api(
        endpoint=f"/case/{case_id}",
    )

    # Get the most recent job object in the case
    informatics_job_obj = sorted(
        case_data.get("informaticsJobs"),
        key=lambda x: int(x.get("id")),
        reverse=True
    )[0]

    # Get the job id
    job_id = informatics_job_obj.get("id")

    # Get job status
    job_status = informatics_job_obj.get("status")
    if job_status in ['waiting', 'ready']:
        return {
            "informaticsjobId": job_id,
            "status": "RUNNABLE",
            "reportId": -1,
        }
    if job_status in ['running', 'completed']:
        return {
            "informaticsjobId": job_id,
            "status": "RUNNING",
            "reportId": -1,
        }

    if job_status == "failed":
        if (max_retries + 1) < len(case_data.get("informaticsJobs")):
            # Write a comment on the workflow run,
            add_comment_to_workflow_run(
                workflow_run_orcabus_id=get_workflow_run_from_portal_run_id(cast(str, portal_run_id))['orcabusId'],
                comment=f"informatics job {job_id} has failed, retrying with a new job submission"
            )

            # Get the latest
            sequencerrun_run_id = case_data['sequencerRuns'][0]['runId']
            sequencerrun_specimen_object = case_data['sequencerRuns'][0]['specimens'][0]
            # Lets give this another go - rerun the job
            job_obj = pyriandx_client._post_api(
                endpoint=f"/case/{case_id}/informaticsJobs",
                data={
                    "input": [
                        {
                            "accessionNumber": case_data['specimens'][0]['accessionNumber'],
                            "sequencerRunInfos": [{
                                "runId": sequencerrun_run_id,
                                "barcode": sequencerrun_specimen_object['barcode'],
                                "lane": sequencerrun_specimen_object['lane'],
                                "sampleId": sequencerrun_specimen_object['sampleId'],
                                "sampleType": sequencerrun_specimen_object['sampleType'],
                            }]
                        }
                    ]
                }
            )

            # Get the new job id
            job_id = job_obj.json()['jobId']

            # Write a comment on the workflow run,
            add_comment_to_workflow_run(
                workflow_run_orcabus_id=get_workflow_run_from_portal_run_id(cast(str, portal_run_id))['orcabusId'],
                comment=f"New job id assigned, {job_id}"
            )

            return {
                "informaticsjobId": job_id,
                "status": "RUNNING",
                "reportId": -1,
            }

        else:
            return {
                "informaticsjobId": job_id,
                "status": "FAILED",
                "reportId": -1,
            }

    # If the job is complete, check the reports
    reports_list = sorted(
        (
            case_data.get("reports", None)
            if case_data.get("reports", None) is not None
            else []
        ),
        key=lambda x: int(x.get("id")),
        reverse=True
    )

    # No report generated yet
    if len(reports_list) == 0:
        return {
            "informaticsjobId": job_id,
            "status": "RUNNING",
            "reportId": -1,
        }

    # Get the most recent job object in the case
    reports_obj = sorted(
        case_data.get("reports"),
        key=lambda x: int(x.get("id")),
        reverse=True
    )[0]

    # Reassign - a new report may have been kicked off.
    report_id = reports_obj.get("id")

    if REPORT_STATUS_BOOL[reports_obj.get("status")]:
        return {
            "informaticsjobId": job_id,
            "status": "SUCCEEDED",
            "reportId": report_id,
        }

    return {
        "informaticsjobId": job_id,
        "status": "RUNNING",
        "reportId": report_id,
    }

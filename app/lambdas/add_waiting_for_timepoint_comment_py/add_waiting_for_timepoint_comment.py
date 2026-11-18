#!/usr/bin/env python3
"""
Add a workflow run comment stating that we are waiting for a timepoint to have completed
before generating the PierianDx case (see calculate_time_to_wait_before_generating_case).

Event shape:
{
    "workflowRunId": "<orcabus-id>",
    "latestTimestamp": "2025-09-25T16:35:48+10:00",
    "executionArn": "<step-functions-execution-arn>"
}

Returns:
{
    "commentAdded": true
}
"""
# Standard imports
from os import environ
from typing import Dict, Any

# Layer imports
from orcabus_api_tools.workflow import add_comment_to_workflow_run

# Globals
WORKFLOW_NAME_ENV_VAR = "WORKFLOW_NAME"
COMMENT_AUTHOR = "{workflow_name}-launch-pieriandx-service"
COMMENT_TEMPLATE = "Waiting until timepoint {latest_timestamp} has completed"


def handler(event: Dict[str, Any], context) -> Dict[str, bool]:
    workflow_run_id = event["workflowRunId"]
    latest_timestamp = event["latestTimestamp"]
    execution_arn = event.get("executionArn", "")

    workflow_name = environ.get(WORKFLOW_NAME_ENV_VAR, "unknown")

    comment = COMMENT_TEMPLATE.format(latest_timestamp=latest_timestamp)
    full_comment = f"{comment}\n---\nStep Functions Execution: {execution_arn}"

    add_comment_to_workflow_run(
        workflow_run_orcabus_id=workflow_run_id,
        comment=full_comment,
        author=COMMENT_AUTHOR.format(workflow_name=workflow_name),
    )

    return {"commentAdded": True}
